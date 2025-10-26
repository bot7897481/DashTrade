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
    def get_all_stocks() -> List[Dict]:
        """Get all stocks in watchlist"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, symbol, name, added_at, notes 
                    FROM watchlist 
                    ORDER BY added_at DESC
                """)
                return [dict(row) for row in cur.fetchall()]
    
    @staticmethod
    def add_stock(symbol: str, name: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """Add a stock to watchlist"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO watchlist (symbol, name, notes)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (symbol) DO NOTHING
                        RETURNING id
                    """, (symbol.upper(), name, notes))
                    return cur.fetchone() is not None
        except Exception:
            return False
    
    @staticmethod
    def remove_stock(symbol: str) -> bool:
        """Remove a stock from watchlist"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM watchlist WHERE symbol = %s", (symbol.upper(),))
                    return cur.rowcount > 0
        except Exception:
            return False
    
    @staticmethod
    def update_notes(symbol: str, notes: str) -> bool:
        """Update notes for a stock"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE watchlist SET notes = %s WHERE symbol = %s
                    """, (notes, symbol.upper()))
                    return cur.rowcount > 0
        except Exception:
            return False

class AlertsDB:
    """Database operations for alerts"""
    
    @staticmethod
    def get_active_alerts(symbol: Optional[str] = None) -> List[Dict]:
        """Get active alerts, optionally filtered by symbol"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if symbol:
                    cur.execute("""
                        SELECT * FROM alerts 
                        WHERE symbol = %s AND is_active = TRUE
                        ORDER BY created_at DESC
                    """, (symbol.upper(),))
                else:
                    cur.execute("""
                        SELECT * FROM alerts 
                        WHERE is_active = TRUE
                        ORDER BY created_at DESC
                    """)
                return [dict(row) for row in cur.fetchall()]
    
    @staticmethod
    def add_alert(symbol: str, alert_type: str, condition_text: str) -> bool:
        """Add a new alert"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO alerts (symbol, alert_type, condition_text)
                        VALUES (%s, %s, %s)
                        RETURNING id
                    """, (symbol.upper(), alert_type, condition_text))
                    return cur.fetchone() is not None
        except Exception:
            return False
    
    @staticmethod
    def trigger_alert(alert_id: int) -> bool:
        """Mark alert as triggered"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE alerts 
                        SET triggered_at = CURRENT_TIMESTAMP, is_active = FALSE
                        WHERE id = %s
                    """, (alert_id,))
                    return cur.rowcount > 0
        except Exception:
            return False
    
    @staticmethod
    def delete_alert(alert_id: int) -> bool:
        """Delete an alert"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM alerts WHERE id = %s", (alert_id,))
                    return cur.rowcount > 0
        except Exception:
            return False

class PreferencesDB:
    """Database operations for user preferences"""
    
    @staticmethod
    def get_preference(key: str) -> Optional[str]:
        """Get a preference value"""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT value FROM user_preferences WHERE key = %s", (key,))
                result = cur.fetchone()
                return result[0] if result else None
    
    @staticmethod
    def set_preference(key: str, value: str) -> bool:
        """Set a preference value"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO user_preferences (key, value, updated_at)
                        VALUES (%s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (key) DO UPDATE SET value = %s, updated_at = CURRENT_TIMESTAMP
                    """, (key, value, value))
                    return True
        except Exception:
            return False
    
    @staticmethod
    def get_all_preferences() -> Dict[str, str]:
        """Get all preferences"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT key, value FROM user_preferences")
                return {row['key']: row['value'] for row in cur.fetchall()}
