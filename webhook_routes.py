"""
Webhook Routes for Streamlit Integration
These routes are added to Streamlit's Tornado server to handle webhooks on the same port
"""
import json
import logging
from datetime import datetime
from tornado.web import RequestHandler

logger = logging.getLogger(__name__)

# Import database classes
try:
    from bot_database import (
        BotConfigDB, WebhookTokenDB, SystemStrategyDB,
        UserStrategySubscriptionDB, UserOutgoingWebhookDB
    )
    from bot_engine import TradingEngine
    import requests
    WEBHOOK_ENABLED = True
except ImportError as e:
    logger.warning(f"Webhook dependencies not available: {e}")
    WEBHOOK_ENABLED = False


def forward_to_outgoing_webhooks(user_id: int, event_type: str, payload: dict):
    """Forward signal/trade to user's outgoing webhooks"""
    if not WEBHOOK_ENABLED:
        return
    try:
        webhooks = UserOutgoingWebhookDB.get_user_webhooks(user_id, active_only=True)
        for wh in webhooks:
            if event_type == 'signal' and not wh.get('include_signals', True):
                continue
            if event_type == 'trade' and not wh.get('include_trades', True):
                continue
            try:
                response = requests.post(
                    wh['webhook_url'],
                    json={'event': event_type, 'timestamp': datetime.utcnow().isoformat(), **payload},
                    timeout=10,
                    headers={'Content-Type': 'application/json'}
                )
                UserOutgoingWebhookDB.increment_call_count(wh['id'], success=response.status_code < 400)
            except Exception as e:
                UserOutgoingWebhookDB.increment_call_count(wh['id'], success=False)
                logger.error(f"Outgoing webhook error: {e}")
    except Exception as e:
        logger.error(f"Error forwarding to outgoing webhooks: {e}")


class WebhookHandler(RequestHandler):
    """Handle user TradingView webhooks"""

    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")

    def post(self):
        if not WEBHOOK_ENABLED:
            self.set_status(503)
            self.write(json.dumps({'error': 'Webhook service not available'}))
            return

        try:
            # Get token from query params
            token = self.get_argument('token', None)
            if not token:
                self.set_status(401)
                self.write(json.dumps({'error': 'Missing token parameter'}))
                return

            # Validate token
            user_id = WebhookTokenDB.get_user_by_token(token)
            if not user_id:
                self.set_status(401)
                self.write(json.dumps({'error': 'Invalid or inactive token'}))
                return

            # Parse JSON body
            try:
                data = json.loads(self.request.body)
            except:
                self.set_status(400)
                self.write(json.dumps({'error': 'Invalid JSON'}))
                return

            action = data.get('action', '').upper()
            symbol = data.get('symbol', '').upper()
            timeframe = data.get('timeframe', '')

            if not action or not symbol or not timeframe:
                self.set_status(400)
                self.write(json.dumps({'error': 'Missing required fields', 'required': ['action', 'symbol', 'timeframe']}))
                return

            if action not in ['BUY', 'SELL', 'CLOSE']:
                self.set_status(400)
                self.write(json.dumps({'error': f'Invalid action: {action}'}))
                return

            logger.info(f"WEBHOOK: User {user_id} - {action} {symbol} {timeframe}")

            # Get bot config
            bot_config = BotConfigDB.get_bot_by_symbol_timeframe(user_id, symbol, timeframe, signal_source='webhook')
            if not bot_config:
                self.write(json.dumps({'status': 'skipped', 'reason': 'No webhook bot found for this symbol+timeframe'}))
                return

            if not bot_config['is_active']:
                self.write(json.dumps({'status': 'skipped', 'reason': 'Bot is disabled'}))
                return

            # Execute trade
            try:
                engine = TradingEngine(user_id)
                result = engine.execute_trade(bot_config, action)
            except ValueError as e:
                self.set_status(400)
                self.write(json.dumps({'status': 'error', 'message': str(e)}))
                return

            # Forward to outgoing webhooks
            forward_to_outgoing_webhooks(user_id, 'signal', {
                'source': 'user_webhook', 'symbol': symbol, 'action': action, 'timeframe': timeframe
            })

            self.write(json.dumps({
                'status': result.get('status'),
                'user_id': user_id,
                'action': action,
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': datetime.utcnow().isoformat(),
                **result
            }))

        except Exception as e:
            logger.error(f"Webhook error: {e}", exc_info=True)
            self.set_status(500)
            self.write(json.dumps({'status': 'error', 'message': str(e)}))


