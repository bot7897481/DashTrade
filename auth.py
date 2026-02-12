"""
Authentication module for DashTrade
"""
import os
import bcrypt
import secrets
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional, Dict
from datetime import datetime, timedelta

from database import get_db_connection, DATABASE_URL

class UserDB:
    """Database operations for user authentication"""

    @staticmethod
    def create_users_table():
        """Create users table if it doesn't exist"""
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
                            email_enabled BOOLEAN DEFAULT TRUE
                        )
                    """)

                    # Create watchlist table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS watchlist (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                            symbol VARCHAR(10) NOT NULL,
                            name VARCHAR(255),
                            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            notes TEXT,
                            UNIQUE(user_id, symbol)
                        )
                    """)

                    # Create alerts table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS alerts (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                            symbol VARCHAR(10) NOT NULL,
                            alert_type VARCHAR(50) NOT NULL,
                            condition_text TEXT NOT NULL,
                            is_active BOOLEAN DEFAULT TRUE,
                            triggered_at TIMESTAMP,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Create user preferences table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS user_preferences (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                            key VARCHAR(100) NOT NULL,
                            value TEXT,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(user_id, key)
                        )
                    """)

                    # Create user API keys table for Alpaca
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS user_api_keys (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                            alpaca_api_key_encrypted TEXT NOT NULL,
                            alpaca_secret_key_encrypted TEXT NOT NULL,
                            alpaca_mode VARCHAR(10) DEFAULT 'paper',
                            is_active BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Create user bot configs table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS user_bot_configs (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                            symbol VARCHAR(10) NOT NULL,
                            timeframe VARCHAR(10) NOT NULL,
                            position_size DECIMAL(10,2) NOT NULL,
                            strategy_name VARCHAR(100),
                            risk_limit_percent DECIMAL(5,2) DEFAULT 10.0,
                            daily_loss_limit DECIMAL(10,2),
                            max_position_size DECIMAL(10,2),
                            signal_source VARCHAR(50) DEFAULT 'webhook',
                            strategy_type VARCHAR(50) DEFAULT 'none',
                            is_active BOOLEAN DEFAULT FALSE,
                            order_status VARCHAR(20) DEFAULT 'IDLE',
                            last_signal VARCHAR(10),
                            last_signal_time TIMESTAMP,
                            current_position_side VARCHAR(10),
                            total_pnl DECIMAL(15,2) DEFAULT 0.0,
                            total_trades INTEGER DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Create bot trades table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS bot_trades (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                            bot_config_id INTEGER REFERENCES user_bot_configs(id) ON DELETE CASCADE,
                            symbol VARCHAR(10) NOT NULL,
                            timeframe VARCHAR(10) NOT NULL,
                            action VARCHAR(10) NOT NULL,
                            notional DECIMAL(15,2) NOT NULL,
                            order_id VARCHAR(100),
                            filled_qty DECIMAL(15,8),
                            filled_avg_price DECIMAL(15,8),
                            status VARCHAR(20) DEFAULT 'SUBMITTED',
                            error_message TEXT,
                            filled_at TIMESTAMP,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Create user webhook tokens table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS user_webhook_tokens (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                            token VARCHAR(100) UNIQUE NOT NULL,
                            is_active BOOLEAN DEFAULT TRUE,
                            request_count INTEGER DEFAULT 0,
                            last_used_at TIMESTAMP,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Create bot risk events table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS bot_risk_events (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                            bot_config_id INTEGER REFERENCES user_bot_configs(id) ON DELETE CASCADE,
                            event_type VARCHAR(50) NOT NULL,
                            symbol VARCHAR(10) NOT NULL,
                            timeframe VARCHAR(10) NOT NULL,
                            threshold_value DECIMAL(15,2) NOT NULL,
                            current_value DECIMAL(15,2) NOT NULL,
                            action_taken TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    print("✓ Database tables created successfully")
                    return True
        except Exception as e:
            print(f"Error creating database tables: {e}")
            # Don't fail completely on Railway if tables already exist
            import os
            if os.getenv('RAILWAY_ENVIRONMENT'):
                print("Running on Railway - continuing despite table creation error")
                return True
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
    def validate_admin_code(admin_code: Optional[str] = None) -> bool:
        """
        Validate admin activation code
        Returns True if code is valid
        """
        if not admin_code:
            return False
        
        # Clean the input code
        admin_code_clean = admin_code.replace('-', '').replace(' ', '').strip()
        
        # Must be exactly 16 digits
        if len(admin_code_clean) != 16 or not admin_code_clean.isdigit():
            return False
        
        # Get admin code from environment variable
        expected_code = os.getenv('ADMIN_CODE', '').strip()
        
        # If ADMIN_CODE is set in environment, use it
        if expected_code:
            # Remove dashes/spaces from expected code
            expected_code_clean = expected_code.replace('-', '').replace(' ', '').strip()
            
            # Compare codes
            if admin_code_clean == expected_code_clean:
                return True
        else:
            # If no ADMIN_CODE is set, use default: 1234-5678-9012-3456
            default_code = '1234567890123456'
            if admin_code_clean == default_code:
                return True
        
        return False
    
    @staticmethod
    def get_default_admin_code() -> str:
        """Get the default admin code for display"""
        admin_code = os.getenv('ADMIN_CODE', '').strip()
        if not admin_code:
            # Default code for first-time setup
            return '1234-5678-9012-3456'
        # Format with dashes for display
        code_clean = admin_code.replace('-', '').replace(' ', '')
        if len(code_clean) == 16:
            return f"{code_clean[:4]}-{code_clean[4:8]}-{code_clean[8:12]}-{code_clean[12:16]}"
        return admin_code

    @staticmethod
    def register_user(username: str, email: str, password: str, full_name: Optional[str] = None, role: str = 'user', admin_code: Optional[str] = None) -> Dict:
        """
        Register a new user
        Returns: {'success': True, 'user_id': int} or {'success': False, 'error': str}
        """
        # #region agent log
        import json
        print(f"[DEBUG] register_user called: username='{username}', email='{email}'")
        try:
            with open('/Users/abedsaeedi/Documents/GitHub/DashTrade/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A,B,C,D,E,F","location":"auth.py:242","message":"register_user called","data":{"username":username,"email":email,"username_lower":username.lower(),"email_lower":email.lower()},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        except: pass
        # #endregion
        
        try:
            # Validate inputs
            if len(username) < 3:
                return {'success': False, 'error': 'Username must be at least 3 characters'}
            if len(password) < 6:
                return {'success': False, 'error': 'Password must be at least 6 characters'}
            if '@' not in email:
                return {'success': False, 'error': 'Invalid email address'}

            # Check admin code if provided
            if admin_code:
                if UserDB.validate_admin_code(admin_code):
                    role = 'admin'  # Grant admin role if code is valid
                else:
                    return {'success': False, 'error': 'Invalid admin activation code'}

            # Validate role
            if role not in ['user', 'admin', 'superadmin']:
                role = 'user'

            # Hash password
            password_hash = UserDB.hash_password(password)

            # #region agent log
            print(f"[DEBUG] Before DB check: checking for existing users with username='{username.lower()}' or email='{email.lower()}'")
            try:
                with open('/Users/abedsaeedi/Documents/GitHub/DashTrade/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A,B,C","location":"auth.py:270","message":"Before DB check - checking if user exists","data":{"username_lower":username.lower(),"email_lower":email.lower()},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            except: pass
            # #endregion

            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Check if username already exists (HYPOTHESIS A, B, C)
                    cur.execute("""
                        SELECT id, username, email, is_active, role 
                        FROM users 
                        WHERE LOWER(username) = LOWER(%s) OR LOWER(email) = LOWER(%s)
                    """, (username, email))
                    existing_users = cur.fetchall()
                    
                    # #region agent log
                    try:
                        with open('/Users/abedsaeedi/Documents/GitHub/DashTrade/.cursor/debug.log', 'a') as f:
                            existing_list = [dict(row) for row in existing_users] if existing_users else []
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A,B,C","location":"auth.py:285","message":"DB check result","data":{"existing_users":existing_list,"username_checked":username.lower(),"email_checked":email.lower(),"count":len(existing_users)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                    except: pass
                    # #endregion
                    
                    if existing_users:
                        # #region agent log
                        print(f"[DEBUG] Found {len(existing_users)} existing user(s) matching username/email")
                        # #endregion
                        
                        for existing in existing_users:
                            existing_dict = dict(existing)
                            existing_username = existing_dict.get('username')
                            existing_email = existing_dict.get('email')
                            existing_id = existing_dict.get('id')
                            
                            # #region agent log
                            print(f"[DEBUG] Checking existing user: ID={existing_id}, username='{existing_username}', email='{existing_email}'")
                            print(f"[DEBUG] Input: username='{username}' (lower: '{username.lower()}'), email='{email}' (lower: '{email.lower()}')")
                            # #endregion
                            
                            # Check username match (case-insensitive)
                            if existing_username and str(existing_username).lower() == username.lower():
                                error_msg = f"Username already exists. Found user ID {existing_id} with username '{existing_username}' (your input: '{username}')"
                                print(f"[DEBUG] Username match detected: {error_msg}")
                                return {'success': False, 'error': error_msg}
                            # Check email match (case-insensitive)
                            elif existing_email and str(existing_email).lower() == email.lower():
                                error_msg = f"Email already registered. Found user ID {existing_id} with email '{existing_email}' (your input: '{email}')"
                                print(f"[DEBUG] Email match detected: {error_msg}")
                                return {'success': False, 'error': error_msg}
                        
                        # If we get here, there was a match but username/email didn't match exactly
                        # This shouldn't happen, but log it for debugging
                        print(f"[DEBUG] WARNING: Found existing users but no exact match. This is unexpected.")
                        return {'success': False, 'error': f'Registration conflict detected. Please try a different username or email.'}
                    
                    # #region agent log
                    try:
                        with open('/Users/abedsaeedi/Documents/GitHub/DashTrade/.cursor/debug.log', 'a') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"auth.py:300","message":"Before INSERT attempt","data":{"username_lower":username.lower(),"email_lower":email.lower()},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                    except: pass
                    # #endregion
                    
                    cur.execute("""
                        INSERT INTO users (username, email, password_hash, full_name, role)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (username.lower(), email.lower(), password_hash, full_name, role))

                    result = cur.fetchone()
                    # Handle both dict (RealDictCursor) and tuple returns
                    user_id = result['id'] if isinstance(result, dict) else result[0]
                    
                    # #region agent log
                    try:
                        with open('/Users/abedsaeedi/Documents/GitHub/DashTrade/.cursor/debug.log', 'a') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"auth.py:310","message":"INSERT successful","data":{"user_id":user_id,"username":username.lower()},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                    except: pass
                    # #endregion
                    
                    return {'success': True, 'user_id': user_id, 'username': username, 'role': role}

        except Exception as e:
            err_msg = str(e).lower()
            full_error = str(e)
            
            # #region agent log
            try:
                with open('/Users/abedsaeedi/Documents/GitHub/DashTrade/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D,E,F","location":"auth.py:320","message":"Exception caught","data":{"error":full_error,"error_lower":err_msg,"username":username,"email":email},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            except: pass
            # #endregion
            
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
        Authenticate a user by username OR email address

        Args:
            username: Can be either a username or email address
            password: User's password

        Returns: {'success': True, 'user': dict} or {'success': False, 'error': str}
        """
        try:
            identifier = username.strip().lower()

            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Check if identifier is an email (contains @) or username
                    if '@' in identifier:
                        # Login with email
                        cur.execute("""
                            SELECT id, username, email, password_hash, full_name, role, is_active, email_enabled
                            FROM users
                            WHERE LOWER(email) = %s
                        """, (identifier,))
                    else:
                        # Login with username
                        cur.execute("""
                            SELECT id, username, email, password_hash, full_name, role, is_active, email_enabled
                            FROM users
                            WHERE LOWER(username) = %s
                        """, (identifier,))

                    user = cur.fetchone()

                    if not user:
                        return {'success': False, 'error': 'Invalid username/email or password'}

                    if not user['is_active']:
                        return {'success': False, 'error': 'Account is disabled'}

                    # Verify password
                    if not UserDB.verify_password(password, user['password_hash']):
                        return {'success': False, 'error': 'Invalid username/email or password'}

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
    def create_password_reset_tokens_table():
        """Create password_reset_tokens table if it doesn't exist"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS password_reset_tokens (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                            token VARCHAR(255) UNIQUE NOT NULL,
                            expires_at TIMESTAMP NOT NULL,
                            used BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    # Create index for faster lookups
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_password_reset_token 
                        ON password_reset_tokens(token)
                    """)
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_password_reset_user 
                        ON password_reset_tokens(user_id)
                    """)
        except Exception as e:
            print(f"Error creating password_reset_tokens table: {e}")

    @staticmethod
    def generate_password_reset_token(email: str) -> Dict:
        """
        Generate a password reset token for a user
        
        Args:
            email: User's email address
            
        Returns: {'success': True, 'token': str, 'user_id': int} or {'success': False, 'error': str}
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Find user by email
                    cur.execute("""
                        SELECT id, email, username FROM users 
                        WHERE LOWER(email) = %s
                    """, (email.lower(),))
                    
                    user = cur.fetchone()
                    if not user:
                        # Don't reveal if email exists or not (security best practice)
                        return {'success': True, 'message': 'If the email exists, a reset link has been sent'}
                    
                    # Generate secure token
                    token = secrets.token_urlsafe(32)
                    
                    # Token expires in 1 hour
                    expires_at = datetime.now() + timedelta(hours=1)
                    
                    # Invalidate any existing tokens for this user
                    cur.execute("""
                        UPDATE password_reset_tokens 
                        SET used = TRUE 
                        WHERE user_id = %s AND used = FALSE
                    """, (user['id'],))
                    
                    # Insert new token
                    cur.execute("""
                        INSERT INTO password_reset_tokens (user_id, token, expires_at)
                        VALUES (%s, %s, %s)
                    """, (user['id'], token, expires_at))
                    
                    return {
                        'success': True,
                        'token': token,
                        'user_id': user['id'],
                        'email': user['email'],
                        'username': user['username']
                    }
                    
        except Exception as e:
            return {'success': False, 'error': f'Error generating reset token: {str(e)}'}

    @staticmethod
    def validate_reset_token(token: str) -> Dict:
        """
        Validate a password reset token
        
        Args:
            token: Reset token to validate
            
        Returns: {'success': True, 'user_id': int} or {'success': False, 'error': str}
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT user_id, expires_at, used
                        FROM password_reset_tokens
                        WHERE token = %s
                    """, (token,))
                    
                    result = cur.fetchone()
                    
                    if not result:
                        return {'success': False, 'error': 'Invalid or expired reset token'}
                    
                    if result['used']:
                        return {'success': False, 'error': 'This reset token has already been used'}
                    
                    if datetime.now() > result['expires_at']:
                        return {'success': False, 'error': 'Reset token has expired'}
                    
                    return {
                        'success': True,
                        'user_id': result['user_id']
                    }
                    
        except Exception as e:
            return {'success': False, 'error': f'Error validating token: {str(e)}'}

    @staticmethod
    def reset_password_with_token(token: str, new_password: str) -> Dict:
        """
        Reset user password using a valid reset token
        
        Args:
            token: Valid reset token
            new_password: New password to set
            
        Returns: {'success': True} or {'success': False, 'error': str}
        """
        try:
            # Validate new password
            if len(new_password) < 6:
                return {'success': False, 'error': 'Password must be at least 6 characters'}
            
            # Validate token
            token_validation = UserDB.validate_reset_token(token)
            if not token_validation['success']:
                return token_validation
            
            user_id = token_validation['user_id']
            
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Update password
                    new_hash = UserDB.hash_password(new_password)
                    cur.execute("""
                        UPDATE users SET password_hash = %s
                        WHERE id = %s
                    """, (new_hash, user_id))
                    
                    # Mark token as used
                    cur.execute("""
                        UPDATE password_reset_tokens 
                        SET used = TRUE 
                        WHERE token = %s
                    """, (token,))
                    
                    return {'success': True}
                    
        except Exception as e:
            return {'success': False, 'error': f'Password reset error: {str(e)}'}

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
