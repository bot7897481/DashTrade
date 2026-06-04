"""
Robinhood Trading Engine - Executes trades via Robinhood's MCP server
Mirrors the TradingEngine interface from bot_engine.py so callers
can swap brokers transparently.
"""
import logging
from datetime import datetime
import time
from typing import Dict, Optional, List

from bot_database import (
    RobinhoodTokenDB, BotConfigDB, BotTradesDB, RiskEventDB, TradeMarketContextDB
)
from market_data_service import MarketDataService
from email_service import TradeNotificationService
from robinhood_mcp_client import RobinhoodMCPClient, run_sync

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RobinhoodTradingEngine:
    """Execute trades for multi-user bot system via Robinhood MCP"""

    def __init__(self, user_id: int):
        self.user_id = user_id

        tokens = RobinhoodTokenDB.get_tokens(user_id)
        if not tokens:
            raise ValueError(f"No Robinhood connection found for user {user_id}")

        self.access_token = tokens['access_token']
        self.client = RobinhoodMCPClient(self.access_token)

        logger.info(f"Robinhood trading engine initialized for user {user_id}")

    def _call(self, coro):
        """Run an async MCP call synchronously."""
        return run_sync(coro)

    def get_account_info(self) -> Dict:
        try:
            result = self._call(self.client.get_account())
            if isinstance(result, dict):
                return {
                    'equity': float(result.get('equity', result.get('portfolio_value', 0))),
                    'cash': float(result.get('cash', result.get('buying_power', 0))),
                    'buying_power': float(result.get('buying_power', 0)),
                    'portfolio_value': float(result.get('portfolio_value', result.get('equity', 0))),
                    'broker': 'robinhood'
                }
            return {'broker': 'robinhood', 'raw': result}
        except Exception as e:
            logger.error(f"Error getting Robinhood account info: {e}")
            return {'broker': 'robinhood', 'error': str(e)}

    def get_all_positions(self) -> List[Dict]:
        try:
            result = self._call(self.client.get_positions())
            if isinstance(result, list):
                positions = []
                for pos in result:
                    qty = float(pos.get('quantity', pos.get('qty', 0)))
                    positions.append({
                        'symbol': pos.get('symbol', ''),
                        'qty': abs(qty),
                        'side': 'LONG' if qty > 0 else 'SHORT',
                        'market_value': float(pos.get('market_value', 0)),
                        'unrealized_pl': float(pos.get('unrealized_pl', pos.get('unrealized_pnl', 0))),
                        'unrealized_plpc': float(pos.get('unrealized_plpc', 0)),
                        'entry_price': float(pos.get('average_buy_price', pos.get('avg_entry_price', 0))),
                        'current_price': float(pos.get('current_price', pos.get('last_trade_price', 0))),
                        'broker': 'robinhood'
                    })
                return positions
            return []
        except Exception as e:
            logger.error(f"Error getting Robinhood positions: {e}")
            return []

    def get_current_position(self, symbol: str) -> Optional[Dict]:
        try:
            positions = self.get_all_positions()
            symbol_upper = symbol.upper()
            for pos in positions:
                if pos['symbol'].upper() == symbol_upper:
                    return pos
            return {'side': 'FLAT', 'qty': 0, 'market_value': 0, 'unrealized_pl': 0}
        except Exception as e:
            logger.error(f"Error getting position for {symbol}: {e}")
            return None

    def get_price_quote(self, symbol: str) -> Dict:
        try:
            result = self._call(self.client.get_quote(symbol))
            if isinstance(result, dict):
                bid = float(result.get('bid_price', result.get('bid', 0)))
                ask = float(result.get('ask_price', result.get('ask', 0)))
                return {
                    'symbol': symbol.upper(),
                    'bid_price': bid,
                    'ask_price': ask,
                    'last_price': float(result.get('last_trade_price', result.get('last', 0))),
                    'broker': 'robinhood'
                }
            return {'error': f"Unexpected response: {result}"}
        except Exception as e:
            logger.error(f"Error getting Robinhood quote for {symbol}: {e}")
            return {'error': str(e)}

    def place_manual_order(self, symbol: str, qty: float, side: str,
                           order_type: str = 'market', limit_price: float = None) -> Dict:
        try:
            result = self._call(self.client.place_order(
                symbol=symbol,
                side=side,
                quantity=qty,
                order_type=order_type,
                limit_price=limit_price
            ))
            if isinstance(result, dict):
                return {
                    'status': 'success',
                    'order_id': result.get('order_id', result.get('id', '')),
                    'symbol': symbol.upper(),
                    'qty': qty,
                    'side': side.upper(),
                    'order_status': result.get('state', result.get('status', 'submitted')),
                    'broker': 'robinhood'
                }
            return {'status': 'error', 'message': f"Unexpected: {result}"}
        except Exception as e:
            logger.error(f"Error placing Robinhood order: {e}")
            return {'status': 'error', 'message': str(e)}

    def close_position(self, symbol: str) -> Dict:
        """Close entire position by placing an opposite order."""
        logger.info(f"CLOSE POSITION REQUEST (Robinhood) for: {symbol}")
        try:
            position = self.get_current_position(symbol)
            if not position or position.get('side') == 'FLAT':
                return {'status': 'info', 'message': 'No position to close'}

            qty = position['qty']
            close_side = 'sell' if position['side'] == 'LONG' else 'buy'

            result = self._call(self.client.place_order(
                symbol=symbol,
                side=close_side,
                quantity=qty,
                order_type='market'
            ))

            if isinstance(result, dict):
                order_id = result.get('order_id', result.get('id', ''))
                return {
                    'status': 'success',
                    'message': f'Position closed for {symbol}',
                    'order_id': order_id,
                    'broker': 'robinhood'
                }
            return {'status': 'error', 'message': f"Unexpected: {result}"}
        except Exception as e:
            logger.error(f"Failed to close Robinhood position for {symbol}: {e}")
            return {'status': 'error', 'message': str(e)}

    def check_risk_limits(self, bot_config: Dict, current_position: Dict) -> Dict:
        """Check if bot has hit risk limits (same logic as Alpaca engine)."""
        if not current_position or current_position.get('side') == 'FLAT':
            return {'hit': False}

        risk_limit_percent = bot_config.get('risk_limit_percent', 10.0)
        unrealized_pl = current_position.get('unrealized_pl', 0)
        market_value = abs(current_position.get('market_value', 0))

        if market_value == 0:
            return {'hit': False}

        loss_percent = (unrealized_pl / market_value) * 100

        if loss_percent < 0 and abs(loss_percent) >= risk_limit_percent:
            logger.warning(
                f"RISK LIMIT HIT (Robinhood): {bot_config['symbol']} - "
                f"Loss: {loss_percent:.2f}% (Limit: {risk_limit_percent}%)"
            )
            RiskEventDB.log_risk_event(
                user_id=self.user_id,
                bot_config_id=bot_config['id'],
                event_type='RISK_LIMIT_HIT',
                symbol=bot_config['symbol'],
                timeframe=bot_config['timeframe'],
                threshold_value=risk_limit_percent,
                current_value=abs(loss_percent),
                action_taken='CLOSE_POSITION_AND_DISABLE'
            )
            return {
                'hit': True,
                'reason': f"Loss {abs(loss_percent):.2f}% exceeds limit {risk_limit_percent}%",
                'action': 'CLOSE_POSITION_AND_DISABLE'
            }
        return {'hit': False}

    def execute_trade(self, bot_config: Dict, action: str,
                      signal_received_at: datetime = None,
                      signal_source: str = 'webhook') -> Dict:
        """
        Execute a trade based on signal - mirrors TradingEngine.execute_trade().
        """
        if signal_received_at is None:
            signal_received_at = datetime.utcnow()

        symbol = bot_config['symbol'].upper()
        timeframe = bot_config['timeframe']
        position_size = float(bot_config['position_size'])
        bot_id = bot_config['id']

        logger.info(f"WEBHOOK (Robinhood): {action} ${position_size} {symbol} {timeframe} (User: {self.user_id})")

        current_position = self.get_current_position(symbol)
        if current_position is None:
            return {'status': 'error', 'message': 'Failed to get position from Robinhood'}

        current_side = current_position.get('side', 'FLAT')

        # Risk check
        risk_check = self.check_risk_limits(bot_config, current_position)
        if risk_check['hit']:
            self.close_position(symbol)
            BotConfigDB.toggle_bot(bot_id, self.user_id, False)
            BotConfigDB.update_bot_status(bot_id, self.user_id, 'RISK_LIMIT_HIT', position_side='FLAT')
            return {
                'status': 'risk_limit',
                'message': f"Risk limit hit: {risk_check['reason']}. Position closed, bot disabled.",
                'action_taken': 'POSITION_CLOSED_BOT_DISABLED'
            }

        # CLOSE
        if action == 'CLOSE':
            if current_side == 'FLAT':
                return {'status': 'info', 'message': 'Already flat'}

            close_result = self.close_position(symbol)
            if close_result.get('status') != 'success':
                BotConfigDB.update_bot_status(bot_id, self.user_id, 'FAILED', last_signal='CLOSE')
                return close_result

            order_id = close_result.get('order_id', '')
            BotConfigDB.update_bot_status(bot_id, self.user_id, 'ORDER SUBMITTED', last_signal='CLOSE')

            trade_id = BotTradesDB.log_trade(
                user_id=self.user_id, bot_config_id=bot_id,
                symbol=symbol, timeframe=timeframe, action='CLOSE',
                notional=current_position.get('market_value', 0),
                order_id=str(order_id),
                trade_details={
                    'signal_source': signal_source,
                    'signal_received_at': signal_received_at,
                    'order_submitted_at': datetime.utcnow(),
                    'broker': 'robinhood',
                    'position_before': current_side,
                    'position_after': 'FLAT',
                }
            )

            # Check fill (wait briefly)
            time.sleep(2)
            try:
                order_status = self._call(self.client.get_order(str(order_id)))
                state = order_status.get('state', order_status.get('status', ''))
                if state in ('filled', 'FILLED'):
                    filled_price = float(order_status.get('average_price',
                                         order_status.get('filled_avg_price', 0)))
                    filled_qty = float(order_status.get('quantity',
                                       order_status.get('filled_qty', 0)))
                    BotConfigDB.update_bot_status(bot_id, self.user_id, 'WAITING',
                                                  last_signal='CLOSE', position_side='FLAT')
                    BotTradesDB.update_trade_status(trade_id, 'FILLED', filled_qty, filled_price,
                                                    execution_details={'broker': 'robinhood',
                                                                       'position_after': 'FLAT'})
                    return {
                        'status': 'success', 'action': 'CLOSE', 'symbol': symbol,
                        'order_id': order_id, 'trade_id': trade_id,
                        'filled_qty': filled_qty, 'filled_price': filled_price,
                        'broker': 'robinhood'
                    }
            except Exception as e:
                logger.warning(f"Could not check Robinhood order status: {e}")

            return {'status': 'pending', 'order_id': order_id, 'trade_id': trade_id,
                    'broker': 'robinhood'}

        # BUY
        if action == 'BUY':
            if current_side == 'LONG':
                BotConfigDB.update_bot_status(bot_id, self.user_id, 'ALREADY LONG')
                return {'status': 'skipped', 'message': 'Already long'}
            if current_side == 'SHORT':
                self.close_position(symbol)
                time.sleep(1)

            return self._execute_order(bot_id, symbol, timeframe, position_size,
                                       'buy', 'BUY', 'LONG', signal_received_at, signal_source)

        # SELL
        if action == 'SELL':
            if current_side == 'SHORT':
                BotConfigDB.update_bot_status(bot_id, self.user_id, 'ALREADY SHORT')
                return {'status': 'skipped', 'message': 'Already short'}
            if current_side == 'LONG':
                self.close_position(symbol)
                time.sleep(1)

            return self._execute_order(bot_id, symbol, timeframe, position_size,
                                       'sell', 'SELL', 'SHORT', signal_received_at, signal_source)

        return {'status': 'error', 'message': f'Unknown action: {action}'}

    def _execute_order(self, bot_id: int, symbol: str, timeframe: str,
                       position_size: float, side: str, action: str,
                       position_after: str, signal_received_at: datetime,
                       signal_source: str) -> Dict:
        """Execute a BUY or SELL order via Robinhood MCP."""
        trade_id = None
        try:
            order_submitted_at = datetime.utcnow()
            BotConfigDB.update_bot_status(bot_id, self.user_id, 'ORDER SUBMITTED', last_signal=action)

            result = self._call(self.client.place_order(
                symbol=symbol,
                side=side,
                notional=position_size,
                order_type='market'
            ))

            if not isinstance(result, dict):
                raise Exception(f"Unexpected MCP response: {result}")

            order_id = str(result.get('order_id', result.get('id', '')))
            logger.info(f"ORDER SUBMITTED (Robinhood): {order_id}")

            # Send email notification
            try:
                TradeNotificationService.send_trade_executed_email(
                    user_id=self.user_id,
                    trade_data={
                        'symbol': symbol, 'action': action,
                        'status': 'SUBMITTED', 'order_id': order_id,
                        'bot_name': f"{symbol} {timeframe}",
                        'timeframe': timeframe,
                    }
                )
            except Exception:
                pass

            trade_id = BotTradesDB.log_trade(
                user_id=self.user_id, bot_config_id=bot_id,
                symbol=symbol, timeframe=timeframe, action=action,
                notional=position_size, order_id=order_id,
                trade_details={
                    'signal_source': signal_source,
                    'signal_received_at': signal_received_at,
                    'order_submitted_at': order_submitted_at,
                    'order_type': 'market',
                    'broker': 'robinhood',
                }
            )

            # Check fill
            time.sleep(2)
            try:
                order_status = self._call(self.client.get_order(order_id))
                state = order_status.get('state', order_status.get('status', ''))
                if state in ('filled', 'FILLED'):
                    filled_qty = float(order_status.get('quantity',
                                       order_status.get('filled_qty', 0)))
                    filled_price = float(order_status.get('average_price',
                                         order_status.get('filled_avg_price', 0)))

                    execution_latency_ms = int(
                        (order_submitted_at - signal_received_at).total_seconds() * 1000
                    ) if signal_received_at else None

                    BotConfigDB.update_bot_status(bot_id, self.user_id, 'FILLED',
                                                  position_side=position_after)
                    BotTradesDB.update_trade_status(trade_id, 'FILLED', filled_qty, filled_price,
                                                    execution_details={
                                                        'execution_latency_ms': execution_latency_ms,
                                                        'position_after': position_after,
                                                        'broker': 'robinhood',
                                                    })

                    return {
                        'status': 'success', 'action': action, 'symbol': symbol,
                        'timeframe': timeframe, 'order_id': order_id, 'trade_id': trade_id,
                        'filled_qty': filled_qty, 'filled_price': filled_price,
                        'execution_latency_ms': execution_latency_ms,
                        'broker': 'robinhood'
                    }
            except Exception as e:
                logger.warning(f"Could not check order status: {e}")

            return {'status': 'pending', 'order_id': order_id, 'trade_id': trade_id,
                    'broker': 'robinhood'}

        except Exception as e:
            logger.error(f"{action} ORDER FAILED (Robinhood): {e}")
            BotConfigDB.update_bot_status(bot_id, self.user_id, 'FAILED')
            if trade_id:
                BotTradesDB.update_trade_status(trade_id, 'FAILED', error_msg=str(e))
            return {'status': 'error', 'message': str(e)}

    def cancel_all_orders(self):
        """Cancel all open orders - not directly supported via MCP, returns empty."""
        logger.warning("cancel_all_orders not yet supported via Robinhood MCP")
        return []

    def capture_market_context(self, trade_id: int, symbol: str,
                               current_position: Dict = None) -> bool:
        """Capture market context using Yahoo Finance (same as Alpaca engine)."""
        try:
            account_info = self.get_account_info()
            all_positions = self.get_all_positions()
            context = MarketDataService.get_complete_market_context(
                symbol=symbol,
                alpaca_account=account_info,
                alpaca_position=current_position,
                alpaca_positions=all_positions
            )
            context_id = TradeMarketContextDB.save_context(
                trade_id=trade_id, user_id=self.user_id, context=context
            )
            return context_id is not None
        except Exception as e:
            logger.error(f"Error capturing market context: {e}")
            return False


def get_trading_engine(user_id: int, broker: str = 'alpaca'):
    """
    Factory function - returns the appropriate trading engine based on broker.
    Used by webhook handlers and API server to get the right engine.
    """
    if broker == 'robinhood':
        return RobinhoodTradingEngine(user_id)
    else:
        from bot_engine import TradingEngine
        return TradingEngine(user_id)
