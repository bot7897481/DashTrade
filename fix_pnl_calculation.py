"""
Fix P&L calculation for CLOSE orders
Uses FIFO method to properly match BUY orders with CLOSE orders
"""
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot_database import BotTradesDB, get_db_connection
from psycopg2.extras import RealDictCursor

def calculate_fifo_pnl(buy_orders: List[Dict], close_order: Dict) -> float:
    """
    Calculate P&L using FIFO (First In First Out) method
    
    Args:
        buy_orders: List of BUY orders sorted by time (oldest first)
        close_order: CLOSE order with filled_qty and filled_avg_price
    
    Returns:
        Total realized P&L
    """
    if not buy_orders or not close_order:
        return 0.0
    
    close_qty = float(close_order.get('filled_qty', 0))
    close_price = float(close_order.get('filled_avg_price', 0))
    
    if close_qty == 0 or close_price == 0:
        return 0.0
    
    total_pnl = 0.0
    remaining_close_qty = close_qty
    
    # Process buys in FIFO order (oldest first)
    for buy in buy_orders:
        if remaining_close_qty <= 0:
            break
        
        buy_qty = float(buy.get('filled_qty', buy.get('quantity', 0)))
        buy_price = float(buy.get('filled_avg_price', buy.get('price', 0)))
        
        if buy_qty == 0 or buy_price == 0:
            continue
        
        # Match quantity
        matched_qty = min(remaining_close_qty, buy_qty)
        
        # Calculate P&L for this match
        trade_pnl = (close_price - buy_price) * matched_qty
        total_pnl += trade_pnl
        
        remaining_close_qty -= matched_qty
    
    return total_pnl

def recalculate_close_order_pnl(trade_id: int) -> Optional[float]:
    """
    Recalculate P&L for a CLOSE order using FIFO method
    
    Args:
        trade_id: Trade ID of the CLOSE order
    
    Returns:
        Calculated P&L or None if error
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get the CLOSE order
                cur.execute("""
                    SELECT id, user_id, bot_config_id, symbol, timeframe,
                           filled_qty, filled_avg_price, created_at, action
                    FROM bot_trades
                    WHERE id = %s
                """, (trade_id,))
                close_order = cur.fetchone()
                
                if not close_order or close_order['action'] != 'CLOSE':
                    print(f"❌ Trade {trade_id} is not a CLOSE order")
                    return None
                
                if not close_order['filled_qty'] or not close_order['filled_avg_price']:
                    print(f"❌ Trade {trade_id} doesn't have filled_qty or filled_avg_price")
                    return None
                
                user_id = close_order['user_id']
                symbol = close_order['symbol']
                close_time = close_order['created_at']
                
                # Get all BUY orders for this symbol before the close
                cur.execute("""
                    SELECT id, filled_qty, filled_avg_price, created_at, action
                    FROM bot_trades
                    WHERE user_id = %s
                    AND symbol = %s
                    AND action = 'BUY'
                    AND status = 'FILLED'
                    AND filled_qty IS NOT NULL
                    AND filled_avg_price IS NOT NULL
                    AND created_at < %s
                    ORDER BY created_at ASC
                """, (user_id, symbol, close_time))
                buy_orders = cur.fetchall()
                
                if not buy_orders:
                    print(f"⚠️  No BUY orders found for {symbol} before close")
                    return None
                
                # Calculate FIFO P&L
                fifo_pnl = calculate_fifo_pnl(buy_orders, close_order)
                
                # Also get Alpaca's avg_entry_price for comparison
                # (We'll use this to verify our calculation)
                print(f"\n📊 P&L Calculation for Trade {trade_id}:")
                print(f"   Symbol: {symbol}")
                print(f"   Close Qty: {close_order['filled_qty']}")
                print(f"   Close Price: ${close_order['filled_avg_price']:.2f}")
                print(f"\n   BUY Orders (FIFO):")
                
                total_buy_qty = 0
                weighted_avg_entry = 0
                
                for buy in buy_orders:
                    buy_qty = float(buy['filled_qty'])
                    buy_price = float(buy['filled_avg_price'])
                    total_buy_qty += buy_qty
                    weighted_avg_entry += buy_price * buy_qty
                    print(f"     - {buy_qty} @ ${buy_price:.2f} (Total: ${buy_qty * buy_price:.2f})")
                
                if total_buy_qty > 0:
                    weighted_avg_entry = weighted_avg_entry / total_buy_qty
                    print(f"\n   Weighted Avg Entry: ${weighted_avg_entry:.2f}")
                    
                    # Calculate using average method (what Alpaca uses)
                    avg_method_pnl = (close_order['filled_avg_price'] - weighted_avg_entry) * close_order['filled_qty']
                    print(f"   Average Method P&L: ${avg_method_pnl:.2f}")
                
                print(f"   FIFO Method P&L: ${fifo_pnl:.2f}")
                
                # Update the trade with FIFO P&L
                cur.execute("""
                    UPDATE bot_trades
                    SET realized_pnl = %s
                    WHERE id = %s
                """, (fifo_pnl, trade_id))
                conn.commit()
                
                print(f"\n✅ Updated trade {trade_id} with P&L: ${fifo_pnl:.2f}")
                return fifo_pnl
                
    except Exception as e:
        print(f"❌ Error recalculating P&L: {e}")
        import traceback
        traceback.print_exc()
        return None

def fix_all_close_orders_pnl(user_id: int = None, days_back: int = 30):
    """
    Fix P&L for all CLOSE orders using FIFO method
    
    Args:
        user_id: Specific user ID (None = all users)
        days_back: How many days back to check
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cutoff_time = datetime.utcnow() - timedelta(days=days_back)
                
                query = """
                    SELECT id FROM bot_trades
                    WHERE action = 'CLOSE'
                    AND status = 'FILLED'
                    AND filled_qty IS NOT NULL
                    AND filled_avg_price IS NOT NULL
                    AND created_at >= %s
                """
                params = [cutoff_time]
                
                if user_id:
                    query += " AND user_id = %s"
                    params.append(user_id)
                
                cur.execute(query, params)
                close_orders = cur.fetchall()
                
                print(f"Found {len(close_orders)} CLOSE orders to recalculate")
                
                fixed_count = 0
                for order in close_orders:
                    pnl = recalculate_close_order_pnl(order['id'])
                    if pnl is not None:
                        fixed_count += 1
                
                print(f"\n✅ Fixed P&L for {fixed_count} orders")
                return fixed_count
                
    except Exception as e:
        print(f"❌ Error fixing P&L: {e}")
        return 0

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix P&L calculation for CLOSE orders')
    parser.add_argument('--trade-id', type=int, help='Specific trade ID to fix')
    parser.add_argument('--user-id', type=int, help='User ID (optional)')
    parser.add_argument('--days', type=int, default=30, help='Days back to check (default: 30)')
    
    args = parser.parse_args()
    
    if args.trade_id:
        recalculate_close_order_pnl(args.trade_id)
    else:
        fix_all_close_orders_pnl(user_id=args.user_id, days_back=args.days)

