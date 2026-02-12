#!/usr/bin/env python3
"""
DashTrade API Server - REST API for React Frontend
Handles user authentication, bot management, and account operations
Runs as a separate service from the webhook server

Port: 8081 (default)
"""
from flask import Flask, request, jsonify, g
from flask_cors import CORS
import logging
import os
import jwt
import functools
import traceback
from datetime import datetime, timedelta

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import database modules with error handling
try:
    from bot_database import (
        BotConfigDB, WebhookTokenDB, SystemStrategyDB,
        UserStrategySubscriptionDB, BotAPIKeysDB, BotTradesDB,
        TradeMarketContextDB
    )
    from bot_engine import TradingEngine
    from auth import UserDB
    from database import get_db_connection
    from psycopg2.extras import RealDictCursor
    DB_AVAILABLE = True
    logger.info("Database modules imported successfully")
except Exception as e:
    DB_AVAILABLE = False
    logger.error(f"Failed to import database modules: {e}")
    logger.error(traceback.format_exc())

# Setup Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.environ.get('ENCRYPTION_KEY', 'dev-secret-key-change-in-production'))

# Enable CORS for React frontend (allow all origins for development)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Crypto symbol helpers
CRYPTO_SYMBOLS = {
    'BTC/USD': 'Bitcoin',
    'ETH/USD': 'Ethereum',
    'SOL/USD': 'Solana',
    'DOGE/USD': 'Dogecoin',
    'XRP/USD': 'Ripple',
    'ADA/USD': 'Cardano',
    'DOT/USD': 'Polkadot',
    'LINK/USD': 'Chainlink',
    'AVAX/USD': 'Avalanche',
    'MATIC/USD': 'Polygon',
    'SHIB/USD': 'Shiba Inu',
    'LTC/USD': 'Litecoin',
    'UNI/USD': 'Uniswap',
    'ATOM/USD': 'Cosmos',
    'XLM/USD': 'Stellar',
    'ALGO/USD': 'Algorand',
    'NEAR/USD': 'NEAR Protocol',
    'FTM/USD': 'Fantom',
    'AAVE/USD': 'Aave',
    'MKR/USD': 'Maker',
    'BCH/USD': 'Bitcoin Cash',
    'TRX/USD': 'TRON',
    'APE/USD': 'ApeCoin',
    'CRV/USD': 'Curve DAO',
    'GRT/USD': 'The Graph',
    'SUSHI/USD': 'SushiSwap',
    'BAT/USD': 'Basic Attention Token',
    'XTZ/USD': 'Tezos',
    'USDC/USD': 'USD Coin',
    'USDT/USD': 'Tether',
}


def is_crypto_symbol(symbol: str) -> bool:
    """Check if a symbol is a cryptocurrency"""
    if not symbol:
        return False
    symbol_upper = symbol.upper().strip()
    # Check if it's in our known crypto list
    if symbol_upper in CRYPTO_SYMBOLS:
        return True
    # Check for /USD suffix pattern
    if '/USD' in symbol_upper:
        return True
    # Check for common crypto without slash (e.g., BTCUSD)
    if symbol_upper.endswith('USD') and len(symbol_upper) >= 6:
        base = symbol_upper[:-3]
        if f"{base}/USD" in CRYPTO_SYMBOLS:
            return True
    return False


def normalize_crypto_symbol(symbol: str) -> str:
    """Normalize crypto symbol to Alpaca format (e.g., BTCUSD -> BTC/USD)"""
    if not symbol:
        return symbol
    symbol_upper = symbol.upper().strip()
    # Already in correct format
    if '/' in symbol_upper:
        return symbol_upper
    # Convert BTCUSD to BTC/USD
    if symbol_upper.endswith('USD') and len(symbol_upper) >= 6:
        base = symbol_upper[:-3]
        return f"{base}/USD"
    return symbol_upper


def get_crypto_name(symbol: str) -> str:
    """Get the name of a cryptocurrency from its symbol"""
    normalized = normalize_crypto_symbol(symbol)
    return CRYPTO_SYMBOLS.get(normalized, normalized.replace('/USD', ''))

# Run migrations on startup
try:
    from run_migrations import run_migrations
    run_migrations()
except Exception as e:
    logger.warning(f"Migration check skipped: {e}")

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# ============================================================================
# JWT AUTHENTICATION HELPERS
# ============================================================================

def generate_token(user_id: int, username: str, role: str) -> str:
    """Generate JWT token for authenticated user"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')


def verify_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    """Decorator to require valid JWT token"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Token is invalid or expired'}), 401

        g.user_id = payload['user_id']
        g.username = payload['username']
        g.role = payload['role']

        return f(*args, **kwargs)
    return decorated


