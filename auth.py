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

from database import get_db_connection

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
                            role VARCHAR(50) DEFAULT 'user' NOT NULL,
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
    def register_user(username: str, email: str, password: str, full_name: Optional[str] = None, role: str = 'user') -> Dict:
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

            # Validate role
            if role not in ['user', 'admin', 'superadmin']:
                role = 'user'

            # Hash password
            password_hash = UserDB.hash_password(password)

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO users (username, email, password_hash, full_name, role)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (username.lower(), email.lower(), password_hash, full_name, role))

                    user_id = cur.fetchone()[0]
                    return {'success': True, 'user_id': user_id, 'username': username, 'role': role}

        except Exception as e:
            err_msg = str(e).lower()
            if 'username' in err_msg:
                return {'success': False, 'error': 'Username already exists'}
            elif 'email' in err_msg:
                return {'success': False, 'error': 'Email already registered'}
            
            # Check for generic integrity/constraint errors if specific field scan failed
            if 'integrity' in err_msg or 'constraint' in err_msg or 'unique' in err_msg:
                 return {'success': False, 'error': 'Registration failed (Constraint Error)'}
                 
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
                        SELECT id, username, email, password_hash, full_name, role, is_active, email_enabled
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
                        SELECT id, username, email, full_name, role, created_at, last_login, is_active, email_enabled
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

    @staticmethod
    def get_all_users() -> list:
        """Get all users (admin function)"""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, username, email, full_name, role,
                               created_at, last_login, is_active
                        FROM users
                        ORDER BY created_at DESC
                    """)
                    return [dict(row) for row in cur.fetchall()]
        except Exception:
            return []

    @staticmethod
    def update_user_role(user_id: int, new_role: str) -> Dict:
        """Update user role (admin function)"""
        try:
            if new_role not in ['user', 'admin', 'superadmin']:
                return {'success': False, 'error': 'Invalid role'}

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE users SET role = %s
                        WHERE id = %s
                    """, (new_role, user_id))

                    if cur.rowcount > 0:
                        return {'success': True}
                    else:
                        return {'success': False, 'error': 'User not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def toggle_user_status(user_id: int) -> Dict:
        """Enable/disable user account (admin function)"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE users SET is_active = NOT is_active
                        WHERE id = %s
                        RETURNING is_active
                    """, (user_id,))

                    result = cur.fetchone()
                    if result:
                        return {'success': True, 'is_active': result[0]}
                    else:
                        return {'success': False, 'error': 'User not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def delete_user(user_id: int) -> Dict:
        """Delete user account (admin function)"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if user exists and is not superadmin
                    cur.execute("SELECT role FROM users WHERE id = %s", (user_id,))
                    result = cur.fetchone()

                    if not result:
                        return {'success': False, 'error': 'User not found'}

                    if result[0] == 'superadmin':
                        return {'success': False, 'error': 'Cannot delete superadmin'}

                    # Delete user (cascade will delete all related data)
                    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))

                    return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def is_admin(user_id: int) -> bool:
        """Check if user is admin or superadmin"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT role FROM users WHERE id = %s", (user_id,))
                    result = cur.fetchone()
                    return result and result[0] in ['admin', 'superadmin']
        except Exception:
            return False

    @staticmethod
    def is_superadmin(user_id: int) -> bool:
        """Check if user is superadmin"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT role FROM users WHERE id = %s", (user_id,))
                    result = cur.fetchone()
                    return result and result[0] == 'superadmin'
        except Exception:
            return False

    @staticmethod
    def update_email_preference(user_id: int, enabled: bool) -> bool:
        """Update user's email notification preference"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE users SET email_enabled = %s
                        WHERE id = %s
                    """, (enabled, user_id))
                    return cur.rowcount > 0
        except Exception as e:
            print(f"Error updating email preference: {e}")
            return False
