-- Migration: Create Trading Bot Tables
-- Description: Multi-user trading bot system with risk management

-- Store encrypted Alpaca API credentials per user
CREATE TABLE IF NOT EXISTS user_api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alpaca_api_key_encrypted TEXT NOT NULL,
    alpaca_secret_key_encrypted TEXT NOT NULL,
    alpaca_mode VARCHAR(10) DEFAULT 'paper' CHECK (alpaca_mode IN ('paper', 'live')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Bot configuration (one row per symbol+timeframe combination)
CREATE TABLE IF NOT EXISTS user_bot_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    timeframe VARCHAR(20) NOT NULL, -- '5 Min', '15 Min', '30 Min', '45 Min', etc.
    position_size DECIMAL(12, 2) NOT NULL CHECK (position_size > 0),
    is_active BOOLEAN DEFAULT TRUE,
    strategy_name VARCHAR(100),

    -- Risk Management
    risk_limit_percent DECIMAL(5, 2) DEFAULT 10.00, -- Stop trading if loss hits this %
    daily_loss_limit DECIMAL(12, 2), -- Max $ loss per day
    max_position_size DECIMAL(12, 2), -- Max $ per position

    -- Tracking
    order_status VARCHAR(50) DEFAULT 'READY',
    last_signal VARCHAR(10), -- 'BUY', 'SELL', 'CLOSE'
    last_signal_time TIMESTAMP,
    current_position_side VARCHAR(10), -- 'LONG', 'SHORT', 'FLAT'

    -- Performance
    total_pnl DECIMAL(12, 2) DEFAULT 0,
    total_trades INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, symbol, timeframe)
);

-- Trade execution log (every trade recorded)
CREATE TABLE IF NOT EXISTS bot_trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bot_config_id INTEGER REFERENCES user_bot_configs(id) ON DELETE SET NULL,

    symbol VARCHAR(10) NOT NULL,
    timeframe VARCHAR(20),
    action VARCHAR(10) NOT NULL CHECK (action IN ('BUY', 'SELL', 'CLOSE')),

    -- Order details
    quantity DECIMAL(16, 8),
    price DECIMAL(16, 4),
    notional DECIMAL(12, 2), -- Dollar amount
    order_id VARCHAR(100), -- Alpaca order ID

    -- Status tracking
    status VARCHAR(50) DEFAULT 'SUBMITTED', -- 'SUBMITTED', 'FILLED', 'PARTIAL', 'FAILED', 'CANCELLED'
    filled_qty DECIMAL(16, 8),
    filled_avg_price DECIMAL(16, 4),
    filled_at TIMESTAMP,

    -- P&L (calculated when position closed)
    realized_pnl DECIMAL(12, 2),

    -- Error handling
    error_message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance metrics per symbol per user
CREATE TABLE IF NOT EXISTS bot_performance (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,

    -- Trade statistics
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    win_rate DECIMAL(5, 2) DEFAULT 0,

    -- P&L metrics
    total_pnl DECIMAL(12, 2) DEFAULT 0,
    best_trade DECIMAL(12, 2) DEFAULT 0,
    worst_trade DECIMAL(12, 2) DEFAULT 0,
    avg_pnl_per_trade DECIMAL(12, 2) DEFAULT 0,

    -- Risk metrics
    max_drawdown DECIMAL(12, 2) DEFAULT 0,
    sharpe_ratio DECIMAL(8, 4),

    -- Timeframes
    timeframes TEXT[], -- Array of timeframes this symbol is traded on

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, symbol)
);

-- Webhook authentication tokens (one token per user for TradingView)
CREATE TABLE IF NOT EXISTS user_webhook_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    request_count INTEGER DEFAULT 0,

    UNIQUE(user_id)
);

-- Risk events log (when risk limits are triggered)
CREATE TABLE IF NOT EXISTS bot_risk_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bot_config_id INTEGER REFERENCES user_bot_configs(id) ON DELETE SET NULL,

    event_type VARCHAR(50) NOT NULL, -- 'RISK_LIMIT_HIT', 'DAILY_LOSS_LIMIT', 'MAX_POSITION_EXCEEDED'
    symbol VARCHAR(10),
    timeframe VARCHAR(20),

    threshold_value DECIMAL(12, 2),
    current_value DECIMAL(12, 2),

    action_taken VARCHAR(100), -- 'DISABLED_BOT', 'CLOSED_POSITION', 'ALERT_SENT'

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_bot_configs_user_active ON user_bot_configs(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_bot_trades_user_symbol ON bot_trades(user_id, symbol, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bot_trades_config ON bot_trades(bot_config_id);
CREATE INDEX IF NOT EXISTS idx_bot_performance_user ON bot_performance(user_id);
CREATE INDEX IF NOT EXISTS idx_webhook_tokens_token ON user_webhook_tokens(token) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_risk_events_user ON bot_risk_events(user_id, created_at DESC);
