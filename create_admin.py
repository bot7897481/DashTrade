#!/usr/bin/env python3
"""
Quick Superadmin Creator
Simpler script to create superadmin account
"""
import os
import getpass

def create_superadmin():
    """Create superadmin account"""
    print("="*70)
    print("👑 DashTrade Superadmin Creator")
    print("="*70)

    # Import here to show any errors clearly
    try:
        from auth import UserDB
        print("✅ Authentication module loaded")
    except ImportError as e:
        print(f"❌ Failed to import auth module: {e}")
        print("\n💡 Run this command to install dependencies:")
        print("   poetry install")
        print("\nOr in the Replit shell, click 'Packages' and ensure all dependencies are installed.")
        return False

    # Check if superadmin exists
    try:
        import psycopg2
        db_url = os.getenv('DATABASE_URL')

        if not db_url:
            print("❌ DATABASE_URL not set in environment")
            print("Please set it in Replit Secrets")
            return False

        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users WHERE role = 'superadmin'")
        superadmin_count = cur.fetchone()[0]
        cur.close()
        conn.close()

        if superadmin_count > 0:
            print(f"\n⚠️  {superadmin_count} superadmin(s) already exist.")
            create_another = input("Create another superadmin? (yes/no): ").lower()
            if create_another not in ['yes', 'y']:
                print("✅ Keeping existing superadmin")
                return True
    except Exception as e:
        print(f"⚠️  Could not check existing superadmins: {e}")
        print("Continuing anyway...")

    print("\n📝 Enter superadmin details:")
    print("-" * 70)

    # Get user input
    username = input("Username (min 3 chars): ").strip()
    if len(username) < 3:
        print("❌ Username must be at least 3 characters")
        return False

    email = input("Email: ").strip()
    if '@' not in email:
        print("❌ Invalid email address")
        return False

    full_name = input("Full Name (optional, press Enter to skip): ").strip()
    if not full_name:
        full_name = None

    password = getpass.getpass("Password (min 6 chars, hidden): ")
    if len(password) < 6:
        print("❌ Password must be at least 6 characters")
        return False

    password_confirm = getpass.getpass("Confirm Password: ")
    if password != password_confirm:
        print("❌ Passwords do not match")
        return False

    # Create superadmin
    print("\n🔐 Creating superadmin account...")

    try:
        result = UserDB.register_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            role='superadmin'
        )

        if result['success']:
            print("\n" + "="*70)
            print("✅ SUPERADMIN CREATED SUCCESSFULLY!")
            print("="*70)
            print(f"\n👤 Username: {username}")
            print(f"📧 Email: {email}")
            if full_name:
                print(f"👨‍💼 Name: {full_name}")
            print(f"👑 Role: SUPERADMIN")
            print("\n" + "="*70)
            print("\n🚀 Next Steps:")
            print("  1. Run: streamlit run app.py")
            print("  2. Login with your superadmin credentials")
            print("  3. Access the Admin Panel!")
            print("="*70)
            return True
        else:
            print(f"\n❌ Failed to create superadmin: {result['error']}")
            return False

    except Exception as e:
        print(f"\n❌ Error creating superadmin: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_superadmin()
    exit(0 if success else 1)
