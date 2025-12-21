"""
Comprehensive Backtest Analysis for AAPL
$100,000 starting capital, 1-hour timeframe, 6 months
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from technical_analyzer import TechnicalAnalyzer
from backtester import Backtester

# Configuration
SYMBOL = "AAPL"
START_CAPITAL = 100000.0
POSITION_SIZE_PCT = 10.0  # 10% of capital per trade
INTERVAL = "1h"
PERIOD = "6mo"  # Last 6 months

# Risk management
USE_STOP_LOSS = True
STOP_LOSS_PCT = 2.0  # 2% stop loss
USE_TAKE_PROFIT = False
TAKE_PROFIT_PCT = 5.0  # 5% take profit

print("=" * 80)
print(f"BACKTEST ANALYSIS: {SYMBOL}")
print(f"Starting Capital: ${START_CAPITAL:,.2f}")
print(f"Interval: {INTERVAL}")
print(f"Period: {PERIOD} (most recent 6 months)")
print(f"Position Size: {POSITION_SIZE_PCT}% per trade")
print(f"Stop Loss: {STOP_LOSS_PCT}% ({'Enabled' if USE_STOP_LOSS else 'Disabled'})")
print("=" * 80)

# Fetch data
print(f"\n📊 Fetching {SYMBOL} data...")
ticker = yf.Ticker(SYMBOL)
df = ticker.history(period=PERIOD, interval=INTERVAL)

if df.empty:
    print("❌ Error: No data retrieved")
    exit(1)

# Convert column names to lowercase
df.columns = [col.lower() for col in df.columns]

print(f"✅ Data fetched: {len(df)} bars")
print(f"   Date range: {df.index[0]} to {df.index[-1]}")
print(f"   Trading days: {(df.index[-1] - df.index[0]).days} days")

# Calculate technical indicators
print("\n🔧 Calculating technical indicators...")
analyzer = TechnicalAnalyzer(df)
analyzer.calculate_emas()
analyzer.calculate_ma_cloud()
analyzer.calculate_qqe()

print("✅ Indicators calculated")

# Count signals
long_signals = analyzer.df['qqe_long'].sum()
short_signals = analyzer.df['qqe_short'].sum()
print(f"   QQE Long signals: {long_signals}")
print(f"   QQE Short signals: {short_signals}")
print(f"   Total signals: {long_signals + short_signals}")

# Run backtest
print("\n🚀 Running backtest...")
backtester = Backtester(
    analyzer.df,
    initial_capital=START_CAPITAL,
    position_size_pct=POSITION_SIZE_PCT,
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
total_return = ((results.final_capital - results.initial_capital) / results.initial_capital) * 100
total_pnl = results.final_capital - results.initial_capital

print("\n" + "=" * 80)
print("BACKTEST RESULTS")
print("=" * 80)

# Performance Overview
print("\n📈 PERFORMANCE OVERVIEW:")
print(f"   Initial Capital:  ${results.initial_capital:,.2f}")
print(f"   Final Capital:    ${results.final_capital:,.2f}")
print(f"   Total P&L:        ${total_pnl:+,.2f}")
print(f"   Total Return:     {total_return:+.2f}%")

# Trade Statistics
print(f"\n📊 TRADE STATISTICS:")
print(f"   Total Trades:     {results.total_trades()}")
print(f"   Winning Trades:   {results.winning_trades()}")
print(f"   Losing Trades:    {results.losing_trades()}")
print(f"   Win Rate:         {results.win_rate():.1f}%")

# P&L Analysis
print(f"\n💰 P&L ANALYSIS:")
print(f"   Average Win:      ${results.average_win():,.2f}")
print(f"   Average Loss:     ${results.average_loss():,.2f}")
print(f"   Profit Factor:    {results.profit_factor():.2f}")
print(f"   Total P&L:        ${results.total_pnl():,.2f}")

# Risk Metrics
print(f"\n⚠️  RISK METRICS:")
print(f"   Max Drawdown:     {results.max_drawdown():.2f}%")
print(f"   Sharpe Ratio:     {results.sharpe_ratio():.2f}")
print(f"   Avg Trade Duration: {results.average_trade_duration():.1f} hours")

# Detailed Trade Log
print(f"\n📝 DETAILED TRADE LOG (Last 10 trades):")
print("-" * 80)

completed_trades = [t for t in results.trades if not t.is_open()]
for trade in completed_trades[-10:]:
    pnl = trade.pnl()
    pnl_pct = trade.pnl_percent()
    pnl_symbol = "✅" if pnl > 0 else "❌"
    
    print(f"{pnl_symbol} {trade.position_type.upper():5s} | "
          f"Entry: {trade.entry_date.strftime('%Y-%m-%d %H:%M')} @ ${trade.entry_price:.2f} | "
          f"Exit: {trade.exit_date.strftime('%Y-%m-%d %H:%M')} @ ${trade.exit_price:.2f} | "
          f"P&L: ${pnl:+,.2f} ({pnl_pct:+.2f}%) | "
          f"{trade.exit_reason}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if total_return > 0:
    print(f"✅ PROFITABLE: Strategy returned ${total_pnl:+,.2f} ({total_return:+.2f}%)")
else:
    print(f"❌ LOSS: Strategy lost ${total_pnl:+,.2f} ({total_return:+.2f}%)")

print(f"\nOver {(df.index[-1] - df.index[0]).days} days of trading,")
print(f"with {results.total_trades()} total trades,")
print(f"the QQE strategy {'MADE' if total_return > 0 else 'LOST'} ${abs(total_pnl):,.2f}.")

# Comparison to Buy & Hold
buy_hold_return = ((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]) * 100
buy_hold_pnl = START_CAPITAL * (buy_hold_return / 100)

print(f"\n📊 COMPARISON TO BUY & HOLD:")
print(f"   Buy & Hold Return: {buy_hold_return:+.2f}%")
print(f"   Buy & Hold P&L:    ${buy_hold_pnl:+,.2f}")
print(f"   Strategy vs B&H:   {total_return - buy_hold_return:+.2f}% {'(BETTER)' if total_return > buy_hold_return else '(WORSE)'}")

print("\n" + "=" * 80)
