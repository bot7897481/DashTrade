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
        "ALTER TABLE user_bot_configs ADD COLUMN IF NOT EXISTS webhook_token VARCHAR(255) UNIQUE;",
        "CREATE INDEX IF NOT EXISTS idx_bot_configs_webhook_token ON user_bot_configs(webhook_token) WHERE webhook_token IS NOT NULL AND is_active = TRUE;",
        "ALTER TABLE user_bot_configs ADD COLUMN IF NOT EXISTS signal_source VARCHAR(50) DEFAULT 'webhook';",
        "ALTER TABLE user_bot_configs ADD COLUMN IF NOT EXISTS strategy_type VARCHAR(50) DEFAULT 'none';",

        # Migration 003: Enhanced trade details
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS bid_price DECIMAL(16, 4);",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS ask_price DECIMAL(16, 4);",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS spread DECIMAL(16, 4);",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS spread_percent DECIMAL(8, 4);",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS market_open BOOLEAN;",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS extended_hours BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS signal_source VARCHAR(50) DEFAULT 'webhook';",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS signal_received_at TIMESTAMP;",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS order_submitted_at TIMESTAMP;",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS execution_latency_ms INTEGER;",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS time_to_fill_ms INTEGER;",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS order_type VARCHAR(20) DEFAULT 'market';",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS time_in_force VARCHAR(10) DEFAULT 'day';",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS limit_price DECIMAL(16, 4);",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS stop_price DECIMAL(16, 4);",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS expected_price DECIMAL(16, 4);",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS slippage DECIMAL(16, 4);",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS slippage_percent DECIMAL(8, 4);",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS position_before VARCHAR(10);",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS position_after VARCHAR(10);",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS position_qty_before DECIMAL(16, 8) DEFAULT 0;",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS position_value_before DECIMAL(12, 2) DEFAULT 0;",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS account_equity DECIMAL(12, 2);",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS account_buying_power DECIMAL(12, 2);",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS alpaca_order_status VARCHAR(50);",
        "ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS alpaca_client_order_id VARCHAR(100);",
        "CREATE INDEX IF NOT EXISTS idx_trades_signal_received ON bot_trades(signal_received_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_trades_signal_source ON bot_trades(signal_source);",
        "ALTER TABLE user_bot_configs ADD COLUMN IF NOT EXISTS last_trade_at TIMESTAMP;",
        "ALTER TABLE user_bot_configs ADD COLUMN IF NOT EXISTS last_trade_pnl DECIMAL(12, 2);",
        "ALTER TABLE user_bot_configs ADD COLUMN IF NOT EXISTS consecutive_wins INTEGER DEFAULT 0;",
        "ALTER TABLE user_bot_configs ADD COLUMN IF NOT EXISTS consecutive_losses INTEGER DEFAULT 0;",
        "ALTER TABLE user_bot_configs ADD COLUMN IF NOT EXISTS avg_trade_duration_minutes INTEGER;",
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