class SystemWebhookHandler(RequestHandler):
    """Handle system strategy webhooks"""

    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")

    def post(self):
        if not WEBHOOK_ENABLED:
            self.set_status(503)
            self.write(json.dumps({'error': 'Webhook service not available'}))
            return

        try:
            token = self.get_argument('token', None)
            if not token or not token.startswith('sys_'):
                self.set_status(401)
                self.write(json.dumps({'error': 'Invalid system token'}))
                return

            strategy = SystemStrategyDB.get_strategy_by_token(token)
            if not strategy:
                self.set_status(401)
                self.write(json.dumps({'error': 'Invalid or inactive strategy token'}))
                return

            try:
                data = json.loads(self.request.body)
            except:
                self.set_status(400)
                self.write(json.dumps({'error': 'Invalid JSON'}))
                return

            action = data.get('action', '').upper()
            symbol = data.get('symbol', '').upper()
            timeframe = data.get('timeframe', '')

            if not action or not symbol:
                self.set_status(400)
                self.write(json.dumps({'error': 'Missing required fields'}))
                return

            if action not in ['BUY', 'SELL', 'CLOSE']:
                self.set_status(400)
                self.write(json.dumps({'error': f'Invalid action: {action}'}))
                return

            logger.info(f"SYSTEM WEBHOOK: Strategy '{strategy['name']}' - {action} {symbol}")

            SystemStrategyDB.increment_signal_count(strategy['id'])
            subscribers = UserStrategySubscriptionDB.get_strategy_subscribers(strategy['id'])

            if not subscribers:
                self.write(json.dumps({'status': 'no_subscribers', 'strategy': strategy['name']}))
                return

            results = []
            successful = 0
            failed = 0

            for sub in subscribers:
                user_id = sub['user_id']
                bot_config_id = sub['bot_config_id']

                try:
                    user_bots = BotConfigDB.get_user_bots(user_id)
                    bot_config = next((b for b in user_bots if b['id'] == bot_config_id), None)

                    if not bot_config or not bot_config['is_active']:
                        results.append({'user_id': user_id, 'status': 'skipped'})
                        continue

                    engine = TradingEngine(user_id)
                    result = engine.execute_trade(bot_config, action)

                    if result.get('status') == 'success':
                        successful += 1
                    else:
                        failed += 1

                    results.append({'user_id': user_id, **result})

                    forward_to_outgoing_webhooks(user_id, 'signal', {
                        'source': 'system_strategy',
                        'strategy_name': strategy['name'],
                        'symbol': symbol,
                        'action': action,
                        'timeframe': timeframe
                    })

                except Exception as e:
                    failed += 1
                    results.append({'user_id': user_id, 'status': 'error', 'error': str(e)})

            self.write(json.dumps({
                'status': 'executed',
                'strategy': strategy['name'],
                'symbol': symbol,
                'action': action,
                'total_subscribers': len(subscribers),
                'successful': successful,
                'failed': failed,
                'timestamp': datetime.utcnow().isoformat()
            }))

        except Exception as e:
            logger.error(f"System webhook error: {e}", exc_info=True)
            self.set_status(500)
            self.write(json.dumps({'status': 'error', 'message': str(e)}))


class HealthHandler(RequestHandler):
    """Health check endpoint"""

    def get(self):
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps({
            'status': 'healthy',
            'service': 'DashTrade Webhook',
            'webhook_enabled': WEBHOOK_ENABLED,
            'timestamp': datetime.utcnow().isoformat()
        }))


class TestWebhookHandler(RequestHandler):
    """Test webhook endpoint"""

    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")

    def post(self):
        try:
            data = json.loads(self.request.body) if self.request.body else {}
        except:
            data = {}

        self.write(json.dumps({
            'status': 'test_received',
            'your_data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'message': 'Test successful! Use /webhook?token=YOUR_TOKEN for actual trading.'
        }))


# Routes to add to Streamlit's Tornado server
WEBHOOK_ROUTES = [
    (r"/webhook", WebhookHandler),
    (r"/system-webhook", SystemWebhookHandler),
    (r"/health", HealthHandler),
    (r"/test-webhook", TestWebhookHandler),
]
