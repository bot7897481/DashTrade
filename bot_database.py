"""
Database operations for Trading Bot system
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import secrets
from encryption import encrypt_alpaca_keys, decrypt_alpaca_keys

from database import get_db_connection, DATABASE_URL

class BotAPIKeysDB:
    """Manage user Alpaca API keys"""

    @staticmethod
    def save_api_keys(user_id: int, api_key: str, secret_key: str, mode: str = 'paper') -> Tuple[bool, str]:
        """
        Save or update user's Alpaca API keys (encrypted)

        Args:
            user_id: User ID
            api_key: Alpaca API key (plain text)
            secret_key: Alpaca secret key (plain text)
            mode: 'paper' or 'live'

        Returns:
            Tuple[bool, str]: (Success status, error message if failed)
        """
        try:
            # Encrypt keys
            enc_api_key, enc_secret_key = encrypt_alpaca_keys(api_key, secret_key)

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO user_api_keys
                        (user_id, alpaca_api_key_encrypted, alpaca_secret_key_encrypted, alpaca_mode, updated_at)
                        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (user_id) DO UPDATE
                        SET alpaca_api_key_encrypted = %s,
                            alpaca_secret_key_encrypted = %s,
                            alpaca_mode = %s,
                            updated_at = CURRENT_TIMESTAMP,
                            is_active = TRUE
                    """, (user_id, enc_api_key, enc_secret_key, mode,
                          enc_api_key, enc_secret_key, mode))
            return True, ""
        except ValueError as e:
            # Encryption key not set
            error_msg = str(e)
            print(f"Error saving API keys (encryption): {error_msg}")
            if "ENCRYPTION_KEY" in error_msg:
                return False, "Server configuration error: ENCRYPTION_KEY not set. Please contact admin."
            return False, f"Encryption error: {error_msg}"
        except Exception as e:
            error_msg = str(e)
            print(f"Error saving API keys: {error_msg}")
            if "user_api_keys" in error_msg.lower() and "does not exist" in error_msg.lower():
                return False, "Database table missing. Please run migrations."
            return False, f"Database error: {error_msg}"

    @staticmethod
    def get_api_keys(user_id: int) -> Optional[Dict]:
        """
        Get user's Alpaca API keys (decrypted)

        Args:
            user_id: User ID

        Returns:
            dict: {'api_key': str, 'secret_key': str, 'mode': str} or None
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT alpaca_api_key_encrypted, alpaca_secret_key_encrypted, alpaca_mode
                        FROM user_api_keys
                        WHERE user_id = %s AND is_active = TRUE
                    """, (user_id,))
                    row = cur.fetchone()

                    if not row:
                        return None

                    # Decrypt keys
                    api_key, secret_key = decrypt_alpaca_keys(
                        row['alpaca_api_key_encrypted'],
                        row['alpaca_secret_key_encrypted']
                    )

                    return {
                        'api_key': api_key,
                        'secret_key': secret_key,
                        'mode': row['alpaca_mode']
                    }
        except Exception as e:
            print(f"Error getting API keys: {e}")
            return None

    @staticmethod
    def has_api_keys(user_id: int) -> bool:
        """Check if user has API keys configured"""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM user_api_keys
                    WHERE user_id = %s AND is_active = TRUE
                """, (user_id,))
                return cur.fetchone() is not None

    @staticmethod
    def delete_api_keys(user_id: int) -> bool:
        """Delete user's API keys"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM user_api_keys WHERE user_id = %s", (user_id,))
            return True
        except Exception:
            return False


