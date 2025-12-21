"""
Long-Only Backtest Analysis for AAPL
$100,000 starting capital, 30-minute timeframe, 6 months
Strategy: BUY on QQE Long, SELL on QQE Short (no actual shorting)
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from technical_analyzer import TechnicalAnalyzer
from backtester import Backtester

# Configuration
SYMBOL = "AAPL"
START_CAPITAL = 100000.0
POSITION_SIZE_PCT = 100.0  # Use 100% of available capital (fully invested when long)
INTERVAL = "30m"
PERIOD = "60d"  # Yahoo Finance limits: 60 days max for 30m interval

# Risk management
USE_STOP_LOSS = True
STOP_LOSS_PCT = 2.0  # 2% stop loss
USE_TAKE_PROFIT = False
TAKE_PROFIT_PCT = 5.0

print("=" * 80)
print(f"LONG-ONLY BACKTEST: {SYMBOL}")
print(f"Starting Capital: ${START_CAPITAL:,.2f}")
print(f"Interval: {INTERVAL}")
print(f"Period: 60 days (Yahoo Finance limit for 30m data)")
print(f"Strategy:BUY on Long signal, SELL on Short signal (no shorting)")
print(f"Position Size: 100% of capital (fully invested)")
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
print(f"   QQE Long signals (BUY): {long_signals}")
print(f"   QQE Short signals (SELL): {short_signals}")
print(f"   Total signals: {long_signals + short_signals}")

# Manual long-only backtest
print("\n🚀 Running LONG-ONLY backtest...")

capital = START_CAPITAL
position = None  # Track current long position
trades = []
equity_curve = []

for idx, row in analyzer.df.iterrows():
    date = idx
    close = row['close']
    low = row['low']
    high = row['high']
    
    # Check for stop loss if we have a position
    if position is not None and USE_STOP_LOSS:
        if low <= position['stop_loss']:
            # Stop loss hit
            exit_price = position['stop_loss']
            shares = position['shares']
            capital += shares * exit_price
            
            pnl = (exit_price - position['entry_price']) * shares
            pnl_pct = ((exit_price - position['entry_price']) / position['entry_price']) * 100
            
            trades.append({
                'entry_date': position['entry_date'],
                'entry_price': position['entry_price'],
                'exit_date': date,
                'exit_price': exit_price,
                'shares': shares,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'exit_reason': 'stop_loss'
            })
            
            position = None
    
    # Check for long signal (BUY)
    if row.get('qqe_long', False) and position is None:
        # Buy signal - enter long position
        shares = int(capital / close)
        if shares > 0:
            cost = shares * close
            capital -= cost
            
            position = {
                'entry_date': date,
                'entry_price': close,
                'shares': shares,
                'stop_loss': close * (1 - STOP_LOSS_PCT / 100)
            }
    
    # Check for short signal (SELL position, don't short)
    elif row.get('qqe_short', False) and position is not None:
        # Sell signal - exit long position
        shares = position['shares']
        exit_price = close
        capital += shares * exit_price
        
        pnl = (exit_price - position['entry_price']) * shares
        pnl_pct = ((exit_price - position['entry_price']) / position['entry_price']) * 100
        
        trades.append({
            'entry_date': position['entry_date'],
            'entry_price': position['entry_price'],
            'exit_date': date,
            'exit_price': exit_price,
            'shares': shares,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'exit_reason': 'qqe_short_signal'
        })
        
        position = None
    
    # Calculate current equity
    current_equity = capital
    if position is not None:
        current_equity += position['shares'] * close
    equity_curve.append(current_equity)

# Close any open position at the end
if position is not None:
    last_price = analyzer.df.iloc[-1]['close']
    shares = position['shares']
    capital += shares * last_price
    
    pnl = (last_price - position['entry_price']) * shares
    pnl_pct = ((last_price - position['entry_price']) / position['entry_price']) * 100
    
    trades.append({
        'entry_date': position['entry_date'],
        'entry_price': position['entry_price'],
        'exit_date': analyzer.df.index[-1],
        'exit_price': last_price,
        'shares': shares,
        'pnl': pnl,
        'pnl_pct': pnl_pct,
        'exit_reason': 'end_of_period'
    })

final_capital = capital
total_pnl = final_capital - START_CAPITAL
total_return = (total_pnl / START_CAPITAL) * 100

# Calculate statistics
winning_trades = [t for t in trades if t['pnl'] > 0]
losing_trades = [t for t in trades if t['pnl'] <= 0]
win_rate = (len(winning_trades) / len(trades) * 100) if trades else 0
avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0

# Calculate max drawdown
equity_series = pd.Series(equity_curve, index=analyzer.df.index)
running_max = equity_series.expanding().max()
drawdown = (equity_series - running_max) / running_max * 100
max_dd = drawdown.min()

print("\n" + "=" * 80)
print("LONG-ONLY BACKTEST RESULTS")
print("=" * 80)

# Performance Overview
print("\n📈 PERFORMANCE OVERVIEW:")
print(f"   Initial Capital:  ${START_CAPITAL:,.2f}")
print(f"   Final Capital:    ${final_capital:,.2f}")
print(f"   Total P&L:        ${total_pnl:+,.2f}")
print(f"   Total Return:     {total_return:+.2f}%")

# Trade Statistics
print(f"\n📊 TRADE STATISTICS:")
print(f"   Total Trades:     {len(trades)}")
print(f"   Winning Trades:   {len(winning_trades)}")
print(f"   Losing Trades:    {len(losing_trades)}")
print(f"   Win Rate:         {win_rate:.1f}%")

# P&L Analysis
print(f"\n💰 P&L ANALYSIS:")
print(f"   Average Win:      ${avg_win:,.2f}")
print(f"   Average Loss:     ${avg_loss:,.2f}")
if avg_loss != 0:
    profit_factor = abs(sum(t['pnl'] for t in winning_trades) / sum(t['pnl'] for t in losing_trades))
    print(f"   Profit Factor:    {profit_factor:.2f}")
print(f"   Total P&L:        ${total_pnl:,.2f}")

# Risk Metrics
print(f"\n⚠️  RISK METRICS:")
print(f"   Max Drawdown:     {max_dd:.2f}%")

# Detailed Trade Log
print(f"\n📝 DETAILED TRADE LOG (All trades):")
print("-" * 80)

for trade in trades:
    pnl = trade['pnl']
    pnl_pct = trade['pnl_pct']
    pnl_symbol = "✅" if pnl > 0 else "❌"
    
    print(f"{pnl_symbol} LONG  | "
          f"Entry: {trade['entry_date'].strftime('%Y-%m-%d %H:%M')} @ ${trade['entry_price']:.2f} | "
          f"Exit: {trade['exit_date'].strftime('%Y-%m-%d %H:%M')} @ ${trade['exit_price']:.2f} | "
          f"P&L: ${pnl:+,.2f} ({pnl_pct:+.2f}%) | "
          f"{trade['exit_reason']}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if total_return > 0:
    print(f"✅ PROFITABLE: Strategy returned ${total_pnl:+,.2f} ({total_return:+.2f}%)")
else:
    print(f"❌ LOSS: Strategy lost ${total_pnl:+,.2f} ({total_return:+.2f}%)")

print(f"\nOver {(df.index[-1] - df.index[0]).days} days of trading,")
print(f"with {len(trades)} total trades,")
print(f"the LONG-ONLY QQE strategy {'MADE' if total_return > 0 else 'LOST'} ${abs(total_pnl):,.2f}.")

# Comparison to Buy & Hold
buy_hold_return = ((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]) * 100
buy_hold_pnl = START_CAPITAL * (buy_hold_return / 100)

print(f"\n📊 COMPARISON TO BUY & HOLD:")
print(f"   Buy & Hold Return: {buy_hold_return:+.2f}%")
print(f"   Buy & Hold P&L:    ${buy_hold_pnl:+,.2f}")
print(f"   Strategy vs B&H:   {total_return - buy_hold_return:+.2f}% {'(BETTER)' if total_return > buy_hold_return else '(WORSE)'}")

print("\n" + "=" * 80)
