#!/usr/bin/env python3
"""
Database Migration Script for Trading Bot Tables
Run this script to create all necessary tables for the multi-user trading bot system
"""
import os
import psycopg2

DATABASE_URL = os.getenv('DATABASE_URL')

def run_migration():
    """Run the bot tables migration"""
    if not DATABASE_URL:
        print("❌ DATABASE_URL environment variable not set")
        print("Please set DATABASE_URL in your Replit Secrets")
        return False

    print("=" * 80)
    print("🤖 TRADING BOT DATABASE MIGRATION")
    print("=" * 80)
    print(f"\nDatabase: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Unknown'}")
    print("\nThis will create the following tables:")
    print("  - user_api_keys (encrypted Alpaca API credentials)")
    print("  - user_bot_configs (bot configurations)")
    print("  - bot_trades (trade execution log)")
    print("  - bot_performance (performance metrics)")
    print("  - user_webhook_tokens (TradingView webhook tokens)")
    print("  - bot_risk_events (risk management events)")
    print("\n⚠️  This is safe to run multiple times (CREATE TABLE IF NOT EXISTS)")
    print("=" * 80)

    response = input("\nProceed with migration? (yes/no): ")

    if response.lower() != 'yes':
        print("❌ Migration cancelled")
        return False

    try:
        # Read migration SQL
        migration_path = os.path.join(os.path.dirname(__file__), 'migrations', '001_create_bot_tables.sql')

        if not os.path.exists(migration_path):
            print(f"❌ Migration file not found: {migration_path}")
            return False

        with open(migration_path, 'r') as f:
            sql = f.read()

        # Connect to database
        print("\n📡 Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Execute migration
        print("⚙️  Running migration...")
        cur.execute(sql)
        conn.commit()

        # Verify tables created
        print("\n✅ Verifying tables...")
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN (
                'user_api_keys', 'user_bot_configs', 'bot_trades',
                'bot_performance', 'user_webhook_tokens', 'bot_risk_events'
            )
            ORDER BY table_name
        """)

        tables = cur.fetchall()

        if len(tables) == 6:
            print("✅ All 6 tables created successfully:")
            for table in tables:
                print(f"   ✓ {table[0]}")
        else:
            print(f"⚠️  Expected 6 tables, found {len(tables)}")
            for table in tables:
                print(f"   ✓ {table[0]}")

        cur.close()
        conn.close()

        print("\n" + "=" * 80)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Generate encryption key: python encryption.py")
        print("2. Add ENCRYPTION_KEY to Replit Secrets")
        print("3. Start the servers: Click 'Run' button")
        print("4. Go to Trading Bot page in the app")
        print("5. Add your Alpaca API keys")
        print("6. Create your first bot!")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)