class BotConfigDB:
    """Manage bot configurations"""

    @staticmethod
    def create_bot(user_id: int, symbol: str, timeframe: str, position_size: float,
                   strategy_name: str = None, risk_limit_percent: float = 10.0,
                   daily_loss_limit: float = None, max_position_size: float = None,
                   signal_source: str = 'webhook', strategy_type: str = 'none') -> Optional[int]:
        """
        Create a new bot configuration with unique webhook token

        Returns:
            int: Bot ID or None on failure
        """
        try:
            # Generate unique webhook token for this bot
            webhook_token = f"bot_{secrets.token_urlsafe(32)}"

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO user_bot_configs
                        (user_id, symbol, timeframe, position_size, strategy_name,
                         risk_limit_percent, daily_loss_limit, max_position_size,
                         signal_source, strategy_type, webhook_token)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (user_id, symbol.upper(), timeframe, position_size, strategy_name,
                          risk_limit_percent, daily_loss_limit, max_position_size,
                          signal_source, strategy_type, webhook_token))
                    return cur.fetchone()[0]
        except Exception as e:
            print(f"Error creating bot: {e}")
            return None

    @staticmethod
    def get_bot_by_webhook_token(token: str) -> Optional[Dict]:
        """
        Get bot configuration by webhook token

        Returns:
            dict: Bot config with user_id or None if not found
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM user_bot_configs
                        WHERE webhook_token = %s AND is_active = TRUE
                    """, (token,))
                    result = cur.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            print(f"Error getting bot by token: {e}")
            return None

    @staticmethod
    def regenerate_bot_webhook_token(bot_id: int, user_id: int) -> Optional[str]:
        """
        Regenerate webhook token for a bot

        Returns:
            str: New token or None on failure
        """
        try:
            new_token = f"bot_{secrets.token_urlsafe(32)}"
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE user_bot_configs
                        SET webhook_token = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND user_id = %s
                        RETURNING webhook_token
                    """, (new_token, bot_id, user_id))
                    result = cur.fetchone()
                    return result[0] if result else None
        except Exception as e:
            print(f"Error regenerating bot token: {e}")
            return None

    @staticmethod
    def get_user_bots(user_id: int, active_only: bool = False) -> List[Dict]:
        """Get all bot configurations for a user"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT * FROM user_bot_configs
                    WHERE user_id = %s
                """
                if active_only:
                    query += " AND is_active = TRUE"
                query += " ORDER BY created_at DESC"

                cur.execute(query, (user_id,))
                return [dict(row) for row in cur.fetchall()]

    @staticmethod
    def get_all_active_internal_bots() -> List[Dict]:
        """Get all active bots across all users that use internal signal source"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM user_bot_configs
                    WHERE is_active = TRUE AND signal_source LIKE 'internal%'
                """)
                return [dict(row) for row in cur.fetchall()]

    @staticmethod
    def get_bot_by_symbol_timeframe(user_id: int, symbol: str, timeframe: str,
                                    signal_source: str = None) -> Optional[Dict]:
        """
        Get specific bot configuration

        Args:
            user_id: User ID
            symbol: Trading symbol
            timeframe: Timeframe
            signal_source: Optional - filter by signal source (webhook, system, internal, etc.)
        """
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if signal_source:
                    cur.execute("""
                        SELECT * FROM user_bot_configs
                        WHERE user_id = %s AND symbol = %s AND timeframe = %s AND signal_source = %s
                    """, (user_id, symbol.upper(), timeframe, signal_source.lower()))
                else:
                    # For webhook lookups, prioritize 'webhook' signal source
                    cur.execute("""
                        SELECT * FROM user_bot_configs
                        WHERE user_id = %s AND symbol = %s AND timeframe = %s
                        ORDER BY CASE WHEN signal_source = 'webhook' THEN 0 ELSE 1 END
                        LIMIT 1
                    """, (user_id, symbol.upper(), timeframe))
                row = cur.fetchone()
                return dict(row) if row else None

    @staticmethod
    def get_bots_by_symbol_timeframe(user_id: int, symbol: str, timeframe: str) -> List[Dict]:
        """Get ALL bot configurations for a symbol+timeframe (multiple signal sources)"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM user_bot_configs
                    WHERE user_id = %s AND symbol = %s AND timeframe = %s
                    ORDER BY created_at DESC
                """, (user_id, symbol.upper(), timeframe))
                return [dict(row) for row in cur.fetchall()]

    @staticmethod
    def update_bot_status(bot_id: int, user_id: int, status: str,
                         last_signal: str = None, position_side: str = None) -> bool:
        """Update bot order status and tracking"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    updates = ["order_status = %s", "updated_at = CURRENT_TIMESTAMP"]
                    params = [status]

                    if last_signal:
                        updates.append("last_signal = %s")
                        updates.append("last_signal_time = CURRENT_TIMESTAMP")
                        params.extend([last_signal])

                    if position_side:
                        updates.append("current_position_side = %s")
                        params.append(position_side)

                    params.extend([bot_id, user_id])

                    query = f"""
                        UPDATE user_bot_configs
                        SET {', '.join(updates)}
                        WHERE id = %s AND user_id = %s
                    """
                    cur.execute(query, params)
            return True
        except Exception as e:
            print(f"Error updating bot status: {e}")
            return False

    @staticmethod
    def toggle_bot(bot_id: int, user_id: int, is_active: bool) -> bool:
        """Enable/disable a bot"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE user_bot_configs
                        SET is_active = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND user_id = %s
                    """, (is_active, bot_id, user_id))
            return True
        except Exception:
            return False

    @staticmethod
    def delete_bot(bot_id: int, user_id: int) -> bool:
        """Delete a bot configuration"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM user_bot_configs
                        WHERE id = %s AND user_id = %s
                    """, (bot_id, user_id))
            return True
        except Exception:
            return False

    @staticmethod
    def update_bot_pnl(bot_id: int, user_id: int, pnl_change: float) -> bool:
        """Update bot's total P&L and trade count"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE user_bot_configs
                        SET total_pnl = total_pnl + %s,
                            total_trades = total_trades + 1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND user_id = %s
                    """, (pnl_change, bot_id, user_id))
            return True
        except Exception:
            return False


