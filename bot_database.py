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
    def save_api_keys(user_id: int, api_key: str, secret_key: str, mode: str = 'paper') -> bool:
        """
        Save or update user's Alpaca API keys (encrypted)

        Args:
            user_id: User ID
            api_key: Alpaca API key (plain text)
            secret_key: Alpaca secret key (plain text)
            mode: 'paper' or 'live'

        Returns:
            bool: Success status
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
            return True
        except Exception as e:
            print(f"Error saving API keys: {e}")
            return False

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
        Create a new bot configuration

        Returns:
            int: Bot ID or None on failure
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO user_bot_configs
                        (user_id, symbol, timeframe, position_size, strategy_name,
                         risk_limit_percent, daily_loss_limit, max_position_size,
                         signal_source, strategy_type)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (user_id, symbol.upper(), timeframe, position_size, strategy_name,
                          risk_limit_percent, daily_loss_limit, max_position_size,
                          signal_source, strategy_type))
                    return cur.fetchone()[0]
        except Exception as e:
            print(f"Error creating bot: {e}")
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
    def get_bot_by_symbol_timeframe(user_id: int, symbol: str, timeframe: str) -> Optional[Dict]:
        """Get specific bot configuration"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM user_bot_configs
                    WHERE user_id = %s AND symbol = %s AND timeframe = %s
                """, (user_id, symbol.upper(), timeframe))
                row = cur.fetchone()
                return dict(row) if row else None

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
                  action: str, notional: float, order_id: str = None) -> Optional[int]:
        """
        Log a new trade execution

        Returns:
            int: Trade ID
        """
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
        except Exception as e:
            print(f"Error logging trade: {e}")
            return None

    @staticmethod
    def update_trade_status(trade_id: int, status: str, filled_qty: float = None,
                           filled_price: float = None, error_msg: str = None) -> bool:
        """Update trade status after Alpaca response"""
        try:
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

                    params.append(trade_id)

                    query = f"""
                        UPDATE bot_trades
                        SET {', '.join(updates)}
                        WHERE id = %s
                    """
                    cur.execute(query, params)
            return True
        except Exception:
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
                    return result['user_id'] if result else None
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
                return result['token'] if result else None


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
