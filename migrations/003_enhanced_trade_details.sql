-- Migration: Enhanced Trade Details
-- Description: Add detailed execution information for better trade analysis and planning

-- Add detailed execution columns to bot_trades
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS bid_price DECIMAL(16, 4);
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS ask_price DECIMAL(16, 4);
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS spread DECIMAL(16, 4);
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS spread_percent DECIMAL(8, 4);

-- Market conditions at time of trade
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS market_open BOOLEAN;
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS extended_hours BOOLEAN DEFAULT FALSE;

-- Signal information
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS signal_source VARCHAR(50) DEFAULT 'webhook';
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS signal_received_at TIMESTAMP;
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS order_submitted_at TIMESTAMP;

-- Execution timing
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS execution_latency_ms INTEGER;
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS time_to_fill_ms INTEGER;

-- Order type and details
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS order_type VARCHAR(20) DEFAULT 'market';
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS time_in_force VARCHAR(10) DEFAULT 'day';
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS limit_price DECIMAL(16, 4);
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS stop_price DECIMAL(16, 4);

-- Slippage tracking
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS expected_price DECIMAL(16, 4);
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS slippage DECIMAL(16, 4);
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS slippage_percent DECIMAL(8, 4);

-- Position context
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS position_before VARCHAR(10);
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS position_after VARCHAR(10);
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS position_qty_before DECIMAL(16, 8) DEFAULT 0;
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS position_value_before DECIMAL(12, 2) DEFAULT 0;

-- Account context at trade time
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS account_equity DECIMAL(12, 2);
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS account_buying_power DECIMAL(12, 2);

-- Alpaca order details
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS alpaca_order_status VARCHAR(50);
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS alpaca_client_order_id VARCHAR(100);

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_trades_signal_received ON bot_trades(signal_received_at DESC);
CREATE INDEX IF NOT EXISTS idx_trades_signal_source ON bot_trades(signal_source);
CREATE INDEX IF NOT EXISTS idx_trades_status_created ON bot_trades(status, created_at DESC);

-- Update bot_configs with more tracking fields
ALTER TABLE user_bot_configs ADD COLUMN IF NOT EXISTS last_trade_at TIMESTAMP;
ALTER TABLE user_bot_configs ADD COLUMN IF NOT EXISTS last_trade_pnl DECIMAL(12, 2);
ALTER TABLE user_bot_configs ADD COLUMN IF NOT EXISTS consecutive_wins INTEGER DEFAULT 0;
ALTER TABLE user_bot_configs ADD COLUMN IF NOT EXISTS consecutive_losses INTEGER DEFAULT 0;
ALTER TABLE user_bot_configs ADD COLUMN IF NOT EXISTS avg_trade_duration_minutes INTEGER;
