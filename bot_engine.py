"""
Trading Bot Engine - Multi-user trading execution with risk management
Adapted from standalone bot, now supports per-user Alpaca accounts
"""
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
import logging
from datetime import datetime
import time
from typing import Dict, Optional
from bot_database import (
    BotAPIKeysDB, BotConfigDB, BotTradesDB, RiskEventDB
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradingEngine:
    """Execute trades for multi-user bot system"""

    def __init__(self, user_id: int):
        """
        Initialize trading engine for specific user

        Args:
            user_id: User ID

        Raises:
            ValueError: If user has no API keys configured
        """
        self.user_id = user_id

        # Get user's Alpaca API keys
        keys = BotAPIKeysDB.get_api_keys(user_id)
        if not keys:
            raise ValueError(f"No Alpaca API keys found for user {user_id}")

        self.api_key = keys['api_key']
        self.secret_key = keys['secret_key']
        self.mode = keys['mode']

        # Initialize Alpaca API (new alpaca-py library)
        paper = (self.mode == 'paper')
        self.api = TradingClient(self.api_key, self.secret_key, paper=paper)
        self.data_client = StockHistoricalDataClient(self.api_key, self.secret_key)

        logger.info(f"✅ Trading engine initialized for user {user_id} ({self.mode} mode)")

    def get_market_clock(self) -> Dict:
        """Get Alpaca market clock"""
        try:
            clock = self.api.get_clock()
            return {
                'timestamp': clock.timestamp.isoformat(),
                'is_open': clock.is_open,
                'next_open': clock.next_open.isoformat(),
                'next_close': clock.next_close.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting clock: {e}")
            return {'error': str(e)}

    def get_price_quote(self, symbol: str) -> Dict:
        """Get latest quote for a stock"""
        try:
            request_params = StockLatestQuoteRequest(symbol_or_symbols=symbol.upper())
            quote = self.data_client.get_stock_latest_quote(request_params)
            
            # The result is a dictionary-like object mapping symbols to quotes
            if symbol.upper() in quote:
                q = quote[symbol.upper()]
                return {
                    'symbol': symbol.upper(),
                    'bid_price': float(q.bid_price),
                    'ask_price': float(q.ask_price),
                    'timestamp': q.timestamp.isoformat()
                }
            return {'error': f"No quote found for {symbol}"}
        except Exception as e:
            logger.error(f"Error getting quote: {e}")
            return {'error': str(e)}

    def place_manual_order(self, symbol: str, qty: float, side: str, order_type: str = 'market', limit_price: float = None) -> Dict:
        """Place a manual order from the AI Assistant"""
        try:
            side_enum = OrderSide.BUY if side.upper() == 'BUY' else OrderSide.SELL
            
            if order_type.lower() == 'limit' and limit_price:
                request = LimitOrderRequest(
                    symbol=symbol.upper(),
                    qty=qty,
                    side=side_enum,
                    type=OrderType.LIMIT,
                    limit_price=limit_price,
                    time_in_force=TimeInForce.DAY
                )
            else:
                request = MarketOrderRequest(
                    symbol=symbol.upper(),
                    qty=qty,
                    side=side_enum,
                    time_in_force=TimeInForce.DAY
                )
            
            order = self.api.submit_order(request)
            return {
                'status': 'success',
                'order_id': order.id,
                'client_order_id': order.client_order_id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side.value,
                'order_status': order.status.value
            }
        except Exception as e:
            logger.error(f"Error placing manual order: {e}")
            return {'status': 'error', 'message': str(e)}

    def get_current_position(self, symbol: str) -> Optional[Dict]:
        """
        Get current position for a symbol

        Returns:
            dict: {'side': 'LONG'|'SHORT'|'FLAT', 'qty': float, 'market_value': float} or None
        """
        try:
            positions = self.api.get_all_positions()
            for pos in positions:
                if pos.symbol == symbol:
                    qty = float(pos.qty)
                    return {
                        'side': 'LONG' if qty > 0 else 'SHORT',
                        'qty': abs(qty),
                        'market_value': float(pos.market_value),
                        'unrealized_pl': float(pos.unrealized_pl),
                        'entry_price': float(pos.avg_entry_price)
                    }
            return {'side': 'FLAT', 'qty': 0, 'market_value': 0, 'unrealized_pl': 0}
        except Exception as e:
            logger.error(f"❌ Error getting position for {symbol}: {e}")
            return None

    def check_risk_limits(self, bot_config: Dict, current_position: Dict) -> Dict:
        """
        Check if bot has hit risk limits

        Returns:
            dict: {'hit': bool, 'reason': str, 'action': str}
        """
        if not current_position or current_position['side'] == 'FLAT':
            return {'hit': False}

        risk_limit_percent = bot_config.get('risk_limit_percent', 10.0)
        unrealized_pl = current_position.get('unrealized_pl', 0)
        market_value = abs(current_position.get('market_value', 0))

        if market_value == 0:
            return {'hit': False}

        # Calculate current loss percentage
        loss_percent = (unrealized_pl / market_value) * 100

        # Check if loss exceeds risk limit
        if loss_percent < 0 and abs(loss_percent) >= risk_limit_percent:
            logger.warning(
                f"⚠️  RISK LIMIT HIT: {bot_config['symbol']} {bot_config['timeframe']} - "
                f"Loss: {loss_percent:.2f}% (Limit: {risk_limit_percent}%)"
            )

            # Log risk event
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

    def close_position(self, symbol: str) -> Dict:
        """
        Close entire position for a symbol

        Returns:
            dict: {'status': 'success'|'error', 'message': str}
        """
        try:
            logger.info(f"🔴 Closing position: {symbol}")
            self.api.close_position(symbol)
            time.sleep(2)  # Wait for order to process

            return {'status': 'success', 'message': f'Position closed for {symbol}'}
        except Exception as e:
            logger.error(f"❌ Error closing position {symbol}: {e}")
            return {'status': 'error', 'message': str(e)}

    def execute_trade(self, bot_config: Dict, action: str) -> Dict:
        """
        Execute a trade based on TradingView signal

        Args:
            bot_config: Bot configuration dict
            action: 'BUY', 'SELL', or 'CLOSE'

        Returns:
            dict: Result with status, order_id, message
        """
        symbol = bot_config['symbol']
        timeframe = bot_config['timeframe']
        position_size = float(bot_config['position_size'])
        bot_id = bot_config['id']

        logger.info(f"📨 WEBHOOK: {action} ${position_size} {symbol} {timeframe} (User: {self.user_id})")

        # Get current position
        current_position = self.get_current_position(symbol)
        if not current_position:
            return {'status': 'error', 'message': 'Failed to get current position'}

        current_side = current_position['side']

        # Check risk limits BEFORE executing
        risk_check = self.check_risk_limits(bot_config, current_position)
        if risk_check['hit']:
            # Close position and disable bot
            close_result = self.close_position(symbol)
            BotConfigDB.toggle_bot(bot_id, self.user_id, False)
            BotConfigDB.update_bot_status(bot_id, self.user_id, 'RISK_LIMIT_HIT', position_side='FLAT')

            return {
                'status': 'risk_limit',
                'message': f"Risk limit hit: {risk_check['reason']}. Position closed, bot disabled.",
                'action_taken': 'POSITION_CLOSED_BOT_DISABLED'
            }

        # Handle CLOSE signal
        if action == 'CLOSE':
            if current_side == 'FLAT':
                logger.info(f"ℹ️  {symbol} already flat")
                return {'status': 'info', 'message': 'Already flat'}

            close_result = self.close_position(symbol)
            BotConfigDB.update_bot_status(bot_id, self.user_id, 'WAITING', last_signal='CLOSE', position_side='FLAT')

            # Log trade
            BotTradesDB.log_trade(
                user_id=self.user_id,
                bot_config_id=bot_id,
                symbol=symbol,
                timeframe=timeframe,
                action='CLOSE',
                notional=0,
                order_id=None
            )

            return close_result

        # Handle BUY signal
        if action == 'BUY':
            # Check if already long
            if current_side == 'LONG':
                logger.info(f"⏭️  {symbol} already LONG - skipping")
                BotConfigDB.update_bot_status(bot_id, self.user_id, 'ALREADY LONG')
                return {'status': 'skipped', 'message': 'Already long'}

            # Close short position first if needed
            if current_side == 'SHORT':
                logger.info(f"🔄 Closing SHORT position before buying")
                self.close_position(symbol)
                time.sleep(1)

            # Execute BUY order
            return self._execute_long(bot_id, symbol, timeframe, position_size)

        # Handle SELL signal
        if action == 'SELL':
            # Check if already short
            if current_side == 'SHORT':
                logger.info(f"⏭️  {symbol} already SHORT - skipping")
                BotConfigDB.update_bot_status(bot_id, self.user_id, 'ALREADY SHORT')
                return {'status': 'skipped', 'message': 'Already short'}

            # Close long position first if needed
            if current_side == 'LONG':
                logger.info(f"🔄 Closing LONG position before shorting")
                self.close_position(symbol)
                time.sleep(1)

            # Execute SELL order
            return self._execute_short(bot_id, symbol, timeframe, position_size)

        return {'status': 'error', 'message': f'Unknown action: {action}'}

    def _execute_long(self, bot_id: int, symbol: str, timeframe: str, position_size: float) -> Dict:
        """Execute a BUY (long) order"""
        trade_id = None
        try:
            logger.info(f"🟢 Submitting BUY order: ${position_size} {symbol}")

            # Update status: ORDER SUBMITTED
            BotConfigDB.update_bot_status(bot_id, self.user_id, 'ORDER SUBMITTED', last_signal='BUY')

            # Submit order to Alpaca (new alpaca-py API)
            order_request = MarketOrderRequest(
                symbol=symbol,
                notional=position_size,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            order = self.api.submit_order(order_request)

            order_id = str(order.id)
            logger.info(f"✅ ORDER SUBMITTED: {order_id}")

            # Log trade
            trade_id = BotTradesDB.log_trade(
                user_id=self.user_id,
                bot_config_id=bot_id,
                symbol=symbol,
                timeframe=timeframe,
                action='BUY',
                notional=position_size,
                order_id=order_id
            )

            # Wait 2 seconds and check status
            time.sleep(2)
            order_status = self.api.get_order_by_id(order_id)

            if order_status.status == 'filled':
                filled_qty = float(order_status.filled_qty)
                filled_price = float(order_status.filled_avg_price)

                logger.info(f"✅ ORDER FILLED: {filled_qty} shares @ ${filled_price}")

                BotConfigDB.update_bot_status(bot_id, self.user_id, 'FILLED', position_side='LONG')
                BotTradesDB.update_trade_status(trade_id, 'FILLED', filled_qty, filled_price)

                return {
                    'status': 'success',
                    'action': 'BUY',
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'order_id': order_id,
                    'filled_qty': filled_qty,
                    'filled_price': filled_price
                }
            else:
                logger.warning(f"⏳ ORDER PENDING: {order_status.status}")
                BotTradesDB.update_trade_status(trade_id, order_status.status.upper())
                return {
                    'status': 'pending',
                    'order_id': order_id,
                    'order_status': order_status.status
                }

        except Exception as e:
            logger.error(f"❌ BUY ORDER FAILED: {e}")
            BotConfigDB.update_bot_status(bot_id, self.user_id, 'FAILED')
            if trade_id:
                BotTradesDB.update_trade_status(trade_id, 'FAILED', error_msg=str(e))
            return {'status': 'error', 'message': str(e)}

    def _execute_short(self, bot_id: int, symbol: str, timeframe: str, position_size: float) -> Dict:
        """Execute a SELL (short) order"""
        trade_id = None
        try:
            # Shorting typically requires whole shares (cannot use notional for shorting on Alpaca)
            quote = self.get_price_quote(symbol)
            if 'error' in quote:
                raise Exception(f"Could not get price for {symbol}: {quote['error']}")
            
            # Fallback to bid if ask is 0 (can happen after hours)
            current_price = max(float(quote.get('ask_price', 0)), float(quote.get('bid_price', 0)))
            
            if current_price <= 0:
                raise Exception(f"Market is closed and no valid price found for {symbol}")
            
            qty = int(position_size / current_price)
            
            if qty <= 0:
                raise Exception(f"Position size ${position_size} is too small for 1 whole share of {symbol} @ ${current_price}")

            logger.info(f"🔴 Submitting SELL order: {qty} shares of {symbol} (@ ~${current_price})")

            # Submit order to Alpaca (new alpaca-py API)
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            order = self.api.submit_order(order_request)

            order_id = str(order.id)
            logger.info(f"✅ ORDER SUBMITTED: {order_id}")

            # Log trade
            trade_id = BotTradesDB.log_trade(
                user_id=self.user_id,
                bot_config_id=bot_id,
                symbol=symbol,
                timeframe=timeframe,
                action='SELL',
                notional=position_size,
                order_id=order_id
            )

            # Wait 2 seconds and check status
            time.sleep(2)
            order_status = self.api.get_order_by_id(order_id)

            if order_status.status == 'filled':
                filled_qty = float(order_status.filled_qty)
                filled_price = float(order_status.filled_avg_price)

                logger.info(f"✅ ORDER FILLED: {filled_qty} shares @ ${filled_price}")

                BotConfigDB.update_bot_status(bot_id, self.user_id, 'FILLED', position_side='SHORT')
                BotTradesDB.update_trade_status(trade_id, 'FILLED', filled_qty, filled_price)

                return {
                    'status': 'success',
                    'action': 'SELL',
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'order_id': order_id,
                    'filled_qty': filled_qty,
                    'filled_price': filled_price
                }
            else:
                logger.warning(f"⏳ ORDER PENDING: {order_status.status}")
                BotTradesDB.update_trade_status(trade_id, order_status.status.upper())
                return {
                    'status': 'pending',
                    'order_id': order_id,
                    'order_status': order_status.status
                }

        except Exception as e:
            logger.error(f"❌ SELL ORDER FAILED: {e}")
            BotConfigDB.update_bot_status(bot_id, self.user_id, 'FAILED')
            if trade_id:
                BotTradesDB.update_trade_status(trade_id, 'FAILED', error_msg=str(e))
            return {'status': 'error', 'message': str(e)}

    def get_account_info(self) -> Dict:
        """Get Alpaca account information"""
        try:
            account = self.api.get_account()
            return {
                'equity': float(account.equity),
                'cash': float(account.cash),
                'buying_power': float(account.buying_power),
                'portfolio_value': float(account.portfolio_value)
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}

    def get_all_positions(self) -> list:
        """Get all current positions"""
        try:
            positions = self.api.get_all_positions()
            return [{
                'symbol': pos.symbol,
                'qty': float(pos.qty),
                'side': 'LONG' if float(pos.qty) > 0 else 'SHORT',
                'market_value': float(pos.market_value),
                'unrealized_pl': float(pos.unrealized_pl),
                'unrealized_plpc': float(pos.unrealized_plpc) * 100,
                'entry_price': float(pos.avg_entry_price),
                'current_price': float(pos.current_price)
            } for pos in positions]
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def cancel_all_orders(self):
        """Cancel all open orders"""
        try:
            results = self.api.cancel_orders()
            logger.info(f"✅ Cancelled all open orders: {results}")
            return results
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
            return []
