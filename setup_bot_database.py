#!/usr/bin/env python3
"""
Automated Bot Database Setup Script for Replit
Creates all necessary tables for the Trading Bot system
"""
import os
import sys
import psycopg2

DATABASE_URL = os.getenv('DATABASE_URL')

def setup_bot_tables():
    """Automatically create bot tables"""
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print("Please set DATABASE_URL in your Replit Secrets")
        return False

    print("=" * 80)
    print("🤖 TRADING BOT DATABASE SETUP")
    print("=" * 80)

    try:
        # Read migration SQL
        migration_path = os.path.join(os.path.dirname(__file__), 'migrations', '001_create_bot_tables.sql')

        if not os.path.exists(migration_path):
            print(f"❌ Migration file not found: {migration_path}")
            return False

        with open(migration_path, 'r') as f:
            sql = f.read()

        # Connect to database
        print("📡 Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Execute migration
        print("⚙️  Creating bot tables...")
        cur.execute(sql)
        conn.commit()

        # Verify tables created
        print("✅ Verifying tables...")
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
            print("✅ All 6 bot tables created successfully:")
            for table in tables:
                print(f"   ✓ {table[0]}")
        else:
            print(f"⚠️  Expected 6 tables, found {len(tables)}")
            for table in tables:
                print(f"   ✓ {table[0]}")

        cur.close()
        conn.close()

        print("\n" + "=" * 80)
        print("✅ BOT DATABASE SETUP COMPLETED!")
        print("=" * 80)
        print("\n🎉 Your Trading Bot is now ready to use!")
        print("\nNext steps:")
        print("1. Refresh your Streamlit app")
        print("2. Go to the 🤖 Trading Bot page")
        print("3. Navigate to the ⚙️ Setup tab")
        print("4. Add your Alpaca API keys")
        print("5. Create your first trading bot!")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = setup_bot_tables()
    sys.exit(0 if success else 1)
