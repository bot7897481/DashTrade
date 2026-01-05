"""
Script to update pending CLOSE orders that may have filled
This can be run manually or as a background job
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot_engine import TradingEngine
from bot_database import BotTradesDB, get_db_connection
from psycopg2.extras import RealDictCursor

def update_pending_close_orders(user_id: int = None, hours_back: int = 24):
    """
    Check and update pending CLOSE orders that may have filled
    
    Args:
        user_id: Specific user ID (None = all users)
        hours_back: How many hours back to check
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Find pending CLOSE orders from last N hours
                cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
                
                query = """
                    SELECT id, user_id, order_id, symbol, action, status, created_at
                    FROM bot_trades
                    WHERE action = 'CLOSE'
                    AND status IN ('SUBMITTED', 'PENDING', 'ACCEPTED', 'PENDING_NEW', 'PARTIALLY_FILLED')
                    AND order_id IS NOT NULL
                    AND created_at >= %s
                """
                params = [cutoff_time]
                
                if user_id:
                    query += " AND user_id = %s"
                    params.append(user_id)
                
                query += " ORDER BY created_at DESC"
                
                cur.execute(query, params)
                pending_orders = cur.fetchall()
                
                print(f"Found {len(pending_orders)} pending CLOSE orders to check")
                
                updated_count = 0
                error_count = 0
                
                # Group by user_id to reuse TradingEngine instances
                users_processed = {}
                
                for order in pending_orders:
                    trade_id = order['id']
                    order_user_id = order['user_id']
                    order_id = order['order_id']
                    symbol = order['symbol']
                    
                    try:
                        # Get or create TradingEngine for this user
                        if order_user_id not in users_processed:
                            engine = TradingEngine(order_user_id)
                            users_processed[order_user_id] = engine
                        else:
                            engine = users_processed[order_user_id]
                        
                        # Check order status from Alpaca
                        alpaca_order = engine.api.get_order_by_id(order_id)
                        
                        if alpaca_order.status == 'filled':
                            # Order filled! Update the trade record
                            filled_qty = float(alpaca_order.filled_qty)
                            filled_price = float(alpaca_order.filled_avg_price)
                            
                            # Get original trade details to calculate P&L
                            cur.execute("""
                                SELECT trade_details::text, action
                                FROM bot_trades
                                WHERE id = %s
                            """, (trade_id,))
                            trade_data = cur.fetchone()
                            
                            import json
                            trade_details = {}
                            if trade_data and trade_data['trade_details']:
                                if isinstance(trade_data['trade_details'], str):
                                    trade_details = json.loads(trade_data['trade_details'])
                                else:
                                    trade_details = trade_data['trade_details']
                            
                            # Try multiple ways to get entry price
                            position_entry_price = None
                            if trade_details:
                                position_entry_price = (
                                    trade_details.get('position_entry_price') or 
                                    trade_details.get('entry_price') or
                                    trade_details.get('position_qty_before')  # Fallback
                                )
                            
                            # If still no entry price, try to get from position before close
                            if not position_entry_price:
                                # Get position_before to determine if LONG or SHORT
                                position_before = trade_details.get('position_before', 'LONG')
                                # We can't calculate P&L without entry price, but we can still update the order
                                print(f"⚠️  No entry price found for trade {trade_id}, P&L will be NULL")
                            
                            # Calculate P&L if we have entry price
                            realized_pnl = None
                            if position_entry_price:
                                # For CLOSE, we need to know if it was LONG or SHORT
                                # Check position_before from trade_details
                                position_before = trade_details.get('position_before', 'LONG')
                                if position_before == 'LONG':
                                    realized_pnl = (filled_price - position_entry_price) * filled_qty
                                elif position_before == 'SHORT':
                                    realized_pnl = (position_entry_price - filled_price) * filled_qty
                            
                            # Update trade status
                            execution_details = {
                                'alpaca_order_status': 'filled',
                                'position_after': 'FLAT',
                                'realized_pnl': realized_pnl,
                                'entry_price': position_entry_price
                            }
                            
                            BotTradesDB.update_trade_status(
                                trade_id, 
                                'FILLED', 
                                filled_qty, 
                                filled_price,
                                execution_details=execution_details
                            )
                            
                            print(f"✅ Updated trade {trade_id}: FILLED - {filled_qty} @ ${filled_price:.2f} | P&L: ${realized_pnl:.2f}" if realized_pnl else f"✅ Updated trade {trade_id}: FILLED - {filled_qty} @ ${filled_price:.2f}")
                            updated_count += 1
                            
                        elif alpaca_order.status in ['partially_filled', 'pending_new', 'accepted', 'pending_replace']:
                            # Still pending, update status
                            BotTradesDB.update_trade_status(
                                trade_id,
                                alpaca_order.status.upper(),
                                execution_details={'alpaca_order_status': str(alpaca_order.status)}
                            )
                            print(f"⏳ Trade {trade_id}: Still {alpaca_order.status}")
                            
                        else:
                            # Failed or rejected
                            BotTradesDB.update_trade_status(
                                trade_id,
                                alpaca_order.status.upper(),
                                execution_details={'alpaca_order_status': str(alpaca_order.status)}
                            )
                            print(f"❌ Trade {trade_id}: {alpaca_order.status}")
                            
                    except Exception as e:
                        print(f"❌ Error checking order {order_id} (trade {trade_id}): {e}")
                        error_count += 1
                        continue
                
                print(f"\n✅ Summary: {updated_count} updated, {error_count} errors")
                return updated_count
                
    except Exception as e:
        print(f"❌ Error updating pending orders: {e}")
        return 0

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Update pending CLOSE orders')
    parser.add_argument('--user-id', type=int, help='Specific user ID (optional)')
    parser.add_argument('--hours', type=int, default=24, help='Hours back to check (default: 24)')
    
    args = parser.parse_args()
    
    update_pending_close_orders(user_id=args.user_id, hours_back=args.hours)

