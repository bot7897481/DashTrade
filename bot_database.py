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

                    # Update realized P&L if provided (for CLOSE orders)
                    if details.get('realized_pnl') is not None:
                        updates.append("realized_pnl = %s")
                        params.append(details['realized_pnl'])

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
        """Get user's trade history - includes all actions: BUY, SELL, CLOSE"""
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

                # No filtering by action - return ALL trades (BUY, SELL, CLOSE)
                query += " ORDER BY created_at DESC LIMIT %s"
                params.append(limit)

                cur.execute(query, params)
                trades = [dict(row) for row in cur.fetchall()]
                
                # Debug: Log action distribution
                action_counts = {}
                for trade in trades:
                    action = trade.get('action', 'UNKNOWN')
                    action_counts[action] = action_counts.get(action, 0) + 1
                
                if action_counts:
                    print(f"[DEBUG] get_user_trades: {action_counts}")
                
                return trades

    @staticmethod
    def get_trade_statistics(user_id: int = None) -> Dict:
        """Get trade statistics - counts by action type"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if user_id:
                    # Get stats for specific user
                    cur.execute("""
                        SELECT 
                            action,
                            COUNT(*) as count,
                            COUNT(CASE WHEN status = 'FILLED' THEN 1 END) as filled_count,
                            COUNT(CASE WHEN status = 'SUBMITTED' THEN 1 END) as submitted_count,
                            COUNT(CASE WHEN status = 'FAILED' THEN 1 END) as failed_count,
                            COALESCE(SUM(notional), 0) as total_notional,
                            COALESCE(SUM(CASE WHEN realized_pnl IS NOT NULL THEN realized_pnl ELSE 0 END), 0) as total_pnl
                        FROM bot_trades
                        WHERE user_id = %s
                        GROUP BY action
                        ORDER BY action
                    """, (user_id,))
                else:
                    # Get stats for all users
                    cur.execute("""
                        SELECT 
                            action,
                            COUNT(*) as count,
                            COUNT(CASE WHEN status = 'FILLED' THEN 1 END) as filled_count,
                            COUNT(CASE WHEN status = 'SUBMITTED' THEN 1 END) as submitted_count,
                            COUNT(CASE WHEN status = 'FAILED' THEN 1 END) as failed_count,
                            COALESCE(SUM(notional), 0) as total_notional,
                            COALESCE(SUM(CASE WHEN realized_pnl IS NOT NULL THEN realized_pnl ELSE 0 END), 0) as total_pnl
                        FROM bot_trades
                        GROUP BY action
                        ORDER BY action
                    """)
                
                results = cur.fetchall()
                
                # Get total count
                if user_id:
                    cur.execute("SELECT COUNT(*) as total FROM bot_trades WHERE user_id = %s", (user_id,))
                else:
                    cur.execute("SELECT COUNT(*) as total FROM bot_trades")
                
                total_row = cur.fetchone()
                total = total_row['total'] if total_row else 0
                
                stats = {
                    'total_trades': total,
                    'by_action': {}
                }
                
                for row in results:
                    action = row['action']
                    stats['by_action'][action] = {
                        'count': row['count'],
                        'filled': row['filled_count'] or 0,
                        'submitted': row['submitted_count'] or 0,
                        'failed': row['failed_count'] or 0,
                        'total_notional': float(row['total_notional'] or 0),
                        'total_pnl': float(row['total_pnl'] or 0)
                    }
                
                return stats


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


class TradeMarketContextDB:
    """Store and retrieve comprehensive market context for trades"""

    @staticmethod
    def save_context(trade_id: int, user_id: int, context: Dict) -> Optional[int]:
        """
        Save market context for a trade

        Args:
            trade_id: ID of the trade in bot_trades table
            user_id: User ID
            context: Dict with all market context data

        Returns:
            ID of the saved context record or None
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO trade_market_context (
                            trade_id, user_id, captured_at,
                            -- Stock data
                            stock_open, stock_high, stock_low, stock_close, stock_volume,
                            stock_prev_close, stock_change_percent, stock_avg_volume, stock_volume_ratio,
                            -- Fundamentals
                            market_cap, pe_ratio, forward_pe, eps, beta, dividend_yield,
                            shares_outstanding, float_shares, short_ratio,
                            fifty_two_week_high, fifty_two_week_low, fifty_day_ma, two_hundred_day_ma,
                            -- Market indices
                            sp500_price, sp500_change_percent, nasdaq_price, nasdaq_change_percent,
                            dji_price, dji_change_percent, russell_price, russell_change_percent,
                            -- Volatility
                            vix_price, vix_change_percent,
                            treasury_10y_yield, treasury_2y_yield, yield_curve_spread,
                            -- Sector
                            sector_etf_symbol, sector_etf_price, sector_etf_change_percent,
                            xlk_price, xlf_price, xle_price, xlv_price, xly_price,
                            xlp_price, xli_price, xlb_price, xlu_price, xlre_price,
                            -- Account
                            account_equity, account_cash, account_buying_power, account_portfolio_value,
                            position_qty_before, position_value_before, position_avg_entry,
                            position_unrealized_pl, total_positions_count, total_positions_value,
                            -- Technical
                            price_vs_50ma_percent, price_vs_200ma_percent,
                            price_vs_52w_high_percent, price_vs_52w_low_percent, rsi_14,
                            -- Metadata
                            data_source, fetch_latency_ms, errors
                        ) VALUES (
                            %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, %s, %s
                        )
                        RETURNING id
                    """, (
                        trade_id, user_id, context.get('captured_at'),
                        # Stock data
                        context.get('stock_open'), context.get('stock_high'),
                        context.get('stock_low'), context.get('stock_close'),
                        context.get('stock_volume'), context.get('stock_prev_close'),
                        context.get('stock_change_percent'), context.get('stock_avg_volume'),
                        context.get('stock_volume_ratio'),
                        # Fundamentals
                        context.get('market_cap'), context.get('pe_ratio'),
                        context.get('forward_pe'), context.get('eps'), context.get('beta'),
                        context.get('dividend_yield'), context.get('shares_outstanding'),
                        context.get('float_shares'), context.get('short_ratio'),
                        context.get('fifty_two_week_high'), context.get('fifty_two_week_low'),
                        context.get('fifty_day_ma'), context.get('two_hundred_day_ma'),
                        # Market indices
                        context.get('sp500_price'), context.get('sp500_change_percent'),
                        context.get('nasdaq_price'), context.get('nasdaq_change_percent'),
                        context.get('dji_price'), context.get('dji_change_percent'),
                        context.get('russell_price'), context.get('russell_change_percent'),
                        # Volatility
                        context.get('vix_price'), context.get('vix_change_percent'),
                        context.get('treasury_10y_yield'), context.get('treasury_2y_yield'),
                        context.get('yield_curve_spread'),
                        # Sector
                        context.get('sector_etf_symbol'), context.get('sector_etf_price'),
                        context.get('sector_etf_change_percent'),
                        context.get('xlk_price'), context.get('xlf_price'),
                        context.get('xle_price'), context.get('xlv_price'),
                        context.get('xly_price'), context.get('xlp_price'),
                        context.get('xli_price'), context.get('xlb_price'),
                        context.get('xlu_price'), context.get('xlre_price'),
                        # Account
                        context.get('account_equity'), context.get('account_cash'),
                        context.get('account_buying_power'), context.get('account_portfolio_value'),
                        context.get('position_qty_before'), context.get('position_value_before'),
                        context.get('position_avg_entry'), context.get('position_unrealized_pl'),
                        context.get('total_positions_count'), context.get('total_positions_value'),
                        # Technical
                        context.get('price_vs_50ma_percent'), context.get('price_vs_200ma_percent'),
                        context.get('price_vs_52w_high_percent'), context.get('price_vs_52w_low_percent'),
                        context.get('rsi_14'),
                        # Metadata
                        context.get('data_source', 'yfinance'),
                        context.get('fetch_latency_ms'), context.get('errors')
                    ))
                    result = cur.fetchone()
                    return result[0] if result else None

        except Exception as e:
            print(f"Error saving trade market context: {e}")
            return None

    @staticmethod
    def get_context_by_trade_id(trade_id: int) -> Optional[Dict]:
        """
        Get market context for a specific trade

        Args:
            trade_id: Trade ID

        Returns:
            Dict with market context or None
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM trade_market_context
                        WHERE trade_id = %s
                    """, (trade_id,))
                    result = cur.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            print(f"Error getting trade market context: {e}")
            return None

    @staticmethod
    def get_trade_with_context(trade_id: int, user_id: int) -> Optional[Dict]:
        """
        Get trade details with full market context

        Args:
            trade_id: Trade ID
            user_id: User ID (for authorization)

        Returns:
            Dict with trade and market context combined
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT
                            t.*,
                            c.stock_open, c.stock_high, c.stock_low, c.stock_close,
                            c.stock_volume, c.stock_prev_close, c.stock_change_percent,
                            c.stock_avg_volume, c.stock_volume_ratio,
                            c.market_cap, c.pe_ratio, c.forward_pe, c.eps, c.beta,
                            c.dividend_yield, c.shares_outstanding, c.short_ratio,
                            c.fifty_two_week_high, c.fifty_two_week_low,
                            c.fifty_day_ma, c.two_hundred_day_ma,
                            c.sp500_price, c.sp500_change_percent,
                            c.nasdaq_price, c.nasdaq_change_percent,
                            c.dji_price, c.dji_change_percent,
                            c.russell_price, c.russell_change_percent,
                            c.vix_price, c.vix_change_percent,
                            c.treasury_10y_yield, c.treasury_2y_yield, c.yield_curve_spread,
                            c.sector_etf_symbol, c.sector_etf_price, c.sector_etf_change_percent,
                            c.xlk_price, c.xlf_price, c.xle_price, c.xlv_price,
                            c.xlp_price, c.xli_price, c.xlb_price, c.xlu_price, c.xlre_price,
                            c.price_vs_50ma_percent, c.price_vs_200ma_percent,
                            c.price_vs_52w_high_percent, c.price_vs_52w_low_percent,
                            c.rsi_14, c.fetch_latency_ms as context_fetch_latency_ms
                        FROM bot_trades t
                        LEFT JOIN trade_market_context c ON t.id = c.trade_id
                        WHERE t.id = %s AND t.user_id = %s
                    """, (trade_id, user_id))
                    result = cur.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            print(f"Error getting trade with context: {e}")
            return None


class StrategyParamsDB:
    """Store and retrieve strategy parameters for trades - enables AI learning"""

    @staticmethod
    def save_params(trade_id: int, user_id: int, params: Dict) -> Optional[int]:
        """
        Save strategy parameters for a trade

        Args:
            trade_id: ID of the trade in bot_trades table
            user_id: User ID
            params: Dict with all strategy parameters

        Returns:
            ID of the saved params record or None
        """
        try:
            import json
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO trade_strategy_params (
                            trade_id, user_id,
                            -- Strategy identification
                            strategy_type, strategy_name, strategy_version,
                            -- Entry parameters
                            entry_indicator, entry_condition, entry_threshold, entry_value_at_signal,
                            -- Moving averages
                            ma_fast_period, ma_fast_type, ma_slow_period, ma_slow_type,
                            ma_trend_period, price_vs_ma_fast, price_vs_ma_slow,
                            -- RSI
                            rsi_period, rsi_value_at_entry, rsi_oversold_level, rsi_overbought_level,
                            -- MACD
                            macd_fast_period, macd_slow_period, macd_signal_period,
                            macd_value_at_entry, macd_signal_at_entry, macd_histogram_at_entry,
                            -- Bollinger Bands
                            bb_period, bb_std_dev, bb_position,
                            -- ATR
                            atr_period, atr_value_at_entry, atr_multiplier_stop, atr_multiplier_target,
                            -- Volume
                            volume_ma_period, volume_ratio_at_entry, volume_condition,
                            -- Risk management
                            stop_loss_type, stop_loss_value, take_profit_type, take_profit_value,
                            risk_reward_ratio, position_size_method,
                            -- Time
                            trade_session, day_of_week, hour_of_day, minutes_since_open,
                            -- Trend
                            trend_short, trend_medium, trend_long,
                            -- Custom
                            custom_params
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        ON CONFLICT (trade_id) DO UPDATE SET
                            strategy_type = EXCLUDED.strategy_type,
                            strategy_name = EXCLUDED.strategy_name,
                            entry_indicator = EXCLUDED.entry_indicator,
                            entry_threshold = EXCLUDED.entry_threshold,
                            custom_params = EXCLUDED.custom_params
                        RETURNING id
                    """, (
                        trade_id, user_id,
                        params.get('strategy_type'), params.get('strategy_name'), params.get('strategy_version'),
                        params.get('entry_indicator'), params.get('entry_condition'),
                        params.get('entry_threshold'), params.get('entry_value_at_signal'),
                        params.get('ma_fast_period'), params.get('ma_fast_type'),
                        params.get('ma_slow_period'), params.get('ma_slow_type'),
                        params.get('ma_trend_period'), params.get('price_vs_ma_fast'), params.get('price_vs_ma_slow'),
                        params.get('rsi_period'), params.get('rsi_value_at_entry'),
                        params.get('rsi_oversold_level'), params.get('rsi_overbought_level'),
                        params.get('macd_fast_period'), params.get('macd_slow_period'), params.get('macd_signal_period'),
                        params.get('macd_value_at_entry'), params.get('macd_signal_at_entry'),
                        params.get('macd_histogram_at_entry'),
                        params.get('bb_period'), params.get('bb_std_dev'), params.get('bb_position'),
                        params.get('atr_period'), params.get('atr_value_at_entry'),
                        params.get('atr_multiplier_stop'), params.get('atr_multiplier_target'),
                        params.get('volume_ma_period'), params.get('volume_ratio_at_entry'),
                        params.get('volume_condition'),
                        params.get('stop_loss_type'), params.get('stop_loss_value'),
                        params.get('take_profit_type'), params.get('take_profit_value'),
                        params.get('risk_reward_ratio'), params.get('position_size_method'),
                        params.get('trade_session'), params.get('day_of_week'),
                        params.get('hour_of_day'), params.get('minutes_since_open'),
                        params.get('trend_short'), params.get('trend_medium'), params.get('trend_long'),
                        json.dumps(params.get('custom_params')) if params.get('custom_params') else None
                    ))
                    result = cur.fetchone()
                    return result[0] if result else None
        except Exception as e:
            print(f"Error saving strategy params: {e}")
            return None

    @staticmethod
    def get_params_by_trade_id(trade_id: int) -> Optional[Dict]:
        """Get strategy parameters for a trade"""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM trade_strategy_params WHERE trade_id = %s
                    """, (trade_id,))
                    result = cur.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            print(f"Error getting strategy params: {e}")
            return None


class TradeOutcomesDB:
    """Track trade outcomes (P&L) for performance analysis"""

    @staticmethod
    def create_entry(trade_id: int, user_id: int, entry_price: float, entry_time: datetime,
                     quantity: float, position_type: str = 'long', entry_order_id: str = None) -> Optional[int]:
        """
        Create trade outcome record when trade opens

        Args:
            trade_id: ID of the trade
            user_id: User ID
            entry_price: Entry fill price
            entry_time: Entry timestamp
            quantity: Number of shares
            position_type: 'long' or 'short'
            entry_order_id: Alpaca order ID

        Returns:
            ID of the outcome record
        """
        try:
            entry_value = float(entry_price) * float(quantity)
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO trade_outcomes (
                            trade_id, user_id, position_type,
                            entry_price, entry_time, entry_order_id,
                            quantity, entry_value, status
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'open')
                        ON CONFLICT (trade_id) DO UPDATE SET
                            entry_price = EXCLUDED.entry_price,
                            entry_time = EXCLUDED.entry_time,
                            quantity = EXCLUDED.quantity,
                            entry_value = EXCLUDED.entry_value
                        RETURNING id
                    """, (trade_id, user_id, position_type, entry_price, entry_time,
                          entry_order_id, quantity, entry_value))
                    result = cur.fetchone()
                    return result[0] if result else None
        except Exception as e:
            print(f"Error creating trade outcome entry: {e}")
            return None

    @staticmethod
    def close_trade(trade_id: int, exit_price: float, exit_time: datetime,
                    exit_reason: str = 'signal', exit_order_id: str = None,
                    commission: float = 0, slippage: float = 0) -> Optional[Dict]:
        """
        Close a trade and calculate P&L

        Args:
            trade_id: ID of the trade
            exit_price: Exit fill price
            exit_time: Exit timestamp
            exit_reason: 'signal', 'stop_loss', 'take_profit', 'trailing_stop', 'manual'
            exit_order_id: Alpaca order ID
            commission: Total commission paid
            slippage: Estimated slippage in dollars

        Returns:
            Dict with calculated P&L stats
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get current outcome record
                    cur.execute("""
                        SELECT * FROM trade_outcomes WHERE trade_id = %s
                    """, (trade_id,))
                    outcome = cur.fetchone()

                    if not outcome:
                        print(f"No outcome record found for trade {trade_id}")
                        return None

                    # Calculate P&L
                    entry_price = float(outcome['entry_price'])
                    quantity = float(outcome['quantity'])
                    position_type = outcome['position_type']

                    if position_type == 'long':
                        pnl_dollars = (float(exit_price) - entry_price) * quantity
                    else:  # short
                        pnl_dollars = (entry_price - float(exit_price)) * quantity

                    pnl_dollars -= commission
                    pnl_percent = (pnl_dollars / float(outcome['entry_value'])) * 100 if outcome['entry_value'] else 0
                    exit_value = float(exit_price) * quantity

                    # Calculate duration
                    entry_time = outcome['entry_time']
                    duration_seconds = int((exit_time - entry_time).total_seconds())
                    duration_minutes = duration_seconds // 60
                    duration_hours = duration_seconds / 3600

                    # Determine win/loss
                    is_winner = pnl_dollars > 0
                    is_breakeven = abs(pnl_percent) < 0.1  # Within 0.1%

                    # Update record
                    cur.execute("""
                        UPDATE trade_outcomes SET
                            exit_price = %s,
                            exit_time = %s,
                            exit_order_id = %s,
                            exit_reason = %s,
                            exit_value = %s,
                            pnl_dollars = %s,
                            pnl_percent = %s,
                            commission_paid = %s,
                            slippage_dollars = %s,
                            slippage_percent = %s,
                            hold_duration_seconds = %s,
                            hold_duration_minutes = %s,
                            hold_duration_hours = %s,
                            is_winner = %s,
                            is_breakeven = %s,
                            status = 'closed',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE trade_id = %s
                        RETURNING *
                    """, (
                        exit_price, exit_time, exit_order_id, exit_reason,
                        exit_value, pnl_dollars, pnl_percent, commission, slippage,
                        (slippage / float(outcome['entry_value']) * 100) if outcome['entry_value'] else 0,
                        duration_seconds, duration_minutes, duration_hours,
                        is_winner, is_breakeven, trade_id
                    ))
                    result = cur.fetchone()
                    return dict(result) if result else None

        except Exception as e:
            print(f"Error closing trade outcome: {e}")
            return None

    @staticmethod
    def get_outcome_by_trade_id(trade_id: int) -> Optional[Dict]:
        """Get outcome for a specific trade"""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM trade_outcomes WHERE trade_id = %s
                    """, (trade_id,))
                    result = cur.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            print(f"Error getting trade outcome: {e}")
            return None

    @staticmethod
    def get_user_outcomes(user_id: int, status: str = None, limit: int = 100) -> List[Dict]:
        """Get all outcomes for a user"""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    if status:
                        cur.execute("""
                            SELECT * FROM trade_outcomes
                            WHERE user_id = %s AND status = %s
                            ORDER BY entry_time DESC LIMIT %s
                        """, (user_id, status, limit))
                    else:
                        cur.execute("""
                            SELECT * FROM trade_outcomes
                            WHERE user_id = %s
                            ORDER BY entry_time DESC LIMIT %s
                        """, (user_id, limit))
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error getting user outcomes: {e}")
            return []

    @staticmethod
    def get_open_position(user_id: int, symbol: str) -> Optional[Dict]:
        """Find open position for a symbol to close it"""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT o.*, t.symbol, t.timeframe
                        FROM trade_outcomes o
                        JOIN bot_trades t ON o.trade_id = t.id
                        WHERE o.user_id = %s AND t.symbol = %s AND o.status = 'open'
                        ORDER BY o.entry_time DESC LIMIT 1
                    """, (user_id, symbol.upper()))
                    result = cur.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            print(f"Error finding open position: {e}")
            return None


class StrategyPerformanceDB:
    """Calculate and store strategy performance metrics"""

    @staticmethod
    def calculate_performance(user_id: int, strategy_type: str = None,
                              symbol: str = None, timeframe: str = None) -> Dict:
        """
        Calculate performance metrics for a strategy

        Args:
            user_id: User ID
            strategy_type: Filter by strategy type (optional)
            symbol: Filter by symbol (optional)
            timeframe: Filter by timeframe (optional)

        Returns:
            Dict with performance metrics
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Build WHERE clause
                    conditions = ["o.user_id = %s", "o.status = 'closed'"]
                    params = [user_id]

                    if strategy_type:
                        conditions.append("p.strategy_type = %s")
                        params.append(strategy_type)
                    if symbol:
                        conditions.append("t.symbol = %s")
                        params.append(symbol.upper())
                    if timeframe:
                        conditions.append("t.timeframe = %s")
                        params.append(timeframe)

                    where_clause = " AND ".join(conditions)

                    cur.execute(f"""
                        SELECT
                            COUNT(*) as total_trades,
                            SUM(CASE WHEN o.is_winner THEN 1 ELSE 0 END) as winning_trades,
                            SUM(CASE WHEN NOT o.is_winner AND NOT o.is_breakeven THEN 1 ELSE 0 END) as losing_trades,
                            SUM(CASE WHEN o.is_breakeven THEN 1 ELSE 0 END) as breakeven_trades,
                            ROUND(100.0 * SUM(CASE WHEN o.is_winner THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) as win_rate,
                            SUM(o.pnl_dollars) as total_pnl_dollars,
                            AVG(o.pnl_percent) as avg_pnl_percent,
                            AVG(CASE WHEN o.is_winner THEN o.pnl_dollars END) as avg_win_dollars,
                            AVG(CASE WHEN NOT o.is_winner AND NOT o.is_breakeven THEN o.pnl_dollars END) as avg_loss_dollars,
                            AVG(CASE WHEN o.is_winner THEN o.pnl_percent END) as avg_win_percent,
                            AVG(CASE WHEN NOT o.is_winner AND NOT o.is_breakeven THEN o.pnl_percent END) as avg_loss_percent,
                            MAX(o.pnl_dollars) as largest_win_dollars,
                            MIN(o.pnl_dollars) as largest_loss_dollars,
                            AVG(o.hold_duration_minutes) as avg_hold_duration_minutes,
                            SUM(CASE WHEN o.is_winner THEN o.pnl_dollars ELSE 0 END) /
                                NULLIF(ABS(SUM(CASE WHEN NOT o.is_winner THEN o.pnl_dollars ELSE 0 END)), 0) as profit_factor
                        FROM trade_outcomes o
                        LEFT JOIN trade_strategy_params p ON o.trade_id = p.trade_id
                        LEFT JOIN bot_trades t ON o.trade_id = t.id
                        WHERE {where_clause}
                    """, params)

                    result = cur.fetchone()
                    return dict(result) if result else {}

        except Exception as e:
            print(f"Error calculating performance: {e}")
            return {}

    @staticmethod
    def get_performance_by_indicator(user_id: int, min_trades: int = 10) -> List[Dict]:
        """
        Get performance breakdown by entry indicator

        Args:
            user_id: User ID
            min_trades: Minimum trades required for inclusion

        Returns:
            List of performance stats per indicator
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT
                            p.entry_indicator,
                            COUNT(*) as total_trades,
                            ROUND(100.0 * SUM(CASE WHEN o.is_winner THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate,
                            ROUND(AVG(o.pnl_percent)::numeric, 2) as avg_return_percent,
                            ROUND(SUM(o.pnl_dollars)::numeric, 2) as total_pnl
                        FROM trade_outcomes o
                        JOIN trade_strategy_params p ON o.trade_id = p.trade_id
                        WHERE o.user_id = %s AND o.status = 'closed' AND p.entry_indicator IS NOT NULL
                        GROUP BY p.entry_indicator
                        HAVING COUNT(*) >= %s
                        ORDER BY win_rate DESC, avg_return_percent DESC
                    """, (user_id, min_trades))
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error getting performance by indicator: {e}")
            return []

    @staticmethod
    def get_performance_by_market_condition(user_id: int, min_trades: int = 10) -> List[Dict]:
        """
        Get performance breakdown by VIX level (market volatility)

        Returns insights like: "Trades work best when VIX is 15-20"
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT
                            CASE
                                WHEN c.vix_price < 15 THEN 'Low VIX (<15)'
                                WHEN c.vix_price BETWEEN 15 AND 20 THEN 'Normal VIX (15-20)'
                                WHEN c.vix_price BETWEEN 20 AND 25 THEN 'Elevated VIX (20-25)'
                                WHEN c.vix_price > 25 THEN 'High VIX (>25)'
                                ELSE 'Unknown'
                            END as vix_regime,
                            COUNT(*) as total_trades,
                            ROUND(100.0 * SUM(CASE WHEN o.is_winner THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate,
                            ROUND(AVG(o.pnl_percent)::numeric, 2) as avg_return_percent,
                            ROUND(SUM(o.pnl_dollars)::numeric, 2) as total_pnl
                        FROM trade_outcomes o
                        JOIN trade_market_context c ON o.trade_id = c.trade_id
                        WHERE o.user_id = %s AND o.status = 'closed'
                        GROUP BY vix_regime
                        HAVING COUNT(*) >= %s
                        ORDER BY avg_return_percent DESC
                    """, (user_id, min_trades))
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error getting performance by market condition: {e}")
            return []


