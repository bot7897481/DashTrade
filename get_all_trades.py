#!/usr/bin/env python3
"""
Get all trades from the database with purchase and sell prices
"""
import os
from database import get_db_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime
from collections import defaultdict

# Ensure we're using Railway database
if not os.getenv('DATABASE_URL'):
    print("ERROR: DATABASE_URL not set!")
    print("Please set it first:")
    print("export DATABASE_URL='your-railway-postgres-url'")
    exit(1)

def get_all_trades():
    """Get all trades and match BUY/SELL pairs"""

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get all filled trades
            cur.execute('''
                SELECT
                    id,
                    user_id,
                    symbol,
                    action,
                    notional,
                    filled_qty,
                    filled_avg_price,
                    status,
                    created_at,
                    filled_at,
                    order_id
                FROM bot_trades
                WHERE status = 'FILLED'
                ORDER BY symbol, filled_at
            ''')

            trades = cur.fetchall()

            if not trades:
                print('❌ No trades found in database')
                return

            print(f'\n✅ Found {len(trades)} total trades\n')
            print('='*120)
            print(f'{"DATE":<20} {"SYMBOL":<10} {"ACTION":<6} {"QUANTITY":>12} {"PRICE":>12} {"VALUE":>15} {"ORDER ID":<30}')
            print('='*120)

            # Group trades by symbol for P&L calculation
            trades_by_symbol = defaultdict(list)

            for t in trades:
                action = t['action']
                symbol = t['symbol']
                qty = float(t['filled_qty'] or 0)
                price = float(t['filled_avg_price'] or 0)
                notional = float(t['notional'] or 0)
                status = t['status']
                date = t['filled_at'] or t['created_at']
                order_id = t['order_id'] or 'N/A'

                # Store trade for P&L calculation
                trades_by_symbol[symbol].append({
                    'date': date,
                    'action': action,
                    'qty': qty,
                    'price': price,
                    'notional': notional,
                    'order_id': order_id
                })

                # Print trade
                date_str = date.strftime('%Y-%m-%d %H:%M:%S') if isinstance(date, datetime) else str(date)
                print(f'{date_str:<20} {symbol:<10} {action:<6} {qty:>12.4f} ${price:>11.2f} ${notional:>14.2f} {order_id[:28]:<30}')

            print('='*120)

            # Calculate P&L for each symbol
            print('\n\n' + '='*120)
            print('PROFIT & LOSS SUMMARY BY SYMBOL')
            print('='*120)
            print(f'{"SYMBOL":<10} {"BUY QTY":>12} {"AVG BUY":>12} {"SELL QTY":>12} {"AVG SELL":>12} {"P&L":>15} {"P&L %":>10}')
            print('='*120)

            total_pnl = 0

            for symbol, symbol_trades in sorted(trades_by_symbol.items()):
                buy_qty = 0
                buy_value = 0
                sell_qty = 0
                sell_value = 0

                for trade in symbol_trades:
                    if trade['action'] in ['BUY', 'LONG']:
                        buy_qty += trade['qty']
                        buy_value += trade['notional']
                    elif trade['action'] in ['SELL', 'SHORT', 'CLOSE']:
                        sell_qty += trade['qty']
                        sell_value += trade['notional']

                avg_buy = buy_value / buy_qty if buy_qty > 0 else 0
                avg_sell = sell_value / sell_qty if sell_qty > 0 else 0

                # Calculate P&L (assuming we sold what we bought)
                matched_qty = min(buy_qty, sell_qty)
                pnl = (avg_sell - avg_buy) * matched_qty if matched_qty > 0 else 0
                pnl_pct = (pnl / buy_value * 100) if buy_value > 0 else 0

                total_pnl += pnl

                pnl_str = f'${pnl:,.2f}'
                pnl_pct_str = f'{pnl_pct:+.2f}%'

                print(f'{symbol:<10} {buy_qty:>12.4f} ${avg_buy:>11.2f} {sell_qty:>12.4f} ${avg_sell:>11.2f} {pnl_str:>15} {pnl_pct_str:>10}')

            print('='*120)
            print(f'{"TOTAL P&L:":<70} ${total_pnl:>15,.2f}')
            print('='*120)

            # Show individual trade pairs
            print('\n\n' + '='*120)
            print('MATCHED BUY/SELL PAIRS')
            print('='*120)

            for symbol, symbol_trades in sorted(trades_by_symbol.items()):
                buys = [t for t in symbol_trades if t['action'] in ['BUY', 'LONG']]
                sells = [t for t in symbol_trades if t['action'] in ['SELL', 'SHORT', 'CLOSE']]

                if buys and sells:
                    print(f'\n{symbol}:')
                    for i, (buy, sell) in enumerate(zip(buys, sells), 1):
                        pnl = (sell['price'] - buy['price']) * min(buy['qty'], sell['qty'])
                        pnl_pct = ((sell['price'] - buy['price']) / buy['price'] * 100) if buy['price'] > 0 else 0

                        buy_date = buy['date'].strftime('%Y-%m-%d %H:%M') if isinstance(buy['date'], datetime) else str(buy['date'])
                        sell_date = sell['date'].strftime('%Y-%m-%d %H:%M') if isinstance(sell['date'], datetime) else str(sell['date'])

                        print(f'  #{i}:')
                        print(f'    BUY:  {buy_date} | {buy["qty"]:.4f} @ ${buy["price"]:.2f} = ${buy["notional"]:.2f}')
                        print(f'    SELL: {sell_date} | {sell["qty"]:.4f} @ ${sell["price"]:.2f} = ${sell["notional"]:.2f}')
                        print(f'    P&L: ${pnl:,.2f} ({pnl_pct:+.2f}%)')

if __name__ == "__main__":
    try:
        get_all_trades()
    except Exception as e:
        print(f'\n❌ Error: {e}')
        import traceback
        traceback.print_exc()
