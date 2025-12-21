"""
HOOD Backtest Analysis (Jan 1, 2025 - Dec 10, 2025)
$100,000 starting capital, 1-hour timeframe
Strategy: Long-Only (Buy on Long Signal, Sell on Short Signal)
"""
import yfinance as yf
import pandas as pd
from datetime import datetime
from technical_analyzer import TechnicalAnalyzer
from backtester import Backtester

# Configuration
SYMBOL = "HOOD"
START_CAPITAL = 100000.0
POSITION_SIZE_PCT = 100.0  # Fully invested
INTERVAL = "1h"  # 1h required for >60 days of data on Yahoo
START_DATE = "2025-01-01"
END_DATE = "2025-12-10"

# Risk management
USE_STOP_LOSS = True
STOP_LOSS_PCT = 2.0
USE_TAKE_PROFIT = False
TAKE_PROFIT_PCT = 5.0
STRATEGY_MODE = 'long_only'  # Buy on Long, Sell on Short

print("=" * 80)
print(f"BACKTEST: {SYMBOL}")
print(f"Period: {START_DATE} to {END_DATE}")
print(f"Interval: {INTERVAL}")
print(f"Capital: ${START_CAPITAL:,.2f}")
print(f"Strategy: {STRATEGY_MODE} (Buy on Long, Sell on Short)")
print("=" * 80)

# Fetch data
print(f"\n📊 Fetching {SYMBOL} data...")
ticker = yf.Ticker(SYMBOL)
df = ticker.history(start=START_DATE, end=END_DATE, interval=INTERVAL)

if df.empty:
    print("❌ Error: No data retrieved")
    exit(1)

# Convert column names to lowercase
df.columns = [col.lower() for col in df.columns]

print(f"✅ Data fetched: {len(df)} bars")
print(f"   Date range: {df.index[0]} to {df.index[-1]}")

# Calculate technical indicators
print("\n🔧 Calculating technical indicators...")
analyzer = TechnicalAnalyzer(df)
analyzer.calculate_emas()
analyzer.calculate_ma_cloud()
analyzer.calculate_qqe()

# Run backtest
print("\n🚀 Running backtest...")
backtester = Backtester(
    analyzer.df,
    initial_capital=START_CAPITAL,
    position_size_pct=POSITION_SIZE_PCT,
    strategy_mode=STRATEGY_MODE,
    use_trend_filter=True,  # Using the trend filter we just implemented
    trend_ema_period=200,
    use_stop_loss=USE_STOP_LOSS,
    stop_loss_pct=STOP_LOSS_PCT,
    use_take_profit=USE_TAKE_PROFIT,
    take_profit_pct=TAKE_PROFIT_PCT
)

results = backtester.run_simple_strategy(
    long_signal_col='qqe_long',
    short_signal_col='qqe_short',
    exit_on_opposite=True
)

# Calculate statistics
total_pnl = results.final_capital - results.initial_capital
total_return = (total_pnl / results.initial_capital) * 100

print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)

# Performance
print(f"Final Capital:    ${results.final_capital:,.2f}")
print(f"Total P&L:        ${total_pnl:+,.2f}")
print(f"Total Return:     {total_return:+.2f}%")
print(f"Total Trades:     {results.total_trades()}")
print(f"Win Rate:         {results.win_rate():.1f}%")
print(f"Max Drawdown:     {results.max_drawdown():.2f}%")

# Buy & Hold Comparison
start_price = df.iloc[0]['close']
end_price = df.iloc[-1]['close']
buy_hold_return = ((end_price - start_price) / start_price) * 100
buy_hold_pnl = START_CAPITAL * (buy_hold_return / 100)

print("\n📊 COMPARISON:")
print(f"Strategy Return:   {total_return:+.2f}% (${total_pnl:+,.2f})")
print(f"Buy & Hold Return: {buy_hold_return:+.2f}% (${buy_hold_pnl:+,.2f})")

print("\n📝 TRADE LOG (Last 5):")
completed_trades = [t for t in results.trades if not t.is_open()]
for t in completed_trades[-5:]:
    print(f"{'✅' if t.pnl() > 0 else '❌'} {t.entry_date} -> {t.exit_date} | P&L: ${t.pnl():,.2f}")
