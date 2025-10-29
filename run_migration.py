#!/usr/bin/env python
"""
Simple script to run database migration
This can be run via: streamlit run run_migration.py or executed directly
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the migration
from migrate_database import run_migration

if __name__ == "__main__":
    print("=" * 80)
    print("DashTrade Database Migration")
    print("=" * 80)
    
    # Check DATABASE_URL
    if not os.getenv('DATABASE_URL'):
        print("❌ ERROR: DATABASE_URL environment variable not set!")
        print("Please set DATABASE_URL in your Replit Secrets.")
        sys.exit(1)
    
    print(f"✓ DATABASE_URL is set")
    print()
    
    # Ask for confirmation
    print("This will:")
    print("  1. Create users table with role support")
    print("  2. Add user_id to watchlist, alerts, and user_preferences tables")
    print("  3. Add proper constraints and indexes")
    print()
    
    response = input("Do you want to proceed? (yes/no): ").strip().lower()
    
    if response == 'yes' or response == 'y':
        try:
            run_migration()
            print()
            print("=" * 80)
            print("✅ Migration completed successfully!")
            print("=" * 80)
            print()
            print("Next steps:")
            print("1. Run: python create_admin.py")
            print("2. Then restart your app and login!")
        except Exception as e:
            print()
            print("=" * 80)
            print(f"❌ Migration failed: {e}")
            print("=" * 80)
            sys.exit(1)
    else:
        print("Migration cancelled.")
        sys.exit(0)