def convert_decimals(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif hasattr(obj, '__float__'):
        return float(obj)
    return obj


# ============================================================================
# REST API - AUTHENTICATION
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """Register a new user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400

        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip() or None
        admin_code = data.get('admin_code', '').strip() or None

        if not username or not email or not password:
            return jsonify({'error': 'Username, email, and password are required'}), 400

        result = UserDB.register_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            admin_code=admin_code
        )

        if result['success']:
            # Generate token for the new user
            token = generate_token(result['user_id'], username, result.get('role', 'user'))
            return jsonify({
                'success': True,
                'message': 'Registration successful',
                'user_id': result['user_id'],
                'token': token
            }), 201
        else:
            return jsonify({'error': result.get('error', 'Registration failed')}), 400

    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Authenticate user and return JWT token"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400

        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        result = UserDB.authenticate_user(username, password)

        if result['success']:
            user = result['user']
            token = generate_token(user['id'], user['username'], user.get('role', 'user'))
            return jsonify({
                'success': True,
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'full_name': user.get('full_name'),
                    'role': user.get('role', 'user')
                }
            }), 200
        else:
            return jsonify({'error': result.get('error', 'Invalid credentials')}), 401

    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/auth/me', methods=['GET'])
@token_required
def api_get_current_user():
    """Get current authenticated user info"""
    try:
        user = UserDB.get_user_by_id(g.user_id)
        if user:
            return jsonify({
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user.get('full_name'),
                'role': user.get('role', 'user'),
                'created_at': user.get('created_at').isoformat() if user.get('created_at') else None
            }), 200
        return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        logger.error(f"Get user error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/auth/forgot-password', methods=['POST'])
def api_forgot_password():
    """
    Request password reset - sends email with reset link
    
    Body: { "email": "user@example.com" }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400
        
        email = data.get('email', '').strip().lower()
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Ensure password reset tokens table exists
        UserDB.create_password_reset_tokens_table()
        
        # Generate reset token
        result = UserDB.generate_password_reset_token(email)
        
        if not result['success']:
            # Don't reveal if email exists (security best practice)
            # Return success even if email doesn't exist to prevent email enumeration
            return jsonify({
                'success': True,
                'message': 'If the email exists, a password reset link has been sent'
            }), 200
        
        # Send email with reset link using SMTP2GO (same as trade emails)
        try:
            from email_service import EmailService

            reset_url = f"https://alert-to-action-bot.lovable.app/reset-password?token={result['token']}"

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f3f4f6; padding: 20px; }}
                    .container {{ max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); color: white; padding: 24px; text-align: center; }}
                    .header h1 {{ margin: 0; font-size: 24px; }}
                    .content {{ padding: 24px; }}
                    .reset-button {{ display: inline-block; background: #1976d2; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                    .reset-button:hover {{ background: #1565c0; }}
                    .footer {{ background: #f9fafb; padding: 16px 24px; text-align: center; color: #6b7280; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔐 Password Reset Request</h1>
                        <p style="margin: 8px 0 0 0; opacity: 0.9;">DashTrade</p>
                    </div>
                    <div class="content">
                        <p>Hello <strong>{result.get('username', 'User')}</strong>,</p>
                        <p>You requested to reset your password for your DashTrade account.</p>
                        <p>Click the button below to reset your password:</p>

                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{reset_url}" class="reset-button">Reset Password</a>
                        </div>

                        <p>Or copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; background: #f3f4f6; padding: 10px; border-radius: 4px; font-size: 12px; color: #1976d2;">
                            {reset_url}
                        </p>

                        <p style="margin-top: 20px;"><strong>⏰ This link will expire in 1 hour.</strong></p>
                    </div>
                    <div class="footer">
                        <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
                        <p>This is an automated notification from DashTrade.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_body = f"""
Password Reset Request - DashTrade

Hello {result.get('username', 'User')},

You requested to reset your password for your DashTrade account.

Click this link to reset your password:
{reset_url}

This link will expire in 1 hour.

If you didn't request a password reset, please ignore this email.

---
This is an automated notification from DashTrade.
            """

            # Use EmailService (SMTP2GO) instead of NotificationService (SMTP)
            email_result = EmailService.send_email(
                to_email=result['email'],
                subject='🔐 DashTrade Password Reset',
                html_body=html_body,
                text_body=text_body
            )

            if email_result['success']:
                logger.info(f"Password reset email sent to {result['email']}")
                return jsonify({
                    'success': True,
                    'message': 'If the email exists, a password reset link has been sent'
                }), 200
            else:
                logger.warning(f"Failed to send password reset email to {result['email']}: {email_result['message']}")
                return jsonify({
                    'success': False,
                    'error': 'Failed to send reset email. Please try again later.'
                }), 500

        except Exception as e:
            logger.error(f"Error sending password reset email: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Failed to send reset email. Please try again later.'
            }), 500
        
    except Exception as e:
        logger.error(f"Forgot password error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/auth/reset-password', methods=['POST'])
def api_reset_password():
    """
    Reset password using a valid reset token
    
    Body: { "token": "reset_token_here", "new_password": "new_password_here" }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400
        
        token = data.get('token', '').strip()
        new_password = data.get('new_password', '').strip()
        
        if not token:
            return jsonify({'error': 'Reset token is required'}), 400
        
        if not new_password:
            return jsonify({'error': 'New password is required'}), 400
        
        # Validate password length
        if len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Reset password
        result = UserDB.reset_password_with_token(token, new_password)
        
        if result['success']:
            logger.info(f"Password reset successful for token: {token[:10]}...")
            return jsonify({
                'success': True,
                'message': 'Password has been reset successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to reset password')
            }), 400
        
    except Exception as e:
        logger.error(f"Reset password error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# REST API - BOT MANAGEMENT
# ============================================================================

@app.route('/api/bots', methods=['GET'])
@token_required
def api_get_bots():
    """Get all bots for the authenticated user"""
    try:
        bots = BotConfigDB.get_user_bots(g.user_id)
        bots = convert_decimals(bots)

        # Build webhook URL for each bot
        webhook_base = os.environ.get('WEBHOOK_SERVER_URL', 'https://webhook.novalgo.org')
        if not webhook_base.startswith('http'):
            webhook_base = f"https://{webhook_base}"

        for bot in bots:
            if bot.get('webhook_token'):
                bot['webhook_url'] = f"{webhook_base}/webhook?token={bot['webhook_token']}"

                # Auto-generate TradingView setup info
                symbol = bot.get('symbol', '')
                timeframe = bot.get('timeframe', '')

                bot['tradingview_setup'] = {
                    # Basic message - minimum required fields
                    'basic_message': '{"action": "{{strategy.order.action}}", "symbol": "{{ticker}}", "timeframe": "{{interval}}"}',
                    # Exit signal (when strategy closes position)
                    'exit_message': '{"action": "CLOSE", "symbol": "{{ticker}}", "timeframe": "{{interval}}"}',
                    # Enhanced message with strategy params for AI learning
                    'ai_learning_message': '{"action": "{{strategy.order.action}}", "symbol": "{{ticker}}", "timeframe": "{{interval}}", "strategy_type": "momentum", "entry_indicator": "RSI", "rsi_value": {{rsi}}, "rsi_period": 14, "ma_fast": 9, "ma_slow": 21}',
                    # Instructions for TradingView
                    'instructions': [
                        "1. In TradingView, create an alert on your strategy",
                        "2. Set 'Webhook URL' to the webhook_url above",
                        "3. For basic alerts: Use 'basic_message' format",
                        "4. For AI learning: Use 'ai_learning_message' with your strategy params",
                        "5. For EXIT alerts: Use 'exit_message'",
                    ],
                    'ai_learning_params': {
                        'strategy_type': 'momentum, mean_reversion, breakout, scalp, trend_follow',
                        'entry_indicator': 'RSI, MACD, MA_cross, volume_breakout',
                        'rsi_value': 'Current RSI value (e.g., 28.5)',
                        'rsi_period': 'RSI period (default 14)',
                        'ma_fast': 'Fast MA period (e.g., 9)',
                        'ma_slow': 'Slow MA period (e.g., 21)',
                        'macd_value': 'Current MACD value',
                        'atr_value': 'Current ATR value',
                        'stop_loss': 'Stop loss percent (e.g., 1.5)',
                        'take_profit': 'Take profit percent (e.g., 3.0)',
                        'trend_short': 'Short-term trend: up, down, sideways',
                    },
                    'notes': {
                        'variables': '{{ticker}} = symbol, {{interval}} = timeframe, {{strategy.order.action}} = buy/sell',
                        'ai_benefit': 'Including strategy params helps AI learn which settings work best',
                        'timeframe_formats': 'System accepts: 5, 15, 60, D or 5min, 15min, 1h, 1d',
                    }
                }
            else:
                bot['webhook_url'] = None
                bot['tradingview_setup'] = None

        return jsonify({
            'bots': bots,
            'total': len(bots),
            'active': sum(1 for b in bots if b.get('is_active'))
        }), 200
    except Exception as e:
        logger.error(f"Get bots error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


def normalize_timeframe(tf: str) -> str:
    """
    Normalize timeframe to consistent format.
    Frontend sends: "1 Min", "5 Min", "15 Min", "1 Hour", "Daily"
    TradingView sends: "1", "5", "15", "60", "D"
    We store: "1min", "5min", "15min", "1h", "1d"
    """
    if not tf:
        return tf

    tf = str(tf).strip().lower()

    # Already in correct format
    if tf in ['1min', '5min', '15min', '30min', '45min', '1h', '2h', '4h', '1d', '1w', '1m']:
        return tf

    # Map various formats to our standard format
    mappings = {
        # Minutes - TradingView numeric
        '1': '1min', '5': '5min', '15': '15min', '30': '30min', '45': '45min',
        # Minutes - with "m" suffix
        '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min', '45m': '45min',
        # Minutes - with space (frontend format)
        '1 min': '1min', '5 min': '5min', '15 min': '15min', '30 min': '30min', '45 min': '45min',
        # Hours - TradingView numeric
        '60': '1h', '120': '2h', '240': '4h',
        # Hours - with "h" suffix
        '1h': '1h', '2h': '2h', '4h': '4h',
        # Hours - frontend format
        '1 hour': '1h', '2 hour': '2h', '4 hour': '4h',
        '1 hr': '1h', '2 hr': '2h', '4 hr': '4h',
        # Days/Weeks/Months
        'd': '1d', '1d': '1d', 'daily': '1d', 'day': '1d', '1 day': '1d',
        'w': '1w', '1w': '1w', 'weekly': '1w', 'week': '1w', '1 week': '1w',
        'm': '1m', '1m': '1m', 'monthly': '1m', 'month': '1m', '1 month': '1m',
    }

    return mappings.get(tf, tf)


def create_bots_batch(data: dict, symbols: list, timeframes: list = None):
    """
    Create multiple bots at once.

    Args:
        data: Request data with position_size, strategy_name, etc.
        symbols: List of symbols to create bots for
        timeframes: Optional list of timeframes (if not provided, uses single timeframe from data)

    Returns:
        JSON response with created bots
    """
    position_size = data.get('position_size')
    if not position_size:
        return jsonify({'error': 'position_size is required'}), 400

    try:
        position_size = float(position_size)
    except (ValueError, TypeError):
        return jsonify({'error': 'position_size must be a number'}), 400

    # Get timeframes list
    if not timeframes:
        single_tf = data.get('timeframe')
        if not single_tf:
            return jsonify({'error': 'timeframe or timeframes is required'}), 400
        timeframes = [single_tf]

    # Normalize all timeframes
    timeframes = [normalize_timeframe(tf) for tf in timeframes]

    # Clean up symbols
    symbols = [s.upper().strip() for s in symbols if s and s.strip()]

    if not symbols:
        return jsonify({'error': 'At least one symbol is required'}), 400

    created_bots = []
    errors = []

    # Create a bot for each symbol+timeframe combination
    for symbol in symbols:
        for timeframe in timeframes:
            try:
                bot_id = BotConfigDB.create_bot(
                    user_id=g.user_id,
                    symbol=symbol,
                    timeframe=timeframe,
                    position_size=position_size,
                    strategy_name=data.get('strategy_name'),
                    risk_limit_percent=float(data.get('risk_limit_percent', 10.0)),
                    daily_loss_limit=float(data['daily_loss_limit']) if data.get('daily_loss_limit') else None,
                    max_position_size=float(data['max_position_size']) if data.get('max_position_size') else None,
                    signal_source=data.get('signal_source', 'webhook')
                )

                if bot_id:
                    created_bots.append({
                        'id': bot_id,
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'position_size': position_size
                    })
                else:
                    errors.append({
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'error': 'Failed to create bot (may already exist)'
                    })
            except Exception as e:
                errors.append({
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'error': str(e)
                })

    # Get webhook URL for all bots (same for user)
    webhook_url = None
    token_data = WebhookTokenDB.get_user_token(g.user_id)
    if token_data:
        webhook_base = os.environ.get('WEBHOOK_SERVER_URL', 'https://webhook.novalgo.org')
        if not webhook_base.startswith('http'):
            webhook_base = f"https://{webhook_base}"
        webhook_url = f"{webhook_base}/webhook?token={token_data['token']}"

    return jsonify({
        'success': len(created_bots) > 0,
        'created_count': len(created_bots),
        'error_count': len(errors),
        'created_bots': created_bots,
        'errors': errors if errors else None,
        'webhook_url': webhook_url,
        'message': f"Created {len(created_bots)} bots" + (f" ({len(errors)} failed)" if errors else "")
    }), 201 if created_bots else 400


@app.route('/api/bots', methods=['POST'])
@token_required
def api_create_bot():
    """Create a new bot configuration (single or batch)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400

        # Check if batch creation (symbols array)
        symbols = data.get('symbols')
        timeframes = data.get('timeframes')

        if symbols and isinstance(symbols, list):
            # Batch creation mode
            return create_bots_batch(data, symbols, timeframes)

        # Single bot creation
        symbol = data.get('symbol', '').upper().strip()
        timeframe = normalize_timeframe(data.get('timeframe', ''))  # Normalize timeframe!
        position_size = data.get('position_size')

        if not symbol or not timeframe or not position_size:
            return jsonify({'error': 'symbol, timeframe, and position_size are required'}), 400

        try:
            position_size = float(position_size)
        except (ValueError, TypeError):
            return jsonify({'error': 'position_size must be a number'}), 400

        bot_id = BotConfigDB.create_bot(
            user_id=g.user_id,
            symbol=symbol,
            timeframe=timeframe,
            position_size=position_size,
            strategy_name=data.get('strategy_name'),
            risk_limit_percent=float(data.get('risk_limit_percent', 10.0)),
            daily_loss_limit=float(data['daily_loss_limit']) if data.get('daily_loss_limit') else None,
            max_position_size=float(data['max_position_size']) if data.get('max_position_size') else None,
            signal_source=data.get('signal_source', 'webhook')
        )

        if bot_id:
            # Get the created bot to retrieve its webhook token
            bots = BotConfigDB.get_user_bots(g.user_id)
            bot = next((b for b in bots if b['id'] == bot_id), None)

            webhook_url = None
            tradingview_setup = None

            if bot and bot.get('webhook_token'):
                webhook_base = os.environ.get('WEBHOOK_SERVER_URL', 'https://webhook.novalgo.org')
                if not webhook_base.startswith('http'):
                    webhook_base = f"https://{webhook_base}"
                webhook_url = f"{webhook_base}/webhook?token={bot['webhook_token']}"

                # Auto-generate TradingView setup info (fully dynamic with TradingView variables)
                tradingview_setup = {
                    'entry_message': '{"action": "{{strategy.order.action}}", "symbol": "{{ticker}}", "timeframe": "{{interval}}"}',
                    'exit_message': '{"action": "CLOSE", "symbol": "{{ticker}}", "timeframe": "{{interval}}"}',
                    'instructions': [
                        "1. In TradingView, create an alert on your strategy",
                        "2. Set 'Webhook URL' to the webhook_url above",
                        "3. For ENTRY alerts: Copy the 'entry_message' into the alert message",
                        "4. For EXIT alerts: Copy the 'exit_message' into the alert message",
                        "5. Check 'Webhook' checkbox to enable",
                    ],
                    'notes': {
                        'variables': '{{ticker}} = symbol, {{interval}} = timeframe, {{strategy.order.action}} = buy/sell',
                    }
                }

            return jsonify({
                'success': True,
                'bot_id': bot_id,
                'message': f'Bot created for {symbol} {timeframe}',
                'webhook_url': webhook_url,
                'tradingview_setup': tradingview_setup
            }), 201
        else:
            return jsonify({'error': 'Failed to create bot. May already exist for this symbol+timeframe.'}), 400

    except Exception as e:
        logger.error(f"Create bot error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/bots/<int:bot_id>', methods=['PUT'])
@token_required
def api_update_bot(bot_id):
    """Update a bot configuration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400

        # Build update dict with only provided fields
        updates = {}
        if 'position_size' in data:
            updates['position_size'] = float(data['position_size'])
        if 'strategy_name' in data:
            updates['strategy_name'] = data['strategy_name']
        if 'risk_limit_percent' in data:
            updates['risk_limit_percent'] = float(data['risk_limit_percent'])
        if 'daily_loss_limit' in data:
            updates['daily_loss_limit'] = float(data['daily_loss_limit']) if data['daily_loss_limit'] else None
        if 'max_position_size' in data:
            updates['max_position_size'] = float(data['max_position_size']) if data['max_position_size'] else None

        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400

        success = BotConfigDB.update_bot(bot_id, g.user_id, **updates)

        if success:
            return jsonify({'success': True, 'message': 'Bot updated'}), 200
        else:
            return jsonify({'error': 'Bot not found or update failed'}), 404

    except Exception as e:
        logger.error(f"Update bot error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/bots/<int:bot_id>', methods=['DELETE'])
@token_required
def api_delete_bot(bot_id):
    """Delete a bot configuration"""
    try:
        success = BotConfigDB.delete_bot(bot_id, g.user_id)

        if success:
            return jsonify({'success': True, 'message': 'Bot deleted'}), 200
        else:
            return jsonify({'error': 'Bot not found'}), 404

    except Exception as e:
        logger.error(f"Delete bot error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/bots/<int:bot_id>/toggle', methods=['POST'])
@token_required
def api_toggle_bot(bot_id):
    """Toggle bot active/inactive status"""
    try:
        # Use silent=True to handle empty request bodies
        data = request.get_json(silent=True) or {}
        is_active = data.get('is_active')

        if is_active is None:
            # Toggle - get current state and flip it
            bots = BotConfigDB.get_user_bots(g.user_id)
            bot = next((b for b in bots if b['id'] == bot_id), None)
            if not bot:
                return jsonify({'error': 'Bot not found'}), 404
            is_active = not bot.get('is_active', False)

        success = BotConfigDB.toggle_bot(bot_id, g.user_id, is_active)

        if success:
            return jsonify({
                'success': True,
                'is_active': is_active,
                'message': f"Bot {'activated' if is_active else 'deactivated'}"
            }), 200
        else:
            return jsonify({'error': 'Bot not found'}), 404

    except Exception as e:
        logger.error(f"Toggle bot error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/bots/<int:bot_id>/regenerate-token', methods=['POST'])
@token_required
def api_regenerate_bot_token(bot_id):
    """Regenerate webhook token for a specific bot"""
    try:
        new_token = BotConfigDB.regenerate_bot_webhook_token(bot_id, g.user_id)

        if new_token:
            webhook_base = os.environ.get('WEBHOOK_SERVER_URL', 'https://webhook.novalgo.org')
            if not webhook_base.startswith('http'):
                webhook_base = f"https://{webhook_base}"

            return jsonify({
                'success': True,
                'webhook_token': new_token,
                'webhook_url': f"{webhook_base}/webhook?token={new_token}",
                'webhook_payload': '{"action": "{{strategy.order.action}}"}',
                'message': 'Webhook token regenerated. Update your TradingView alert with the new URL.'
            }), 200
        else:
            return jsonify({'error': 'Bot not found or token regeneration failed'}), 404

    except Exception as e:
        logger.error(f"Regenerate bot token error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# REST API - ACCOUNT & POSITIONS
# ============================================================================

@app.route('/api/account', methods=['GET'])
@token_required
def api_get_account():
    """Get Alpaca account info for the authenticated user"""
    try:
        engine = TradingEngine(g.user_id)
        account = engine.get_account_info()
        return jsonify(convert_decimals(account)), 200
    except ValueError as e:
        return jsonify({'error': 'Alpaca API keys not configured', 'details': str(e)}), 400
    except Exception as e:
        logger.error(f"Get account error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch account info'}), 500


@app.route('/api/positions', methods=['GET'])
@token_required
def api_get_positions():
    """Get all open positions for the authenticated user"""
    try:
        engine = TradingEngine(g.user_id)
        positions = engine.get_all_positions()
        return jsonify({
            'positions': convert_decimals(positions),
            'total': len(positions)
        }), 200
    except ValueError as e:
        return jsonify({'error': 'Alpaca API keys not configured', 'details': str(e)}), 400
    except Exception as e:
        logger.error(f"Get positions error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch positions'}), 500


@app.route('/api/trades', methods=['GET'])
@token_required
def api_get_trades():
    """Get trade history for the authenticated user"""
    try:
        limit = request.args.get('limit', 50, type=int)
        symbol = request.args.get('symbol')
        
        # Auto-update pending CLOSE orders before returning trades
        # This ensures the frontend always sees the latest status
        try:
            from update_pending_orders import update_pending_close_orders
            # Only check orders from last 24 hours to avoid performance issues
            updated = update_pending_close_orders(user_id=g.user_id, hours_back=24)
            if updated > 0:
                logger.info(f"Auto-updated {updated} pending CLOSE orders for user {g.user_id}")
        except Exception as e:
            # Don't fail the request if update fails, just log it
            logger.warning(f"Failed to auto-update pending orders: {e}")

        trades = BotTradesDB.get_user_trades(g.user_id, limit=limit, symbol=symbol)
        trades = convert_decimals(trades)
        
        # Debug: Log trade counts by action
        buy_count = sum(1 for t in trades if t.get('action') == 'BUY')
        sell_count = sum(1 for t in trades if t.get('action') == 'SELL')
        close_count = sum(1 for t in trades if t.get('action') == 'CLOSE')
        logger.info(f"📊 Trades returned: BUY={buy_count}, SELL={sell_count}, CLOSE={close_count}, Total={len(trades)}")
        
        # Ensure all trades are included (no filtering)
        return jsonify({
            'trades': trades,
            'total': len(trades),
            'counts': {
                'buy': buy_count,
                'sell': sell_count,
                'close': close_count
            }
        }), 200
    except Exception as e:
        logger.error(f"Get trades error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/trades/recent', methods=['GET'])
@token_required
def api_get_recent_trades():
    """Get recent trades directly from Alpaca API (fixes $NaN issue)"""
    try:
        days = request.args.get('days', 7, type=int)
        limit = request.args.get('limit', 20, type=int)

        engine = TradingEngine(g.user_id)
        trades = engine.get_recent_trades(days=days, limit=limit)
        
        # Format trades for frontend
        formatted_trades = []
        for trade in trades:
            formatted_trades.append({
                'symbol': trade['symbol'],
                'side': trade['side'],
                'action': trade['side'],  # BUY/SELL/CLOSE
                'qty': trade['qty'],
                'price': trade['price'],
                'transaction_time': trade['transaction_time'].isoformat() if isinstance(trade['transaction_time'], datetime) else str(trade['transaction_time']),
                'order_id': trade.get('order_id'),
                'value': abs(trade['qty'] * trade['price'])
            })
        
        return jsonify({
            'trades': formatted_trades,
            'total': len(formatted_trades),
            'source': 'alpaca_api'
        }), 200
    except ValueError as e:
        return jsonify({'error': 'Alpaca API keys not configured', 'details': str(e)}), 400
    except Exception as e:
        logger.error(f"Get recent trades error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch recent trades'}), 500


@app.route('/api/trades/<int:trade_id>', methods=['GET'])
@token_required
def api_get_trade_detail(trade_id):
    """
    Get detailed trade information with full market context

    This endpoint returns comprehensive data captured at the time of trade execution:
    - Trade execution details (price, quantity, slippage, timing)
    - Stock data (OHLCV, volume, fundamentals)
    - Market indices (S&P 500, NASDAQ, DJI, Russell, VIX)
    - Treasury yields and yield curve
    - Sector ETF prices
    - Account and position context
    - Technical indicators (RSI, MAs)
    """
    try:
        # Auto-update pending CLOSE orders before returning trade details
        # This ensures the trade status is up-to-date
        try:
            from update_pending_orders import update_pending_close_orders
            # Check orders from last 24 hours (will include this trade if it's pending)
            update_pending_close_orders(user_id=g.user_id, hours_back=24)
        except Exception as e:
            # Don't fail the request if update fails, just log it
            logger.warning(f"Failed to auto-update pending orders: {e}")
        
        # Get trade with full market context
        trade = TradeMarketContextDB.get_trade_with_context(trade_id, g.user_id)

        if not trade:
            return jsonify({'error': 'Trade not found'}), 404

        trade = convert_decimals(trade)

        # Organize response into logical sections for frontend
        response = {
            'trade': {
                'id': trade.get('id'),
                'symbol': trade.get('symbol'),
                'timeframe': trade.get('timeframe'),
                'action': trade.get('action'),
                'status': trade.get('status'),
                'created_at': trade.get('created_at'),
                'filled_at': trade.get('filled_at'),
            },
            'execution': {
                'notional': trade.get('notional'),
                'filled_qty': trade.get('filled_qty'),
                'filled_avg_price': trade.get('filled_avg_price'),
                'expected_price': trade.get('expected_price'),
                'slippage': trade.get('slippage'),
                'slippage_percent': trade.get('slippage_percent'),
                'bid_price': trade.get('bid_price'),
                'ask_price': trade.get('ask_price'),
                'spread': trade.get('spread'),
                'spread_percent': trade.get('spread_percent'),
                'order_id': trade.get('order_id'),
                'order_type': trade.get('order_type'),
                'time_in_force': trade.get('time_in_force'),
            },
            'timing': {
                'signal_received_at': trade.get('signal_received_at'),
                'order_submitted_at': trade.get('order_submitted_at'),
                'execution_latency_ms': trade.get('execution_latency_ms'),
                'time_to_fill_ms': trade.get('time_to_fill_ms'),
                'market_open': trade.get('market_open'),
                'extended_hours': trade.get('extended_hours'),
                'signal_source': trade.get('signal_source'),
            },
            'stock': {
                'open': trade.get('stock_open'),
                'high': trade.get('stock_high'),
                'low': trade.get('stock_low'),
                'close': trade.get('stock_close'),
                'volume': trade.get('stock_volume'),
                'prev_close': trade.get('stock_prev_close'),
                'change_percent': trade.get('stock_change_percent'),
                'avg_volume': trade.get('stock_avg_volume'),
                'volume_ratio': trade.get('stock_volume_ratio'),
            },
            'fundamentals': {
                'market_cap': trade.get('market_cap'),
                'pe_ratio': trade.get('pe_ratio'),
                'forward_pe': trade.get('forward_pe'),
                'eps': trade.get('eps'),
                'beta': trade.get('beta'),
                'dividend_yield': trade.get('dividend_yield'),
                'shares_outstanding': trade.get('shares_outstanding'),
                'short_ratio': trade.get('short_ratio'),
                'fifty_two_week_high': trade.get('fifty_two_week_high'),
                'fifty_two_week_low': trade.get('fifty_two_week_low'),
                'fifty_day_ma': trade.get('fifty_day_ma'),
                'two_hundred_day_ma': trade.get('two_hundred_day_ma'),
            },
            'market_indices': {
                'sp500': {
                    'price': trade.get('sp500_price'),
                    'change_percent': trade.get('sp500_change_percent'),
                },
                'nasdaq': {
                    'price': trade.get('nasdaq_price'),
                    'change_percent': trade.get('nasdaq_change_percent'),
                },
                'dji': {
                    'price': trade.get('dji_price'),
                    'change_percent': trade.get('dji_change_percent'),
                },
                'russell': {
                    'price': trade.get('russell_price'),
                    'change_percent': trade.get('russell_change_percent'),
                },
                'vix': {
                    'price': trade.get('vix_price'),
                    'change_percent': trade.get('vix_change_percent'),
                },
            },
            'treasury': {
                'yield_10y': trade.get('treasury_10y_yield'),
                'yield_2y': trade.get('treasury_2y_yield'),
                'yield_curve_spread': trade.get('yield_curve_spread'),
            },
            'sector': {
                'etf_symbol': trade.get('sector_etf_symbol'),
                'etf_price': trade.get('sector_etf_price'),
                'etf_change_percent': trade.get('sector_etf_change_percent'),
                'sector_etfs': {
                    'XLK': trade.get('xlk_price'),
                    'XLF': trade.get('xlf_price'),
                    'XLE': trade.get('xle_price'),
                    'XLV': trade.get('xlv_price'),
                    'XLY': trade.get('xly_price'),
                    'XLP': trade.get('xlp_price'),
                    'XLI': trade.get('xli_price'),
                    'XLB': trade.get('xlb_price'),
                    'XLU': trade.get('xlu_price'),
                    'XLRE': trade.get('xlre_price'),
                },
            },
            'position': {
                'before': trade.get('position_before'),
                'after': trade.get('position_after'),
                'qty_before': trade.get('position_qty_before'),
                'value_before': trade.get('position_value_before'),
                'avg_entry': trade.get('position_avg_entry'),
                'unrealized_pl': trade.get('position_unrealized_pl'),
            },
            'account': {
                'equity': trade.get('account_equity'),
                'cash': trade.get('account_cash'),
                'buying_power': trade.get('account_buying_power'),
                'portfolio_value': trade.get('account_portfolio_value'),
                'total_positions_count': trade.get('total_positions_count'),
                'total_positions_value': trade.get('total_positions_value'),
            },
            'technical': {
                'rsi_14': trade.get('rsi_14'),
                'price_vs_50ma_percent': trade.get('price_vs_50ma_percent'),
                'price_vs_200ma_percent': trade.get('price_vs_200ma_percent'),
                'price_vs_52w_high_percent': trade.get('price_vs_52w_high_percent'),
                'price_vs_52w_low_percent': trade.get('price_vs_52w_low_percent'),
            },
            'metadata': {
                'context_fetch_latency_ms': trade.get('context_fetch_latency_ms'),
                'error_message': trade.get('error_message'),
            },
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Get trade detail error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# REST API - STOCK DATA (Alpaca Market Data)
# ============================================================================

@app.route('/api/stocks/quote', methods=['GET'])
@token_required
def api_get_stock_quote():
    """
    Get comprehensive stock/crypto quote data from Alpaca

    Query params:
        - symbol: Stock or crypto symbol (required)
                  Stocks: AAPL, TSLA, etc.
                  Crypto: BTC/USD, BTCUSD, ETH/USD, etc.

    Returns:
        - price, open, high, low, close, previousClose
        - volume, avgVolume
        - week52High, week52Low
        - change, changePercent
        - marketCap (from Yahoo Finance as backup)
        - is_crypto: true/false
    """
    try:
        symbol = request.args.get('symbol', '').upper().strip()

        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400

        # Check if this is a crypto symbol
        is_crypto = is_crypto_symbol(symbol)
        if is_crypto:
            symbol = normalize_crypto_symbol(symbol)

        # Import Alpaca data clients
        from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient
        from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest, StockLatestBarRequest
        from alpaca.data.requests import CryptoLatestQuoteRequest, CryptoBarsRequest, CryptoLatestBarRequest
        from alpaca.data.timeframe import TimeFrame
        from alpaca.trading.client import TradingClient

        # Get user's API keys
        keys = BotAPIKeysDB.get_api_keys(g.user_id)
        if not keys:
            return jsonify({'error': 'Alpaca API keys not configured'}), 400

        trading_client = TradingClient(keys['api_key'], keys['secret_key'], paper=(keys['mode'] == 'paper'))

        # Use appropriate data client based on asset type
        if is_crypto:
            data_client = CryptoHistoricalDataClient(keys['api_key'], keys['secret_key'])
        else:
            data_client = StockHistoricalDataClient(keys['api_key'], keys['secret_key'])

        result = {
            'symbol': symbol,
            'name': get_crypto_name(symbol) if is_crypto else symbol,
            'price': None,
            'open': None,
            'high': None,
            'low': None,
            'close': None,
            'previousClose': None,
            'volume': None,
            'avgVolume': None,
            'week52High': None,
            'week52Low': None,
            'change': None,
            'changePercent': None,
            'marketCap': None,
            'bid': None,
            'ask': None,
            'timestamp': None,
            'is_crypto': is_crypto,
            'asset_type': 'crypto' if is_crypto else 'stock'
        }

        # Get asset info (name) - for stocks
        if not is_crypto:
            try:
                asset = trading_client.get_asset(symbol)
                result['name'] = asset.name or symbol
                result['exchange'] = asset.exchange.value if asset.exchange else None
                result['tradable'] = asset.tradable
            except Exception as e:
                logger.warning(f"Could not get asset info for {symbol}: {e}")
        else:
            result['exchange'] = 'CRYPTO'
            result['tradable'] = True

        # Get latest quote (bid/ask)
        try:
            if is_crypto:
                quote_request = CryptoLatestQuoteRequest(symbol_or_symbols=symbol)
                quotes = data_client.get_crypto_latest_quote(quote_request)
            else:
                quote_request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
                quotes = data_client.get_stock_latest_quote(quote_request)

            if symbol in quotes:
                q = quotes[symbol]
                result['bid'] = float(q.bid_price) if q.bid_price else None
                result['ask'] = float(q.ask_price) if q.ask_price else None
                result['timestamp'] = q.timestamp.isoformat() if q.timestamp else None
                # Use mid price as current price
                if q.bid_price and q.ask_price:
                    result['price'] = round((float(q.bid_price) + float(q.ask_price)) / 2, 2)
        except Exception as e:
            logger.warning(f"Could not get quote for {symbol}: {e}")

        # Get latest bar (OHLCV)
        try:
            if is_crypto:
                bar_request = CryptoLatestBarRequest(symbol_or_symbols=symbol)
                bars = data_client.get_crypto_latest_bar(bar_request)
            else:
                bar_request = StockLatestBarRequest(symbol_or_symbols=symbol)
                bars = data_client.get_stock_latest_bar(bar_request)

            if symbol in bars:
                bar = bars[symbol]
                result['open'] = float(bar.open) if bar.open else None
                result['high'] = float(bar.high) if bar.high else None
                result['low'] = float(bar.low) if bar.low else None
                result['close'] = float(bar.close) if bar.close else None
                result['volume'] = float(bar.volume) if bar.volume else None
                # Use close as price if we don't have quote
                if result['price'] is None and bar.close:
                    result['price'] = float(bar.close)
        except Exception as e:
            logger.warning(f"Could not get bar for {symbol}: {e}")

        # Get comprehensive data from Yahoo Finance (more reliable for historical data)
        # Yahoo Finance provides 52-week high/low, previous close, market cap, etc.
        try:
            import yfinance as yf
            # Yahoo Finance uses different format for crypto (BTC-USD instead of BTC/USD)
            yf_symbol = symbol.replace('/', '-') if is_crypto else symbol
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info

            # 52-week high/low (Yahoo Finance has this directly)
            if info.get('fiftyTwoWeekHigh'):
                result['week52High'] = float(info['fiftyTwoWeekHigh'])
            if info.get('fiftyTwoWeekLow'):
                result['week52Low'] = float(info['fiftyTwoWeekLow'])

            # Previous close
            if info.get('previousClose'):
                result['previousClose'] = float(info['previousClose'])

            # If we have price and previousClose, calculate change
            if result['price'] and result['previousClose']:
                result['change'] = round(result['price'] - result['previousClose'], 2)
                result['changePercent'] = round((result['change'] / result['previousClose']) * 100, 2)

            # Average volume
            if info.get('averageVolume'):
                result['avgVolume'] = int(info['averageVolume'])

            # Market cap
            if info.get('marketCap'):
                result['marketCap'] = info['marketCap']

            # PE ratio
            if info.get('trailingPE'):
                result['peRatio'] = info['trailingPE']

            # Dividend yield
            if info.get('dividendYield'):
                result['dividendYield'] = info['dividendYield']

            # Day's open/high/low if not already set from Alpaca
            if result['open'] is None and info.get('open'):
                result['open'] = float(info['open'])
            if result['high'] is None and info.get('dayHigh'):
                result['high'] = float(info['dayHigh'])
            if result['low'] is None and info.get('dayLow'):
                result['low'] = float(info['dayLow'])

            # Current price from Yahoo if Alpaca didn't provide it
            if result['price'] is None:
                if info.get('currentPrice'):
                    result['price'] = float(info['currentPrice'])
                elif info.get('regularMarketPrice'):
                    result['price'] = float(info['regularMarketPrice'])

            # Volume from Yahoo if not set
            if result['volume'] is None and info.get('volume'):
                result['volume'] = int(info['volume'])

            # 50-day and 200-day moving averages (bonus data)
            if info.get('fiftyDayAverage'):
                result['fiftyDayMA'] = float(info['fiftyDayAverage'])
            if info.get('twoHundredDayAverage'):
                result['twoHundredDayMA'] = float(info['twoHundredDayAverage'])

            logger.info(f"Yahoo Finance data loaded for {symbol}: 52WH={result['week52High']}, 52WL={result['week52Low']}")

        except Exception as e:
            logger.warning(f"Could not get Yahoo Finance data for {symbol}: {e}")

        # Fallback: Try Alpaca historical data if Yahoo didn't work
        if result['week52High'] is None or result['week52Low'] is None:
            try:
                from datetime import datetime, timedelta
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)

                if is_crypto:
                    hist_request = CryptoBarsRequest(
                        symbol_or_symbols=symbol,
                        timeframe=TimeFrame.Day,
                        start=start_date,
                        end=end_date
                    )
                    hist_bars = data_client.get_crypto_bars(hist_request)
                else:
                    hist_request = StockBarsRequest(
                        symbol_or_symbols=symbol,
                        timeframe=TimeFrame.Day,
                        start=start_date,
                        end=end_date
                    )
                    hist_bars = data_client.get_stock_bars(hist_request)

                if symbol in hist_bars and len(hist_bars[symbol]) > 0:
                    bars_list = list(hist_bars[symbol])

                    # Calculate 52-week high/low
                    highs = [float(b.high) for b in bars_list if b.high]
                    lows = [float(b.low) for b in bars_list if b.low]
                    volumes = [int(b.volume) for b in bars_list if b.volume]

                    if highs and result['week52High'] is None:
                        result['week52High'] = max(highs)
                    if lows and result['week52Low'] is None:
                        result['week52Low'] = min(lows)
                    if volumes and result['avgVolume'] is None:
                        result['avgVolume'] = int(sum(volumes) / len(volumes))

                    # Get previous close (second to last bar)
                    if result['previousClose'] is None and len(bars_list) >= 2:
                        result['previousClose'] = float(bars_list[-2].close) if bars_list[-2].close else None

                    # Calculate change if not already done
                    if result['change'] is None and result['price'] and result['previousClose']:
                        result['change'] = round(result['price'] - result['previousClose'], 2)
                        result['changePercent'] = round((result['change'] / result['previousClose']) * 100, 2)
            except Exception as e:
                logger.warning(f"Could not get Alpaca historical data for {symbol}: {e}")

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Stock quote error: {e}", exc_info=True)
        return jsonify({'error': f'Failed to get quote: {str(e)}'}), 500


@app.route('/api/stocks/search', methods=['GET'])
@token_required
def api_search_stocks():
    """
    Search for stocks and crypto by symbol or name

    Query params:
        - query: Search query (required, min 1 character)
        - limit: Max results (default 10)
        - type: Filter by type: 'all', 'stock', 'crypto' (default 'all')

    Returns:
        - Array of {symbol, name, exchange, tradable, asset_type}
    """
    try:
        query = request.args.get('query', '').upper().strip()
        limit = int(request.args.get('limit', 10))
        asset_type_filter = request.args.get('type', 'all').lower()

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        if len(query) < 1:
            return jsonify({'results': []}), 200

        results = []

        # Search crypto symbols first (they match faster)
        if asset_type_filter in ['all', 'crypto']:
            for crypto_symbol, crypto_name in CRYPTO_SYMBOLS.items():
                # Match by symbol (BTC, ETH) or name (Bitcoin, Ethereum)
                base_symbol = crypto_symbol.replace('/USD', '')
                symbol_match = base_symbol.startswith(query) or crypto_symbol.startswith(query)
                name_match = query.lower() in crypto_name.lower()

                if symbol_match or name_match:
                    results.append({
                        'symbol': crypto_symbol,
                        'name': crypto_name,
                        'exchange': 'CRYPTO',
                        'tradable': True,
                        'asset_type': 'crypto'
                    })

        # Search stocks from Alpaca
        if asset_type_filter in ['all', 'stock']:
            try:
                from alpaca.trading.client import TradingClient
                from alpaca.trading.enums import AssetClass, AssetStatus

                keys = BotAPIKeysDB.get_api_keys(g.user_id)
                if keys:
                    trading_client = TradingClient(keys['api_key'], keys['secret_key'], paper=(keys['mode'] == 'paper'))
                    assets = trading_client.get_all_assets()

                    for asset in assets:
                        if len(results) >= limit * 2:  # Get extra for sorting
                            break

                        # Only include US equities that are tradeable
                        if asset.asset_class != AssetClass.US_EQUITY:
                            continue
                        if asset.status != AssetStatus.ACTIVE:
                            continue
                        if not asset.tradable:
                            continue

                        # Match by symbol prefix or name contains
                        symbol_match = asset.symbol.upper().startswith(query)
                        name_match = query.lower() in (asset.name or '').lower() if asset.name else False

                        if symbol_match or name_match:
                            results.append({
                                'symbol': asset.symbol,
                                'name': asset.name or asset.symbol,
                                'exchange': asset.exchange.value if asset.exchange else None,
                                'tradable': asset.tradable,
                                'asset_type': 'stock'
                            })
            except Exception as e:
                logger.warning(f"Error searching stock assets: {e}")

        # Sort: exact matches first, then crypto, then alphabetically
        results.sort(key=lambda x: (
            0 if x['symbol'].replace('/USD', '') == query else 1,
            0 if x['symbol'].startswith(query) else 1,
            0 if x['asset_type'] == 'crypto' else 1,  # Crypto first when typing partial
            x['symbol']
        ))

        return jsonify({'results': results[:limit]}), 200

    except Exception as e:
        logger.error(f"Stock search error: {e}", exc_info=True)
        return jsonify({'error': f'Search failed: {str(e)}'}), 500


@app.route('/api/stocks/popular', methods=['GET'])
def api_get_popular_stocks():
    """
    Get a list of popular stocks and crypto for quick selection
    No authentication required - returns static list

    Query params:
        - type: 'all', 'stock', 'crypto' (default 'all')
    """
    asset_type = request.args.get('type', 'all').lower()

    popular_stocks = [
        {'symbol': 'AAPL', 'name': 'Apple Inc.', 'asset_type': 'stock'},
        {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'asset_type': 'stock'},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'asset_type': 'stock'},
        {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'asset_type': 'stock'},
        {'symbol': 'TSLA', 'name': 'Tesla Inc.', 'asset_type': 'stock'},
        {'symbol': 'META', 'name': 'Meta Platforms Inc.', 'asset_type': 'stock'},
        {'symbol': 'NVDA', 'name': 'NVIDIA Corporation', 'asset_type': 'stock'},
        {'symbol': 'JPM', 'name': 'JPMorgan Chase & Co.', 'asset_type': 'stock'},
        {'symbol': 'V', 'name': 'Visa Inc.', 'asset_type': 'stock'},
        {'symbol': 'NFLX', 'name': 'Netflix Inc.', 'asset_type': 'stock'},
        {'symbol': 'AMD', 'name': 'Advanced Micro Devices', 'asset_type': 'stock'},
        {'symbol': 'SPY', 'name': 'SPDR S&P 500 ETF', 'asset_type': 'stock'},
        {'symbol': 'QQQ', 'name': 'Invesco QQQ Trust', 'asset_type': 'stock'},
    ]

    popular_crypto = [
        {'symbol': 'BTC/USD', 'name': 'Bitcoin', 'asset_type': 'crypto'},
        {'symbol': 'ETH/USD', 'name': 'Ethereum', 'asset_type': 'crypto'},
        {'symbol': 'SOL/USD', 'name': 'Solana', 'asset_type': 'crypto'},
        {'symbol': 'DOGE/USD', 'name': 'Dogecoin', 'asset_type': 'crypto'},
        {'symbol': 'XRP/USD', 'name': 'Ripple', 'asset_type': 'crypto'},
        {'symbol': 'ADA/USD', 'name': 'Cardano', 'asset_type': 'crypto'},
        {'symbol': 'AVAX/USD', 'name': 'Avalanche', 'asset_type': 'crypto'},
        {'symbol': 'LINK/USD', 'name': 'Chainlink', 'asset_type': 'crypto'},
        {'symbol': 'DOT/USD', 'name': 'Polkadot', 'asset_type': 'crypto'},
        {'symbol': 'MATIC/USD', 'name': 'Polygon', 'asset_type': 'crypto'},
        {'symbol': 'SHIB/USD', 'name': 'Shiba Inu', 'asset_type': 'crypto'},
        {'symbol': 'LTC/USD', 'name': 'Litecoin', 'asset_type': 'crypto'},
    ]

    if asset_type == 'stock':
        return jsonify({'stocks': popular_stocks}), 200
    elif asset_type == 'crypto':
        return jsonify({'stocks': popular_crypto}), 200
    else:
        # Return both, with crypto first for visibility
        return jsonify({'stocks': popular_crypto + popular_stocks}), 200


# ============================================================================
# REST API - SETTINGS (API KEYS)
# ============================================================================

@app.route('/api/settings/api-keys', methods=['POST'])
@token_required
def api_save_api_keys():
    """Save Alpaca API keys for the authenticated user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400

        api_key = data.get('api_key', '').strip()
        secret_key = data.get('secret_key', '').strip()
        mode = data.get('mode', 'paper').lower()

        if not api_key or not secret_key:
            return jsonify({'error': 'api_key and secret_key are required'}), 400

        if mode not in ['paper', 'live']:
            return jsonify({'error': 'mode must be "paper" or "live"'}), 400

        success = BotAPIKeysDB.save_api_keys(g.user_id, api_key, secret_key, mode)

        if success:
            return jsonify({
                'success': True,
                'message': f'API keys saved ({mode} mode)'
            }), 200
        else:
            return jsonify({'error': 'Failed to save API keys'}), 500

    except Exception as e:
        logger.error(f"Save API keys error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/settings/api-keys/status', methods=['GET'])
@token_required
def api_get_api_keys_status():
    """Check if user has Alpaca API keys configured"""
    try:
        keys = BotAPIKeysDB.get_api_keys(g.user_id)

        if keys:
            return jsonify({
                'configured': True,
                'mode': keys.get('mode', 'paper'),
                'is_active': keys.get('is_active', True)
            }), 200
        else:
            return jsonify({
                'configured': False,
                'mode': None,
                'is_active': False
            }), 200

    except Exception as e:
        logger.error(f"Get API keys status error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# REST API - WEBHOOK TOKEN
# ============================================================================

@app.route('/api/webhook-token', methods=['GET'])
@token_required
def api_get_webhook_token():
    """Get user's webhook token and URL"""
    try:
        # get_user_token returns just the token string, not a dict
        token = WebhookTokenDB.get_user_token(g.user_id)

        if not token:
            # Create token if doesn't exist - method is generate_token
            token = WebhookTokenDB.generate_token(g.user_id)

        if not token:
            return jsonify({'error': 'Failed to get or create webhook token'}), 500

        # Build webhook URL - use WEBHOOK_SERVER_URL for the separate webhook service
        webhook_base = os.environ.get('WEBHOOK_SERVER_URL') or os.environ.get('RAILWAY_PUBLIC_DOMAIN') or os.environ.get('BASE_URL') or request.host_url.rstrip('/')
        if not webhook_base.startswith('http'):
            webhook_base = f"https://{webhook_base}"

        webhook_url = f"{webhook_base}/webhook?token={token}"

        return jsonify({
            'token': token,
            'webhook_url': webhook_url
        }), 200

    except Exception as e:
        logger.error(f"Get webhook token error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/webhook-token/regenerate', methods=['POST'])
@token_required
def api_regenerate_webhook_token():
    """Regenerate user's webhook token"""
    try:
        # generate_token with existing user will update the token
        new_token = WebhookTokenDB.generate_token(g.user_id)

        if new_token:
            webhook_base = os.environ.get('WEBHOOK_SERVER_URL') or os.environ.get('RAILWAY_PUBLIC_DOMAIN') or os.environ.get('BASE_URL') or request.host_url.rstrip('/')
            if not webhook_base.startswith('http'):
                webhook_base = f"https://{webhook_base}"

            return jsonify({
                'success': True,
                'token': new_token,
                'webhook_url': f"{webhook_base}/webhook?token={new_token}"
            }), 200
        else:
            return jsonify({'error': 'Failed to regenerate token'}), 500

    except Exception as e:
        logger.error(f"Regenerate token error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# REST API - DASHBOARD SUMMARY
# ============================================================================

@app.route('/api/dashboard', methods=['GET'])
@token_required
def api_get_dashboard():
    """Get dashboard summary for the authenticated user"""
    try:
        # Get bots
        bots = BotConfigDB.get_user_bots(g.user_id)
        active_bots = sum(1 for b in bots if b.get('is_active'))

        # Get recent trades from database (for bot tracking)
        db_trades = BotTradesDB.get_user_trades(g.user_id, limit=10)

        # Try to get account info and recent trades from Alpaca (may fail if no API keys)
        account = None
        positions = []
        recent_trades_alpaca = []
        try:
            engine = TradingEngine(g.user_id)
            account = engine.get_account_info()
            positions = engine.get_all_positions()
            # Get recent trades directly from Alpaca API (fixes $NaN issue)
            recent_trades_alpaca = engine.get_recent_trades(days=7, limit=10)
            # Format for frontend
            for trade in recent_trades_alpaca:
                trade['transaction_time'] = trade['transaction_time'].isoformat() if isinstance(trade['transaction_time'], datetime) else str(trade['transaction_time'])
                trade['value'] = abs(trade['qty'] * trade['price'])
        except:
            pass

        # Calculate total P&L from all bots
        total_pnl = sum(float(bot.get('total_pnl', 0) or 0) for bot in bots)
        total_trades = sum(bot.get('total_trades', 0) or 0 for bot in bots)
        
        # Calculate realized P&L from closed trades (CLOSE orders with realized_pnl)
        realized_pnl = 0.0
        for trade in db_trades:
            if trade.get('action') == 'CLOSE' and trade.get('realized_pnl') is not None:
                realized_pnl += float(trade.get('realized_pnl', 0) or 0)

        return jsonify(convert_decimals({
            'account': account,
            'positions': positions,
            'bots': {
                'total': len(bots),
                'active': active_bots,
                'total_pnl': total_pnl,
                'total_trades': total_trades
            },
            'pnl': {
                'total_pnl': total_pnl,
                'realized_pnl': realized_pnl,
                'unrealized_pnl': sum(float(p.get('unrealized_pl', 0) or 0) for p in positions) if positions else 0.0
            },
            'recent_trades': recent_trades_alpaca[:5] if recent_trades_alpaca else db_trades[:5],  # Prefer Alpaca, fallback to DB
            'recent_trades_source': 'alpaca' if recent_trades_alpaca else 'database',
            'api_keys_configured': account is not None
        })), 200

    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# REST API - SYSTEM STRATEGIES (for subscription)
# ============================================================================

@app.route('/api/strategies', methods=['GET'])
@token_required
def api_get_strategies():
    """Get all available system strategies"""
    try:
        strategies = SystemStrategyDB.get_all_strategies(active_only=True)
        strategies = convert_decimals(strategies)

        # Get user's subscriptions
        subscriptions = UserStrategySubscriptionDB.get_user_subscriptions(g.user_id)
        subscribed_ids = {s['strategy_id'] for s in subscriptions}

        for strategy in strategies:
            strategy['is_subscribed'] = strategy['id'] in subscribed_ids

        return jsonify({
            'strategies': strategies,
            'total': len(strategies)
        }), 200
    except Exception as e:
        logger.error(f"Get strategies error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/strategies/<int:strategy_id>/subscribe', methods=['POST'])
@token_required
def api_subscribe_strategy(strategy_id):
    """Subscribe to a system strategy"""
    try:
        data = request.get_json() or {}
        bot_config_id = data.get('bot_config_id')

        if not bot_config_id:
            return jsonify({'error': 'bot_config_id is required'}), 400

        # Verify bot belongs to user
        bots = BotConfigDB.get_user_bots(g.user_id)
        bot = next((b for b in bots if b['id'] == bot_config_id), None)
        if not bot:
            return jsonify({'error': 'Bot not found'}), 404

        success = UserStrategySubscriptionDB.subscribe(g.user_id, strategy_id, bot_config_id)

        if success:
            return jsonify({
                'success': True,
                'message': 'Subscribed to strategy'
            }), 200
        else:
            return jsonify({'error': 'Failed to subscribe'}), 400

    except Exception as e:
        logger.error(f"Subscribe error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/strategies/<int:strategy_id>/unsubscribe', methods=['POST'])
@token_required
def api_unsubscribe_strategy(strategy_id):
    """Unsubscribe from a system strategy"""
    try:
        success = UserStrategySubscriptionDB.unsubscribe(g.user_id, strategy_id)

        if success:
            return jsonify({
                'success': True,
                'message': 'Unsubscribed from strategy'
            }), 200
        else:
            return jsonify({'error': 'Subscription not found'}), 404

    except Exception as e:
        logger.error(f"Unsubscribe error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# STRATEGY PERFORMANCE & AI INSIGHTS
# ============================================================================

@app.route('/api/performance', methods=['GET'])
@token_required
def api_get_performance():
    """
    Get strategy performance metrics for the authenticated user

    Query params:
        - strategy_type: Filter by strategy type (optional)
        - symbol: Filter by symbol (optional)
        - timeframe: Filter by timeframe (optional)
    """
    try:
        from bot_database import StrategyPerformanceDB

        strategy_type = request.args.get('strategy_type')
        symbol = request.args.get('symbol')
        timeframe = request.args.get('timeframe')

        # Get overall performance
        summary = StrategyPerformanceDB.calculate_performance(
            user_id=g.user_id,
            strategy_type=strategy_type,
            symbol=symbol,
            timeframe=timeframe
        )
        summary = convert_decimals(summary)

        # Get performance by indicator
        by_indicator = StrategyPerformanceDB.get_performance_by_indicator(g.user_id, min_trades=5)
        by_indicator = convert_decimals(by_indicator)

        # Get performance by market condition
        by_market = StrategyPerformanceDB.get_performance_by_market_condition(g.user_id, min_trades=5)
        by_market = convert_decimals(by_market)

        return jsonify({
            'summary': summary,
            'by_indicator': by_indicator,
            'by_market_condition': by_market
        }), 200

    except Exception as e:
        logger.error(f"Get performance error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/trades/recalculate-pnl', methods=['POST'])
@token_required
def api_recalculate_pnl():
    """
    Recalculate P&L for CLOSE orders using FIFO method
    
    Query params:
        - trade_id: Specific trade ID (optional, if not provided, recalculates all)
        - days: Days back to check (default: 30)
    """
    try:
        from fix_pnl_calculation import recalculate_close_order_pnl, fix_all_close_orders_pnl
        
        trade_id = request.args.get('trade_id', type=int)
        days = request.args.get('days', 30, type=int)
        
        if trade_id:
            pnl = recalculate_close_order_pnl(trade_id)
            if pnl is not None:
                return jsonify({
                    'success': True,
                    'trade_id': trade_id,
                    'realized_pnl': pnl,
                    'message': f'Recalculated P&L for trade {trade_id}'
                }), 200
            else:
                return jsonify({'error': 'Failed to recalculate P&L'}), 400
        else:
            fixed_count = fix_all_close_orders_pnl(user_id=g.user_id, days_back=days)
            return jsonify({
                'success': True,
                'updated': fixed_count,
                'message': f'Recalculated P&L for {fixed_count} trades'
            }), 200
        
    except Exception as e:
        logger.error(f"Recalculate P&L error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/trades/update-pending', methods=['POST'])
@token_required
def api_update_pending_orders():
    """
    Manually check and update pending CLOSE orders that may have filled
    
    This endpoint checks all pending CLOSE orders for the authenticated user
    and updates them if they've been filled on Alpaca.
    """
    try:
        from update_pending_orders import update_pending_close_orders
        
        hours_back = request.args.get('hours', 24, type=int)
        updated_count = update_pending_close_orders(user_id=g.user_id, hours_back=hours_back)
        
        return jsonify({
            'success': True,
            'updated': updated_count,
            'message': f'Updated {updated_count} pending orders'
        }), 200
        
    except Exception as e:
        logger.error(f"Update pending orders error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/trades/statistics', methods=['GET'])
@token_required
def api_get_trade_statistics():
    """Get trade statistics (counts by action type: BUY, SELL, CLOSE)"""
    try:
        # Get stats for the authenticated user
        stats = BotTradesDB.get_trade_statistics(user_id=g.user_id)
        return jsonify(convert_decimals(stats)), 200
    except Exception as e:
        logger.error(f"Get trade statistics error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/trades/outcomes', methods=['GET'])
@token_required
def api_get_trade_outcomes():
    """
    Get trade outcomes (P&L) for the authenticated user

    Query params:
        - status: 'open', 'closed', or all (optional)
        - limit: Number of results (default 50)
    """
    try:
        from bot_database import TradeOutcomesDB

        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))

        outcomes = TradeOutcomesDB.get_user_outcomes(g.user_id, status=status, limit=limit)
        outcomes = convert_decimals(outcomes)

        # Calculate summary stats
        closed_outcomes = [o for o in outcomes if o.get('status') == 'closed']
        total_pnl = sum(o.get('pnl_dollars', 0) or 0 for o in closed_outcomes)
        winning = sum(1 for o in closed_outcomes if o.get('is_winner'))
        losing = len(closed_outcomes) - winning

        return jsonify({
            'outcomes': outcomes,
            'summary': {
                'total_trades': len(closed_outcomes),
                'winning_trades': winning,
                'losing_trades': losing,
                'win_rate': (winning / len(closed_outcomes) * 100) if closed_outcomes else 0,
                'total_pnl': total_pnl
            }
        }), 200

    except Exception as e:
        logger.error(f"Get outcomes error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/insights', methods=['GET'])
@token_required
def api_get_insights():
    """
    Get AI-discovered strategy insights

    Query params:
        - symbol: Filter by symbol (optional)
        - strategy_type: Filter by strategy type (optional)
        - min_confidence: Minimum confidence score (default 50)
    """
    try:
        from bot_database import AIStrategyInsightsDB

        symbol = request.args.get('symbol')
        strategy_type = request.args.get('strategy_type')
        min_confidence = float(request.args.get('min_confidence', 50))

        insights = AIStrategyInsightsDB.get_active_insights(
            symbol=symbol,
            strategy_type=strategy_type,
            min_confidence=min_confidence
        )
        insights = convert_decimals(insights)

        return jsonify({
            'insights': insights,
            'total': len(insights)
        }), 200

    except Exception as e:
        logger.error(f"Get insights error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/analyze', methods=['POST'])
@token_required
def api_run_analysis():
    """
    Run AI analysis on trading data and generate insights

    This endpoint uses the hybrid AI approach:
    1. SQL queries to detect statistical patterns (RSI, VIX, timeframe, etc.)
    2. Claude API to generate natural language insights and recommendations
    3. Stores insights in the database for retrieval via /api/insights

    Request body (optional):
        - min_trades: Minimum trades required for pattern significance (default 10)
        - analyze_all: If true, analyze all users' data (admin only)

    Returns:
        - insights_generated: Number of insights generated
        - insights_saved: Number successfully saved to database
        - insights: Array of generated insights with title, description, recommendations
    """
    try:
        from ai_strategy_analyzer import AIStrategyAnalyzer

        data = request.get_json(silent=True) or {}
        min_trades = int(data.get('min_trades', 10))

        # Only admin can analyze all data
        analyze_all = data.get('analyze_all', False) and g.role == 'admin'
        user_id = None if analyze_all else g.user_id

        # Initialize analyzer
        analyzer = AIStrategyAnalyzer()

        # Check if we have enough data
        overall_stats = analyzer.get_overall_stats(user_id)
        total_trades = overall_stats.get('total_trades', 0)

        if total_trades < min_trades:
            return jsonify({
                'success': False,
                'error': f'Not enough trades for analysis. Have {total_trades}, need {min_trades}.',
                'total_trades': total_trades,
                'min_required': min_trades
            }), 400

        # Run full analysis
        insights = analyzer.run_full_analysis(user_id=user_id, min_trades=min_trades)

        # Save insights to database
        saved = analyzer.save_insights_to_db(insights, user_id=user_id) if insights else 0

        return jsonify({
            'success': True,
            'insights_generated': len(insights),
            'insights_saved': saved,
            'total_trades_analyzed': total_trades,
            'overall_stats': convert_decimals(overall_stats),
            'insights': convert_decimals(insights),
            'claude_api_used': analyzer.client is not None
        }), 200

    except Exception as e:
        logger.error(f"AI analysis error: {e}", exc_info=True)
        return jsonify({'error': 'Analysis failed', 'details': str(e)}), 500


@app.route('/api/analyze/patterns', methods=['GET'])
@token_required
def api_get_patterns():
    """
    Get raw pattern data without AI processing

    This is useful for viewing the statistical patterns directly
    without Claude API interpretation.

    Query params:
        - pattern_type: 'rsi', 'vix', 'timeframe', 'time_of_day', 'trend', or 'all'
        - min_trades: Minimum trades for significance (default 10)
    """
    try:
        from ai_strategy_analyzer import AIStrategyAnalyzer

        pattern_type = request.args.get('pattern_type', 'all')
        min_trades = int(request.args.get('min_trades', 10))

        analyzer = AIStrategyAnalyzer()
        patterns = {}

        if pattern_type in ['rsi', 'all']:
            patterns['rsi'] = analyzer.get_performance_by_rsi_threshold(g.user_id, min_trades)

        if pattern_type in ['vix', 'all']:
            patterns['vix'] = analyzer.get_performance_by_vix_level(g.user_id, min_trades)

        if pattern_type in ['timeframe', 'all']:
            patterns['timeframe'] = analyzer.get_performance_by_timeframe(g.user_id, min_trades)

        if pattern_type in ['time_of_day', 'all']:
            patterns['time_of_day'] = analyzer.get_performance_by_time_of_day(g.user_id, min_trades)

        if pattern_type in ['trend', 'all']:
            patterns['trend'] = analyzer.get_performance_by_trend(g.user_id, min_trades)

        # Get overall stats
        overall = analyzer.get_overall_stats(g.user_id)

        return jsonify({
            'overall_stats': convert_decimals(overall),
            'patterns': convert_decimals(patterns),
            'min_trades_filter': min_trades
        }), 200

    except Exception as e:
        logger.error(f"Get patterns error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# REST API - NOTIFICATION SETTINGS
# ============================================================================

@app.route('/api/settings/notifications', methods=['GET'])
@token_required
def api_get_notification_settings():
    """Get user's email notification preferences"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT email, email_notifications_enabled, notify_on_trade,
                           notify_on_error, notify_on_risk_event, notify_daily_summary
                    FROM users WHERE id = %s
                """, (g.user_id,))
                user = cur.fetchone()

                if not user:
                    return jsonify({'error': 'User not found'}), 404

                return jsonify({
                    'email': user['email'],
                    'email_notifications_enabled': user.get('email_notifications_enabled', False),
                    'notify_on_trade': user.get('notify_on_trade', True),
                    'notify_on_error': user.get('notify_on_error', True),
                    'notify_on_risk_event': user.get('notify_on_risk_event', True),
                    'notify_daily_summary': user.get('notify_daily_summary', False)
                }), 200

    except Exception as e:
        logger.error(f"Get notification settings error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/settings/notifications', methods=['PUT'])
@token_required
def api_update_notification_settings():
    """Update user's email notification preferences"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400

        # Build update query dynamically
        updates = []
        params = []

        if 'email_notifications_enabled' in data:
            updates.append('email_notifications_enabled = %s')
            params.append(bool(data['email_notifications_enabled']))

        if 'notify_on_trade' in data:
            updates.append('notify_on_trade = %s')
            params.append(bool(data['notify_on_trade']))

        if 'notify_on_error' in data:
            updates.append('notify_on_error = %s')
            params.append(bool(data['notify_on_error']))

        if 'notify_on_risk_event' in data:
            updates.append('notify_on_risk_event = %s')
            params.append(bool(data['notify_on_risk_event']))

        if 'notify_daily_summary' in data:
            updates.append('notify_daily_summary = %s')
            params.append(bool(data['notify_daily_summary']))

        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400

        params.append(g.user_id)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE users SET {', '.join(updates)}
                    WHERE id = %s
                """, params)
                conn.commit()

        return jsonify({
            'success': True,
            'message': 'Notification settings updated'
        }), 200

    except Exception as e:
        logger.error(f"Update notification settings error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/settings/notifications/test', methods=['POST'])
@token_required
def api_test_notification():
    """Send a test email to verify notification setup"""
    try:
        from email_service import EmailService, TradeNotificationService

        if not EmailService.is_configured():
            return jsonify({
                'success': False,
                'error': 'Email service not configured (SMTP2GO_API_KEY missing)'
            }), 400

        # Get user settings
        settings = TradeNotificationService.get_user_notification_settings(g.user_id)
        if not settings or not settings.get('email'):
            return jsonify({
                'success': False,
                'error': 'No email address found for user'
            }), 400

        # Send test email
        test_html = """
        <div style="font-family: sans-serif; padding: 20px;">
            <h2>DashTrade Test Notification</h2>
            <p>This is a test email to confirm your notification settings are working correctly.</p>
            <p>You will receive emails for:</p>
            <ul>
                <li>Trade executions (when enabled)</li>
                <li>Trade errors (when enabled)</li>
                <li>Risk events (when enabled)</li>
            </ul>
            <p>You can manage these settings in the DashTrade app.</p>
        </div>
        """

        result = EmailService.send_email(
            to_email=settings['email'],
            subject='DashTrade - Test Notification',
            html_body=test_html
        )

        if result['success']:
            return jsonify({
                'success': True,
                'message': f"Test email sent to {settings['email']}"
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('message', 'Failed to send test email')
            }), 500

    except Exception as e:
        logger.error(f"Test notification error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/debug/trade/<int:trade_id>', methods=['GET'])
def api_debug_trade(trade_id):
    """Debug endpoint to check trade and market context data (no auth for debugging)"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get trade
                cur.execute("SELECT * FROM bot_trades WHERE id = %s", (trade_id,))
                trade = cur.fetchone()

                # Get market context
                cur.execute("SELECT * FROM trade_market_context WHERE trade_id = %s", (trade_id,))
                context = cur.fetchone()

                return jsonify({
                    'trade_exists': trade is not None,
                    'trade': convert_decimals(dict(trade)) if trade else None,
                    'market_context_exists': context is not None,
                    'market_context': convert_decimals(dict(context)) if context else None,
                    'user_id_in_trade': trade.get('user_id') if trade else None
                }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/debug/user/<int:user_id>/trades', methods=['GET'])
def api_debug_user_trades(user_id):
    """Debug endpoint to check all trades for a user (no auth for debugging)"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, symbol, action, status, filled_qty, filled_avg_price,
                           notional, created_at, timeframe
                    FROM bot_trades
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
                trades = [dict(row) for row in cur.fetchall()]

                # Also check user exists
                cur.execute("SELECT id, username, email FROM users WHERE id = %s", (user_id,))
                user = cur.fetchone()

                return jsonify({
                    'user_exists': user is not None,
                    'user': dict(user) if user else None,
                    'total_trades': len(trades),
                    'trades': convert_decimals(trades)
                }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/debug/whoami', methods=['GET'])
@token_required
def api_debug_whoami():
    """Debug endpoint to verify JWT token resolves to correct user"""
    return jsonify({
        'user_id_from_token': g.user_id,
        'username': g.username,
        'email': g.email,
        'role': g.role
    }), 200


@app.route('/api/debug/user/<int:user_id>/bots', methods=['GET'])
def api_debug_user_bots(user_id):
    """Debug endpoint to check all bots for a user"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, symbol, timeframe, position_size, is_active,
                           signal_source, strategy_name, created_at
                    FROM user_bot_configs
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
                bots = [dict(row) for row in cur.fetchall()]

                return jsonify({
                    'total_bots': len(bots),
                    'bots': convert_decimals(bots)
                }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/debug/capture-context/<int:trade_id>', methods=['POST'])
def api_debug_capture_context(trade_id):
    """Debug endpoint to manually capture market context for a trade"""
    try:
        # Get trade info
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM bot_trades WHERE id = %s", (trade_id,))
                trade = cur.fetchone()

        if not trade:
            return jsonify({'error': 'Trade not found'}), 404

        # Try to capture market context
        from market_data_service import MarketDataService
        from bot_database import TradeMarketContextDB

        symbol = trade['symbol']
        user_id = trade['user_id']

        logger.info(f"Manually capturing market context for trade {trade_id} ({symbol})")

        context = MarketDataService.get_complete_market_context(
            symbol=symbol,
            alpaca_account=None,
            alpaca_position=None,
            alpaca_positions=None
        )

        # Save to database
        context_id = TradeMarketContextDB.save_context(
            trade_id=trade_id,
            user_id=user_id,
            context=context
        )

        return jsonify({
            'success': context_id is not None,
            'context_id': context_id,
            'context_data': convert_decimals(context) if context else None,
            'errors': context.get('errors') if context else None
        }), 200

    except Exception as e:
        logger.error(f"Manual context capture error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy' if DB_AVAILABLE else 'degraded',
        'service': 'DashTrade API Server',
        'database': 'connected' if DB_AVAILABLE else 'unavailable',
        'database_url': 'configured' if os.environ.get('DATABASE_URL') else 'missing',
        'port': int(os.environ.get('PORT', 8081)),
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API info"""
    return jsonify({
        'service': 'DashTrade API Server',
        'version': '1.0.0',
        'documentation': '/api/docs',
        'health': '/health'
    }), 200


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': {
            'auth': [
                'POST /api/auth/register - Create account',
                'POST /api/auth/login - Get JWT token',
                'GET /api/auth/me - Get current user'
            ],
            'bots': [
                'GET /api/bots - List all bots',
                'POST /api/bots - Create bot',
                'PUT /api/bots/:id - Update bot',
                'DELETE /api/bots/:id - Delete bot',
                'POST /api/bots/:id/toggle - Toggle bot active/inactive'
            ],
            'trading': [
                'GET /api/account - Alpaca account info',
                'GET /api/positions - Open positions (from Alpaca API)',
                'GET /api/trades - Trade history (from database)',
                'GET /api/trades/recent - Recent trades (from Alpaca API, fixes $NaN)',
                'GET /api/trades/:id - Trade detail with market context',
                'POST /api/trades/update-pending - Update pending CLOSE orders status',
                'GET /api/dashboard - Dashboard summary'
            ],
            'ai_analysis': [
                'POST /api/analyze - Run AI analysis and generate insights',
                'GET /api/analyze/patterns - Get raw pattern data',
                'GET /api/performance - Strategy performance metrics',
                'GET /api/trades/outcomes - Trade P&L outcomes',
                'GET /api/insights - AI-discovered insights'
            ],
            'strategies': [
                'GET /api/strategies - List system strategies',
                'POST /api/strategies/:id/subscribe - Subscribe to strategy',
                'POST /api/strategies/:id/unsubscribe - Unsubscribe from strategy'
            ],
            'stocks': [
                'GET /api/stocks/quote?symbol=XXX - Get stock quote data',
                'GET /api/stocks/search?query=XXX - Search stocks by symbol/name',
                'GET /api/stocks/popular - Get popular stocks list'
            ],
            'settings': [
                'POST /api/settings/api-keys - Save Alpaca keys',
                'GET /api/settings/api-keys/status - Check if keys configured',
                'GET /api/webhook-token - Get webhook URL',
                'POST /api/webhook-token/regenerate - Regenerate token'
            ],
            'utility': [
                'GET /health - Health check'
            ]
        }
    }), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}", exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 8081))

    logger.info("=" * 80)
    logger.info("🌐 DASHTRADE API SERVER")
    logger.info("=" * 80)
    logger.info(f"Port: {PORT}")
    logger.info("REST API for React frontend")
    logger.info("Endpoints: /api/auth, /api/bots, /api/account, /api/dashboard")
    logger.info("=" * 80)

    # Run Flask server
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