class BotTradesDB:
    """Manage trade executions"""

    @staticmethod
    def log_trade(user_id: int, bot_config_id: int, symbol: str, timeframe: str,
                  action: str, notional: float, order_id: str = None,
                  trade_details: Dict = None) -> Optional[int]:
        """
        Log a new trade execution with detailed information

        Args:
            user_id: User ID
            bot_config_id: Bot configuration ID
            symbol: Trading symbol
            timeframe: Timeframe
            action: BUY, SELL, or CLOSE
            notional: Dollar amount
            order_id: Alpaca order ID
            trade_details: Optional dict with additional trade info:
                - bid_price, ask_price, spread, spread_percent
                - market_open, extended_hours
                - signal_source, signal_received_at, order_submitted_at
                - expected_price, order_type, time_in_force
                - position_before, position_after, position_qty_before, position_value_before
                - account_equity, account_buying_power
                - alpaca_client_order_id

        Returns:
            int: Trade ID
        """
        try:
            details = trade_details or {}

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO bot_trades
                        (user_id, bot_config_id, symbol, timeframe, action, notional, order_id, status,
                         bid_price, ask_price, spread, spread_percent,
                         market_open, extended_hours,
                         signal_source, signal_received_at, order_submitted_at,
                         expected_price, order_type, time_in_force,
                         position_before, position_after, position_qty_before, position_value_before,
                         account_equity, account_buying_power, alpaca_client_order_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'SUBMITTED',
                                %s, %s, %s, %s,
                                %s, %s,
                                %s, %s, %s,
                                %s, %s, %s,
                                %s, %s, %s, %s,
                                %s, %s, %s)
                        RETURNING id
                    """, (
                        user_id, bot_config_id, symbol, timeframe, action, notional, order_id,
                        details.get('bid_price'), details.get('ask_price'),
                        details.get('spread'), details.get('spread_percent'),
                        details.get('market_open'), details.get('extended_hours', False),
                        details.get('signal_source', 'webhook'),
                        details.get('signal_received_at'), details.get('order_submitted_at'),
                        details.get('expected_price'), details.get('order_type', 'market'),
                        details.get('time_in_force', 'day'),
                        details.get('position_before'), details.get('position_after'),
                        details.get('position_qty_before', 0), details.get('position_value_before', 0),
                        details.get('account_equity'), details.get('account_buying_power'),
                        details.get('alpaca_client_order_id')
                    ))
                    return cur.fetchone()[0]
        except Exception as e:
            print(f"Error logging trade: {e}")
            # Fallback to simple insert if new columns don't exist yet
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO bot_trades
                            (user_id, bot_config_id, symbol, timeframe, action, notional, order_id, status)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, 'SUBMITTED')
                            RETURNING id
                        """, (user_id, bot_config_id, symbol, timeframe, action, notional, order_id))
                        return cur.fetchone()[0]
            except Exception as e2:
                print(f"Error in fallback trade logging: {e2}")
                return None

    @staticmethod
    def update_trade_status(trade_id: int, status: str, filled_qty: float = None,
                           filled_price: float = None, error_msg: str = None,
                           execution_details: Dict = None) -> bool:
        """
        Update trade status after Alpaca response

        Args:
            trade_id: Trade ID
            status: New status (FILLED, PARTIAL, FAILED, etc.)
            filled_qty: Quantity filled
            filled_price: Average fill price
            error_msg: Error message if failed
            execution_details: Optional dict with:
                - slippage, slippage_percent
                - execution_latency_ms, time_to_fill_ms
                - alpaca_order_status, position_after
        """
        try:
            details = execution_details or {}

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    updates = ["status = %s"]
                    params = [status]

                    if filled_qty is not None:
                        updates.append("filled_qty = %s")
                        params.append(filled_qty)

                    if filled_price is not None:
                        updates.append("filled_avg_price = %s")
                        params.append(filled_price)

                    if status == 'FILLED':
                        updates.append("filled_at = CURRENT_TIMESTAMP")

                    if error_msg:
                        updates.append("error_message = %s")
                        params.append(error_msg)

                    # Enhanced execution details
                    if details.get('slippage') is not None:
                        updates.append("slippage = %s")
                        params.append(details['slippage'])

                    if details.get('slippage_percent') is not None:
                        updates.append("slippage_percent = %s")
                        params.append(details['slippage_percent'])

                    if details.get('execution_latency_ms') is not None:
                        updates.append("execution_latency_ms = %s")
                        params.append(details['execution_latency_ms'])

                    if details.get('time_to_fill_ms') is not None:
                        updates.append("time_to_fill_ms = %s")
                        params.append(details['time_to_fill_ms'])

                    if details.get('alpaca_order_status'):
                        updates.append("alpaca_order_status = %s")
                        params.append(details['alpaca_order_status'])

                    if details.get('position_after'):
                        updates.append("position_after = %s")
                        params.append(details['position_after'])

                    params.append(trade_id)

                    query = f"""
                        UPDATE bot_trades
                        SET {', '.join(updates)}
                        WHERE id = %s
                    """
                    cur.execute(query, params)
            return True
        except Exception as e:
            print(f"Error updating trade status: {e}")
            return False

    @staticmethod
    def get_user_trades(user_id: int, limit: int = 100, symbol: str = None) -> List[Dict]:
        """Get user's trade history"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT * FROM bot_trades
                    WHERE user_id = %s
                """
                params = [user_id]

                if symbol:
                    query += " AND symbol = %s"
                    params.append(symbol.upper())

                query += " ORDER BY created_at DESC LIMIT %s"
                params.append(limit)

                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]


