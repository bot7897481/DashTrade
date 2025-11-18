#!/usr/bin/env python3
"""
DashTrade Webhook Server - Multi-user Trading Bot
Receives TradingView webhooks and executes trades via Alpaca
Runs on port 8080 alongside Streamlit (port 5000)
"""
from flask import Flask, request, jsonify
import logging
from datetime import datetime
from bot_database import BotConfigDB, WebhookTokenDB
from bot_engine import TradingEngine

# Setup Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Main webhook endpoint for TradingView signals

    URL format: /webhook?token=usr_abc123...

    POST body (JSON):
    {
        "action": "BUY" | "SELL" | "CLOSE",
        "symbol": "AAPL",
        "timeframe": "15 Min",
        "price": 145.50  (optional)
    }

    Returns:
        JSON response with status and execution details
    """
    try:
        # 1. Validate token
        token = request.args.get('token')
        if not token:
            logger.warning("⚠️  Webhook request missing token")
            return jsonify({'error': 'Missing token parameter'}), 401

        # 2. Get user_id from token
        user_id = WebhookTokenDB.get_user_by_token(token)
        if not user_id:
            logger.warning(f"⚠️  Invalid token: {token[:10]}...")
            return jsonify({'error': 'Invalid or inactive token'}), 401

        # 3. Parse request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400

        action = data.get('action', '').upper()
        symbol = data.get('symbol', '').upper()
        timeframe = data.get('timeframe', '')

        # Validate required fields
        if not action or not symbol or not timeframe:
            return jsonify({
                'error': 'Missing required fields',
                'required': ['action', 'symbol', 'timeframe']
            }), 400

        if action not in ['BUY', 'SELL', 'CLOSE']:
            return jsonify({'error': f'Invalid action: {action}'}), 400

        logger.info(f"📨 WEBHOOK: User {user_id} - {action} {symbol} {timeframe}")

        # 4. Get bot configuration
        bot_config = BotConfigDB.get_bot_by_symbol_timeframe(user_id, symbol, timeframe)

        if not bot_config:
            logger.info(f"ℹ️  No bot config found: {symbol} {timeframe}")
            return jsonify({
                'status': 'skipped',
                'reason': 'No bot configuration found for this symbol+timeframe',
                'symbol': symbol,
                'timeframe': timeframe
            }), 200

        if not bot_config['is_active']:
            logger.info(f"ℹ️  Bot inactive: {symbol} {timeframe}")
            return jsonify({
                'status': 'skipped',
                'reason': 'Bot is disabled',
                'symbol': symbol,
                'timeframe': timeframe
            }), 200

        # 5. Initialize trading engine for this user
        try:
            engine = TradingEngine(user_id)
        except ValueError as e:
            logger.error(f"❌ Failed to initialize trading engine: {e}")
            return jsonify({
                'status': 'error',
                'message': 'Alpaca API keys not configured. Please add them in Bot Settings.'
            }), 400

        # 6. Execute trade
        result = engine.execute_trade(bot_config, action)

        # 7. Return result
        response = {
            'status': result.get('status'),
            'user_id': user_id,
            'action': action,
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': datetime.utcnow().isoformat(),
            **result
        }

        status_code = 200
        if result.get('status') == 'error':
            status_code = 500

        return jsonify(response), status_code

    except Exception as e:
        logger.error(f"❌ Webhook error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'error': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'DashTrade Webhook Server',
        'port': 8080,
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/test-webhook', methods=['POST'])
def test_webhook():
    """
    Test webhook endpoint (no authentication required)
    Useful for debugging and testing webhook payloads
    """
    data = request.get_json()
    logger.info(f"📥 Test webhook received: {data}")

    return jsonify({
        'status': 'test_received',
        'your_data': data,
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'This is a test endpoint. Use /webhook?token=YOUR_TOKEN for actual trading.'
    }), 200


@app.route('/user/<int:user_id>/positions', methods=['GET'])
def get_user_positions(user_id: int):
    """
    Get current positions for a user
    Useful for debugging

    Requires: ?token=USER_WEBHOOK_TOKEN (for authentication)
    """
    token = request.args.get('token')
    if not token:
        return jsonify({'error': 'Missing token'}), 401

    # Verify token belongs to this user
    token_user_id = WebhookTokenDB.get_user_by_token(token)
    if token_user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        engine = TradingEngine(user_id)
        positions = engine.get_all_positions()
        account = engine.get_account_info()

        return jsonify({
            'user_id': user_id,
            'account': account,
            'positions': positions,
            'total_positions': len(positions)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/user/<int:user_id>/bots', methods=['GET'])
def get_user_bots(user_id: int):
    """
    Get all bot configurations for a user
    Useful for debugging

    Requires: ?token=USER_WEBHOOK_TOKEN (for authentication)
    """
    token = request.args.get('token')
    if not token:
        return jsonify({'error': 'Missing token'}), 401

    # Verify token belongs to this user
    token_user_id = WebhookTokenDB.get_user_by_token(token)
    if token_user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    bots = BotConfigDB.get_user_bots(user_id)

    # Convert Decimal to float for JSON serialization
    for bot in bots:
        for key, value in bot.items():
            if hasattr(value, '__float__'):
                bot[key] = float(value)

    return jsonify({
        'user_id': user_id,
        'bots': bots,
        'total_bots': len(bots),
        'active_bots': sum(1 for b in bots if b['is_active'])
    }), 200


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            'POST /webhook?token=YOUR_TOKEN',
            'GET /health',
            'POST /test-webhook',
            'GET /user/<id>/positions?token=YOUR_TOKEN',
            'GET /user/<id>/bots?token=YOUR_TOKEN'
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}", exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("🤖 DASHTRADE WEBHOOK SERVER STARTING")
    logger.info("=" * 80)
    logger.info("Port: 8080")
    logger.info("Endpoints:")
    logger.info("  POST /webhook?token=YOUR_TOKEN")
    logger.info("  GET  /health")
    logger.info("  POST /test-webhook")
    logger.info("=" * 80)

    # Run Flask server
    app.run(host='0.0.0.0', port=8080, debug=False)
