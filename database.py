"""
Database operations for NovAlgo Trading Dashboard
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import List, Dict, Optional
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL')

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

class WatchlistDB:
    """Database operations for watchlist management"""

    @staticmethod
    def create_table():
        """Create watchlist table if it doesn't exist"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS watchlist (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            symbol VARCHAR(10) NOT NULL,
                            name VARCHAR(255),
                            notes TEXT,
                            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(user_id, symbol)
                        )
                    """)
                    return True
        except Exception as e:
            print(f"Error creating watchlist table: {e}")
            return False

    @staticmethod
    def get_all_stocks(user_id: int) -> List[Dict]:
        """Get all stocks in watchlist for a specific user"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, symbol, name, added_at, notes
                    FROM watchlist
                    WHERE user_id = %s
                    ORDER BY added_at DESC
                """, (user_id,))
                return [dict(row) for row in cur.fetchall()]

    @staticmethod
    def add_stock(user_id: int, symbol: str, name: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """Add a stock to watchlist for a specific user"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO watchlist (user_id, symbol, name, notes)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (user_id, symbol) DO NOTHING
                        RETURNING id
                    """, (user_id, symbol.upper(), name, notes))
                    return cur.fetchone() is not None
        except Exception:
            return False

    @staticmethod
    def remove_stock(user_id: int, symbol: str) -> bool:
        """Remove a stock from watchlist for a specific user"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM watchlist WHERE user_id = %s AND symbol = %s",
                        (user_id, symbol.upper())
                    )
                    return cur.rowcount > 0
        except Exception:
            return False

    @staticmethod
    def update_notes(user_id: int, symbol: str, notes: str) -> bool:
        """Update notes for a stock for a specific user"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE watchlist SET notes = %s
                        WHERE user_id = %s AND symbol = %s
                    """, (notes, user_id, symbol.upper()))
                    return cur.rowcount > 0
        except Exception:
            return False

class AlertsDB:
    """Database operations for alerts"""

    @staticmethod
    def create_table():
        """Create alerts table if it doesn't exist"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS alerts (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            symbol VARCHAR(10) NOT NULL,
                            alert_type VARCHAR(50) NOT NULL,
                            condition VARCHAR(50) NOT NULL,
                            threshold DECIMAL(15, 2) NOT NULL,
                            message TEXT,
                            is_active BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            triggered_at TIMESTAMP
                        )
                    """)
                    return True
        except Exception as e:
            print(f"Error creating alerts table: {e}")
            return False

    @staticmethod
    def get_active_alerts(user_id: int, symbol: Optional[str] = None) -> List[Dict]:
        """Get active alerts for a specific user, optionally filtered by symbol"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if symbol:
                    cur.execute("""
                        SELECT * FROM alerts
                        WHERE user_id = %s AND symbol = %s AND is_active = TRUE
                        ORDER BY created_at DESC
                    """, (user_id, symbol.upper()))
                else:
                    cur.execute("""
                        SELECT * FROM alerts
                        WHERE user_id = %s AND is_active = TRUE
                        ORDER BY created_at DESC
                    """, (user_id,))
                return [dict(row) for row in cur.fetchall()]

    @staticmethod
    def add_alert(user_id: int, symbol: str, alert_type: str, condition_text: str) -> bool:
        """Add a new alert for a specific user"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO alerts (user_id, symbol, alert_type, condition_text)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (user_id, symbol.upper(), alert_type, condition_text))
                    return cur.fetchone() is not None
        except Exception:
            return False

    @staticmethod
    def trigger_alert(user_id: int, alert_id: int) -> bool:
        """Mark alert as triggered for a specific user"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE alerts
                        SET triggered_at = CURRENT_TIMESTAMP, is_active = FALSE
                        WHERE id = %s AND user_id = %s
                    """, (alert_id, user_id))
                    return cur.rowcount > 0
        except Exception:
            return False

    @staticmethod
    def delete_alert(user_id: int, alert_id: int) -> bool:
        """Delete an alert for a specific user"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM alerts WHERE id = %s AND user_id = %s",
                        (alert_id, user_id)
                    )
                    return cur.rowcount > 0
        except Exception:
            return False

class PreferencesDB:
    """Database operations for user preferences"""

    @staticmethod
    def create_table():
        """Create user_preferences table if it doesn't exist"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS user_preferences (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            key VARCHAR(100) NOT NULL,
                            value TEXT,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(user_id, key)
                        )
                    """)
                    return True
        except Exception as e:
            print(f"Error creating user_preferences table: {e}")
            return False

    @staticmethod
    def get_preference(user_id: int, key: str) -> Optional[str]:
        """Get a preference value for a specific user"""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT value FROM user_preferences WHERE user_id = %s AND key = %s",
                    (user_id, key)
                )
                result = cur.fetchone()
                return result[0] if result else None

    @staticmethod
    def set_preference(user_id: int, key: str, value: str) -> bool:
        """Set a preference value for a specific user"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO user_preferences (user_id, key, value, updated_at)
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (user_id, key) DO UPDATE
                        SET value = %s, updated_at = CURRENT_TIMESTAMP
                    """, (user_id, key, value, value))
                    return True
        except Exception:
            return False

    @staticmethod
    def get_all_preferences(user_id: int) -> Dict[str, str]:
        """Get all preferences for a specific user"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT key, value FROM user_preferences WHERE user_id = %s",
                    (user_id,)
                )
                return {row['key']: row['value'] for row in cur.fetchall()}
