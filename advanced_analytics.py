#!/usr/bin/env python3
"""
Advanced Trading Analytics Dashboard
Comprehensive trading statistics, risk metrics, and performance analysis
"""

import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta
import pytz
from collections import defaultdict

# ============================================================================
# CONFIGURATION
# ============================================================================

ALPACA_API_KEY = "PKL3QOG3TPAQ7NUYB86D"
ALPACA_SECRET_KEY = "zZxfTNPa7gBmU0RvSY0akIZujQWPXAeYhPD0O8Cz"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

PST = pytz.timezone('America/Los_Angeles')

# ============================================================================
# CONNECT TO ALPACA
# ============================================================================

api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL, api_version='v2')

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_currency(value):
    """Format number as currency"""
    return f"${value:,.2f}"

def format_percent(value):
    """Format number as percentage"""
    return f"{value:.2f}%"

def get_color_indicator(value):
    """Return color indicator based on positive/negative"""
    if value > 0:
        return "🟢"
    elif value < 0:
        return "🔴"
    else:
        return "⚪"

# ============================================================================
# MAIN ANALYTICS
# ============================================================================

print("\n" + "=" * 80)
print("🤖 NOVALGO TRADING BOT - ADVANCED ANALYTICS DASHBOARD")
print("=" * 80)
print()

# ============================================================================
# 1. ACCOUNT OVERVIEW
# ============================================================================

account = api.get_account()
total_equity = float(account.equity)
total_cash = float(account.cash)
buying_power = float(account.buying_power)
portfolio_value = float(account.portfolio_value)
last_equity = float(account.last_equity)
day_pnl = total_equity - last_equity
day_pnl_percent = (day_pnl / last_equity * 100) if last_equity > 0 else 0

print("📊 ACCOUNT OVERVIEW")
print("─" * 80)
print(f"Total Equity:          {format_currency(total_equity)}")
print(f"Cash Available:        {format_currency(total_cash)}")
print(f"Buying Power:          {format_currency(buying_power)}")
print(f"Portfolio Value:       {format_currency(portfolio_value)}")
print(f"Today's P&L:           {get_color_indicator(day_pnl)} {format_currency(day_pnl)} ({format_percent(day_pnl_percent)})")
print()

# ============================================================================
# 2. CURRENT POSITIONS ANALYSIS
# ============================================================================

positions = api.list_positions()

