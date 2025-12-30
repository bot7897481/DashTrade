#!/usr/bin/env python3
"""
Run database migrations for DashTrade
Can be run standalone or imported and called from other modules
"""
import os
import sys

def run_migrations():
    """Run all pending migrations"""
    # Import here to avoid circular imports
    from database import get_db_connection, DATABASE_URL

    print(f"Running migrations...")
    print(f"Database: {DATABASE_URL[:50]}..." if DATABASE_URL else "DATABASE_URL not set!")

    if not DATABASE_URL or DATABASE_URL.startswith('sqlite'):
        print("Skipping migrations - not PostgreSQL")
        return False

    migrations = [
        # Migration 002: Add webhook_token per bot
        """
        ALTER TABLE user_bot_configs
        ADD COLUMN IF NOT EXISTS webhook_token VARCHAR(255) UNIQUE;
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_bot_configs_webhook_token
        ON user_bot_configs(webhook_token) WHERE webhook_token IS NOT NULL AND is_active = TRUE;
        """,
        """
        ALTER TABLE user_bot_configs
        ADD COLUMN IF NOT EXISTS signal_source VARCHAR(50) DEFAULT 'webhook';
        """,
        """
        ALTER TABLE user_bot_configs
        ADD COLUMN IF NOT EXISTS strategy_type VARCHAR(50) DEFAULT 'none';
        """
    ]

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for i, migration in enumerate(migrations, 1):
                    try:
                        cur.execute(migration)
                        print(f"  Migration {i}: OK")
                    except Exception as e:
                        # Ignore errors for columns that already exist
                        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                            print(f"  Migration {i}: Already applied (skipped)")
                        else:
                            print(f"  Migration {i}: ERROR - {e}")
                            raise
        print("Migrations completed successfully!")
        return True
    except Exception as e:
        print(f"Migration failed: {e}")
        return False


if __name__ == '__main__':
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    success = run_migrations()
    sys.exit(0 if success else 1)
