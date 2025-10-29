#!/usr/bin/env python3
"""
Database Setup Script for DashTrade
This script helps you set up and verify your database connection.
"""
import os
import sys

def check_database_url():
    """Check if DATABASE_URL is set"""
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        print("✓ DATABASE_URL is set")
        # Mask the password for security
        if '@' in db_url:
            parts = db_url.split('@')
            if ':' in parts[0]:
                user_pass = parts[0].split(':')
                masked = f"{user_pass[0]}:{'*' * 8}@{parts[1]}"
                print(f"  Connection: {masked}")
        return True
    else:
        print("✗ DATABASE_URL is not set")
        return False

def test_connection():
    """Test database connection"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("\n✗ Cannot test connection: DATABASE_URL not set")
        return False

    try:
        import psycopg2
        print("\n✓ psycopg2 library is installed")

        print("Testing connection...")
        conn = psycopg2.connect(db_url)
        print("✓ Successfully connected to database!")

        # Test query
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"✓ PostgreSQL version: {version[0].split(',')[0]}")

        cur.close()
        conn.close()
        return True

    except ImportError:
        print("✗ psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

def show_setup_instructions():
    """Show database setup instructions"""
    print("\n" + "="*70)
    print("DATABASE SETUP INSTRUCTIONS")
    print("="*70)
    print("\nOption 1: Replit PostgreSQL (Recommended for Replit)")
    print("-" * 70)
    print("1. Go to your Replit project")
    print("2. Click on 'Secrets' (🔒) in the left sidebar")
    print("3. Add a new secret:")
    print("   Key: DATABASE_URL")
    print("   Value: Your PostgreSQL connection string")
    print("\nFor Replit's built-in PostgreSQL:")
    print("   postgresql://username:password@localhost:5432/database")

    print("\n\nOption 2: External PostgreSQL Service (For Production)")
    print("-" * 70)
    print("\nFree PostgreSQL Providers:")
    print("  • Neon (https://neon.tech) - Free tier with 500 MB")
    print("  • ElephantSQL (https://elephantsql.com) - Free tier with 20 MB")
    print("  • Supabase (https://supabase.com) - Free tier with 500 MB")
    print("  • Railway (https://railway.app) - Free tier available")

    print("\n\nSteps for external service:")
    print("  1. Sign up for a free PostgreSQL service")
    print("  2. Create a new database")
    print("  3. Copy the connection string (DATABASE_URL)")
    print("  4. Add it to Replit Secrets or set as environment variable")

    print("\n\nOption 3: Local Development")
    print("-" * 70)
    print("If you have PostgreSQL installed locally:")
    print("  export DATABASE_URL='postgresql://user:password@localhost:5432/dashtrade'")

    print("\n" + "="*70)
    print("\nAfter setting DATABASE_URL, run this script again to verify.")
    print("="*70)

def main():
    print("="*70)
    print("DashTrade Database Setup Checker")
    print("="*70)

    # Check if DATABASE_URL is set
    if not check_database_url():
        show_setup_instructions()
        sys.exit(1)

    # Test connection
    if not test_connection():
        print("\n⚠️  Database URL is set but connection failed.")
        print("Please check your connection string and ensure PostgreSQL is running.")
        sys.exit(1)

    print("\n" + "="*70)
    print("✅ Database setup is complete and working!")
    print("="*70)
    print("\nNext steps:")
    print("  1. Run migration: python migrate_database.py")
    print("  2. Start the app: streamlit run app.py")
    print("="*70)

if __name__ == "__main__":
    main()