if len(positions) > 0:
    print("📈 CURRENT POSITIONS ANALYSIS")
    print("─" * 80)
    
    # Position metrics
    total_unrealized_pnl = 0
    total_market_value = 0
    long_positions = []
    short_positions = []
    position_details = []
    
    for pos in positions:
        qty = float(pos.qty)
        market_value = float(pos.market_value)
        unrealized_pl = float(pos.unrealized_pl)
        unrealized_plpc = float(pos.unrealized_plpc) * 100
        
        total_unrealized_pnl += unrealized_pl
        total_market_value += abs(market_value)
        
        pos_data = {
            'symbol': pos.symbol,
            'qty': abs(qty),
            'side': 'LONG' if qty > 0 else 'SHORT',
            'market_value': abs(market_value),
            'unrealized_pl': unrealized_pl,
            'unrealized_plpc': unrealized_plpc,
            'entry_price': float(pos.avg_entry_price),
            'current_price': float(pos.current_price)
        }
        
        position_details.append(pos_data)
        
        if qty > 0:
            long_positions.append(pos_data)
        else:
            short_positions.append(pos_data)
    
    # Overall position metrics
    print(f"Total Positions:       {len(positions)}")
    print(f"Long Positions:        {len(long_positions)}")
    print(f"Short Positions:       {len(short_positions)}")
    print(f"Total Unrealized P&L:  {get_color_indicator(total_unrealized_pnl)} {format_currency(total_unrealized_pnl)}")
    print(f"Total Market Value:    {format_currency(total_market_value)}")
    if total_market_value > 0:
        print(f"Portfolio Return:      {format_percent(total_unrealized_pnl/total_market_value*100)}")
    
    # Win/Loss ratio
    winning_positions = [p for p in position_details if p['unrealized_pl'] > 0]
    losing_positions = [p for p in position_details if p['unrealized_pl'] < 0]
    win_rate = len(winning_positions) / len(positions) * 100 if len(positions) > 0 else 0
    
    print(f"Winning Positions:     {len(winning_positions)} 🟢")
    print(f"Losing Positions:      {len(losing_positions)} 🔴")
    print(f"Position Win Rate:     {format_percent(win_rate)}")
    print()
    
    # Top performers
    sorted_positions = sorted(position_details, key=lambda x: x['unrealized_pl'], reverse=True)
    
    print("🏆 TOP 3 PERFORMERS:")
    for i, pos in enumerate(sorted_positions[:3], 1):
        print(f"   {i}. {pos['symbol']:6} {get_color_indicator(pos['unrealized_pl'])} {format_currency(pos['unrealized_pl'])} ({format_percent(pos['unrealized_plpc'])})")
    print()
    
    print("📉 BOTTOM 3 PERFORMERS:")
    for i, pos in enumerate(sorted_positions[-3:][::-1], 1):
        print(f"   {i}. {pos['symbol']:6} {get_color_indicator(pos['unrealized_pl'])} {format_currency(pos['unrealized_pl'])} ({format_percent(pos['unrealized_plpc'])})")
    print()
    
    # Concentration analysis
    print("📊 POSITION CONCENTRATION:")
    for pos in sorted(position_details, key=lambda x: x['market_value'], reverse=True)[:5]:
        concentration = (pos['market_value'] / total_market_value * 100)
        print(f"   {pos['symbol']:6} {format_currency(pos['market_value'])} ({format_percent(concentration)})")
    print()

else:
    print("❌ No open positions")
    print()

# ============================================================================
# 3. TRADING HISTORY ANALYSIS (Last 30 Days)
# ============================================================================

print("📜 TRADING HISTORY (Last 30 Days)")
print("─" * 80)

end_date = datetime.now()
start_date = end_date - timedelta(days=30)

