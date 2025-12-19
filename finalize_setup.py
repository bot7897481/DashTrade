#!/usr/bin/env python3
"""
DashTrade Setup Finalization Script
This script completes the setup by:
1. Verifying DATABASE_URL
2. Running database migration
3. Creating superadmin account
"""
import os
import sys
import getpass
from dotenv import load_dotenv

load_dotenv()

def check_database_url():
    """Check if DATABASE_URL is set"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("\n❌ DATABASE_URL is not set!")
        print("\nPlease set DATABASE_URL first:")
        print("="*70)
        print("\nQuick Setup Options:")
        print("\n1. Neon.tech (Recommended)")
        print("   • Go to https://neon.tech")
        print("   • Sign up and create project")
        print("   • Copy connection string")
        print("   • Add to Replit Secrets: DATABASE_URL")
        print("\n2. Supabase")
        print("   • Go to https://supabase.com")
        print("   • Create project and copy database URL")
        print("\n3. Local PostgreSQL")
        print("   • Set: export DATABASE_URL='postgresql://user:pass@localhost:5432/dashtrade'")
        print("="*70)
        return False
    return True

def test_connection():
    """Test database connection"""
    try:
        db_url = os.getenv('DATABASE_URL')
        if db_url and db_url.startswith('sqlite'):
            import sqlite3
            print("\n🔌 Testing database connection (SQLite)...")
            db_path = db_url.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            # Create the file if it doesn't exist to ensure write permissions
            conn.execute("CREATE TABLE IF NOT EXISTS _test_conn (id INTEGER)")
            conn.execute("DROP TABLE _test_conn")
            print("✅ Database connection successful!")
            conn.close()
            return True

        import psycopg2
        print("\n🔌 Testing database connection...")
        conn = psycopg2.connect(db_url)
        print("✅ Database connection successful!")
        conn.close()
        return True
    except ImportError:
        # Check if we're using SQLite
        if db_url and db_url.startswith('sqlite'):
            print("ℹ️ Using SQLite (psycopg2 not needed)")
            return True
        print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def run_migration():
    """Run database migration"""
    print("\n📊 Running database migration...")
    print("="*70)

    try:
        # Import migration functionality
        db_url = os.getenv('DATABASE_URL')
        
        # Determine strict mode (PostgreSQL) vs compat mode (SQLite)
        is_sqlite = db_url and db_url.startswith('sqlite')
        
        if is_sqlite:
            import sqlite3
            db_path = db_url.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            # SQLite doesn't need autocommit=False for this simple script usually, but let's keep it safe
            # conn.autocommit = False # Not attribute in sqlite3
        else:
            conn = psycopg2.connect(db_url)
            conn.autocommit = False
            
        cur = conn.cursor()

        # Create users table with role support
        # SQLite uses INTEGER PRIMARY KEY AUTOINCREMENT instead of SERIAL
        serial_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if is_sqlite else "SERIAL PRIMARY KEY"
        
        print("Creating users table with role support...")
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS users (
                id {serial_type},
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                email_enabled BOOLEAN DEFAULT FALSE,
                role VARCHAR(50) DEFAULT 'user' NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        print("  ✅ Users table created")

        # Check for email_enabled column
        if is_sqlite:
            cur.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cur.fetchall()]
            if 'email_enabled' not in columns:
                print("Adding email_enabled column to users...")
                cur.execute("ALTER TABLE users ADD COLUMN email_enabled BOOLEAN DEFAULT 0")
        else:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_name = 'users' AND column_name = 'email_enabled'
                )
            """)
            if not cur.fetchone()[0]:
                print("Adding email_enabled column to users...")
                cur.execute("ALTER TABLE users ADD COLUMN email_enabled BOOLEAN DEFAULT FALSE")

        # Check if watchlist exists
        if is_sqlite:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='watchlist'")
            watchlist_exists = cur.fetchone() is not None
        else:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'watchlist'
                )
            """)
            watchlist_exists = cur.fetchone()[0]

        if watchlist_exists:
            # Add user_id if it doesn't exist
            if is_sqlite:
                # SQLite PRAGMA table_info returns (cid, name, type, notnull, dflt_value, pk)
                cur.execute("PRAGMA table_info(watchlist)")
                columns = [row[1] for row in cur.fetchall()]
                has_user_id = 'user_id' in columns
            else:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_name = 'watchlist' AND column_name = 'user_id'
                    )
                """)
                has_user_id = cur.fetchone()[0]

            if not has_user_id:
                print("Updating watchlist table...")
                cur.execute("""
                    ALTER TABLE watchlist
                    ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
                """)
                cur.execute("""
                    ALTER TABLE watchlist
                    DROP CONSTRAINT IF EXISTS watchlist_symbol_key
                """)
                cur.execute("""
                    ALTER TABLE watchlist
                    ADD CONSTRAINT watchlist_user_symbol_unique UNIQUE (user_id, symbol)
                """)
                print("  ✅ Watchlist table updated")
        else:
            print("Creating watchlist table...")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS watchlist (
                    id {serial_type},
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    symbol VARCHAR(10) NOT NULL,
                    name VARCHAR(255),
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    CONSTRAINT watchlist_user_symbol_unique UNIQUE (user_id, symbol)
                )
            """)
            print("  ✅ Watchlist table created")

        # Alerts table
        if is_sqlite:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'")
            alerts_exists = cur.fetchone() is not None
        else:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'alerts'
                )
            """)
            alerts_exists = cur.fetchone()[0]

        if alerts_exists:
            if is_sqlite:
                cur.execute("PRAGMA table_info(alerts)")
                columns = [row[1] for row in cur.fetchall()]
                has_user_id = 'user_id' in columns
            else:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_name = 'alerts' AND column_name = 'user_id'
                    )
                """)
                has_user_id = cur.fetchone()[0]

            if not has_user_id:
                print("Updating alerts table...")
                cur.execute("""
                    ALTER TABLE alerts
                    ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
                """)
                print("  ✅ Alerts table updated")
        else:
            print("Creating alerts table...")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS alerts (
                    id {serial_type},
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    symbol VARCHAR(10) NOT NULL,
                    alert_type VARCHAR(50) NOT NULL,
                    condition_text TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    triggered_at TIMESTAMP
                )
            """)
            print("  ✅ Alerts table created")

        # User preferences table
        if is_sqlite:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_preferences'")
            prefs_exists = cur.fetchone() is not None
        else:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'user_preferences'
                )
            """)
            prefs_exists = cur.fetchone()[0]

        if prefs_exists:
            if is_sqlite:
                cur.execute("PRAGMA table_info(user_preferences)")
                columns = [row[1] for row in cur.fetchall()]
                has_user_id = 'user_id' in columns
            else:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_name = 'user_preferences' AND column_name = 'user_id'
                    )
                """)
                has_user_id = cur.fetchone()[0]

            if not has_user_id:
                print("Updating user_preferences table...")
                cur.execute("""
                    ALTER TABLE user_preferences
                    ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
                """)
                cur.execute("""
                    ALTER TABLE user_preferences
                    DROP CONSTRAINT IF EXISTS user_preferences_key_key
                """)
                cur.execute("""
                    ALTER TABLE user_preferences
                    ADD CONSTRAINT user_preferences_user_key_unique UNIQUE (user_id, key)
                """)
                print("  ✅ User preferences table updated")
        else:
            print("Creating user_preferences table...")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id {serial_type},
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    key VARCHAR(100) NOT NULL,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT user_preferences_user_key_unique UNIQUE (user_id, key)
                )
            """)
            print("  ✅ User preferences table created")

        # User LLM Keys table
        if is_sqlite:
            print("Creating 'user_llm_keys' table (SQLite)...")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS user_llm_keys (
                user_id INTEGER PRIMARY KEY,
                provider TEXT NOT NULL,
                api_key_encrypted TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """)
        else:
            print("Creating 'user_llm_keys' table (PostgreSQL)...")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS user_llm_keys (
                user_id INTEGER PRIMARY KEY,
                provider VARCHAR(50) NOT NULL,
                api_key_encrypted TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """)
        print("  ✅ User LLM Keys table created")

        # Create indexes
        print("Creating indexes...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_user_id ON watchlist(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON alerts(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(user_id, is_active)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_preferences_user_id ON user_preferences(user_id)")
        print("  ✅ Indexes created")

        conn.commit()
        cur.close()
        conn.close()

        print("\n✅ Database migration completed successfully!")
        print("="*70)
        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        if conn:
            conn.rollback()
        return False

def create_superadmin():
    """Create superadmin account"""
    print("\n👑 Creating Superadmin Account")
    print("="*70)

    try:
        from auth import UserDB

        # Check if any superadmin exists
        db_url = os.getenv('DATABASE_URL')
        if db_url and db_url.startswith('sqlite'):
            import sqlite3
            db_path = db_url.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
        else:
            import psycopg2
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            
        cur.execute("SELECT COUNT(*) FROM users WHERE role = 'superadmin'")
        superadmin_count = cur.fetchone()[0]
        cur.close()
        conn.close()

        if superadmin_count > 0:
            print(f"\n⚠️  {superadmin_count} superadmin(s) already exist.")
            create_another = input("\nCreate another superadmin? (yes/no): ").lower()
            if create_another not in ['yes', 'y']:
                print("Skipping superadmin creation.")
                return True

        print("\nPlease provide superadmin account details:")
        print("-" * 70)

        username = input("Username: ").strip()
        if len(username) < 3:
            print("❌ Username must be at least 3 characters")
            return False

        email = input("Email: ").strip()
        if '@' not in email:
            print("❌ Invalid email address")
            return False

        full_name = input("Full Name (optional): ").strip() or None

        password = getpass.getpass("Password (min 6 chars): ")
        if len(password) < 6:
            print("❌ Password must be at least 6 characters")
            return False

        password_confirm = getpass.getpass("Confirm Password: ")
        if password != password_confirm:
            print("❌ Passwords do not match")
            return False

        print("\n🔐 Creating superadmin account...")

        result = UserDB.register_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            role='superadmin'
        )

        if result['success']:
            print("\n✅ Superadmin account created successfully!")
            print("="*70)
            print(f"\n👤 Username: {username}")
            print(f"📧 Email: {email}")
            print(f"👑 Role: SUPERADMIN")
            print("\n" + "="*70)
            return True
        else:
            print(f"\n❌ Failed to create superadmin: {result['error']}")
            return False

    except Exception as e:
        print(f"\n❌ Error creating superadmin: {e}")
        return False

def main():
    print("="*70)
    print("       DashTrade Setup Finalization")
    print("="*70)

    # Step 1: Check DATABASE_URL
    if not check_database_url():
        sys.exit(1)

    # Step 2: Test connection
    if not test_connection():
        sys.exit(1)

    # Step 3: Run migration
    if not run_migration():
        print("\n❌ Setup failed at migration step")
        sys.exit(1)

    # Step 4: Create superadmin
    if not create_superadmin():
        print("\n⚠️  Setup completed but superadmin creation failed")
        print("You can create superadmin later using this script")
        sys.exit(1)

    # Success!
    print("\n" + "="*70)
    print("🎉 Setup Complete!")
    print("="*70)
    print("\n✅ Database configured")
    print("✅ Tables migrated")
    print("✅ Superadmin account created")
    print("\n📱 Next Steps:")
    print("  1. Run: streamlit run app.py")
    print("  2. Login with your superadmin credentials")
    print("  3. Start trading!")
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
