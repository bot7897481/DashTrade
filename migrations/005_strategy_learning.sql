-- Migration 005: Strategy Learning System
-- Description: Tables for AI to learn from trades and discover optimal strategy parameters
--
-- This enables:
-- 1. Capturing strategy parameters for each trade (MA periods, RSI thresholds, etc.)
-- 2. Tracking trade outcomes (P&L, duration, exit reason)
-- 3. AI analysis to find winning patterns
-- 4. Data-driven strategy recommendations

-- ============================================================================
-- Trade Strategy Parameters Table
-- Captures the strategy settings used for each trade
-- ============================================================================
CREATE TABLE IF NOT EXISTS trade_strategy_params (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER UNIQUE REFERENCES bot_trades(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    -- Strategy Identification
    strategy_type VARCHAR(50),            -- momentum, mean_reversion, breakout, scalp, trend_follow
    strategy_name VARCHAR(100),           -- User-defined name or system strategy name
    strategy_version VARCHAR(20),         -- v1.0, v2.1, etc. for tracking iterations

    -- Entry Signal Parameters
    entry_indicator VARCHAR(50),          -- RSI, MACD, MA_cross, price_action, volume_breakout
    entry_condition VARCHAR(100),         -- crosses_above, crosses_below, greater_than, etc.
    entry_threshold DECIMAL(10,4),        -- The trigger value (e.g., RSI=30)
    entry_value_at_signal DECIMAL(10,4),  -- Actual indicator value when signal fired

    -- Moving Average Parameters
    ma_fast_period INTEGER,               -- Fast MA period: 9, 12, 20
    ma_fast_type VARCHAR(10),             -- SMA, EMA, WMA, VWMA
    ma_slow_period INTEGER,               -- Slow MA period: 21, 50, 200
    ma_slow_type VARCHAR(10),             -- SMA, EMA, WMA, VWMA
    ma_trend_period INTEGER,              -- Trend MA period: 200
    price_vs_ma_fast DECIMAL(8,4),        -- % above/below fast MA at entry
    price_vs_ma_slow DECIMAL(8,4),        -- % above/below slow MA at entry

    -- RSI Parameters
    rsi_period INTEGER,                   -- Typically 14
    rsi_value_at_entry DECIMAL(5,2),      -- RSI value when trade entered
    rsi_oversold_level INTEGER,           -- 30 default
    rsi_overbought_level INTEGER,         -- 70 default

    -- MACD Parameters
    macd_fast_period INTEGER,             -- 12 default
    macd_slow_period INTEGER,             -- 26 default
    macd_signal_period INTEGER,           -- 9 default
    macd_value_at_entry DECIMAL(10,4),
    macd_signal_at_entry DECIMAL(10,4),
    macd_histogram_at_entry DECIMAL(10,4),

    -- Bollinger Bands Parameters
    bb_period INTEGER,                    -- 20 default
    bb_std_dev DECIMAL(3,1),              -- 2.0 default
    bb_position VARCHAR(20),              -- above_upper, below_lower, middle

    -- ATR / Volatility Parameters
    atr_period INTEGER,                   -- 14 default
    atr_value_at_entry DECIMAL(10,4),
    atr_multiplier_stop DECIMAL(3,1),     -- Stop loss = ATR * multiplier
    atr_multiplier_target DECIMAL(3,1),   -- Take profit = ATR * multiplier

    -- Volume Parameters
    volume_ma_period INTEGER,             -- 20 default
    volume_ratio_at_entry DECIMAL(5,2),   -- Current vol / avg vol
    volume_condition VARCHAR(50),         -- above_average, spike, declining

    -- Risk Management Parameters
    stop_loss_type VARCHAR(20),           -- percent, atr, fixed, trailing
    stop_loss_value DECIMAL(8,4),         -- The stop loss value/percent
    take_profit_type VARCHAR(20),         -- percent, atr, fixed, ratio
    take_profit_value DECIMAL(8,4),       -- The take profit value/percent
    risk_reward_ratio DECIMAL(4,2),       -- Target R:R ratio
    position_size_method VARCHAR(20),     -- fixed_dollar, percent_equity, kelly

    -- Time-Based Parameters
    trade_session VARCHAR(20),            -- pre_market, regular, after_hours
    day_of_week INTEGER,                  -- 1=Monday, 5=Friday
    hour_of_day INTEGER,                  -- 0-23 UTC
    minutes_since_open INTEGER,           -- Minutes since market open

    -- Trend Context at Entry
    trend_short VARCHAR(10),              -- up, down, sideways (based on fast MA)
    trend_medium VARCHAR(10),             -- up, down, sideways (based on slow MA)
    trend_long VARCHAR(10),               -- up, down, sideways (based on 200 MA)

    -- Raw JSON for additional/custom parameters
    custom_params JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Trade Outcomes Table
-- Tracks the result of each trade for P&L analysis
-- ============================================================================
CREATE TABLE IF NOT EXISTS trade_outcomes (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER UNIQUE REFERENCES bot_trades(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    -- Position Tracking
    position_type VARCHAR(10),            -- long, short

    -- Entry Details
    entry_price DECIMAL(16,4) NOT NULL,
    entry_time TIMESTAMP NOT NULL,
    entry_order_id VARCHAR(100),

    -- Exit Details
    exit_price DECIMAL(16,4),
    exit_time TIMESTAMP,
    exit_order_id VARCHAR(100),
    exit_reason VARCHAR(50),              -- signal, stop_loss, take_profit, trailing_stop, manual, time_exit

    -- Quantity & Value
    quantity DECIMAL(16,8),
    entry_value DECIMAL(16,2),            -- Total $ at entry
    exit_value DECIMAL(16,2),             -- Total $ at exit

    -- P&L Calculations
    pnl_dollars DECIMAL(12,2),            -- Profit/Loss in dollars
    pnl_percent DECIMAL(8,4),             -- Profit/Loss as percentage
    pnl_r_multiple DECIMAL(6,2),          -- P&L as multiple of risk (R)

    -- Fees & Slippage
    commission_paid DECIMAL(8,2),
    slippage_dollars DECIMAL(8,2),
    slippage_percent DECIMAL(6,4),

    -- Duration
    hold_duration_seconds INTEGER,
    hold_duration_minutes INTEGER,
    hold_duration_hours DECIMAL(8,2),
    bars_held INTEGER,                    -- Number of candles held

    -- Price Movement During Trade
    max_favorable_excursion DECIMAL(8,4), -- MFE: Max profit seen during trade (%)
    max_adverse_excursion DECIMAL(8,4),   -- MAE: Max drawdown during trade (%)

    -- Classification
    is_winner BOOLEAN,
    is_breakeven BOOLEAN DEFAULT FALSE,   -- Within small threshold of 0

    -- Status
    status VARCHAR(20) DEFAULT 'open',    -- open, closed, cancelled

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Strategy Performance Summary (Aggregated View)
-- Pre-calculated stats for quick dashboard access
-- ============================================================================
CREATE TABLE IF NOT EXISTS strategy_performance_summary (
    id SERIAL PRIMARY KEY,

    -- Grouping Keys
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    strategy_type VARCHAR(50),
    symbol VARCHAR(20),
    timeframe VARCHAR(20),

    -- Date Range
    period_start DATE,
    period_end DATE,

    -- Trade Counts
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    breakeven_trades INTEGER DEFAULT 0,

    -- Win Rate
    win_rate DECIMAL(5,2),                -- Percentage

    -- P&L Stats
    total_pnl_dollars DECIMAL(14,2) DEFAULT 0,
    total_pnl_percent DECIMAL(10,4) DEFAULT 0,
    avg_win_dollars DECIMAL(12,2),
    avg_loss_dollars DECIMAL(12,2),
    avg_win_percent DECIMAL(8,4),
    avg_loss_percent DECIMAL(8,4),
    largest_win_dollars DECIMAL(12,2),
    largest_loss_dollars DECIMAL(12,2),

    -- Risk Metrics
    profit_factor DECIMAL(6,2),           -- Gross profit / Gross loss
    avg_r_multiple DECIMAL(5,2),          -- Average R per trade
    expectancy DECIMAL(8,4),              -- Expected $ per trade

    -- Drawdown
    max_drawdown_dollars DECIMAL(12,2),
    max_drawdown_percent DECIMAL(8,4),
    max_consecutive_wins INTEGER,
    max_consecutive_losses INTEGER,

    -- Duration Stats
    avg_hold_duration_minutes INTEGER,
    avg_winner_duration_minutes INTEGER,
    avg_loser_duration_minutes INTEGER,

    -- MFE/MAE Analysis
    avg_mfe_percent DECIMAL(6,4),
    avg_mae_percent DECIMAL(6,4),

    -- Calculated At
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, strategy_type, symbol, timeframe, period_start, period_end)
);

-- ============================================================================
-- AI Learning Insights Table
-- Stores discovered patterns and recommendations
-- ============================================================================
CREATE TABLE IF NOT EXISTS ai_strategy_insights (
    id SERIAL PRIMARY KEY,

    -- Insight Identification
    insight_type VARCHAR(50),             -- optimal_params, market_condition, avoid_pattern
    confidence_score DECIMAL(5,2),        -- 0-100 confidence in insight
    sample_size INTEGER,                  -- Number of trades analyzed

    -- Context
    symbol VARCHAR(20),                   -- NULL for all symbols
    timeframe VARCHAR(20),                -- NULL for all timeframes
    strategy_type VARCHAR(50),            -- NULL for all strategies

    -- The Insight
    title VARCHAR(200),
    description TEXT,

    -- Conditions that trigger this insight
    conditions JSONB,                     -- {"vix_min": 15, "vix_max": 20, "rsi_threshold": 30}

    -- Performance when following this insight
    observed_win_rate DECIMAL(5,2),
    observed_avg_return DECIMAL(8,4),
    observed_trades INTEGER,

    -- Recommendation
    recommendation TEXT,
    recommended_params JSONB,             -- {"rsi_threshold": 32, "ma_fast": 12, "stop_loss": 1.5}

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    validated_at TIMESTAMP,               -- When insight was confirmed with new data

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Trade Strategy Params indexes
CREATE INDEX IF NOT EXISTS idx_strategy_params_trade ON trade_strategy_params(trade_id);
CREATE INDEX IF NOT EXISTS idx_strategy_params_user ON trade_strategy_params(user_id);
CREATE INDEX IF NOT EXISTS idx_strategy_params_type ON trade_strategy_params(strategy_type);
CREATE INDEX IF NOT EXISTS idx_strategy_params_indicator ON trade_strategy_params(entry_indicator);
CREATE INDEX IF NOT EXISTS idx_strategy_params_created ON trade_strategy_params(created_at DESC);

-- Trade Outcomes indexes
CREATE INDEX IF NOT EXISTS idx_outcomes_trade ON trade_outcomes(trade_id);
CREATE INDEX IF NOT EXISTS idx_outcomes_user ON trade_outcomes(user_id);
CREATE INDEX IF NOT EXISTS idx_outcomes_winner ON trade_outcomes(is_winner);
CREATE INDEX IF NOT EXISTS idx_outcomes_status ON trade_outcomes(status);
CREATE INDEX IF NOT EXISTS idx_outcomes_exit_reason ON trade_outcomes(exit_reason);
CREATE INDEX IF NOT EXISTS idx_outcomes_entry_time ON trade_outcomes(entry_time DESC);
CREATE INDEX IF NOT EXISTS idx_outcomes_pnl ON trade_outcomes(pnl_percent);

-- Strategy Performance Summary indexes
CREATE INDEX IF NOT EXISTS idx_perf_summary_user ON strategy_performance_summary(user_id);
CREATE INDEX IF NOT EXISTS idx_perf_summary_strategy ON strategy_performance_summary(strategy_type);
CREATE INDEX IF NOT EXISTS idx_perf_summary_symbol ON strategy_performance_summary(symbol);

-- AI Insights indexes
CREATE INDEX IF NOT EXISTS idx_insights_type ON ai_strategy_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_insights_active ON ai_strategy_insights(is_active);
CREATE INDEX IF NOT EXISTS idx_insights_confidence ON ai_strategy_insights(confidence_score DESC);

-- ============================================================================
-- Comments
-- ============================================================================
COMMENT ON TABLE trade_strategy_params IS 'Captures strategy parameters for each trade to enable AI learning';
COMMENT ON TABLE trade_outcomes IS 'Tracks trade results (P&L, duration, exit reason) for performance analysis';
COMMENT ON TABLE strategy_performance_summary IS 'Pre-aggregated strategy performance metrics for quick access';
COMMENT ON TABLE ai_strategy_insights IS 'AI-discovered patterns and optimal parameter recommendations';

COMMENT ON COLUMN trade_strategy_params.entry_value_at_signal IS 'The actual indicator value when the signal fired (e.g., RSI was 28.5)';
COMMENT ON COLUMN trade_outcomes.pnl_r_multiple IS 'P&L expressed as multiple of initial risk (R). +2R means made 2x the risked amount';
COMMENT ON COLUMN trade_outcomes.max_favorable_excursion IS 'Maximum profit seen during the trade before exit - helps optimize exits';
COMMENT ON COLUMN trade_outcomes.max_adverse_excursion IS 'Maximum drawdown during trade - helps optimize stop losses';
COMMENT ON COLUMN strategy_performance_summary.profit_factor IS 'Gross profits / Gross losses. >1 is profitable, >2 is very good';
COMMENT ON COLUMN strategy_performance_summary.expectancy IS 'Average expected profit per trade in dollars';
COMMENT ON COLUMN ai_strategy_insights.confidence_score IS 'AI confidence in this insight based on sample size and consistency';