class WebhookTokenDB:
    """Manage webhook tokens"""

    @staticmethod
    def generate_token(user_id: int) -> Optional[str]:
        """Generate a unique webhook token for user"""
        try:
            token = f"usr_{secrets.token_urlsafe(32)}"

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO user_webhook_tokens (user_id, token)
                        VALUES (%s, %s)
                        ON CONFLICT (user_id) DO UPDATE
                        SET token = %s, created_at = CURRENT_TIMESTAMP
                        RETURNING token
                    """, (user_id, token, token))
                    return cur.fetchone()[0]
        except Exception as e:
            print(f"Error generating token: {e}")
            return None

    @staticmethod
    def get_user_by_token(token: str) -> Optional[int]:
        """Get user_id from webhook token"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE user_webhook_tokens
                        SET last_used_at = CURRENT_TIMESTAMP,
                            request_count = request_count + 1
                        WHERE token = %s AND is_active = TRUE
                        RETURNING user_id
                    """, (token,))
                    result = cur.fetchone()
                    return result[0] if result else None
        except Exception:
            return None

    @staticmethod
    def get_user_token(user_id: int) -> Optional[str]:
        """Get user's webhook token"""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT token FROM user_webhook_tokens
                    WHERE user_id = %s AND is_active = TRUE
                """, (user_id,))
                result = cur.fetchone()
                return result[0] if result else None

    @staticmethod
    def delete_user_token(user_id: int) -> bool:
        """Delete user's webhook token"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM user_webhook_tokens
                        WHERE user_id = %s
                    """, (user_id,))
                    return True
        except Exception as e:
            print(f"Error deleting token: {e}")
            return False

    @staticmethod
    def deactivate_user_token(user_id: int) -> bool:
        """Deactivate user's webhook token (soft delete)"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE user_webhook_tokens
                        SET is_active = FALSE
                        WHERE user_id = %s
                    """, (user_id,))
                    return True
        except Exception as e:
            print(f"Error deactivating token: {e}")
            return False


class SystemStrategyDB:
    """Manage system-wide TradingView strategies (admin only)"""

    @staticmethod
    def create_strategy(name: str, symbol: str, timeframe: str, description: str = None,
                       risk_warning: str = None) -> Optional[int]:
        """Create a new system strategy"""
        try:
            # Generate unique webhook token for this strategy
            token = f"sys_{secrets.token_urlsafe(32)}"

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO system_strategies
                        (name, symbol, timeframe, description, risk_warning, webhook_token)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (name, symbol.upper(), timeframe, description, risk_warning, token))
                    return cur.fetchone()[0]
        except Exception as e:
            print(f"Error creating system strategy: {e}")
            return None

    @staticmethod
    def get_all_strategies(active_only: bool = True) -> List[Dict]:
        """Get all system strategies"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = "SELECT * FROM system_strategies"
                if active_only:
                    query += " WHERE is_active = TRUE"
                query += " ORDER BY created_at DESC"
                cur.execute(query)
                return [dict(row) for row in cur.fetchall()]

    @staticmethod
    def get_strategy_by_id(strategy_id: int) -> Optional[Dict]:
        """Get a specific strategy"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM system_strategies WHERE id = %s", (strategy_id,))
                row = cur.fetchone()
                return dict(row) if row else None

    @staticmethod
    def get_strategy_by_token(token: str) -> Optional[Dict]:
        """Get strategy by webhook token"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM system_strategies
                    WHERE webhook_token = %s AND is_active = TRUE
                """, (token,))
                row = cur.fetchone()
                return dict(row) if row else None

    @staticmethod
    def update_strategy(strategy_id: int, **kwargs) -> bool:
        """Update strategy fields"""
        try:
            allowed_fields = ['name', 'symbol', 'timeframe', 'description', 'risk_warning', 'is_active']
            updates = []
            params = []

            for field, value in kwargs.items():
                if field in allowed_fields:
                    updates.append(f"{field} = %s")
                    params.append(value)

            if not updates:
                return False

            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(strategy_id)

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"""
                        UPDATE system_strategies
                        SET {', '.join(updates)}
                        WHERE id = %s
                    """, params)
            return True
        except Exception as e:
            print(f"Error updating strategy: {e}")
            return False

    @staticmethod
    def delete_strategy(strategy_id: int) -> bool:
        """Delete a system strategy"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM system_strategies WHERE id = %s", (strategy_id,))
            return True
        except Exception:
            return False

    @staticmethod
    def increment_signal_count(strategy_id: int) -> bool:
        """Increment the signal count for a strategy"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE system_strategies
                        SET total_signals = total_signals + 1,
                            last_signal_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (strategy_id,))
            return True
        except Exception:
            return False

    @staticmethod
    def get_subscriber_count(strategy_id: int) -> int:
        """Get number of active subscribers for a strategy"""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM user_strategy_subscriptions
                    WHERE strategy_id = %s AND is_active = TRUE
                """, (strategy_id,))
                return cur.fetchone()[0]


