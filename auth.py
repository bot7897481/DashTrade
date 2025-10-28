"""
Authentication module for DashTrade
"""
import os
import bcrypt
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional, Dict
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

class UserDB:
    """Database operations for user authentication"""

    @staticmethod
    def create_users_table():
        """Create users table if it doesn't exist"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            id SERIAL PRIMARY KEY,
                            username VARCHAR(255) UNIQUE NOT NULL,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            full_name VARCHAR(255),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_login TIMESTAMP,
                            is_active BOOLEAN DEFAULT TRUE
                        )
                    """)
                    return True
        except Exception as e:
            print(f"Error creating users table: {e}")
            return False

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False

    @staticmethod
    def register_user(username: str, email: str, password: str, full_name: Optional[str] = None) -> Dict:
        """
        Register a new user
        Returns: {'success': True, 'user_id': int} or {'success': False, 'error': str}
        """
        try:
            # Validate inputs
            if len(username) < 3:
                return {'success': False, 'error': 'Username must be at least 3 characters'}
            if len(password) < 6:
                return {'success': False, 'error': 'Password must be at least 6 characters'}
            if '@' not in email:
                return {'success': False, 'error': 'Invalid email address'}

            # Hash password
            password_hash = UserDB.hash_password(password)

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO users (username, email, password_hash, full_name)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (username.lower(), email.lower(), password_hash, full_name))

                    user_id = cur.fetchone()[0]
                    return {'success': True, 'user_id': user_id, 'username': username}

        except psycopg2.IntegrityError as e:
            if 'username' in str(e):
                return {'success': False, 'error': 'Username already exists'}
            elif 'email' in str(e):
                return {'success': False, 'error': 'Email already registered'}
            else:
                return {'success': False, 'error': 'Registration failed'}
        except Exception as e:
            return {'success': False, 'error': f'Registration error: {str(e)}'}

    @staticmethod
    def authenticate_user(username: str, password: str) -> Dict:
        """
        Authenticate a user
        Returns: {'success': True, 'user': dict} or {'success': False, 'error': str}
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, username, email, password_hash, full_name, is_active
                        FROM users
                        WHERE username = %s
                    """, (username.lower(),))

                    user = cur.fetchone()

                    if not user:
                        return {'success': False, 'error': 'Invalid username or password'}

                    if not user['is_active']:
                        return {'success': False, 'error': 'Account is disabled'}

                    # Verify password
                    if not UserDB.verify_password(password, user['password_hash']):
                        return {'success': False, 'error': 'Invalid username or password'}

                    # Update last login
                    cur.execute("""
                        UPDATE users SET last_login = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (user['id'],))

                    # Remove password hash from returned data
                    user_data = dict(user)
                    del user_data['password_hash']

                    return {'success': True, 'user': user_data}

        except Exception as e:
            return {'success': False, 'error': f'Authentication error: {str(e)}'}

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict]:
        """Get user information by ID"""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, username, email, full_name, created_at, last_login, is_active
                        FROM users
                        WHERE id = %s
                    """, (user_id,))

                    user = cur.fetchone()
                    return dict(user) if user else None
        except Exception:
            return None

    @staticmethod
    def update_password(user_id: int, old_password: str, new_password: str) -> Dict:
        """Update user password"""
        try:
            # Validate new password
            if len(new_password) < 6:
                return {'success': False, 'error': 'Password must be at least 6 characters'}

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get current password hash
                    cur.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
                    result = cur.fetchone()

                    if not result:
                        return {'success': False, 'error': 'User not found'}

                    # Verify old password
                    if not UserDB.verify_password(old_password, result[0]):
                        return {'success': False, 'error': 'Current password is incorrect'}

                    # Update password
                    new_hash = UserDB.hash_password(new_password)
                    cur.execute("""
                        UPDATE users SET password_hash = %s
                        WHERE id = %s
                    """, (new_hash, user_id))

                    return {'success': True}

        except Exception as e:
            return {'success': False, 'error': f'Password update error: {str(e)}'}

    @staticmethod
    def get_all_users_count() -> int:
        """Get total number of users (admin function)"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM users")
                    return cur.fetchone()[0]
        except Exception:
            return 0
