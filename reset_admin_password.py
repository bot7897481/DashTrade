#!/usr/bin/env python3
"""
Reset Admin Password Script
This script resets the admin user password to ensure login works.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def reset_admin_password():
    """Reset admin password to Admin123"""
    print("="*70)
    print("🔐 Admin Password Reset Script")
    print("="*70)
    
    try:
        from auth import UserDB
        from database import get_db_connection
        import bcrypt
        
        # Check if admin user exists
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("❌ DATABASE_URL not set in environment")
            print("\n💡 Make sure DATABASE_URL is set in your environment variables")
            return False
        
        print(f"\n📊 Database URL: {db_url[:50]}..." if len(db_url) > 50 else f"\n📊 Database URL: {db_url}")
        print("\n📊 Checking for admin user...")
        
        # First, ensure tables exist
        try:
            UserDB.create_users_table()
            print("✅ Database tables verified")
        except Exception as e:
            print(f"⚠️  Table creation warning: {e}")
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check if admin user exists (case-insensitive)
                cur.execute("""
                    SELECT id, username, email, role, is_active, password_hash 
                    FROM users 
                    WHERE LOWER(username) = LOWER(%s)
                """, ('admin',))
                user = cur.fetchone()
                
                if user:
                    user_id, username, email, role, is_active, old_hash = user
                    print(f"✅ Found admin user:")
                    print(f"   ID: {user_id}")
                    print(f"   Username: {username}")
                    print(f"   Email: {email}")
                    print(f"   Role: {role}")
                    print(f"   Active: {is_active}")
                    
                    # Reset password to Admin123
                    new_password = "Admin123"
                    password_hash = UserDB.hash_password(new_password)
                    
                    # Verify the hash before saving
                    if not UserDB.verify_password(new_password, password_hash):
                        print("❌ Password hash verification failed before saving!")
                        return False
                    
                    cur.execute("""
                        UPDATE users 
                        SET password_hash = %s, is_active = TRUE
                        WHERE id = %s
                    """, (password_hash, user_id))
                    
                    conn.commit()
                    
                    # Verify the update worked
                    cur.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
                    saved_hash = cur.fetchone()[0]
                    
                    if UserDB.verify_password(new_password, saved_hash):
                        print("\n" + "="*70)
                        print("✅ PASSWORD RESET SUCCESSFUL!")
                        print("="*70)
                        print(f"\n👤 Username: {username}")
                        print(f"🔑 Password: Admin123")
                        print(f"👑 Role: {role}")
                        print(f"✅ Account is active")
                        
                        # Test authentication
                        print("\n🧪 Testing authentication...")
                        auth_result = UserDB.authenticate_user('admin', 'Admin123')
                        if auth_result['success']:
                            print("✅ Authentication test PASSED!")
                        else:
                            print(f"⚠️  Authentication test failed: {auth_result['error']}")
                        
                        print("\n" + "="*70)
                        return True
                    else:
                        print("❌ Password verification failed after update!")
                        return False
                else:
                    print("⚠️  Admin user not found. Creating new admin user...")
                    
                    # Create admin user with password Admin123
                    result = UserDB.register_user(
                        username='admin',
                        email='admin@dashtrade.app',
                        password='Admin123',
                        full_name='Admin User',
                        role='admin'
                    )
                    
                    if result['success']:
                        print("\n" + "="*70)
                        print("✅ ADMIN USER CREATED!")
                        print("="*70)
                        print(f"\n👤 Username: admin")
                        print(f"🔑 Password: Admin123")
                        print(f"📧 Email: admin@dashtrade.app")
                        print(f"👑 Role: admin")
                        
                        # Test authentication
                        print("\n🧪 Testing authentication...")
                        auth_result = UserDB.authenticate_user('admin', 'Admin123')
                        if auth_result['success']:
                            print("✅ Authentication test PASSED!")
                        else:
                            print(f"⚠️  Authentication test failed: {auth_result['error']}")
                        
                        print("\n" + "="*70)
                        return True
                    else:
                        print(f"\n❌ Failed to create admin user: {result['error']}")
                        
                        # Try to get more details
                        if 'already exists' in result['error'].lower():
                            print("\n💡 User might exist with different case. Checking...")
                            cur.execute("SELECT username, email FROM users WHERE LOWER(username) = 'admin'")
                            existing = cur.fetchone()
                            if existing:
                                print(f"   Found: username={existing[0]}, email={existing[1]}")
                                print("   Try resetting password for this user")
                        
                        return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = reset_admin_password()
    sys.exit(0 if success else 1)