class UserStrategySubscriptionDB:
    """Manage user subscriptions to system strategies"""

    @staticmethod
    def subscribe(user_id: int, strategy_id: int, bot_config_id: int,
                  disclaimer_accepted: bool = False) -> Tuple[bool, str]:
        """Subscribe user's bot to a system strategy"""
        if not disclaimer_accepted:
            return False, "You must accept the risk disclaimer to subscribe"

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if already subscribed
                    cur.execute("""
                        SELECT id FROM user_strategy_subscriptions
                        WHERE user_id = %s AND strategy_id = %s AND bot_config_id = %s
                    """, (user_id, strategy_id, bot_config_id))

                    if cur.fetchone():
                        # Update existing subscription
                        cur.execute("""
                            UPDATE user_strategy_subscriptions
                            SET is_active = TRUE,
                                disclaimer_accepted_at = CURRENT_TIMESTAMP,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = %s AND strategy_id = %s AND bot_config_id = %s
                        """, (user_id, strategy_id, bot_config_id))
                    else:
                        # Create new subscription
                        cur.execute("""
                            INSERT INTO user_strategy_subscriptions
                            (user_id, strategy_id, bot_config_id, disclaimer_accepted_at)
                            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                        """, (user_id, strategy_id, bot_config_id))

            return True, "Successfully subscribed to strategy"
        except Exception as e:
            print(f"Error subscribing to strategy: {e}")
            return False, f"Database error: {str(e)}"

    @staticmethod
    def unsubscribe(user_id: int, strategy_id: int, bot_config_id: int) -> bool:
        """Unsubscribe user's bot from a system strategy"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE user_strategy_subscriptions
                        SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s AND strategy_id = %s AND bot_config_id = %s
                    """, (user_id, strategy_id, bot_config_id))
            return True
        except Exception:
            return False

    @staticmethod
    def get_user_subscriptions(user_id: int) -> List[Dict]:
        """Get all subscriptions for a user"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT s.*, ss.name as strategy_name, ss.symbol, ss.timeframe,
                           ss.description, bc.position_size
                    FROM user_strategy_subscriptions s
                    JOIN system_strategies ss ON s.strategy_id = ss.id
                    JOIN user_bot_configs bc ON s.bot_config_id = bc.id
                    WHERE s.user_id = %s AND s.is_active = TRUE
                    ORDER BY s.created_at DESC
                """, (user_id,))
                return [dict(row) for row in cur.fetchall()]

    @staticmethod
    def get_strategy_subscribers(strategy_id: int) -> List[Dict]:
        """Get all active subscribers for a strategy (for executing trades)"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT s.user_id, s.bot_config_id, bc.position_size, bc.symbol,
                           bc.timeframe, bc.risk_limit_percent
                    FROM user_strategy_subscriptions s
                    JOIN user_bot_configs bc ON s.bot_config_id = bc.id
                    WHERE s.strategy_id = %s AND s.is_active = TRUE AND bc.is_active = TRUE
                """, (strategy_id,))
                return [dict(row) for row in cur.fetchall()]

    @staticmethod
    def is_subscribed(user_id: int, strategy_id: int, bot_config_id: int) -> bool:
        """Check if user's bot is subscribed to a strategy"""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM user_strategy_subscriptions
                    WHERE user_id = %s AND strategy_id = %s AND bot_config_id = %s AND is_active = TRUE
                """, (user_id, strategy_id, bot_config_id))
                return cur.fetchone() is not None


class UserOutgoingWebhookDB:
    """Manage user's outgoing webhooks for signal forwarding"""

    @staticmethod
    def save_webhook(user_id: int, webhook_url: str, webhook_name: str = None,
                    include_signals: bool = True, include_trades: bool = True) -> Tuple[bool, str]:
        """Save or update user's outgoing webhook"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO user_outgoing_webhooks
                        (user_id, webhook_url, webhook_name, include_signals, include_trades)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (user_id, webhook_url) DO UPDATE
                        SET webhook_name = %s,
                            include_signals = %s,
                            include_trades = %s,
                            is_active = TRUE,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING id
                    """, (user_id, webhook_url, webhook_name, include_signals, include_trades,
                          webhook_name, include_signals, include_trades))
                    return True, "Webhook saved successfully"
        except Exception as e:
            print(f"Error saving outgoing webhook: {e}")
            return False, f"Database error: {str(e)}"

    @staticmethod
    def get_user_webhooks(user_id: int, active_only: bool = True) -> List[Dict]:
        """Get all outgoing webhooks for a user"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = "SELECT * FROM user_outgoing_webhooks WHERE user_id = %s"
                if active_only:
                    query += " AND is_active = TRUE"
                query += " ORDER BY created_at DESC"
                cur.execute(query, (user_id,))
                return [dict(row) for row in cur.fetchall()]

    @staticmethod
    def delete_webhook(user_id: int, webhook_id: int) -> bool:
        """Delete an outgoing webhook"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM user_outgoing_webhooks
                        WHERE id = %s AND user_id = %s
                    """, (webhook_id, user_id))
            return True
        except Exception:
            return False

    @staticmethod
    def toggle_webhook(user_id: int, webhook_id: int, is_active: bool) -> bool:
        """Enable/disable an outgoing webhook"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE user_outgoing_webhooks
                        SET is_active = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND user_id = %s
                    """, (is_active, webhook_id, user_id))
            return True
        except Exception:
            return False

    @staticmethod
    def increment_call_count(webhook_id: int, success: bool = True) -> bool:
        """Increment webhook call count"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    if success:
                        cur.execute("""
                            UPDATE user_outgoing_webhooks
                            SET success_count = success_count + 1,
                                last_called_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (webhook_id,))
                    else:
                        cur.execute("""
                            UPDATE user_outgoing_webhooks
                            SET failure_count = failure_count + 1,
                                last_called_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (webhook_id,))
            return True
        except Exception:
            return False


class RiskEventDB:
    """Log risk management events"""

    @staticmethod
    def log_risk_event(user_id: int, bot_config_id: int, event_type: str,
                      symbol: str, timeframe: str, threshold_value: float,
                      current_value: float, action_taken: str) -> bool:
        """Log a risk limit event"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO bot_risk_events
                        (user_id, bot_config_id, event_type, symbol, timeframe,
                         threshold_value, current_value, action_taken)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (user_id, bot_config_id, event_type, symbol, timeframe,
                          threshold_value, current_value, action_taken))
            return True
        except Exception:
            return False

    @staticmethod
    def get_user_risk_events(user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's risk events"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM bot_risk_events
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (user_id, limit))
                return [dict(row) for row in cur.fetchall()]
