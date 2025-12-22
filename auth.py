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
                        for existing in existing_users:
                            existing_dict = dict(existing) if hasattr(existing, '_asdict') or isinstance(existing, dict) else {'id': existing[0], 'username': existing[1], 'email': existing[2] if len(existing) > 2 else None, 'is_active': existing[3] if len(existing) > 3 else None}
                            existing_username = existing_dict.get('username', existing_dict.get('username'))
                            existing_email = existing_dict.get('email', existing_dict.get('email'))
                            
                            # #region agent log
                            try:
                                with open('/Users/abedsaeedi/Documents/GitHub/DashTrade/.cursor/debug.log', 'a') as f:
                                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A,B,C","location":"auth.py:290","message":"Existing user found","data":{"existing_username":existing_username,"existing_email":existing_email,"input_username":username,"input_email":email,"is_active":existing_dict.get('is_active')},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                            except: pass
                            # #endregion
                            
                            # Check username match (case-insensitive)
                            if existing_username and str(existing_username).lower() == username.lower():
                                return {'success': False, 'error': f'Username already exists (found user ID: {existing_dict.get("id")})'}
                            # Check email match (case-insensitive)
                            elif existing_email and str(existing_email).lower() == email.lower():
                                return {'success': False, 'error': f'Email already registered (found user ID: {existing_dict.get("id")})'}
                    
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

                    user_id = cur.fetchone()[0]
                    
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
