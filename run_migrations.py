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

        # Migration 004: Trade market context table
        """CREATE TABLE IF NOT EXISTS trade_market_context (
            id SERIAL PRIMARY KEY,
            trade_id INTEGER UNIQUE REFERENCES bot_trades(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            stock_open DECIMAL(16, 4), stock_high DECIMAL(16, 4), stock_low DECIMAL(16, 4),
            stock_close DECIMAL(16, 4), stock_volume BIGINT, stock_prev_close DECIMAL(16, 4),
            stock_change_percent DECIMAL(8, 4), stock_vwap DECIMAL(16, 4),
            stock_avg_volume BIGINT, stock_volume_ratio DECIMAL(8, 4),
            market_cap BIGINT, pe_ratio DECIMAL(10, 4), forward_pe DECIMAL(10, 4),
            eps DECIMAL(10, 4), beta DECIMAL(8, 4), dividend_yield DECIMAL(8, 4),
            shares_outstanding BIGINT, float_shares BIGINT, short_ratio DECIMAL(8, 4),
            fifty_two_week_high DECIMAL(16, 4), fifty_two_week_low DECIMAL(16, 4),
            fifty_day_ma DECIMAL(16, 4), two_hundred_day_ma DECIMAL(16, 4),
            sp500_price DECIMAL(16, 4), sp500_change_percent DECIMAL(8, 4),
            nasdaq_price DECIMAL(16, 4), nasdaq_change_percent DECIMAL(8, 4),
            dji_price DECIMAL(16, 4), dji_change_percent DECIMAL(8, 4),
            russell_price DECIMAL(16, 4), russell_change_percent DECIMAL(8, 4),
            vix_price DECIMAL(10, 4), vix_change_percent DECIMAL(8, 4),
            treasury_10y_yield DECIMAL(8, 4), treasury_2y_yield DECIMAL(8, 4),
            yield_curve_spread DECIMAL(8, 4),
            sector_etf_symbol VARCHAR(10), sector_etf_price DECIMAL(16, 4),
            sector_etf_change_percent DECIMAL(8, 4),
            xlk_price DECIMAL(16, 4), xlf_price DECIMAL(16, 4), xle_price DECIMAL(16, 4),
            xlv_price DECIMAL(16, 4), xly_price DECIMAL(16, 4), xlp_price DECIMAL(16, 4),
            xli_price DECIMAL(16, 4), xlb_price DECIMAL(16, 4), xlu_price DECIMAL(16, 4),
            xlre_price DECIMAL(16, 4),
            account_equity DECIMAL(16, 4), account_cash DECIMAL(16, 4),
            account_buying_power DECIMAL(16, 4), account_portfolio_value DECIMAL(16, 4),
            account_margin_used DECIMAL(16, 4),
            position_qty_before DECIMAL(16, 8), position_value_before DECIMAL(16, 4),
            position_avg_entry DECIMAL(16, 4), position_unrealized_pl DECIMAL(16, 4),
            total_positions_count INTEGER, total_positions_value DECIMAL(16, 4),
            price_vs_50ma_percent DECIMAL(8, 4), price_vs_200ma_percent DECIMAL(8, 4),
            price_vs_52w_high_percent DECIMAL(8, 4), price_vs_52w_low_percent DECIMAL(8, 4),
            rsi_14 DECIMAL(8, 4),
            data_source VARCHAR(50) DEFAULT 'yfinance',
            fetch_latency_ms INTEGER, errors TEXT
        )""",
        "CREATE INDEX IF NOT EXISTS idx_trade_context_trade_id ON trade_market_context(trade_id);",
        "CREATE INDEX IF NOT EXISTS idx_trade_context_user_id ON trade_market_context(user_id);",

        # Migration 005: Strategy Learning System
        # Trade Strategy Parameters - captures strategy settings for each trade
        """CREATE TABLE IF NOT EXISTS trade_strategy_params (
            id SERIAL PRIMARY KEY,
            trade_id INTEGER UNIQUE REFERENCES bot_trades(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            strategy_type VARCHAR(50),
            strategy_name VARCHAR(100),
            strategy_version VARCHAR(20),
            entry_indicator VARCHAR(50),
            entry_condition VARCHAR(100),
            entry_threshold DECIMAL(10,4),
            entry_value_at_signal DECIMAL(10,4),
            ma_fast_period INTEGER,
            ma_fast_type VARCHAR(10),
            ma_slow_period INTEGER,
            ma_slow_type VARCHAR(10),
            ma_trend_period INTEGER,
            price_vs_ma_fast DECIMAL(8,4),
            price_vs_ma_slow DECIMAL(8,4),
            rsi_period INTEGER,
            rsi_value_at_entry DECIMAL(5,2),
            rsi_oversold_level INTEGER,
            rsi_overbought_level INTEGER,
            macd_fast_period INTEGER,
            macd_slow_period INTEGER,
            macd_signal_period INTEGER,
            macd_value_at_entry DECIMAL(10,4),
            macd_signal_at_entry DECIMAL(10,4),
            macd_histogram_at_entry DECIMAL(10,4),
            bb_period INTEGER,
            bb_std_dev DECIMAL(3,1),
            bb_position VARCHAR(20),
            atr_period INTEGER,
            atr_value_at_entry DECIMAL(10,4),
            atr_multiplier_stop DECIMAL(3,1),
            atr_multiplier_target DECIMAL(3,1),
            volume_ma_period INTEGER,
            volume_ratio_at_entry DECIMAL(5,2),
            volume_condition VARCHAR(50),
            stop_loss_type VARCHAR(20),
            stop_loss_value DECIMAL(8,4),
            take_profit_type VARCHAR(20),
            take_profit_value DECIMAL(8,4),
            risk_reward_ratio DECIMAL(4,2),
            position_size_method VARCHAR(20),
            trade_session VARCHAR(20),
            day_of_week INTEGER,
            hour_of_day INTEGER,
            minutes_since_open INTEGER,
            trend_short VARCHAR(10),
            trend_medium VARCHAR(10),
            trend_long VARCHAR(10),
            custom_params JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",

        # Trade Outcomes - tracks P&L and results for each trade
        """CREATE TABLE IF NOT EXISTS trade_outcomes (
            id SERIAL PRIMARY KEY,
            trade_id INTEGER UNIQUE REFERENCES bot_trades(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            position_type VARCHAR(10),
            entry_price DECIMAL(16,4) NOT NULL,
            entry_time TIMESTAMP NOT NULL,
            entry_order_id VARCHAR(100),
            exit_price DECIMAL(16,4),
            exit_time TIMESTAMP,
            exit_order_id VARCHAR(100),
            exit_reason VARCHAR(50),
            quantity DECIMAL(16,8),
            entry_value DECIMAL(16,2),
            exit_value DECIMAL(16,2),
            pnl_dollars DECIMAL(12,2),
            pnl_percent DECIMAL(8,4),
            pnl_r_multiple DECIMAL(6,2),
            commission_paid DECIMAL(8,2),
            slippage_dollars DECIMAL(8,2),
            slippage_percent DECIMAL(6,4),
            hold_duration_seconds INTEGER,
            hold_duration_minutes INTEGER,
            hold_duration_hours DECIMAL(8,2),
            bars_held INTEGER,
            max_favorable_excursion DECIMAL(8,4),
            max_adverse_excursion DECIMAL(8,4),
            is_winner BOOLEAN,
            is_breakeven BOOLEAN DEFAULT FALSE,
            status VARCHAR(20) DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",

        # Strategy Performance Summary - aggregated stats
        """CREATE TABLE IF NOT EXISTS strategy_performance_summary (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            strategy_type VARCHAR(50),
            symbol VARCHAR(20),
            timeframe VARCHAR(20),
            period_start DATE,
            period_end DATE,
            total_trades INTEGER DEFAULT 0,
            winning_trades INTEGER DEFAULT 0,
            losing_trades INTEGER DEFAULT 0,
            breakeven_trades INTEGER DEFAULT 0,
            win_rate DECIMAL(5,2),
            total_pnl_dollars DECIMAL(14,2) DEFAULT 0,
            total_pnl_percent DECIMAL(10,4) DEFAULT 0,
            avg_win_dollars DECIMAL(12,2),
            avg_loss_dollars DECIMAL(12,2),
            avg_win_percent DECIMAL(8,4),
            avg_loss_percent DECIMAL(8,4),
            largest_win_dollars DECIMAL(12,2),
            largest_loss_dollars DECIMAL(12,2),
            profit_factor DECIMAL(6,2),
            avg_r_multiple DECIMAL(5,2),
            expectancy DECIMAL(8,4),
            max_drawdown_dollars DECIMAL(12,2),
            max_drawdown_percent DECIMAL(8,4),
            max_consecutive_wins INTEGER,
            max_consecutive_losses INTEGER,
            avg_hold_duration_minutes INTEGER,
            avg_winner_duration_minutes INTEGER,
            avg_loser_duration_minutes INTEGER,
            avg_mfe_percent DECIMAL(6,4),
            avg_mae_percent DECIMAL(6,4),
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, strategy_type, symbol, timeframe, period_start, period_end)
        )""",

        # AI Strategy Insights - discovered patterns
        """CREATE TABLE IF NOT EXISTS ai_strategy_insights (
            id SERIAL PRIMARY KEY,
            insight_type VARCHAR(50),
            confidence_score DECIMAL(5,2),
            sample_size INTEGER,
            symbol VARCHAR(20),
            timeframe VARCHAR(20),
            strategy_type VARCHAR(50),
            title VARCHAR(200),
            description TEXT,
            conditions JSONB,
            observed_win_rate DECIMAL(5,2),
            observed_avg_return DECIMAL(8,4),
            observed_trades INTEGER,
            recommendation TEXT,
            recommended_params JSONB,
            is_active BOOLEAN DEFAULT TRUE,
            validated_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",

        # Indexes for strategy learning tables
        "CREATE INDEX IF NOT EXISTS idx_strategy_params_trade ON trade_strategy_params(trade_id);",
        "CREATE INDEX IF NOT EXISTS idx_strategy_params_user ON trade_strategy_params(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_strategy_params_type ON trade_strategy_params(strategy_type);",
        "CREATE INDEX IF NOT EXISTS idx_strategy_params_indicator ON trade_strategy_params(entry_indicator);",
        "CREATE INDEX IF NOT EXISTS idx_outcomes_trade ON trade_outcomes(trade_id);",
        "CREATE INDEX IF NOT EXISTS idx_outcomes_user ON trade_outcomes(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_outcomes_winner ON trade_outcomes(is_winner);",
        "CREATE INDEX IF NOT EXISTS idx_outcomes_status ON trade_outcomes(status);",
        "CREATE INDEX IF NOT EXISTS idx_outcomes_exit_reason ON trade_outcomes(exit_reason);",
        "CREATE INDEX IF NOT EXISTS idx_perf_summary_user ON strategy_performance_summary(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_perf_summary_strategy ON strategy_performance_summary(strategy_type);",
        "CREATE INDEX IF NOT EXISTS idx_insights_type ON ai_strategy_insights(insight_type);",
        "CREATE INDEX IF NOT EXISTS idx_insights_active ON ai_strategy_insights(is_active);",
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
