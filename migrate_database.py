"""
Database migration script to add authentication support to DashTrade
Run this script ONCE to update your database schema
"""
import os
import psycopg2
from psycopg2 import sql

DATABASE_URL = os.getenv('DATABASE_URL')

def run_migration():
    """Run database migration to add user authentication"""
    print("Starting database migration for authentication support...")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cur = conn.cursor()

        # 1. Create users table with role support
        print("\n1. Creating users table with role support...")
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
                is_active BOOLEAN DEFAULT TRUE
            )
        """)

        # Add role column if table exists but column doesn't
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'role'
            )
        """)
        has_role = cur.fetchone()[0]

        if not has_role:
            cur.execute("""
                ALTER TABLE users
                ADD COLUMN role VARCHAR(50) DEFAULT 'user' NOT NULL
            """)
            print("   ✓ Added role column to existing users table")
        else:
            print("   ✓ Users table created/verified with role support")

        # 2. Check if watchlist table exists and needs migration
        print("\n2. Migrating watchlist table...")
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'watchlist'
            )
        """)
        watchlist_exists = cur.fetchone()[0]

        if watchlist_exists:
            # Check if user_id column already exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_name = 'watchlist' AND column_name = 'user_id'
                )
            """)
            has_user_id = cur.fetchone()[0]

            if not has_user_id:
                # Add user_id column (nullable initially for migration)
                cur.execute("""
                    ALTER TABLE watchlist
                    ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
                """)
                print("   ✓ Added user_id column to watchlist")

                # Drop old unique constraint on symbol
                cur.execute("""
                    ALTER TABLE watchlist
                    DROP CONSTRAINT IF EXISTS watchlist_symbol_key
                """)

                # Add new unique constraint on (user_id, symbol)
                cur.execute("""
                    ALTER TABLE watchlist
                    ADD CONSTRAINT watchlist_user_symbol_unique UNIQUE (user_id, symbol)
                """)
                print("   ✓ Updated watchlist constraints")
            else:
                print("   - Watchlist already migrated")
        else:
            # Create new watchlist table
            cur.execute("""
                CREATE TABLE watchlist (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    symbol VARCHAR(10) NOT NULL,
                    name VARCHAR(255),
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    CONSTRAINT watchlist_user_symbol_unique UNIQUE (user_id, symbol)
                )
            """)
            print("   ✓ Created watchlist table")

        # 3. Migrate alerts table
        print("\n3. Migrating alerts table...")
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'alerts'
            )
        """)
        alerts_exists = cur.fetchone()[0]

        if alerts_exists:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_name = 'alerts' AND column_name = 'user_id'
                )
            """)
            has_user_id = cur.fetchone()[0]

            if not has_user_id:
                cur.execute("""
                    ALTER TABLE alerts
                    ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
                """)
                print("   ✓ Added user_id column to alerts")
            else:
                print("   - Alerts already migrated")
        else:
            # Create new alerts table
            cur.execute("""
                CREATE TABLE alerts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    symbol VARCHAR(10) NOT NULL,
                    alert_type VARCHAR(50) NOT NULL,
                    condition_text TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    triggered_at TIMESTAMP
                )
            """)
            print("   ✓ Created alerts table")

        # 4. Migrate user_preferences table
        print("\n4. Migrating user_preferences table...")
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'user_preferences'
            )
        """)
        prefs_exists = cur.fetchone()[0]

        if prefs_exists:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_name = 'user_preferences' AND column_name = 'user_id'
                )
            """)
            has_user_id = cur.fetchone()[0]

            if not has_user_id:
                cur.execute("""
                    ALTER TABLE user_preferences
                    ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
                """)
                print("   ✓ Added user_id column to user_preferences")

                # Drop old unique constraint
                cur.execute("""
                    ALTER TABLE user_preferences
                    DROP CONSTRAINT IF EXISTS user_preferences_key_key
                """)

                # Add new unique constraint
                cur.execute("""
                    ALTER TABLE user_preferences
                    ADD CONSTRAINT user_preferences_user_key_unique UNIQUE (user_id, key)
                """)
                print("   ✓ Updated user_preferences constraints")
            else:
                print("   - User_preferences already migrated")
        else:
            # Create new user_preferences table
            cur.execute("""
                CREATE TABLE user_preferences (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    key VARCHAR(100) NOT NULL,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT user_preferences_user_key_unique UNIQUE (user_id, key)
                )
            """)
            print("   ✓ Created user_preferences table")

        # 5. Create indexes for performance
        print("\n5. Creating indexes...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_watchlist_user_id ON watchlist(user_id)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON alerts(user_id)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(user_id, is_active)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_preferences_user_id ON user_preferences(user_id)
        """)
        print("   ✓ Indexes created")

        # Commit all changes
        conn.commit()
        print("\n" + "="*60)
        print("✓ Migration completed successfully!")
        print("="*60)
        print("\nNext steps:")
        print("1. The database schema has been updated")
        print("2. Existing data (if any) still exists but needs user assignment")
        print("3. New users can now register and login")
        print("4. Each user will have isolated data")
        print("\nNote: If you had existing data, it won't be visible until")
        print("assigned to a user. Consider it as archived/legacy data.")

    except psycopg2.Error as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {e}")
        print("\nPlease check your DATABASE_URL and database connectivity.")
        return False

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Unexpected error: {e}")
        return False

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    return True

if __name__ == "__main__":
    print("="*60)
    print("DashTrade Database Migration - Authentication Support")
    print("="*60)

    if not DATABASE_URL:
        print("\n✗ ERROR: DATABASE_URL environment variable not set!")
        print("Please set your DATABASE_URL and try again.")
        exit(1)

    proceed = input("\nThis will modify your database schema. Continue? (yes/no): ")

    if proceed.lower() in ['yes', 'y']:
        success = run_migration()
        if success:
            print("\n✓ You can now run the application with authentication enabled!")
        else:
            print("\n✗ Migration failed. Please fix the errors and try again.")
            exit(1)
    else:
        print("\nMigration cancelled.")
        exit(0)
