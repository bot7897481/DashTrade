#!/usr/bin/env python3
"""
Debug Admin Login Script
This script helps diagnose login issues by checking the database state.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def debug_admin_login():
    """Debug admin login issues"""
    print("="*70)
    print("🔍 Admin Login Debug Script")
    print("="*70)
    
    try:
        from auth import UserDB
        from database import get_db_connection
        import bcrypt
        
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("❌ DATABASE_URL not set in environment")
            return False
        
        print("\n📊 Checking database for admin user...")
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check all users with admin in username
                cur.execute("""
                    SELECT id, username, email, role, is_active, 
                           password_hash, created_at
                    FROM users 
                    WHERE username LIKE '%admin%' OR role IN ('admin', 'superadmin')
                    ORDER BY created_at DESC
                """)
                
                users = cur.fetchall()
                
                if not users:
                    print("\n❌ No admin users found in database!")
                    print("\n💡 Creating admin user now...")
                    
                    result = UserDB.register_user(
                        username='admin',
                        email='admin@dashtrade.app',
                        password='Admin123',
                        full_name='Admin User',
                        role='admin'
                    )
                    
                    if result['success']:
                        print("✅ Admin user created!")
                        print(f"   Username: admin")
                        print(f"   Password: Admin123")
                        return True
                    else:
                        print(f"❌ Failed to create admin: {result['error']}")
                        return False
                
                print(f"\n📋 Found {len(users)} admin user(s):")
                print("-" * 70)
                
                for user in users:
                    user_id, username, email, role, is_active, password_hash, created_at = user
                    print(f"\n👤 User ID: {user_id}")
                    print(f"   Username: {username}")
                    print(f"   Email: {email}")
                    print(f"   Role: {role}")
                    print(f"   Active: {is_active}")
                    print(f"   Created: {created_at}")
                    
                    # Test password verification
                    test_password = "Admin123"
                    try:
                        password_match = UserDB.verify_password(test_password, password_hash)
                        print(f"   Password 'Admin123' matches: {password_match}")
                        
                        if not password_match:
                            print(f"\n   ⚠️  Password doesn't match! Resetting...")
                            
                            # Reset password
                            new_hash = UserDB.hash_password(test_password)
                            cur.execute("""
                                UPDATE users 
                                SET password_hash = %s, is_active = TRUE
                                WHERE id = %s
                            """, (new_hash, user_id))
                            conn.commit()
                            
                            print(f"   ✅ Password reset to 'Admin123'")
                            
                            # Verify the reset worked
                            password_match_after = UserDB.verify_password(test_password, new_hash)
                            print(f"   ✅ Verification after reset: {password_match_after}")
                    except Exception as e:
                        print(f"   ❌ Error verifying password: {e}")
                
                print("\n" + "="*70)
                print("🔐 Testing Authentication...")
                print("-" * 70)
                
                # Test authentication
                result = UserDB.authenticate_user('admin', 'Admin123')
                
                if result['success']:
                    print("✅ Authentication SUCCESSFUL!")
                    print(f"   User: {result['user']['username']}")
                    print(f"   Role: {result['user']['role']}")
                else:
                    print(f"❌ Authentication FAILED: {result['error']}")
                    
                    # Try with lowercase username
                    print("\n🔄 Trying with lowercase username...")
                    result2 = UserDB.authenticate_user('admin', 'Admin123')
                    if result2['success']:
                        print("✅ Authentication works with lowercase username!")
                    else:
                        print(f"❌ Still failed: {result2['error']}")
                
                print("\n" + "="*70)
                print("📝 Login Credentials:")
                print("-" * 70)
                print("Username: admin")
                print("Password: Admin123")
                print("="*70)
                
                return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_admin_login()
    sys.exit(0 if success else 1)


