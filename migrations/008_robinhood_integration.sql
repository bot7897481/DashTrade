-- Migration 008: Robinhood MCP Integration
-- Adds support for Robinhood as a second broker alongside Alpaca

-- Store Robinhood OAuth tokens per user
CREATE TABLE IF NOT EXISTS user_robinhood_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMP,
    scope TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_robinhood_tokens_user ON user_robinhood_tokens(user_id);

-- Add broker column to bot configs so bots can target Alpaca or Robinhood
ALTER TABLE user_bot_configs ADD COLUMN IF NOT EXISTS broker VARCHAR(20) DEFAULT 'alpaca';

-- Add broker column to trades for tracking which broker executed
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS broker VARCHAR(20) DEFAULT 'alpaca';
