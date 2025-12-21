#!/usr/bin/env python3
"""
Create Super Admin Account Script
Creates a super admin account with specified credentials.
"""

import os
import sys

# Set DATABASE_URL directly for local development
if not os.getenv('DATABASE_URL'):
    os.environ['DATABASE_URL'] = 'sqlite:///dashtrade.db'

from auth import UserDB

def create_superadmin():
    """Create super admin account"""
    print("🔐 Creating Super Admin Account")
    print("="*50)

    try:
        # Create the super admin account
        result = UserDB.register_user(
            username='admin',
            email='admin@dashtrade.app',
            password='password123',
            full_name='Super Administrator',
            role='superadmin'
        )

        if result['success']:
            print("✅ Super Admin Account Created Successfully!")
            print("="*50)
            print("👤 Username: admin")
            print("🔑 Password: password123")
            print("📧 Email: admin@dashtrade.app")
            print("👑 Role: SUPERADMIN")
            print("="*50)
            print("⚠️  IMPORTANT: Change the password after first login!")
            return True
        else:
            print(f"❌ Failed to create super admin: {result['error']}")
            return False

    except Exception as e:
        print(f"❌ Error creating super admin: {e}")
        return False

def main():
    print("="*50)
    print("       Create Super Admin Account")
    print("="*50)

    # Check if DATABASE_URL is available
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL environment variable not set!")
        print("Please set your database connection first.")
        sys.exit(1)

    # Create the super admin account
    if create_superadmin():
        print("\n🎉 Super admin account created successfully!")
        print("You can now log in with: admin / password123")
    else:
        print("\n❌ Failed to create super admin account")
        sys.exit(1)

if __name__ == "__main__":
    main()
