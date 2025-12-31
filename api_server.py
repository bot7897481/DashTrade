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


@app.route('/api/bots', methods=['POST'])
@token_required
def api_create_bot():
    """Create a new bot configuration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400

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

        trades = BotTradesDB.get_user_trades(g.user_id, limit=limit, symbol=symbol)
        trades = convert_decimals(trades)

        return jsonify({
            'trades': trades,
            'total': len(trades)
        }), 200
    except Exception as e:
        logger.error(f"Get trades error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


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
    Get comprehensive stock quote data from Alpaca

    Query params:
        - symbol: Stock symbol (required)

    Returns:
        - price, open, high, low, close, previousClose
        - volume, avgVolume
        - week52High, week52Low
        - change, changePercent
        - marketCap (from Yahoo Finance as backup)
    """
    try:
        symbol = request.args.get('symbol', '').upper().strip()

        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400

        # Import Alpaca data client
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest, StockLatestBarRequest
        from alpaca.data.timeframe import TimeFrame
        from alpaca.trading.client import TradingClient

        # Get user's API keys
        keys = BotAPIKeysDB.get_api_keys(g.user_id)
        if not keys:
            return jsonify({'error': 'Alpaca API keys not configured'}), 400

        data_client = StockHistoricalDataClient(keys['api_key'], keys['secret_key'])
        trading_client = TradingClient(keys['api_key'], keys['secret_key'], paper=(keys['mode'] == 'paper'))

        result = {
            'symbol': symbol,
            'name': symbol,  # Will be updated if we can get asset info
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
            'timestamp': None
        }

        # Get asset info (name)
        try:
            asset = trading_client.get_asset(symbol)
            result['name'] = asset.name or symbol
            result['exchange'] = asset.exchange.value if asset.exchange else None
            result['tradable'] = asset.tradable
        except Exception as e:
            logger.warning(f"Could not get asset info for {symbol}: {e}")

        # Get latest quote (bid/ask)
        try:
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
            bar_request = StockLatestBarRequest(symbol_or_symbols=symbol)
            bars = data_client.get_stock_latest_bar(bar_request)
            if symbol in bars:
                bar = bars[symbol]
                result['open'] = float(bar.open) if bar.open else None
                result['high'] = float(bar.high) if bar.high else None
                result['low'] = float(bar.low) if bar.low else None
                result['close'] = float(bar.close) if bar.close else None
                result['volume'] = int(bar.volume) if bar.volume else None
                # Use close as price if we don't have quote
                if result['price'] is None and bar.close:
                    result['price'] = float(bar.close)
        except Exception as e:
            logger.warning(f"Could not get bar for {symbol}: {e}")

        # Get comprehensive data from Yahoo Finance (more reliable for historical data)
        # Yahoo Finance provides 52-week high/low, previous close, market cap, etc.
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
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
    Search for stocks by symbol or name

    Query params:
        - query: Search query (required, min 1 character)
        - limit: Max results (default 10)

    Returns:
        - Array of {symbol, name, exchange, tradable}
    """
    try:
        query = request.args.get('query', '').upper().strip()
        limit = int(request.args.get('limit', 10))

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        if len(query) < 1:
            return jsonify({'results': []}), 200

        # Import Alpaca trading client
        from alpaca.trading.client import TradingClient
        from alpaca.trading.enums import AssetClass, AssetStatus

        # Get user's API keys
        keys = BotAPIKeysDB.get_api_keys(g.user_id)
        if not keys:
            return jsonify({'error': 'Alpaca API keys not configured'}), 400

        trading_client = TradingClient(keys['api_key'], keys['secret_key'], paper=(keys['mode'] == 'paper'))

        # Get all tradeable US stocks
        try:
            assets = trading_client.get_all_assets()

            # Filter by query (symbol starts with or name contains)
            results = []
            for asset in assets:
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
                        'tradable': asset.tradable
                    })

                if len(results) >= limit:
                    break

            # Sort: exact symbol matches first, then alphabetically
            results.sort(key=lambda x: (
                0 if x['symbol'] == query else 1,
                0 if x['symbol'].startswith(query) else 1,
                x['symbol']
            ))

            return jsonify({'results': results[:limit]}), 200

        except Exception as e:
            logger.error(f"Error searching assets: {e}")
            return jsonify({'error': f'Search failed: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"Stock search error: {e}", exc_info=True)
        return jsonify({'error': f'Search failed: {str(e)}'}), 500


@app.route('/api/stocks/popular', methods=['GET'])
def api_get_popular_stocks():
    """
    Get a list of popular/common stocks for quick selection
    No authentication required - returns static list
    """
    popular = [
        {'symbol': 'AAPL', 'name': 'Apple Inc.'},
        {'symbol': 'MSFT', 'name': 'Microsoft Corporation'},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.'},
        {'symbol': 'AMZN', 'name': 'Amazon.com Inc.'},
        {'symbol': 'TSLA', 'name': 'Tesla Inc.'},
        {'symbol': 'META', 'name': 'Meta Platforms Inc.'},
        {'symbol': 'NVDA', 'name': 'NVIDIA Corporation'},
        {'symbol': 'JPM', 'name': 'JPMorgan Chase & Co.'},
        {'symbol': 'V', 'name': 'Visa Inc.'},
        {'symbol': 'JNJ', 'name': 'Johnson & Johnson'},
        {'symbol': 'WMT', 'name': 'Walmart Inc.'},
        {'symbol': 'PG', 'name': 'Procter & Gamble Co.'},
        {'symbol': 'MA', 'name': 'Mastercard Inc.'},
        {'symbol': 'UNH', 'name': 'UnitedHealth Group Inc.'},
        {'symbol': 'HD', 'name': 'Home Depot Inc.'},
        {'symbol': 'DIS', 'name': 'Walt Disney Co.'},
        {'symbol': 'BAC', 'name': 'Bank of America Corp.'},
        {'symbol': 'NFLX', 'name': 'Netflix Inc.'},
        {'symbol': 'AMD', 'name': 'Advanced Micro Devices'},
        {'symbol': 'INTC', 'name': 'Intel Corporation'},
        {'symbol': 'SPY', 'name': 'SPDR S&P 500 ETF'},
        {'symbol': 'QQQ', 'name': 'Invesco QQQ Trust'},
        {'symbol': 'IWM', 'name': 'iShares Russell 2000 ETF'},
        {'symbol': 'GLD', 'name': 'SPDR Gold Shares'},
        {'symbol': 'SLV', 'name': 'iShares Silver Trust'},
    ]
    return jsonify({'stocks': popular}), 200


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

        # Get recent trades
        trades = BotTradesDB.get_user_trades(g.user_id, limit=10)

        # Try to get account info (may fail if no API keys)
        account = None
        positions = []
        try:
            engine = TradingEngine(g.user_id)
            account = engine.get_account_info()
            positions = engine.get_all_positions()
        except:
            pass

        return jsonify(convert_decimals({
            'account': account,
            'positions': positions,
            'bots': {
                'total': len(bots),
                'active': active_bots
            },
            'recent_trades': trades[:5],
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
                    'trade': dict(trade) if trade else None,
                    'market_context_exists': context is not None,
                    'market_context': dict(context) if context else None,
                    'user_id_in_trade': trade.get('user_id') if trade else None
                }), 200
    except Exception as e:
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
                'GET /api/positions - Open positions',
                'GET /api/trades - Trade history',
                'GET /api/trades/:id - Trade detail with market context',
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
