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

    def execute_trade(self, bot_config: Dict, action: str, signal_received_at: datetime = None,
                       signal_source: str = 'webhook') -> Dict:
        """
        Execute a trade based on TradingView signal

        Args:
            bot_config: Bot configuration dict
            action: 'BUY', 'SELL', or 'CLOSE'
            signal_received_at: Timestamp when signal was received (for latency tracking)
            signal_source: Source of the signal ('webhook', 'bot_webhook', 'system', etc.)

        Returns:
            dict: Result with status, order_id, message, and detailed execution info
        """
        # Record signal receipt time if not provided
        if signal_received_at is None:
            signal_received_at = datetime.utcnow()

        symbol = bot_config['symbol']
        timeframe = bot_config['timeframe']
        position_size = float(bot_config['position_size'])
        bot_id = bot_config['id']

        logger.info(f"📨 WEBHOOK: {action} ${position_size} {symbol} {timeframe} (User: {self.user_id}, Source: {signal_source})")

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

            # Log trade with details
            trade_details = {
                'signal_source': signal_source,
                'signal_received_at': signal_received_at,
                'position_before': current_side,
                'position_after': 'FLAT',
                'position_qty_before': current_position.get('qty', 0),
                'position_value_before': current_position.get('market_value', 0)
            }

            BotTradesDB.log_trade(
                user_id=self.user_id,
                bot_config_id=bot_id,
                symbol=symbol,
                timeframe=timeframe,
                action='CLOSE',
                notional=0,
                order_id=None,
                trade_details=trade_details
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
                # Update current position after closing
                current_position = {'side': 'FLAT', 'qty': 0, 'market_value': 0}

            # Execute BUY order with detailed tracking
            return self._execute_long(bot_id, symbol, timeframe, position_size,
                                      signal_received_at=signal_received_at,
                                      current_position=current_position,
                                      signal_source=signal_source)

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
                # Update current position after closing
                current_position = {'side': 'FLAT', 'qty': 0, 'market_value': 0}

            # Execute SELL order with detailed tracking
            return self._execute_short(bot_id, symbol, timeframe, position_size,
                                       signal_received_at=signal_received_at,
                                       current_position=current_position,
                                       signal_source=signal_source)

        return {'status': 'error', 'message': f'Unknown action: {action}'}

    def _execute_long(self, bot_id: int, symbol: str, timeframe: str, position_size: float,
                       signal_received_at: datetime = None, current_position: dict = None,
                       signal_source: str = 'webhook') -> Dict:
        """Execute a BUY (long) order with detailed logging"""
        trade_id = None
        order_submitted_at = None

        try:
            logger.info(f"🟢 Submitting BUY order: ${position_size} {symbol}")

            # Get pre-trade market data
            quote = self.get_price_quote(symbol)
            bid_price = quote.get('bid_price') if 'error' not in quote else None
            ask_price = quote.get('ask_price') if 'error' not in quote else None
            spread = (ask_price - bid_price) if bid_price and ask_price else None
            spread_percent = (spread / ask_price * 100) if spread and ask_price else None
            expected_price = ask_price  # For BUY, we expect to pay the ask

            # Get market status
            clock = self.get_market_clock()
            market_open = clock.get('is_open', False) if 'error' not in clock else None

            # Get account info
            account = self.get_account_info()
            account_equity = account.get('equity')
            account_buying_power = account.get('buying_power')

            # Position context
            position_before = current_position.get('side', 'FLAT') if current_position else 'FLAT'
            position_qty_before = current_position.get('qty', 0) if current_position else 0
            position_value_before = current_position.get('market_value', 0) if current_position else 0

            # Update status: ORDER SUBMITTED
            BotConfigDB.update_bot_status(bot_id, self.user_id, 'ORDER SUBMITTED', last_signal='BUY')

            # Submit order to Alpaca
            order_submitted_at = datetime.utcnow()
            order_request = MarketOrderRequest(
                symbol=symbol,
                notional=position_size,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            order = self.api.submit_order(order_request)

            order_id = str(order.id)
            client_order_id = str(order.client_order_id)
            logger.info(f"✅ ORDER SUBMITTED: {order_id}")

            # Log trade with detailed info
            trade_details = {
                'bid_price': bid_price,
                'ask_price': ask_price,
                'spread': spread,
                'spread_percent': spread_percent,
                'market_open': market_open,
                'extended_hours': not market_open if market_open is not None else None,
                'signal_source': signal_source,
                'signal_received_at': signal_received_at,
                'order_submitted_at': order_submitted_at,
                'expected_price': expected_price,
                'order_type': 'market',
                'time_in_force': 'day',
                'position_before': position_before,
                'position_qty_before': position_qty_before,
                'position_value_before': position_value_before,
                'account_equity': account_equity,
                'account_buying_power': account_buying_power,
                'alpaca_client_order_id': client_order_id
            }

            trade_id = BotTradesDB.log_trade(
                user_id=self.user_id,
                bot_config_id=bot_id,
                symbol=symbol,
                timeframe=timeframe,
                action='BUY',
                notional=position_size,
                order_id=order_id,
                trade_details=trade_details
            )

            # Wait 2 seconds and check status
            time.sleep(2)
            order_status = self.api.get_order_by_id(order_id)
            fill_check_time = datetime.utcnow()

            if order_status.status == 'filled':
                filled_qty = float(order_status.filled_qty)
                filled_price = float(order_status.filled_avg_price)

                # Calculate slippage
                slippage = (filled_price - expected_price) if expected_price else None
                slippage_percent = (slippage / expected_price * 100) if slippage and expected_price else None

                # Calculate timing
                execution_latency_ms = int((order_submitted_at - signal_received_at).total_seconds() * 1000) if signal_received_at else None
                time_to_fill_ms = int((fill_check_time - order_submitted_at).total_seconds() * 1000)

                logger.info(f"✅ ORDER FILLED: {filled_qty} shares @ ${filled_price:.2f} (slippage: ${slippage:.4f})" if slippage else f"✅ ORDER FILLED: {filled_qty} shares @ ${filled_price:.2f}")

                BotConfigDB.update_bot_status(bot_id, self.user_id, 'FILLED', position_side='LONG')
                BotTradesDB.update_trade_status(trade_id, 'FILLED', filled_qty, filled_price,
                    execution_details={
                        'slippage': slippage,
                        'slippage_percent': slippage_percent,
                        'execution_latency_ms': execution_latency_ms,
                        'time_to_fill_ms': time_to_fill_ms,
                        'alpaca_order_status': 'filled',
                        'position_after': 'LONG'
                    })

                return {
                    'status': 'success',
                    'action': 'BUY',
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'order_id': order_id,
                    'filled_qty': filled_qty,
                    'filled_price': filled_price,
                    'expected_price': expected_price,
                    'slippage': slippage,
                    'slippage_percent': slippage_percent,
                    'bid_price': bid_price,
                    'ask_price': ask_price,
                    'spread': spread,
                    'execution_latency_ms': execution_latency_ms,
                    'time_to_fill_ms': time_to_fill_ms,
                    'market_open': market_open
                }
            else:
                logger.warning(f"⏳ ORDER PENDING: {order_status.status}")
                BotTradesDB.update_trade_status(trade_id, order_status.status.upper(),
                    execution_details={'alpaca_order_status': str(order_status.status)})
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

    def _execute_short(self, bot_id: int, symbol: str, timeframe: str, position_size: float,
                        signal_received_at: datetime = None, current_position: dict = None,
                        signal_source: str = 'webhook') -> Dict:
        """Execute a SELL (short) order with detailed logging"""
        trade_id = None
        order_submitted_at = None

        try:
            # Get pre-trade market data
            quote = self.get_price_quote(symbol)
            if 'error' in quote:
                raise Exception(f"Could not get price for {symbol}: {quote['error']}")

            bid_price = float(quote.get('bid_price', 0))
            ask_price = float(quote.get('ask_price', 0))
            spread = (ask_price - bid_price) if bid_price and ask_price else None
            spread_percent = (spread / bid_price * 100) if spread and bid_price else None
            expected_price = bid_price  # For SELL, we expect to receive the bid

            # Fallback to bid if ask is 0 (can happen after hours)
            current_price = max(ask_price, bid_price)

            if current_price <= 0:
                raise Exception(f"Market is closed and no valid price found for {symbol}")

            qty = int(position_size / current_price)

            if qty <= 0:
                raise Exception(f"Position size ${position_size} is too small for 1 whole share of {symbol} @ ${current_price}")

            # Get market status
            clock = self.get_market_clock()
            market_open = clock.get('is_open', False) if 'error' not in clock else None

            # Get account info
            account = self.get_account_info()
            account_equity = account.get('equity')
            account_buying_power = account.get('buying_power')

            # Position context
            position_before = current_position.get('side', 'FLAT') if current_position else 'FLAT'
            position_qty_before = current_position.get('qty', 0) if current_position else 0
            position_value_before = current_position.get('market_value', 0) if current_position else 0

            logger.info(f"🔴 Submitting SELL order: {qty} shares of {symbol} (@ ~${current_price})")

            # Submit order to Alpaca
            order_submitted_at = datetime.utcnow()
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            order = self.api.submit_order(order_request)

            order_id = str(order.id)
            client_order_id = str(order.client_order_id)
            logger.info(f"✅ ORDER SUBMITTED: {order_id}")

            # Log trade with detailed info
            trade_details = {
                'bid_price': bid_price,
                'ask_price': ask_price,
                'spread': spread,
                'spread_percent': spread_percent,
                'market_open': market_open,
                'extended_hours': not market_open if market_open is not None else None,
                'signal_source': signal_source,
                'signal_received_at': signal_received_at,
                'order_submitted_at': order_submitted_at,
                'expected_price': expected_price,
                'order_type': 'market',
                'time_in_force': 'day',
                'position_before': position_before,
                'position_qty_before': position_qty_before,
                'position_value_before': position_value_before,
                'account_equity': account_equity,
                'account_buying_power': account_buying_power,
                'alpaca_client_order_id': client_order_id
            }

            trade_id = BotTradesDB.log_trade(
                user_id=self.user_id,
                bot_config_id=bot_id,
                symbol=symbol,
                timeframe=timeframe,
                action='SELL',
                notional=position_size,
                order_id=order_id,
                trade_details=trade_details
            )

            # Wait 2 seconds and check status
            time.sleep(2)
            order_status = self.api.get_order_by_id(order_id)
            fill_check_time = datetime.utcnow()

            if order_status.status == 'filled':
                filled_qty = float(order_status.filled_qty)
                filled_price = float(order_status.filled_avg_price)

                # Calculate slippage (for SELL, negative slippage means we got less than expected)
                slippage = (expected_price - filled_price) if expected_price else None
                slippage_percent = (slippage / expected_price * 100) if slippage and expected_price else None

                # Calculate timing
                execution_latency_ms = int((order_submitted_at - signal_received_at).total_seconds() * 1000) if signal_received_at else None
                time_to_fill_ms = int((fill_check_time - order_submitted_at).total_seconds() * 1000)

                logger.info(f"✅ ORDER FILLED: {filled_qty} shares @ ${filled_price:.2f} (slippage: ${slippage:.4f})" if slippage else f"✅ ORDER FILLED: {filled_qty} shares @ ${filled_price:.2f}")

                BotConfigDB.update_bot_status(bot_id, self.user_id, 'FILLED', position_side='SHORT')
                BotTradesDB.update_trade_status(trade_id, 'FILLED', filled_qty, filled_price,
                    execution_details={
                        'slippage': slippage,
                        'slippage_percent': slippage_percent,
                        'execution_latency_ms': execution_latency_ms,
                        'time_to_fill_ms': time_to_fill_ms,
                        'alpaca_order_status': 'filled',
                        'position_after': 'SHORT'
                    })

                return {
                    'status': 'success',
                    'action': 'SELL',
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'order_id': order_id,
                    'filled_qty': filled_qty,
                    'filled_price': filled_price,
                    'expected_price': expected_price,
                    'slippage': slippage,
                    'slippage_percent': slippage_percent,
                    'bid_price': bid_price,
                    'ask_price': ask_price,
                    'spread': spread,
                    'execution_latency_ms': execution_latency_ms,
                    'time_to_fill_ms': time_to_fill_ms,
                    'market_open': market_open
                }
            else:
                logger.warning(f"⏳ ORDER PENDING: {order_status.status}")
                BotTradesDB.update_trade_status(trade_id, order_status.status.upper(),
                    execution_details={'alpaca_order_status': str(order_status.status)})
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