try:
    activities = api.get_activities(
        activity_types='FILL',
        date=start_date.strftime('%Y-%m-%d')
    )
    
    if activities:
        # Analyze fills
        total_fills = len(activities)
        buy_fills = [a for a in activities if a.side == 'buy']
        sell_fills = [a for a in activities if a.side == 'sell']
        
        print(f"Total Trades Executed: {total_fills}")
        print(f"Buy Orders:            {len(buy_fills)}")
        print(f"Sell Orders:           {len(sell_fills)}")
        print()
        
        # Calculate realized P&L (matched buys and sells)
        trades_by_symbol = defaultdict(lambda: {'buys': [], 'sells': []})
        
        for activity in activities:
            symbol = activity.symbol
            side = activity.side
            qty = float(activity.qty)
            price = float(activity.price)
            time = activity.transaction_time
            
            if side == 'buy':
                trades_by_symbol[symbol]['buys'].append({'qty': qty, 'price': price, 'time': time})
            elif side == 'sell':
                trades_by_symbol[symbol]['sells'].append({'qty': qty, 'price': price, 'time': time})
        
        # Calculate realized P&L
        realized_pnl_by_symbol = {}
        total_realized_pnl = 0
        total_trades = 0
        winning_trades = 0
        losing_trades = 0
        
        for symbol, trades in trades_by_symbol.items():
            buys = sorted(trades['buys'], key=lambda x: x['time'])
            sells = sorted(trades['sells'], key=lambda x: x['time'])
            
            buy_queue = list(buys)
            symbol_pnl = 0
            
            for sell in sells:
                sell_qty = sell['qty']
                sell_price = sell['price']
                
                while sell_qty > 0 and buy_queue:
                    buy = buy_queue[0]
                    buy_qty = buy['qty']
                    buy_price = buy['price']
                    
                    matched_qty = min(sell_qty, buy_qty)
                    trade_pnl = (sell_price - buy_price) * matched_qty
                    
                    symbol_pnl += trade_pnl
                    total_realized_pnl += trade_pnl
                    total_trades += 1
                    
                    if trade_pnl > 0:
                        winning_trades += 1
                    elif trade_pnl < 0:
                        losing_trades += 1
                    
                    sell_qty -= matched_qty
                    buy['qty'] -= matched_qty
                    
                    if buy['qty'] == 0:
                        buy_queue.pop(0)
            
            if symbol_pnl != 0:
                realized_pnl_by_symbol[symbol] = symbol_pnl
        
        print(f"Realized P&L (Closed): {get_color_indicator(total_realized_pnl)} {format_currency(total_realized_pnl)}")
        if total_trades > 0:
            print(f"Average P&L per Trade: {format_currency(total_realized_pnl / total_trades)}")
            print(f"Winning Trades:        {winning_trades} ({format_percent(winning_trades/total_trades*100)})")
            print(f"Losing Trades:         {losing_trades} ({format_percent(losing_trades/total_trades*100)})")
        print()
        
        # Top realized P&L by symbol
        if realized_pnl_by_symbol:
            print("💰 REALIZED P&L BY SYMBOL:")
            sorted_realized = sorted(realized_pnl_by_symbol.items(), key=lambda x: x[1], reverse=True)
            for symbol, pnl in sorted_realized[:5]:
                print(f"   {symbol:6} {get_color_indicator(pnl)} {format_currency(pnl)}")
            print()
        
        # Most traded symbols
        symbol_counts = defaultdict(int)
        for activity in activities:
            symbol_counts[activity.symbol] += 1
        
        print("🔥 MOST TRADED SYMBOLS:")
        sorted_symbols = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)
        for symbol, count in sorted_symbols[:5]:
            print(f"   {symbol:6} {count} trades")
        print()
        
        # Recent trades
        print("🕐 RECENT TRADES (Last 5):")
        for activity in activities[:5]:
            time_pst = activity.transaction_time.astimezone(PST)
            print(f"   {time_pst.strftime('%m/%d %I:%M%p')} - {activity.side.upper():4} {activity.qty:6} {activity.symbol:6} @ ${float(activity.price):.2f}")
        print()
        
    else:
        print("No trades executed in the last 30 days")
        print()
        
except Exception as e:
    print(f"Error fetching trading history: {e}")
    print()

# ============================================================================
# 4. RISK METRICS
# ============================================================================

print("⚠️ RISK METRICS")
print("─" * 80)

# Portfolio exposure
long_exposure = sum([abs(float(p.market_value)) for p in positions if float(p.qty) > 0])
short_exposure = sum([abs(float(p.market_value)) for p in positions if float(p.qty) < 0])
gross_exposure = long_exposure + short_exposure
net_exposure = long_exposure - short_exposure

print(f"Long Exposure:         {format_currency(long_exposure)}")
print(f"Short Exposure:        {format_currency(short_exposure)}")
print(f"Gross Exposure:        {format_currency(gross_exposure)}")
print(f"Net Exposure:          {format_currency(net_exposure)}")

if total_equity > 0:
    leverage = gross_exposure / total_equity
    print(f"Leverage:              {leverage:.2f}x")
    print(f"Exposure vs Equity:    {format_percent(gross_exposure/total_equity*100)}")

# Largest position risk
if positions:
    largest_position = max(positions, key=lambda p: abs(float(p.market_value)))
    largest_value = abs(float(largest_position.market_value))
    largest_percent = (largest_value / total_equity * 100) if total_equity > 0 else 0
    print(f"Largest Position:      {largest_position.symbol} - {format_currency(largest_value)} ({format_percent(largest_percent)})")
    
    # Total at-risk capital
    at_risk = sum([abs(float(p.unrealized_pl)) for p in positions if float(p.unrealized_pl) < 0])
    print(f"Capital at Risk:       {format_currency(at_risk)}")

