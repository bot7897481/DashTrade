-- Migration: Trade Market Context
-- Description: Store comprehensive market data captured at the time of each trade
-- This enables detailed post-trade analysis with full market context

-- Create trade_market_context table (linked to bot_trades)
CREATE TABLE IF NOT EXISTS trade_market_context (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER UNIQUE REFERENCES bot_trades(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- ========================================
    -- STOCK-SPECIFIC DATA (at trade time)
    -- ========================================

    -- Current day OHLCV
    stock_open DECIMAL(16, 4),
    stock_high DECIMAL(16, 4),
    stock_low DECIMAL(16, 4),
    stock_close DECIMAL(16, 4),
    stock_volume BIGINT,
    stock_prev_close DECIMAL(16, 4),
    stock_change_percent DECIMAL(8, 4),

    -- Intraday context
    stock_vwap DECIMAL(16, 4),
    stock_avg_volume BIGINT,
    stock_volume_ratio DECIMAL(8, 4),  -- current volume / avg volume

    -- ========================================
    -- FUNDAMENTAL DATA (from Yahoo Finance)
    -- ========================================

    market_cap BIGINT,
    pe_ratio DECIMAL(10, 4),
    forward_pe DECIMAL(10, 4),
    eps DECIMAL(10, 4),
    beta DECIMAL(8, 4),
    dividend_yield DECIMAL(8, 4),
    shares_outstanding BIGINT,
    float_shares BIGINT,
    short_ratio DECIMAL(8, 4),
    fifty_two_week_high DECIMAL(16, 4),
    fifty_two_week_low DECIMAL(16, 4),
    fifty_day_ma DECIMAL(16, 4),
    two_hundred_day_ma DECIMAL(16, 4),

    -- ========================================
    -- MARKET INDICES (at trade time)
    -- ========================================

    -- S&P 500
    sp500_price DECIMAL(16, 4),
    sp500_change_percent DECIMAL(8, 4),

    -- NASDAQ
    nasdaq_price DECIMAL(16, 4),
    nasdaq_change_percent DECIMAL(8, 4),

    -- Dow Jones
    dji_price DECIMAL(16, 4),
    dji_change_percent DECIMAL(8, 4),

    -- Russell 2000
    russell_price DECIMAL(16, 4),
    russell_change_percent DECIMAL(8, 4),

    -- ========================================
    -- VOLATILITY & RISK INDICATORS
    -- ========================================

    vix_price DECIMAL(10, 4),
    vix_change_percent DECIMAL(8, 4),

    -- Treasury yields
    treasury_10y_yield DECIMAL(8, 4),
    treasury_2y_yield DECIMAL(8, 4),
    yield_curve_spread DECIMAL(8, 4),  -- 10y - 2y

    -- ========================================
    -- SECTOR CONTEXT (ETF prices)
    -- ========================================

    -- Stock's sector ETF
    sector_etf_symbol VARCHAR(10),
    sector_etf_price DECIMAL(16, 4),
    sector_etf_change_percent DECIMAL(8, 4),

    -- Major sector ETFs
    xlk_price DECIMAL(16, 4),   -- Technology
    xlf_price DECIMAL(16, 4),   -- Financials
    xle_price DECIMAL(16, 4),   -- Energy
    xlv_price DECIMAL(16, 4),   -- Healthcare
    xly_price DECIMAL(16, 4),   -- Consumer Discretionary
    xlp_price DECIMAL(16, 4),   -- Consumer Staples
    xli_price DECIMAL(16, 4),   -- Industrials
    xlb_price DECIMAL(16, 4),   -- Materials
    xlu_price DECIMAL(16, 4),   -- Utilities
    xlre_price DECIMAL(16, 4),  -- Real Estate

    -- ========================================
    -- ACCOUNT CONTEXT (from Alpaca)
    -- ========================================

    account_equity DECIMAL(16, 4),
    account_cash DECIMAL(16, 4),
    account_buying_power DECIMAL(16, 4),
    account_portfolio_value DECIMAL(16, 4),
    account_margin_used DECIMAL(16, 4),

    -- Position context
    position_qty_before DECIMAL(16, 8),
    position_value_before DECIMAL(16, 4),
    position_avg_entry DECIMAL(16, 4),
    position_unrealized_pl DECIMAL(16, 4),

    -- Total portfolio context
    total_positions_count INTEGER,
    total_positions_value DECIMAL(16, 4),

    -- ========================================
    -- TECHNICAL CONTEXT (calculated)
    -- ========================================

    -- Price relative to moving averages
    price_vs_50ma_percent DECIMAL(8, 4),
    price_vs_200ma_percent DECIMAL(8, 4),

    -- Distance from 52-week range
    price_vs_52w_high_percent DECIMAL(8, 4),
    price_vs_52w_low_percent DECIMAL(8, 4),

    -- RSI (if we calculate it)
    rsi_14 DECIMAL(8, 4),

    -- ========================================
    -- METADATA
    -- ========================================

    data_source VARCHAR(50) DEFAULT 'yfinance',
    fetch_latency_ms INTEGER,
    errors TEXT  -- Any errors during data fetch
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_trade_context_trade_id ON trade_market_context(trade_id);
CREATE INDEX IF NOT EXISTS idx_trade_context_user_id ON trade_market_context(user_id);
CREATE INDEX IF NOT EXISTS idx_trade_context_captured_at ON trade_market_context(captured_at DESC);

-- Add comment explaining the table
COMMENT ON TABLE trade_market_context IS 'Comprehensive market snapshot captured at the time of each trade execution for post-trade analysis';
