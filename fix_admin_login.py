#!/usr/bin/env python3
"""
Fix Admin Login - Comprehensive Script
This script will diagnose and fix admin login issues on Railway.
Run this directly on Railway if you can't login.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def fix_admin_login():
    """Comprehensive fix for admin login"""
    print("="*70)
    print("🔧 ADMIN LOGIN FIX SCRIPT")
    print("="*70)
    
    try:
        from auth import UserDB
        from database import get_db_connection
        import bcrypt
        
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("❌ DATABASE_URL not set!")
            return False
        
        print(f"\n📊 Database: {'PostgreSQL' if 'postgresql' in db_url or 'postgres://' in db_url else 'SQLite'}")
        
        # Step 1: Ensure tables exist
        print("\n📋 Step 1: Ensuring database tables exist...")
        try:
            UserDB.create_users_table()
            print("✅ Tables verified")
        except Exception as e:
            print(f"⚠️  Warning: {e}")
        
        # Step 2: Check for admin user
        print("\n📋 Step 2: Checking for admin user...")
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check all variations
                cur.execute("""
                    SELECT id, username, email, role, is_active, password_hash
                    FROM users 
                    WHERE LOWER(username) = 'admin' OR username = 'admin'
                """)
                
                users = cur.fetchall()
                
                if not users:
                    print("⚠️  No admin user found. Creating one...")
                    
                    result = UserDB.register_user(
                        username='admin',
                        email='admin@dashtrade.app',
                        password='Admin123',
                        full_name='Admin User',
                        role='admin'
                    )
                    
                    if result['success']:
                        print("✅ Admin user created!")
                        user_id = result['user_id']
                    else:
                        print(f"❌ Failed: {result['error']}")
                        return False
                else:
                    # Found existing user(s)
                    print(f"✅ Found {len(users)} admin user(s)")
                    
                    # Use the first one
                    user = users[0]
                    user_id = user[0] if isinstance(user, tuple) else user['id']
                    username = user[1] if isinstance(user, tuple) else user['username']
                    role = user[3] if isinstance(user, tuple) else user['role']
                    is_active = user[4] if isinstance(user, tuple) else user['is_active']
                    
                    print(f"   ID: {user_id}")
                    print(f"   Username: {username}")
                    print(f"   Role: {role}")
                    print(f"   Active: {is_active}")
                
                # Step 3: Reset password
                print("\n📋 Step 3: Resetting password to 'Admin123'...")
                new_password = "Admin123"
                password_hash = UserDB.hash_password(new_password)
                
                # Verify hash works
                if not UserDB.verify_password(new_password, password_hash):
                    print("❌ Password hash verification failed!")
                    return False
                
                # Update password and ensure user is active
                cur.execute("""
                    UPDATE users 
                    SET password_hash = %s, is_active = TRUE
                    WHERE id = %s
                """, (password_hash, user_id))
                
                conn.commit()
                print("✅ Password updated")
                
                # Step 4: Verify the update
                print("\n📋 Step 4: Verifying password reset...")
                cur.execute("SELECT password_hash, is_active FROM users WHERE id = %s", (user_id,))
                result = cur.fetchone()
                
                if result:
                    saved_hash = result[0] if isinstance(result, tuple) else result['password_hash']
                    saved_active = result[1] if isinstance(result, tuple) else result['is_active']
                    
                    if UserDB.verify_password(new_password, saved_hash):
                        print("✅ Password verification PASSED")
                    else:
                        print("❌ Password verification FAILED")
                        return False
                    
                    if saved_active:
                        print("✅ Account is active")
                    else:
                        print("⚠️  Account was inactive, activating now...")
                        cur.execute("UPDATE users SET is_active = TRUE WHERE id = %s", (user_id,))
                        conn.commit()
                
                # Step 5: Test authentication
                print("\n📋 Step 5: Testing authentication...")
                auth_result = UserDB.authenticate_user('admin', 'Admin123')
                
                if auth_result['success']:
                    print("✅ Authentication test PASSED!")
                    print(f"   Logged in as: {auth_result['user']['username']}")
                    print(f"   Role: {auth_result['user']['role']}")
                else:
                    print(f"❌ Authentication test FAILED: {auth_result['error']}")
                    
                    # Try direct database check
                    print("\n🔍 Debugging authentication failure...")
                    cur.execute("""
                        SELECT id, username, password_hash, is_active, role
                        FROM users 
                        WHERE LOWER(username) = 'admin'
                    """)
                    debug_user = cur.fetchone()
                    
                    if debug_user:
                        debug_id, debug_username, debug_hash, debug_active, debug_role = debug_user
                        print(f"   Found user: {debug_username}")
                        print(f"   Active: {debug_active}")
                        print(f"   Role: {debug_role}")
                        print(f"   Hash length: {len(debug_hash) if debug_hash else 0}")
                        
                        # Try manual verification
                        try:
                            manual_check = bcrypt.checkpw(
                                new_password.encode('utf-8'),
                                debug_hash.encode('utf-8')
                            )
                            print(f"   Manual bcrypt check: {manual_check}")
                        except Exception as e:
                            print(f"   Manual check error: {e}")
                    
                    return False
                
                # Success!
                print("\n" + "="*70)
                print("✅ ADMIN LOGIN FIXED SUCCESSFULLY!")
                print("="*70)
                print("\n📝 Login Credentials:")
                print("   Username: admin")
                print("   Password: Admin123")
                print("\n💡 You can now login to your dashboard!")
                print("="*70)
                
                return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_admin_login()
    sys.exit(0 if success else 1)