print()

# ============================================================================
# 5. PERFORMANCE METRICS
# ============================================================================

print("🎯 PERFORMANCE METRICS")
print("─" * 80)

# Total P&L (realized + unrealized)
total_pnl = total_realized_pnl + total_unrealized_pnl if 'total_realized_pnl' in locals() else total_unrealized_pnl
print(f"Total P&L:             {get_color_indicator(total_pnl)} {format_currency(total_pnl)}")
print(f"  Realized:            {format_currency(total_realized_pnl if 'total_realized_pnl' in locals() else 0)}")
print(f"  Unrealized:          {format_currency(total_unrealized_pnl)}")

# Return on equity
if total_equity > 0:
    roe = (total_pnl / total_equity * 100)
    print(f"Return on Equity:      {format_percent(roe)}")

# Average holding time (if data available)
if 'activities' in locals() and activities:
    holding_times = []
    for symbol, trades in trades_by_symbol.items():
        if trades['buys'] and trades['sells']:
            for sell in trades['sells']:
                for buy in trades['buys']:
                    if buy['time'] < sell['time']:
                        hold_time = (sell['time'] - buy['time']).total_seconds() / 3600
                        holding_times.append(hold_time)
                        break
    
    if holding_times:
        avg_hold_time = sum(holding_times) / len(holding_times)
        print(f"Avg Holding Time:      {avg_hold_time:.1f} hours")

print()

# ============================================================================
# 6. TRADING RECOMMENDATIONS
# ============================================================================

print("💡 TRADING INSIGHTS")
print("─" * 80)

# Check for concentration risk
if positions:
    max_concentration = max([abs(float(p.market_value)) / total_market_value * 100 for p in positions]) if total_market_value > 0 else 0
    if max_concentration > 20:
        print(f"⚠️  High concentration: Largest position is {format_percent(max_concentration)} of portfolio")
    else:
        print(f"✅ Good diversification: Largest position is {format_percent(max_concentration)} of portfolio")

# Check leverage
if 'leverage' in locals():
    if leverage > 2:
        print(f"⚠️  High leverage: {leverage:.2f}x - Consider reducing exposure")
    elif leverage > 1.5:
        print(f"⚠️  Moderate leverage: {leverage:.2f}x - Monitor carefully")
    else:
        print(f"✅ Conservative leverage: {leverage:.2f}x")

# Check win rate
if 'win_rate' in locals():
    if win_rate >= 60:
        print(f"✅ Strong win rate: {format_percent(win_rate)}")
    elif win_rate >= 50:
        print(f"✅ Healthy win rate: {format_percent(win_rate)}")
    else:
        print(f"⚠️  Low win rate: {format_percent(win_rate)} - Review strategy")

# Check for stuck positions
if positions:
    stuck_positions = [p for p in position_details if abs(p['unrealized_plpc']) < 1]
    if len(stuck_positions) > len(positions) * 0.3:
        print(f"⚠️  {len(stuck_positions)} positions are flat (±1%) - Consider closing")

# Cash utilization
cash_utilization = ((total_equity - total_cash) / total_equity * 100) if total_equity > 0 else 0
if cash_utilization < 50:
    print(f"💰 Low cash utilization: {format_percent(cash_utilization)} - Room to add positions")
elif cash_utilization > 90:
    print(f"⚠️  High cash utilization: {format_percent(cash_utilization)} - Limited buying power")
else:
    print(f"✅ Good cash utilization: {format_percent(cash_utilization)}")

print()

# ============================================================================
# 7. TIMESTAMP
# ============================================================================

current_time = datetime.now(PST)
print("─" * 80)
print(f"⏰ Analysis Time: {current_time.strftime('%Y-%m-%d %I:%M:%S %p PST')}")
print("=" * 80)
print()
