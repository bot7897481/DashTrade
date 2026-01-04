"""
Webhook Routes for Streamlit Integration
These routes are added to Streamlit's Tornado server to handle webhooks on the same port
"""
import json
import logging
from datetime import datetime
from tornado.web import RequestHandler

logger = logging.getLogger(__name__)


def normalize_timeframe(tf: str) -> str:
    """
    Normalize timeframe from TradingView format to our database format.
    TradingView {{interval}} returns: 1, 5, 15, 30, 45, 60, 120, 240, D, W, M
    Our database stores: 1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1d, 1w, 1m
    """
    if not tf:
        return tf

    tf = str(tf).strip().lower()

    # Already in correct format
    if tf in ['1min', '5min', '15min', '30min', '45min', '1h', '2h', '4h', '1d', '1w', '1m']:
        return tf

    # Map TradingView intervals to our format
    mappings = {
        # Minutes
        '1': '1min', '1m': '1min', '1 min': '1min', '1min': '1min',
        '5': '5min', '5m': '5min', '5 min': '5min', '5min': '5min',
        '15': '15min', '15m': '15min', '15 min': '15min', '15min': '15min',
        '30': '30min', '30m': '30min', '30 min': '30min', '30min': '30min',
        '45': '45min', '45m': '45min', '45 min': '45min', '45min': '45min',
        # Hours
        '60': '1h', '1h': '1h', '1 hour': '1h', '1hour': '1h',
        '120': '2h', '2h': '2h', '2 hour': '2h', '2hour': '2h',
        '240': '4h', '4h': '4h', '4 hour': '4h', '4hour': '4h',
        # Days/Weeks/Months
        'd': '1d', '1d': '1d', 'daily': '1d', 'day': '1d',
        'w': '1w', '1w': '1w', 'weekly': '1w', 'week': '1w',
        'm': '1m', '1m': '1m', 'monthly': '1m', 'month': '1m',
    }

    return mappings.get(tf, tf)


