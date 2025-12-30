-- Migration: Add webhook token per bot
-- Description: Each bot gets its own webhook token for simplified TradingView integration

-- Add webhook_token column to user_bot_configs
ALTER TABLE user_bot_configs
ADD COLUMN IF NOT EXISTS webhook_token VARCHAR(255) UNIQUE;

-- Create index for fast token lookups
CREATE INDEX IF NOT EXISTS idx_bot_configs_webhook_token
ON user_bot_configs(webhook_token) WHERE webhook_token IS NOT NULL AND is_active = TRUE;

-- Add signal_source column if not exists (for differentiating webhook vs system signals)
ALTER TABLE user_bot_configs
ADD COLUMN IF NOT EXISTS signal_source VARCHAR(50) DEFAULT 'webhook';

-- Add strategy_type column if not exists
ALTER TABLE user_bot_configs
ADD COLUMN IF NOT EXISTS strategy_type VARCHAR(50) DEFAULT 'none';
