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
            return False
        
        print("\n📊 Checking for admin user...")
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check if admin user exists
                cur.execute("SELECT id, username, role FROM users WHERE username = %s", ('admin',))
                user = cur.fetchone()
                
                if user:
                    user_id, username, role = user
                    print(f"✅ Found admin user (ID: {user_id}, Role: {role})")
                    
                    # Reset password to Admin123
                    new_password = "Admin123"
                    password_hash = UserDB.hash_password(new_password)
                    
                    cur.execute("""
                        UPDATE users 
                        SET password_hash = %s, is_active = TRUE
                        WHERE id = %s
                    """, (password_hash, user_id))
                    
                    conn.commit()
                    
                    print("\n" + "="*70)
                    print("✅ PASSWORD RESET SUCCESSFUL!")
                    print("="*70)
                    print(f"\n👤 Username: admin")
                    print(f"🔑 Password: Admin123")
                    print(f"👑 Role: {role}")
                    print("\n" + "="*70)
                    return True
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
                        print("\n" + "="*70)
                        return True
                    else:
                        print(f"\n❌ Failed to create admin user: {result['error']}")
                        return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = reset_admin_password()
    sys.exit(0 if success else 1)