# Known crypto symbols supported by Alpaca
CRYPTO_SYMBOLS = {
    'BTC/USD', 'ETH/USD', 'LTC/USD', 'BCH/USD', 'AAVE/USD', 'AVAX/USD',
    'BAT/USD', 'CRV/USD', 'DOT/USD', 'GRT/USD', 'LINK/USD', 'MKR/USD',
    'SHIB/USD', 'SUSHI/USD', 'UNI/USD', 'USDC/USD', 'USDT/USD', 'XTZ/USD',
    'DOGE/USD', 'SOL/USD', 'MATIC/USD', 'ALGO/USD', 'XLM/USD', 'ATOM/USD',
    'ADA/USD', 'XRP/USD', 'TRX/USD', 'NEAR/USD', 'FTM/USD', 'APE/USD'
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
    """
    Normalize crypto symbol to Alpaca format.
    TradingView sends: BTCUSD, ETHUSD
    Alpaca expects: BTC/USD, ETH/USD
    """
    if not symbol:
        return symbol
    symbol_upper = symbol.upper().strip()

    # Already in correct format with slash
    if '/' in symbol_upper:
        return symbol_upper

    # Convert BTCUSD to BTC/USD
    if symbol_upper.endswith('USD') and len(symbol_upper) >= 6:
        base = symbol_upper[:-3]
        normalized = f"{base}/USD"
        # Only convert if it's a known crypto
        if normalized in CRYPTO_SYMBOLS:
            return normalized

    return symbol_upper


# Import database classes
try:
    from bot_database import (
        BotConfigDB, WebhookTokenDB, SystemStrategyDB,
        UserStrategySubscriptionDB, UserOutgoingWebhookDB,
        StrategyParamsDB, TradeOutcomesDB
    )
    from bot_engine import TradingEngine
    from email_service import TradeNotificationService
    import requests
    WEBHOOK_ENABLED = True
    EMAIL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Webhook dependencies not available: {e}")
    WEBHOOK_ENABLED = False
    EMAIL_AVAILABLE = False


def extract_strategy_params(data: dict) -> dict:
    """
    Extract strategy parameters from webhook payload.
    These are optional fields that TradingView Pine Script can send
    for AI learning purposes.
    """
    params = {}

    # Strategy identification
    if data.get('strategy_type'):
        params['strategy_type'] = data.get('strategy_type')
    if data.get('strategy_name'):
        params['strategy_name'] = data.get('strategy_name')
    if data.get('strategy_version'):
        params['strategy_version'] = data.get('strategy_version')

    # Entry indicator info
    if data.get('entry_indicator'):
        params['entry_indicator'] = data.get('entry_indicator')
    if data.get('entry_condition'):
        params['entry_condition'] = data.get('entry_condition')
    if data.get('entry_threshold') is not None:
        params['entry_threshold'] = float(data.get('entry_threshold'))
    if data.get('entry_value') is not None:
        params['entry_value_at_signal'] = float(data.get('entry_value'))

    # RSI parameters
    if data.get('rsi_period') is not None:
        params['rsi_period'] = int(data.get('rsi_period'))
    if data.get('rsi_value') is not None:
        params['rsi_value_at_entry'] = float(data.get('rsi_value'))
    if data.get('rsi_oversold') is not None:
        params['rsi_oversold_level'] = int(data.get('rsi_oversold'))
    if data.get('rsi_overbought') is not None:
        params['rsi_overbought_level'] = int(data.get('rsi_overbought'))

    # Moving average parameters
    if data.get('ma_fast') is not None:
        params['ma_fast_period'] = int(data.get('ma_fast'))
    if data.get('ma_fast_type'):
        params['ma_fast_type'] = data.get('ma_fast_type')
    if data.get('ma_slow') is not None:
        params['ma_slow_period'] = int(data.get('ma_slow'))
    if data.get('ma_slow_type'):
        params['ma_slow_type'] = data.get('ma_slow_type')

    # MACD parameters
    if data.get('macd_fast') is not None:
        params['macd_fast_period'] = int(data.get('macd_fast'))
    if data.get('macd_slow') is not None:
        params['macd_slow_period'] = int(data.get('macd_slow'))
    if data.get('macd_signal') is not None:
        params['macd_signal_period'] = int(data.get('macd_signal'))
    if data.get('macd_value') is not None:
        params['macd_value_at_entry'] = float(data.get('macd_value'))
    if data.get('macd_histogram') is not None:
        params['macd_histogram_at_entry'] = float(data.get('macd_histogram'))

    # ATR parameters
    if data.get('atr_period') is not None:
        params['atr_period'] = int(data.get('atr_period'))
    if data.get('atr_value') is not None:
        params['atr_value_at_entry'] = float(data.get('atr_value'))
    if data.get('atr_stop_mult') is not None:
        params['atr_multiplier_stop'] = float(data.get('atr_stop_mult'))
    if data.get('atr_target_mult') is not None:
        params['atr_multiplier_target'] = float(data.get('atr_target_mult'))

    # Risk management
    if data.get('stop_loss') is not None:
        params['stop_loss_value'] = float(data.get('stop_loss'))
    if data.get('stop_loss_type'):
        params['stop_loss_type'] = data.get('stop_loss_type')
    if data.get('take_profit') is not None:
        params['take_profit_value'] = float(data.get('take_profit'))
    if data.get('take_profit_type'):
        params['take_profit_type'] = data.get('take_profit_type')
    if data.get('risk_reward') is not None:
        params['risk_reward_ratio'] = float(data.get('risk_reward'))

    # Volume
    if data.get('volume_ratio') is not None:
        params['volume_ratio_at_entry'] = float(data.get('volume_ratio'))

    # Trend context
    if data.get('trend_short'):
        params['trend_short'] = data.get('trend_short')
    if data.get('trend_medium'):
        params['trend_medium'] = data.get('trend_medium')
    if data.get('trend_long'):
        params['trend_long'] = data.get('trend_long')

    # Any extra parameters go into custom_params
    known_keys = {
        'action', 'symbol', 'timeframe', 'strategy_type', 'strategy_name', 'strategy_version',
        'entry_indicator', 'entry_condition', 'entry_threshold', 'entry_value',
        'rsi_period', 'rsi_value', 'rsi_oversold', 'rsi_overbought',
        'ma_fast', 'ma_fast_type', 'ma_slow', 'ma_slow_type',
        'macd_fast', 'macd_slow', 'macd_signal', 'macd_value', 'macd_histogram',
        'atr_period', 'atr_value', 'atr_stop_mult', 'atr_target_mult',
        'stop_loss', 'stop_loss_type', 'take_profit', 'take_profit_type', 'risk_reward',
        'volume_ratio', 'trend_short', 'trend_medium', 'trend_long'
    }
    custom = {k: v for k, v in data.items() if k not in known_keys}
    if custom:
        params['custom_params'] = custom

    return params if params else None


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
            symbol_raw = data.get('symbol', '').upper()
            timeframe_raw = data.get('timeframe', '')

            # Normalize crypto symbol (BTCUSD -> BTC/USD)
            if is_crypto_symbol(symbol_raw):
                symbol = normalize_crypto_symbol(symbol_raw)
            else:
                symbol = symbol_raw

            timeframe = normalize_timeframe(timeframe_raw)  # Normalize TradingView format

            if not action or not symbol or not timeframe:
                self.set_status(400)
                self.write(json.dumps({'error': 'Missing required fields', 'required': ['action', 'symbol', 'timeframe']}))
                return

            if action not in ['BUY', 'SELL', 'CLOSE']:
                self.set_status(400)
                self.write(json.dumps({'error': f'Invalid action: {action}'}))
                return

            logger.info(f"WEBHOOK: User {user_id} - {action} {symbol} {timeframe} (raw symbol: {symbol_raw}, raw timeframe: {timeframe_raw})")

            # Get bot config - try normalized symbol first, then raw symbol as fallback
            bot_config = BotConfigDB.get_bot_by_symbol_timeframe(user_id, symbol, timeframe, signal_source='webhook')
            if not bot_config and symbol != symbol_raw:
                # Fallback: try with raw symbol (in case bot was stored before normalization)
                logger.info(f"WEBHOOK: Bot not found with {symbol}, trying raw symbol {symbol_raw}")
                bot_config = BotConfigDB.get_bot_by_symbol_timeframe(user_id, symbol_raw, timeframe, signal_source='webhook')
            if not bot_config:
                self.write(json.dumps({'status': 'skipped', 'reason': 'No webhook bot found for this symbol+timeframe', 'symbol': symbol, 'timeframe': timeframe}))
                return

            if not bot_config['is_active']:
                self.write(json.dumps({'status': 'skipped', 'reason': 'Bot is disabled'}))
                return

            # Extract strategy parameters for AI learning (optional fields)
            strategy_params = extract_strategy_params(data)

            # Execute trade
            try:
                engine = TradingEngine(user_id)
                result = engine.execute_trade(bot_config, action)
            except ValueError as e:
                # Send error notification email
                if EMAIL_AVAILABLE:
                    try:
                        TradeNotificationService.send_trade_error_email(
                            user_id=user_id,
                            error_data={
                                'symbol': symbol,
                                'action': action,
                                'error': str(e)
                            }
                        )
                    except Exception:
                        pass
                self.set_status(400)
                self.write(json.dumps({'status': 'error', 'message': str(e)}))
                return

            # Save strategy params and create outcome entry for AI learning
            trade_id = result.get('trade_id')
            if trade_id and result.get('status') == 'success':
                try:
                    # Save strategy parameters
                    if strategy_params:
                        StrategyParamsDB.save_params(trade_id, user_id, strategy_params)
                        logger.info(f"Saved strategy params for trade {trade_id}")

                    # Create trade outcome entry (will be closed when position exits)
                    if action in ['BUY', 'SELL'] and result.get('filled_avg_price'):
                        position_type = 'long' if action == 'BUY' else 'short'
                        TradeOutcomesDB.create_entry(
                            trade_id=trade_id,
                            user_id=user_id,
                            entry_price=float(result.get('filled_avg_price')),
                            entry_time=datetime.utcnow(),
                            quantity=float(result.get('filled_qty', 0)),
                            position_type=position_type,
                            entry_order_id=result.get('order_id')
                        )
                        logger.info(f"Created outcome entry for trade {trade_id}")

                    # If CLOSE action, find and close the open position outcome
                    if action == 'CLOSE' and result.get('filled_avg_price'):
                        open_position = TradeOutcomesDB.get_open_position(user_id, symbol)
                        if open_position:
                            outcome = TradeOutcomesDB.close_trade(
                                trade_id=open_position['trade_id'],
                                exit_price=float(result.get('filled_avg_price')),
                                exit_time=datetime.utcnow(),
                                exit_reason='signal',
                                exit_order_id=result.get('order_id')
                            )
                            if outcome:
                                logger.info(f"Closed trade outcome: P&L ${outcome.get('pnl_dollars', 0):.2f} ({outcome.get('pnl_percent', 0):.2f}%)")
                except Exception as e:
                    logger.warning(f"Failed to save strategy learning data (non-critical): {e}")

            # Send email notification (async, non-blocking)
            email_sent = False
            if EMAIL_AVAILABLE and result.get('status') == 'success':
                try:
                    email_sent = TradeNotificationService.send_trade_executed_email(
                        user_id=user_id,
                        trade_data={
                            'trade_id': trade_id,
                            'symbol': symbol,
                            'action': action,
                            'timeframe': timeframe,
                            'quantity': result.get('filled_qty'),
                            'filled_price': result.get('filled_avg_price'),
                            'status': 'executed',
                            'bot_name': bot_config.get('strategy_name', 'Bot'),
                            'order_id': result.get('order_id')
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to send trade notification email (non-critical): {e}")

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
                'strategy_params_saved': strategy_params is not None,
                'email_notification_sent': email_sent,
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
            symbol_raw = data.get('symbol', '').upper()
            timeframe_raw = data.get('timeframe', '')

            # Normalize crypto symbol (BTCUSD -> BTC/USD)
            if is_crypto_symbol(symbol_raw):
                symbol = normalize_crypto_symbol(symbol_raw)
            else:
                symbol = symbol_raw

            timeframe = normalize_timeframe(timeframe_raw) if timeframe_raw else ''

            if not action or not symbol:
                self.set_status(400)
                self.write(json.dumps({'error': 'Missing required fields'}))
                return

            if action not in ['BUY', 'SELL', 'CLOSE']:
                self.set_status(400)
                self.write(json.dumps({'error': f'Invalid action: {action}'}))
                return

            logger.info(f"SYSTEM WEBHOOK: Strategy '{strategy['name']}' - {action} {symbol} {timeframe}")

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