class AIStrategyInsightsDB:
    """Store and retrieve AI-discovered strategy insights"""

    @staticmethod
    def save_insight(insight: Dict) -> Optional[int]:
        """Save an AI-generated insight"""
        try:
            import json
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO ai_strategy_insights (
                            insight_type, confidence_score, sample_size,
                            symbol, timeframe, strategy_type,
                            title, description, conditions,
                            observed_win_rate, observed_avg_return, observed_trades,
                            recommendation, recommended_params
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        insight.get('insight_type'), insight.get('confidence_score'),
                        insight.get('sample_size'), insight.get('symbol'),
                        insight.get('timeframe'), insight.get('strategy_type'),
                        insight.get('title'), insight.get('description'),
                        json.dumps(insight.get('conditions')) if insight.get('conditions') else None,
                        insight.get('observed_win_rate'), insight.get('observed_avg_return'),
                        insight.get('observed_trades'), insight.get('recommendation'),
                        json.dumps(insight.get('recommended_params')) if insight.get('recommended_params') else None
                    ))
                    result = cur.fetchone()
                    return result[0] if result else None
        except Exception as e:
            print(f"Error saving insight: {e}")
            return None

    @staticmethod
    def get_active_insights(symbol: str = None, strategy_type: str = None,
                            min_confidence: float = 50) -> List[Dict]:
        """Get active insights, optionally filtered"""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    conditions = ["is_active = TRUE", "confidence_score >= %s"]
                    params = [min_confidence]

                    if symbol:
                        conditions.append("(symbol = %s OR symbol IS NULL)")
                        params.append(symbol.upper())
                    if strategy_type:
                        conditions.append("(strategy_type = %s OR strategy_type IS NULL)")
                        params.append(strategy_type)

                    where_clause = " AND ".join(conditions)

                    cur.execute(f"""
                        SELECT * FROM ai_strategy_insights
                        WHERE {where_clause}
                        ORDER BY confidence_score DESC, observed_win_rate DESC
                    """, params)
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error getting insights: {e}")
            return []
