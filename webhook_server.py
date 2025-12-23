#!/usr/bin/env python3
"""
DashTrade Webhook Server - Multi-user Trading Bot
Receives TradingView webhooks and executes trades via Alpaca
Runs on port 8080 alongside Streamlit (port 5000)
"""
from flask import Flask, request, jsonify
import logging
import requests
from datetime import datetime
from bot_database import (
    BotConfigDB, WebhookTokenDB, SystemStrategyDB,
    UserStrategySubscriptionDB, UserOutgoingWebhookDB
)
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

        # 4. Get bot configuration (specifically for 'webhook' signal source)
        bot_config = BotConfigDB.get_bot_by_symbol_timeframe(user_id, symbol, timeframe, signal_source='webhook')

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

        # 7. Forward to outgoing webhooks
        forward_to_outgoing_webhooks(user_id, 'signal', {
            'source': 'user_webhook',
            'symbol': symbol,
            'action': action,
            'timeframe': timeframe
        })

        # 8. Return result
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


def forward_to_outgoing_webhooks(user_id: int, event_type: str, payload: dict):
    """
    Forward signal/trade to user's outgoing webhooks

    Args:
        user_id: User ID
        event_type: 'signal' or 'trade'
        payload: Data to send
    """
    try:
        webhooks = UserOutgoingWebhookDB.get_user_webhooks(user_id, active_only=True)

        for wh in webhooks:
            # Check if this webhook wants this event type
            if event_type == 'signal' and not wh.get('include_signals', True):
                continue
            if event_type == 'trade' and not wh.get('include_trades', True):
                continue

            try:
                # Send webhook
                response = requests.post(
                    wh['webhook_url'],
                    json={
                        'event': event_type,
                        'timestamp': datetime.utcnow().isoformat(),
                        **payload
                    },
                    timeout=10,
                    headers={'Content-Type': 'application/json'}
                )

                success = response.status_code < 400
                UserOutgoingWebhookDB.increment_call_count(wh['id'], success=success)

                if success:
                    logger.info(f"📤 Outgoing webhook sent: {wh.get('webhook_name', 'Unknown')}")
                else:
                    logger.warning(f"⚠️ Outgoing webhook failed ({response.status_code}): {wh.get('webhook_name', 'Unknown')}")

            except Exception as e:
                UserOutgoingWebhookDB.increment_call_count(wh['id'], success=False)
                logger.error(f"❌ Outgoing webhook error: {e}")

    except Exception as e:
        logger.error(f"❌ Error forwarding to outgoing webhooks: {e}")


@app.route('/system-webhook', methods=['POST'])
def system_webhook():
    """
    System webhook endpoint for NovAlgo's TradingView strategies

    URL format: /system-webhook?token=sys_abc123...

    This endpoint executes trades for ALL users subscribed to this strategy.

    POST body (JSON):
    {
        "action": "BUY" | "SELL" | "CLOSE",
        "symbol": "AAPL",
        "timeframe": "15 Min"
    }
    """
    try:
        # 1. Validate system token
        token = request.args.get('token')
        if not token:
            logger.warning("⚠️  System webhook missing token")
            return jsonify({'error': 'Missing token parameter'}), 401

        if not token.startswith('sys_'):
            logger.warning(f"⚠️  Invalid system token format: {token[:10]}...")
            return jsonify({'error': 'Invalid system token'}), 401

        # 2. Get strategy from token
        strategy = SystemStrategyDB.get_strategy_by_token(token)
        if not strategy:
            logger.warning(f"⚠️  Invalid or inactive strategy token: {token[:15]}...")
            return jsonify({'error': 'Invalid or inactive strategy token'}), 401

        # 3. Parse request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400

        action = data.get('action', '').upper()
        symbol = data.get('symbol', '').upper()
        timeframe = data.get('timeframe', '')

        # Validate required fields
        if not action or not symbol:
            return jsonify({
                'error': 'Missing required fields',
                'required': ['action', 'symbol']
            }), 400

        if action not in ['BUY', 'SELL', 'CLOSE']:
            return jsonify({'error': f'Invalid action: {action}'}), 400

        logger.info(f"📨 SYSTEM WEBHOOK: Strategy '{strategy['name']}' - {action} {symbol}")

        # 4. Increment signal count for strategy
        SystemStrategyDB.increment_signal_count(strategy['id'])

        # 5. Get all subscribers
        subscribers = UserStrategySubscriptionDB.get_strategy_subscribers(strategy['id'])

        if not subscribers:
            logger.info(f"ℹ️  No subscribers for strategy: {strategy['name']}")
            return jsonify({
                'status': 'no_subscribers',
                'strategy': strategy['name'],
                'message': 'Signal received but no active subscribers'
            }), 200

        # 6. Execute trades for each subscriber
        results = []
        successful = 0
        failed = 0

        for sub in subscribers:
            user_id = sub['user_id']
            bot_config_id = sub['bot_config_id']

            try:
                # Get bot config
                bot_config = None
                user_bots = BotConfigDB.get_user_bots(user_id)
                for bot in user_bots:
                    if bot['id'] == bot_config_id:
                        bot_config = bot
                        break

                if not bot_config:
                    results.append({
                        'user_id': user_id,
                        'status': 'skipped',
                        'reason': 'Bot config not found'
                    })
                    continue

                if not bot_config['is_active']:
                    results.append({
                        'user_id': user_id,
                        'status': 'skipped',
                        'reason': 'Bot is disabled'
                    })
                    continue

                # Initialize trading engine
                engine = TradingEngine(user_id)

                # Execute trade
                result = engine.execute_trade(bot_config, action)

                if result.get('status') == 'success':
                    successful += 1
                else:
                    failed += 1

                results.append({
                    'user_id': user_id,
                    **result
                })

                # Forward to outgoing webhooks
                forward_to_outgoing_webhooks(user_id, 'signal', {
                    'source': 'system_strategy',
                    'strategy_name': strategy['name'],
                    'symbol': symbol,
                    'action': action,
                    'timeframe': timeframe
                })

            except Exception as e:
                failed += 1
                results.append({
                    'user_id': user_id,
                    'status': 'error',
                    'error': str(e)
                })
                logger.error(f"❌ Error executing for user {user_id}: {e}")

        # 7. Return summary
        return jsonify({
            'status': 'executed',
            'strategy': strategy['name'],
            'symbol': symbol,
            'action': action,
            'total_subscribers': len(subscribers),
            'successful': successful,
            'failed': failed,
            'timestamp': datetime.utcnow().isoformat(),
            'details': results
        }), 200

    except Exception as e:
        logger.error(f"❌ System webhook error: {e}", exc_info=True)
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
            'POST /webhook?token=YOUR_USER_TOKEN - User webhook for custom TradingView alerts',
            'POST /system-webhook?token=SYS_TOKEN - System strategy webhook (admin)',
            'GET /health - Health check',
            'POST /test-webhook - Test webhook (no auth)',
            'GET /user/<id>/positions?token=YOUR_TOKEN - Get user positions',
            'GET /user/<id>/bots?token=YOUR_TOKEN - Get user bots'
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
