#!/usr/bin/env python3
"""
Count trades by action type (BUY, SELL, CLOSE) in the system
Uses the database method to get statistics
"""
from bot_database import BotTradesDB
import os

def count_trades_by_action(user_id: int = None):
    """Count all trades grouped by action type"""
    try:
        # Use the database method
        stats = BotTradesDB.get_trade_statistics(user_id=user_id)
        
        print("=" * 80)
        if user_id:
            print(f"TRADE STATISTICS FOR USER {user_id}")
        else:
            print("TRADE STATISTICS (ALL USERS)")
        print("=" * 80)
        print()
        
        if not stats.get('by_action'):
            print("No trades found in the system.")
            return
        
        total_all = stats['total_trades']
        total_filled = 0
        total_submitted = 0
        total_failed = 0
        grand_total_notional = 0
        grand_total_pnl = 0
        
        for action, data in sorted(stats['by_action'].items()):
            count = data['count']
            filled = data['filled']
            submitted = data['submitted']
            failed = data['failed']
            notional = data['total_notional']
            pnl = data['total_pnl']
            
            total_filled += filled
            total_submitted += submitted
            total_failed += failed
            grand_total_notional += notional
            grand_total_pnl += pnl
            
            print(f"Action: {action}")
            print(f"  Total Orders:     {count}")
            print(f"    - FILLED:       {filled}")
            print(f"    - SUBMITTED:    {submitted}")
            print(f"    - FAILED:       {failed}")
            print(f"  Total Notional:   ${notional:,.2f}")
            if action == 'CLOSE' or action == 'SELL':
                print(f"  Total P&L:        ${pnl:,.2f}")
            print()
        
        print("-" * 80)
        print("TOTALS (All Actions Combined)")
        print("-" * 80)
        print(f"Total Orders:       {total_all}")
        print(f"  - FILLED:         {total_filled}")
        print(f"  - SUBMITTED:      {total_submitted}")
        print(f"  - FAILED:         {total_failed}")
        print(f"Total Notional:     ${grand_total_notional:,.2f}")
        print(f"Total Realized P&L: ${grand_total_pnl:,.2f}")
        print()
        print("=" * 80)
        
        # Summary
        buy_count = stats['by_action'].get('BUY', {}).get('count', 0)
        sell_count = stats['by_action'].get('SELL', {}).get('count', 0)
        close_count = stats['by_action'].get('CLOSE', {}).get('count', 0)
        
        print()
        print("QUICK SUMMARY:")
        print(f"  BUY orders:   {buy_count}")
        print(f"  SELL orders:  {sell_count}")
        print(f"  CLOSE orders: {close_count}")
        print(f"  Total:        {total_all}")
        print()
        
    except Exception as e:
        print(f"Error counting trades: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("Note: Make sure DATABASE_URL is set in your environment")
        print("      Or the database is accessible from Railway")

if __name__ == "__main__":
    import sys
    # Check if user_id is provided as argument
    user_id = None
    if len(sys.argv) > 1:
        try:
            user_id = int(sys.argv[1])
        except ValueError:
            print(f"Invalid user_id: {sys.argv[1]}")
            sys.exit(1)
    
    count_trades_by_action(user_id=user_id)

