"""
Trading Bot Engine - Multi-user trading execution with risk management
Adapted from standalone bot, now supports per-user Alpaca accounts
"""
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, CryptoLatestQuoteRequest
import logging
from datetime import datetime
import time
from typing import Dict, Optional
from bot_database import (
    BotAPIKeysDB, BotConfigDB, BotTradesDB, RiskEventDB, TradeMarketContextDB
)
from market_data_service import MarketDataService
from email_service import TradeNotificationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    symbol_upper = symbol.upper()
    # Check if it's in our known crypto list
    if symbol_upper in CRYPTO_SYMBOLS:
        return True
    # Check for /USD suffix pattern (common crypto format)
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
    symbol_upper = symbol.upper()
    # Already in correct format
    if '/' in symbol_upper:
        return symbol_upper
    # Convert BTCUSD to BTC/USD
    if symbol_upper.endswith('USD') and len(symbol_upper) >= 6:
        base = symbol_upper[:-3]
        return f"{base}/USD"
    return symbol_upper


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
        self.stock_data_client = StockHistoricalDataClient(self.api_key, self.secret_key)
        self.crypto_data_client = CryptoHistoricalDataClient(self.api_key, self.secret_key)
        # Keep backward compatibility
        self.data_client = self.stock_data_client

        logger.info(f"✅ Trading engine initialized for user {user_id} ({self.mode} mode, stocks + crypto)")

    def capture_market_context(self, trade_id: int, symbol: str, current_position: Dict = None) -> bool:
        """
        Capture comprehensive market context for a trade (async-friendly)
        Called after a trade is logged to capture market snapshot

        Args:
            trade_id: The ID of the trade in bot_trades table
            symbol: The stock symbol traded
            current_position: Current position info from get_current_position

        Returns:
            bool: True if context was saved successfully
        """
        try:
            logger.info(f"📊 Capturing market context for trade {trade_id} ({symbol})...")

            # Get account info
            account_info = self.get_account_info()

            # Get all positions for portfolio context
            all_positions = self.get_all_positions()

            # Get complete market context from Yahoo Finance
            context = MarketDataService.get_complete_market_context(
                symbol=symbol,
                alpaca_account=account_info,
                alpaca_position=current_position,
                alpaca_positions=all_positions
            )

            # Save to database
            context_id = TradeMarketContextDB.save_context(
                trade_id=trade_id,
                user_id=self.user_id,
                context=context
            )

            if context_id:
                logger.info(f"✅ Market context saved (ID: {context_id}, latency: {context.get('fetch_latency_ms')}ms)")
                return True
            else:
                logger.warning(f"⚠️ Failed to save market context for trade {trade_id}")
                return False

        except Exception as e:
            logger.error(f"❌ Error capturing market context: {e}")
            return False

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
        """Get latest quote for a stock or crypto"""
        try:
            symbol_upper = symbol.upper()
            is_crypto = is_crypto_symbol(symbol_upper)

            if is_crypto:
                # Normalize crypto symbol (e.g., BTCUSD -> BTC/USD)
                crypto_symbol = normalize_crypto_symbol(symbol_upper)
                request_params = CryptoLatestQuoteRequest(symbol_or_symbols=crypto_symbol)
                quote = self.crypto_data_client.get_crypto_latest_quote(request_params)

                if crypto_symbol in quote:
                    q = quote[crypto_symbol]
                    return {
                        'symbol': crypto_symbol,
                        'bid_price': float(q.bid_price),
                        'ask_price': float(q.ask_price),
                        'timestamp': q.timestamp.isoformat(),
                        'is_crypto': True
                    }
                return {'error': f"No crypto quote found for {crypto_symbol}"}
            else:
                # Stock quote
                request_params = StockLatestQuoteRequest(symbol_or_symbols=symbol_upper)
                quote = self.stock_data_client.get_stock_latest_quote(request_params)

                if symbol_upper in quote:
                    q = quote[symbol_upper]
                    return {
                        'symbol': symbol_upper,
                        'bid_price': float(q.bid_price),
                        'ask_price': float(q.ask_price),
                        'timestamp': q.timestamp.isoformat(),
                        'is_crypto': False
                    }
                return {'error': f"No quote found for {symbol}"}
        except Exception as e:
            logger.error(f"Error getting quote: {e}")
            return {'error': str(e)}

    def place_manual_order(self, symbol: str, qty: float, side: str, order_type: str = 'market', limit_price: float = None) -> Dict:
        """Place a manual order from the AI Assistant (supports stocks and crypto)"""
        try:
            # Check if crypto and normalize symbol
            is_crypto = is_crypto_symbol(symbol)
            if is_crypto:
                symbol = normalize_crypto_symbol(symbol)
            else:
                symbol = symbol.upper()

            side_enum = OrderSide.BUY if side.upper() == 'BUY' else OrderSide.SELL
            # Use GTC for crypto, DAY for stocks
            time_in_force = TimeInForce.GTC if is_crypto else TimeInForce.DAY

            if order_type.lower() == 'limit' and limit_price:
                request = LimitOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side_enum,
                    type=OrderType.LIMIT,
                    limit_price=limit_price,
                    time_in_force=time_in_force
                )
            else:
                request = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side_enum,
                    time_in_force=time_in_force
                )

            order = self.api.submit_order(request)
            return {
                'status': 'success',
                'order_id': order.id,
                'client_order_id': order.client_order_id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side.value,
                'order_status': order.status.value,
                'is_crypto': is_crypto
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

            # Build list of possible symbol formats to check (for crypto)
            symbols_to_check = [symbol]
            if '/' in symbol:
                # BTC/USD -> also check BTCUSD
                symbols_to_check.append(symbol.replace('/', ''))
            elif is_crypto_symbol(symbol):
                # BTCUSD -> also check BTC/USD
                symbols_to_check.append(normalize_crypto_symbol(symbol))

            for pos in positions:
                if pos.symbol in symbols_to_check:
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
        logger.info(f"🔴 CLOSE POSITION REQUEST for: {symbol}")
        
        # First, check what positions exist in Alpaca
        try:
            all_positions = self.api.get_all_positions()
            position_symbols = [p.symbol for p in all_positions]
            logger.info(f"📊 Positions in Alpaca account: {position_symbols}")
            
            if not position_symbols:
                logger.info(f"ℹ️  No open positions in account")
                return {'status': 'info', 'message': 'No open positions'}
        except Exception as e:
            logger.warning(f"Could not list positions: {e}")
            position_symbols = []
        
        # Find the exact symbol to close from Alpaca's position list
        symbol_to_close = None
        normalized_target = normalize_crypto_symbol(symbol).upper()
        
        for pos_sym in position_symbols:
            normalized_pos = normalize_crypto_symbol(pos_sym).upper()
            if normalized_target == normalized_pos:
                symbol_to_close = pos_sym  # Use exact symbol from Alpaca
                logger.info(f"✅ Found matching position: {pos_sym}")
                break
        
        if not symbol_to_close:
            # Fallback: try the requested symbol directly
            symbol_to_close = normalize_crypto_symbol(symbol) if is_crypto_symbol(symbol) else symbol
            logger.info(f"⚠️  No exact match found, trying: {symbol_to_close}")
        
        # Send ONE close order to Alpaca
        try:
            logger.info(f"🔴 SENDING CLOSE ORDER to Alpaca for: {symbol_to_close}")
            order = self.api.close_position(symbol_to_close)
            logger.info(f"✅ CLOSE ORDER SUBMITTED: {symbol_to_close} - Order ID: {order.id}")
            return {
                'status': 'success', 
                'message': f'Position closed for {symbol_to_close}',
                'order': order,
                'order_id': order.id
            }
        except Exception as e:
            error_str = str(e)
            logger.error(f"❌ Failed to close {symbol_to_close}: {error_str}")
            return {'status': 'error', 'message': error_str}

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

        # Check if this is a crypto trade
        is_crypto = is_crypto_symbol(symbol)
        if is_crypto:
            symbol = normalize_crypto_symbol(symbol)

        asset_type = "CRYPTO" if is_crypto else "STOCK"
        logger.info(f"📨 WEBHOOK: {action} ${position_size} {symbol} {timeframe} [{asset_type}] (User: {self.user_id}, Source: {signal_source})")

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

            # Get position info before closing (including entry price for P&L calculation)
            position_qty_before = abs(current_position.get('qty', 0))
            position_value_before = current_position.get('market_value', 0)
            position_entry_price = current_position.get('entry_price', 0)  # Capture entry price for P&L calculation

            # Get pre-trade market data (same as BUY/SELL orders)
            quote = self.get_price_quote(symbol)
            bid_price = quote.get('bid_price') if 'error' not in quote else None
            ask_price = quote.get('ask_price') if 'error' not in quote else None
            spread = (ask_price - bid_price) if bid_price and ask_price else None
            spread_percent = (spread / bid_price * 100) if spread and bid_price else None
            
            # For CLOSE: if LONG, we're selling (expect bid), if SHORT, we're buying (expect ask)
            if current_side == 'LONG':
                expected_price = bid_price  # Selling, expect bid price
            elif current_side == 'SHORT':
                expected_price = ask_price  # Buying to cover, expect ask price
            else:
                expected_price = bid_price if bid_price else ask_price

            # Get market status (skip for crypto - 24/7)
            is_crypto = is_crypto_symbol(symbol)
            if is_crypto:
                market_open = True  # Crypto markets are always open
                clock = {'is_open': True}
            else:
                clock = self.get_market_clock()
                market_open = clock.get('is_open', False) if 'error' not in clock else None

            # Get account info
            account = self.get_account_info()
            account_equity = account.get('equity')
            account_buying_power = account.get('buying_power')

            close_result = self.close_position(symbol)
            
            if close_result.get('status') != 'success' or not close_result.get('order_id'):
                logger.error(f"❌ Failed to close position: {close_result.get('message')}")
                BotConfigDB.update_bot_status(bot_id, self.user_id, 'FAILED', last_signal='CLOSE')
                return close_result

            order_id = close_result['order_id']
            order_submitted_at = datetime.utcnow()
            BotConfigDB.update_bot_status(bot_id, self.user_id, 'ORDER SUBMITTED', last_signal='CLOSE')

            # Send email notification when CLOSE order is submitted
            try:
                bot_name = f"{symbol} {timeframe}"
                TradeNotificationService.send_trade_executed_email(
                    user_id=self.user_id,
                    trade_data={
                        'symbol': symbol,
                        'action': 'CLOSE',
                        'quantity': position_qty_before,
                        'filled_qty': position_qty_before,
                        'filled_price': None,  # Will be filled when order executes
                        'filled_avg_price': None,
                        'status': 'SUBMITTED',
                        'bot_name': bot_name,
                        'timeframe': timeframe,
                        'order_id': order_id,
                        'trade_id': None  # Will be set after logging
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to send email notification: {e}")

            # Log trade with order ID (include all details like BUY/SELL)
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
                'time_in_force': 'gtc' if is_crypto else 'day',
                'position_before': current_side,
                'position_after': 'FLAT',
                'position_qty_before': position_qty_before,
                'position_value_before': position_value_before,
                'account_equity': account_equity,
                'account_buying_power': account_buying_power,
                'is_crypto': is_crypto
            }

            trade_id = BotTradesDB.log_trade(
                user_id=self.user_id,
                bot_config_id=bot_id,
                symbol=symbol,
                timeframe=timeframe,
                action='CLOSE',
                notional=position_value_before,  # Use position value as notional
                order_id=order_id,
                trade_details=trade_details
            )

            # Wait and check order status with retry logic (same as BUY/SELL)
            max_retries = 3
            retry_delay = 2
            order_status = None
            
            for attempt in range(max_retries):
                time.sleep(retry_delay)
                try:
                    order_status = self.api.get_order_by_id(order_id)
                    
                    if order_status.status == 'filled':
                        filled_qty = float(order_status.filled_qty)
                        filled_price = float(order_status.filled_avg_price)
                        fill_check_time = datetime.utcnow()

                        # Calculate slippage (same as BUY/SELL)
                        slippage = None
                        slippage_percent = None
                        if expected_price:
                            if current_side == 'LONG':
                                # Selling: negative slippage means we got less than expected (bad)
                                slippage = filled_price - expected_price
                            elif current_side == 'SHORT':
                                # Buying to cover: negative slippage means we paid more than expected (bad)
                                slippage = filled_price - expected_price
                            
                            if slippage is not None and expected_price:
                                slippage_percent = (slippage / expected_price * 100)

                        # Calculate realized P&L: (exit_price - entry_price) * quantity
                        # For LONG positions: profit when exit > entry
                        # For SHORT positions: profit when exit < entry (but we're closing, so it's a sell)
                        if current_side == 'LONG':
                            realized_pnl = (filled_price - position_entry_price) * filled_qty
                        elif current_side == 'SHORT':
                            # For SHORT: profit = (entry_price - exit_price) * qty
                            realized_pnl = (position_entry_price - filled_price) * filled_qty
                        else:
                            realized_pnl = 0.0

                        # Calculate timing
                        execution_latency_ms = int((order_submitted_at - signal_received_at).total_seconds() * 1000) if signal_received_at else None
                        time_to_fill_ms = int((fill_check_time - order_submitted_at).total_seconds() * 1000)

                        logger.info(f"✅ CLOSE ORDER FILLED: {filled_qty} shares @ ${filled_price:.2f} | Entry: ${position_entry_price:.2f} | P&L: ${realized_pnl:.2f}" + (f" | Slippage: ${slippage:.4f}" if slippage else ""))

                        BotConfigDB.update_bot_status(bot_id, self.user_id, 'WAITING', last_signal='CLOSE', position_side='FLAT')
                        
                        # Update trade with P&L and all details (same as BUY/SELL)
                        BotTradesDB.update_trade_status(trade_id, 'FILLED', filled_qty, filled_price,
                            execution_details={
                                'slippage': slippage,
                                'slippage_percent': slippage_percent,
                                'execution_latency_ms': execution_latency_ms,
                                'time_to_fill_ms': time_to_fill_ms,
                                'alpaca_order_status': 'filled',
                                'position_after': 'FLAT',
                                'realized_pnl': realized_pnl,
                                'entry_price': position_entry_price,
                                'market_open': market_open
                            })

                        # Update bot's total P&L
                        BotConfigDB.update_bot_pnl(bot_id, self.user_id, realized_pnl)
                        logger.info(f"💰 Updated bot P&L: ${realized_pnl:.2f} (Total P&L updated)")

                        return {
                            'status': 'success',
                            'action': 'CLOSE',
                            'symbol': symbol,
                            'timeframe': timeframe,
                            'order_id': order_id,
                            'trade_id': trade_id,
                            'filled_qty': filled_qty,
                            'filled_price': filled_price,
                            'entry_price': position_entry_price,
                            'realized_pnl': realized_pnl,
                            'slippage': slippage,
                            'slippage_percent': slippage_percent,
                            'execution_latency_ms': execution_latency_ms,
                            'time_to_fill_ms': time_to_fill_ms
                        }
                    elif order_status.status in ['partially_filled', 'pending_new', 'accepted', 'pending_replace']:
                        # Order is still processing, retry
                        logger.info(f"⏳ CLOSE ORDER {order_status.status.upper()} (attempt {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            continue  # Retry
                    else:
                        # Order failed or rejected
                        logger.warning(f"❌ CLOSE ORDER {order_status.status.upper()}")
                        BotTradesDB.update_trade_status(trade_id, order_status.status.upper(),
                            execution_details={'alpaca_order_status': str(order_status.status)})
                        return {
                            'status': 'error',
                            'order_id': order_id,
                            'order_status': order_status.status,
                            'message': f"Order {order_status.status}"
                        }
                except Exception as e:
                    logger.error(f"❌ Error checking close order status (attempt {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        continue  # Retry
                    else:
                        # Final attempt failed
                        logger.error(f"❌ Failed to check order status after {max_retries} attempts")
                        BotTradesDB.update_trade_status(trade_id, 'ERROR',
                            error_msg=f"Failed to check order status: {str(e)}")
                        return {
                            'status': 'error',
                            'order_id': order_id,
                            'message': f"Failed to check order status: {str(e)}"
                        }
            
            # If we get here, order is still pending after all retries
            logger.warning(f"⏳ CLOSE ORDER STILL PENDING after {max_retries} attempts")
            BotTradesDB.update_trade_status(trade_id, 'PENDING',
                execution_details={'alpaca_order_status': 'pending'})
            return {
                'status': 'pending',
                'order_id': order_id,
                'order_status': 'pending',
                'message': f"Order still pending after {max_retries} checks"
            }

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
                                      signal_source=signal_source,
                                      is_crypto=is_crypto)

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
                                       signal_source=signal_source,
                                       is_crypto=is_crypto)

        return {'status': 'error', 'message': f'Unknown action: {action}'}

    def _execute_long(self, bot_id: int, symbol: str, timeframe: str, position_size: float,
                       signal_received_at: datetime = None, current_position: dict = None,
                       signal_source: str = 'webhook', is_crypto: bool = False) -> Dict:
        """Execute a BUY (long) order with detailed logging (supports stocks and crypto)"""
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

            # Get market status (skip for crypto - 24/7)
            if is_crypto:
                market_open = True  # Crypto markets are always open
                clock = {'is_open': True}
            else:
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
            # Use GTC (good till canceled) for crypto, DAY for stocks
            order_submitted_at = datetime.utcnow()
            time_in_force = TimeInForce.GTC if is_crypto else TimeInForce.DAY
            order_request = MarketOrderRequest(
                symbol=symbol,
                notional=position_size,
                side=OrderSide.BUY,
                time_in_force=time_in_force
            )
            order = self.api.submit_order(order_request)

            order_id = str(order.id)
            client_order_id = str(order.client_order_id)
            logger.info(f"✅ ORDER SUBMITTED: {order_id} [{'CRYPTO' if is_crypto else 'STOCK'}]")

            # Send email notification when BUY order is submitted
            try:
                bot_name = f"{symbol} {timeframe}"
                TradeNotificationService.send_trade_executed_email(
                    user_id=self.user_id,
                    trade_data={
                        'symbol': symbol,
                        'action': 'BUY',
                        'quantity': None,  # Will be filled when order executes
                        'filled_qty': None,
                        'filled_price': expected_price,  # Expected price
                        'filled_avg_price': expected_price,
                        'status': 'SUBMITTED',
                        'bot_name': bot_name,
                        'timeframe': timeframe,
                        'order_id': order_id,
                        'trade_id': None  # Will be set after logging
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to send email notification: {e}")

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
                'time_in_force': 'gtc' if is_crypto else 'day',
                'position_before': position_before,
                'position_qty_before': position_qty_before,
                'position_value_before': position_value_before,
                'account_equity': account_equity,
                'account_buying_power': account_buying_power,
                'alpaca_client_order_id': client_order_id,
                'is_crypto': is_crypto
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

                # Capture comprehensive market context (async-friendly, won't block response)
                try:
                    self.capture_market_context(trade_id, symbol, current_position)
                except Exception as ctx_err:
                    logger.warning(f"Market context capture failed (non-critical): {ctx_err}")

                return {
                    'status': 'success',
                    'action': 'BUY',
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'order_id': order_id,
                    'trade_id': trade_id,
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
                        signal_source: str = 'webhook', is_crypto: bool = False) -> Dict:
        """Execute a SELL (short) order with detailed logging (supports stocks and crypto)"""
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

            # Get market status (skip for crypto - 24/7)
            if is_crypto:
                market_open = True  # Crypto markets are always open
                clock = {'is_open': True}
            else:
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

            asset_type = "CRYPTO" if is_crypto else "STOCK"
            logger.info(f"🔴 Submitting SELL order: {qty} of {symbol} (@ ~${current_price}) [{asset_type}]")

            # Submit order to Alpaca
            # Use GTC (good till canceled) for crypto, DAY for stocks
            order_submitted_at = datetime.utcnow()
            time_in_force = TimeInForce.GTC if is_crypto else TimeInForce.DAY
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=time_in_force
            )
            order = self.api.submit_order(order_request)

            order_id = str(order.id)
            client_order_id = str(order.client_order_id)
            logger.info(f"✅ ORDER SUBMITTED: {order_id} [{'CRYPTO' if is_crypto else 'STOCK'}]")

            # Send email notification when SELL order is submitted
            try:
                bot_name = f"{symbol} {timeframe}"
                TradeNotificationService.send_trade_executed_email(
                    user_id=self.user_id,
                    trade_data={
                        'symbol': symbol,
                        'action': 'SELL',
                        'quantity': qty,
                        'filled_qty': qty,
                        'filled_price': expected_price,  # Expected price
                        'filled_avg_price': expected_price,
                        'status': 'SUBMITTED',
                        'bot_name': bot_name,
                        'timeframe': timeframe,
                        'order_id': order_id,
                        'trade_id': None  # Will be set after logging
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to send email notification: {e}")

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
                'time_in_force': 'gtc' if is_crypto else 'day',
                'position_before': position_before,
                'position_qty_before': position_qty_before,
                'position_value_before': position_value_before,
                'account_equity': account_equity,
                'account_buying_power': account_buying_power,
                'alpaca_client_order_id': client_order_id,
                'is_crypto': is_crypto
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

                # Capture comprehensive market context (async-friendly, won't block response)
                try:
                    self.capture_market_context(trade_id, symbol, current_position)
                except Exception as ctx_err:
                    logger.warning(f"Market context capture failed (non-critical): {ctx_err}")

                return {
                    'status': 'success',
                    'action': 'SELL',
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'order_id': order_id,
                    'trade_id': trade_id,
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

    def get_recent_trades(self, days: int = 7, limit: int = 20) -> list:
        """Get recent trades from Alpaca API"""
        try:
            from datetime import timedelta
            import requests
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Use REST API directly for account activities
            base_url = "https://paper-api.alpaca.markets" if self.mode == 'paper' else "https://api.alpaca.markets"
            url = f"{base_url}/v2/account/activities"
            
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key
            }
            
            params = {
                "activity_types": "FILL",
                "date": start_date.strftime('%Y-%m-%d'),
                "page_size": limit
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            activities = response.json()
            
            # Convert to list of dicts
            trades = []
            for activity in activities[:limit]:
                trades.append({
                    'symbol': activity.get('symbol', ''),
                    'side': activity.get('side', '').upper(),
                    'qty': float(activity.get('qty', 0)),
                    'price': float(activity.get('price', 0)),
                    'transaction_time': datetime.fromisoformat(activity.get('transaction_time', '').replace('Z', '+00:00')) if activity.get('transaction_time') else datetime.now(),
                    'order_id': activity.get('order_id')
                })
            
            # Sort by most recent first
            trades.sort(key=lambda x: x['transaction_time'], reverse=True)
            return trades[:limit]
        except Exception as e:
            logger.error(f"Error getting recent trades: {e}")
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
