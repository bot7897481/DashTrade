"""
Authentication module for DashTrade
"""
import os
import bcrypt
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional, Dict
from datetime import datetime, timedelta
import secrets
import re

DATABASE_URL = os.getenv('DATABASE_URL')

# List of common temporary email domains to block
TEMP_EMAIL_DOMAINS = [
    'tempmail.com', 'temp-mail.org', 'guerrillamail.com', 'sharklasers.com',
    '10minutemail.com', 'throwaway.email', 'mailinator.com', 'maildrop.cc',
    'yopmail.com', 'getnada.com', 'trashmail.com', 'tempinbox.com',
    'mohmal.com', 'fakeinbox.com', 'emailondeck.com', 'mintemail.com',
    'temp-mail.io', 'tmpeml.info', 'temp-link.net', 'tempsky.com',
    'guerrillamailblock.com', 'spamgourmet.com', 'mailnesia.com'
]

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
        """Create users table and verification tokens table if they don't exist"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Create users table
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
                            is_active BOOLEAN DEFAULT TRUE,
                            email_verified BOOLEAN DEFAULT FALSE
                        )
                    """)

                    # Add email_verified column if it doesn't exist (for existing databases)
                    cur.execute("""
                        DO $$
                        BEGIN
                            BEGIN
                                ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
                            EXCEPTION
                                WHEN duplicate_column THEN NULL;
                            END;
                        END $$;
                    """)

                    # Create verification tokens table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS email_verification_tokens (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                            token VARCHAR(255) UNIQUE NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP NOT NULL,
                            used BOOLEAN DEFAULT FALSE
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
    def is_temp_email(email: str) -> bool:
        """Check if email is from a temporary email service"""
        email_domain = email.lower().split('@')[-1]
        return email_domain in TEMP_EMAIL_DOMAINS

    @staticmethod
    def generate_verification_token(user_id: int) -> Optional[str]:
        """Generate a verification token for email confirmation"""
        try:
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)  # Token valid for 24 hours

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO email_verification_tokens (user_id, token, expires_at)
                        VALUES (%s, %s, %s)
                    """, (user_id, token, expires_at))
                    return token
        except Exception as e:
            print(f"Error generating verification token: {e}")
            return None

    @staticmethod
    def verify_email_token(token: str) -> Dict:
        """Verify an email verification token and mark email as verified"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if token exists and is valid
                    cur.execute("""
                        SELECT user_id, expires_at, used
                        FROM email_verification_tokens
                        WHERE token = %s
                    """, (token,))

                    result = cur.fetchone()

                    if not result:
                        return {'success': False, 'error': 'Invalid verification token'}

                    user_id, expires_at, used = result

                    if used:
                        return {'success': False, 'error': 'This verification link has already been used'}

                    if datetime.now() > expires_at:
                        return {'success': False, 'error': 'This verification link has expired'}

                    # Mark token as used
                    cur.execute("""
                        UPDATE email_verification_tokens
                        SET used = TRUE
                        WHERE token = %s
                    """, (token,))

                    # Mark email as verified
                    cur.execute("""
                        UPDATE users
                        SET email_verified = TRUE
                        WHERE id = %s
                    """, (user_id,))

                    return {'success': True, 'user_id': user_id}

        except Exception as e:
            return {'success': False, 'error': f'Verification error: {str(e)}'}

    @staticmethod
    def resend_verification_email(email: str) -> Dict:
        """Resend verification email to user"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if user exists and is not verified
                    cur.execute("""
                        SELECT id, email_verified
                        FROM users
                        WHERE email = %s
                    """, (email.lower(),))

                    result = cur.fetchone()

                    if not result:
                        return {'success': False, 'error': 'Email not found'}

                    user_id, email_verified = result

                    if email_verified:
                        return {'success': False, 'error': 'Email already verified'}

                    # Generate new token
                    token = UserDB.generate_verification_token(user_id)

                    if token:
                        return {'success': True, 'token': token, 'user_id': user_id}
                    else:
                        return {'success': False, 'error': 'Failed to generate verification token'}

        except Exception as e:
            return {'success': False, 'error': f'Error: {str(e)}'}

    @staticmethod
    def register_user(username: str, email: str, password: str, full_name: Optional[str] = None, role: str = 'user') -> Dict:
        """
        Register a new user
        Returns: {'success': True, 'user_id': int, 'verification_token': str} or {'success': False, 'error': str}
        """
        try:
            # Validate inputs
            if len(username) < 3:
                return {'success': False, 'error': 'Username must be at least 3 characters'}
            if len(password) < 6:
                return {'success': False, 'error': 'Password must be at least 6 characters'}
            if '@' not in email:
                return {'success': False, 'error': 'Invalid email address'}

            # Check for temporary email services
            if UserDB.is_temp_email(email):
                return {'success': False, 'error': 'Temporary email services are not allowed. Please use a valid email address.'}

            # Validate role
            if role not in ['user', 'admin', 'superadmin']:
                role = 'user'

            # Hash password
            password_hash = UserDB.hash_password(password)

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO users (username, email, password_hash, full_name, role, email_verified)
                        VALUES (%s, %s, %s, %s, %s, FALSE)
                        RETURNING id
                    """, (username.lower(), email.lower(), password_hash, full_name, role))

                    user_id = cur.fetchone()[0]

                    # Generate verification token
                    verification_token = UserDB.generate_verification_token(user_id)

                    return {
                        'success': True,
                        'user_id': user_id,
                        'username': username,
                        'role': role,
                        'email': email,
                        'verification_token': verification_token,
                        'requires_verification': True
                    }

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
                        SELECT id, username, email, password_hash, full_name, role, is_active, email_verified
                        FROM users
                        WHERE username = %s
                    """, (username.lower(),))

                    user = cur.fetchone()

                    if not user:
                        return {'success': False, 'error': 'Invalid username or password'}

                    if not user['is_active']:
                        return {'success': False, 'error': 'Account is disabled'}

                    # Check if email is verified (admin and superadmin bypass this check)
                    if not user['email_verified'] and user['role'] not in ['admin', 'superadmin']:
                        return {
                            'success': False,
                            'error': 'Please verify your email before logging in',
                            'requires_verification': True,
                            'email': user['email']
                        }

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
                        SELECT id, username, email, full_name, role, created_at, last_login, is_active
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
    def verify_all_existing_users() -> Dict:
        """Mark all existing users as email verified (migration helper)"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE users
                        SET email_verified = TRUE
                        WHERE email_verified = FALSE OR email_verified IS NULL
                    """)
                    count = cur.rowcount
                    return {'success': True, 'count': count}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def create_superadmin_if_not_exists(username: str = 'superadmin', password: str = 'admin123', email: str = 'admin@dashtrade.local') -> Dict:
        """Create a superadmin account if it doesn't exist"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if any superadmin exists
                    cur.execute("SELECT COUNT(*) FROM users WHERE role = 'superadmin'")
                    superadmin_count = cur.fetchone()[0]

                    if superadmin_count > 0:
                        return {'success': True, 'message': 'Superadmin already exists'}

                    # Create superadmin
                    password_hash = UserDB.hash_password(password)
                    cur.execute("""
                        INSERT INTO users (username, email, password_hash, full_name, role, email_verified, is_active)
                        VALUES (%s, %s, %s, %s, %s, TRUE, TRUE)
                        RETURNING id
                    """, (username.lower(), email.lower(), password_hash, 'Super Administrator', 'superadmin'))

                    user_id = cur.fetchone()[0]
                    return {
                        'success': True,
                        'message': 'Superadmin created successfully',
                        'user_id': user_id,
                        'username': username,
                        'password': password,
                        'email': email
                    }

        except psycopg2.IntegrityError as e:
            if 'username' in str(e):
                return {'success': False, 'error': 'Username already exists'}
            elif 'email' in str(e):
                return {'success': False, 'error': 'Email already registered'}
            return {'success': False, 'error': 'Failed to create superadmin'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
