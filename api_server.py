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
        UserStrategySubscriptionDB, BotAPIKeysDB, BotTradesDB
    )
    from bot_engine import TradingEngine
    from auth import UserDB
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
            else:
                bot['webhook_url'] = None

        return jsonify({
            'bots': bots,
            'total': len(bots),
            'active': sum(1 for b in bots if b.get('is_active'))
        }), 200
    except Exception as e:
        logger.error(f"Get bots error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/bots', methods=['POST'])
@token_required
def api_create_bot():
    """Create a new bot configuration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400

        symbol = data.get('symbol', '').upper().strip()
        timeframe = data.get('timeframe', '').strip()
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
            if bot and bot.get('webhook_token'):
                webhook_base = os.environ.get('WEBHOOK_SERVER_URL', 'https://webhook.novalgo.org')
                if not webhook_base.startswith('http'):
                    webhook_base = f"https://{webhook_base}"
                webhook_url = f"{webhook_base}/webhook?token={bot['webhook_token']}"

            return jsonify({
                'success': True,
                'bot_id': bot_id,
                'message': f'Bot created for {symbol} {timeframe}',
                'webhook_url': webhook_url,
                'webhook_payload': '{"action": "{{strategy.order.action}}"}'
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
# HEALTH CHECK
# ============================================================================

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
                'GET /api/dashboard - Dashboard summary'
            ],
            'strategies': [
                'GET /api/strategies - List system strategies',
                'POST /api/strategies/:id/subscribe - Subscribe to strategy',
                'POST /api/strategies/:id/unsubscribe - Unsubscribe from strategy'
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
