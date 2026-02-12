#!/usr/bin/env python3
"""
Get ALL trades from Alpaca account (not just bot trades)
This includes manual trades, bot trades, and everything else
"""
import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderSide, QueryOrderStatus
from datetime import datetime, timedelta
from collections import defaultdict

# Get Alpaca credentials
API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
IS_PAPER = os.getenv('ALPACA_MODE', 'paper') == 'paper'

if not API_KEY or not SECRET_KEY:
    print("ERROR: Alpaca credentials not set!")
    print("Please set:")
    print("  export ALPACA_API_KEY='your-api-key'")
    print("  export ALPACA_SECRET_KEY='your-secret-key'")
    exit(1)

def get_all_alpaca_trades():
    """Fetch all filled orders from Alpaca"""

    client = TradingClient(API_KEY, SECRET_KEY, paper=IS_PAPER)

    print(f'\n🔍 Fetching trades from Alpaca {"PAPER" if IS_PAPER else "LIVE"} account...\n')

    # Get all filled orders (last 90 days by default, or specify date range)
    request_params = GetOrdersRequest(
        status=QueryOrderStatus.FILLED,
        limit=500  # Max trades to fetch
    )

    orders = client.get_orders(filter=request_params)

    if not orders:
        print('❌ No filled orders found in Alpaca account')
        return

    print(f'✅ Found {len(orders)} filled orders\n')
    print('='*140)
    print(f'{"DATE":<20} {"SYMBOL":<10} {"SIDE":<6} {"QUANTITY":>12} {"FILLED PRICE":>14} {"VALUE":>16} {"ORDER ID":<36}')
    print('='*140)

    # Track trades by symbol for P&L
    trades_by_symbol = defaultdict(list)

    for order in sorted(orders, key=lambda x: x.filled_at or x.created_at):
        symbol = order.symbol
        side = order.side.value  # buy or sell
        qty = float(order.filled_qty) if order.filled_qty else 0
        filled_price = float(order.filled_avg_price) if order.filled_avg_price else 0
        value = qty * filled_price
        filled_at = order.filled_at or order.created_at
        order_id = order.id

        # Store for P&L calculation
        trades_by_symbol[symbol].append({
            'date': filled_at,
            'side': side,
            'qty': qty,
            'price': filled_price,
            'value': value,
            'order_id': order_id
        })

        # Format and print
        date_str = filled_at.strftime('%Y-%m-%d %H:%M:%S') if filled_at else 'N/A'
        side_display = side.upper()

        print(f'{date_str:<20} {symbol:<10} {side_display:<6} {qty:>12.4f} ${filled_price:>13.2f} ${value:>15.2f} {str(order_id):<36}')

    print('='*140)

    # Calculate P&L by symbol
    print('\n\n' + '='*120)
    print('PROFIT & LOSS SUMMARY BY SYMBOL')
    print('='*120)
    print(f'{"SYMBOL":<10} {"BUY QTY":>12} {"AVG BUY":>12} {"SELL QTY":>12} {"AVG SELL":>12} {"P&L":>16} {"P&L %":>10}')
    print('='*120)

    total_pnl = 0
    total_invested = 0

    for symbol in sorted(trades_by_symbol.keys()):
        symbol_trades = trades_by_symbol[symbol]

        buy_qty = 0
        buy_value = 0
        sell_qty = 0
        sell_value = 0

        for trade in symbol_trades:
            if trade['side'] == 'buy':
                buy_qty += trade['qty']
                buy_value += trade['value']
            elif trade['side'] == 'sell':
                sell_qty += trade['qty']
                sell_value += trade['value']

        avg_buy = buy_value / buy_qty if buy_qty > 0 else 0
        avg_sell = sell_value / sell_qty if sell_qty > 0 else 0

        # Calculate P&L for matched quantity
        matched_qty = min(buy_qty, sell_qty)
        pnl = (avg_sell - avg_buy) * matched_qty if matched_qty > 0 else 0
        pnl_pct = (pnl / buy_value * 100) if buy_value > 0 else 0

        total_pnl += pnl
        total_invested += buy_value

        # Format output
        pnl_str = f'${pnl:,.2f}'
        pnl_pct_str = f'{pnl_pct:+.2f}%'

        print(f'{symbol:<10} {buy_qty:>12.4f} ${avg_buy:>11.2f} {sell_qty:>12.4f} ${avg_sell:>11.2f} {pnl_str:>16} {pnl_pct_str:>10}')

    print('='*120)

    total_roi = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    print(f'{"TOTAL INVESTED:":<70} ${total_invested:>16,.2f}')
    print(f'{"TOTAL P&L:":<70} ${total_pnl:>16,.2f}')
    print(f'{"TOTAL ROI:":<70} {total_roi:>15.2f}%')
    print('='*120)

    # Show matched pairs
    print('\n\n' + '='*120)
    print('MATCHED BUY/SELL PAIRS (Round Trips)')
    print('='*120)

    for symbol in sorted(trades_by_symbol.keys()):
        symbol_trades = trades_by_symbol[symbol]
        buys = [t for t in symbol_trades if t['side'] == 'buy']
        sells = [t for t in symbol_trades if t['side'] == 'sell']

        if buys and sells:
            print(f'\n📊 {symbol}:')

            for i, (buy, sell) in enumerate(zip(buys, sells), 1):
                matched_qty = min(buy['qty'], sell['qty'])
                pnl = (sell['price'] - buy['price']) * matched_qty
                pnl_pct = ((sell['price'] - buy['price']) / buy['price'] * 100) if buy['price'] > 0 else 0

                buy_date = buy['date'].strftime('%Y-%m-%d %H:%M')
                sell_date = sell['date'].strftime('%Y-%m-%d %H:%M')

                pnl_emoji = '🟢' if pnl >= 0 else '🔴'

                print(f'  Trade #{i}: {pnl_emoji}')
                print(f'    🟦 BUY:  {buy_date} | {buy["qty"]:.4f} shares @ ${buy["price"]:.2f} = ${buy["value"]:.2f}')
                print(f'    🟥 SELL: {sell_date} | {sell["qty"]:.4f} shares @ ${sell["price"]:.2f} = ${sell["value"]:.2f}')
                print(f'    💰 P&L: ${pnl:,.2f} ({pnl_pct:+.2f}%)')

                # Calculate holding time
                holding_time = sell['date'] - buy['date']
                hours = holding_time.total_seconds() / 3600
                if hours < 24:
                    print(f'    ⏱️  Holding time: {hours:.1f} hours')
                else:
                    days = hours / 24
                    print(f'    ⏱️  Holding time: {days:.1f} days')

    print('\n' + '='*120)

    # Account summary
    print('\n📈 ACCOUNT SUMMARY:')
    account = client.get_account()
    print(f'  Portfolio Value: ${float(account.portfolio_value):,.2f}')
    print(f'  Buying Power: ${float(account.buying_power):,.2f}')
    print(f'  Cash: ${float(account.cash):,.2f}')
    print(f'  Equity: ${float(account.equity):,.2f}')

if __name__ == "__main__":
    try:
        get_all_alpaca_trades()
    except Exception as e:
        print(f'\n❌ Error: {e}')
        import traceback
        traceback.print_exc()
