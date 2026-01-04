#!/usr/bin/env python3
"""
Test script to close BTC/USD position
"""
import os
import sys

# Set DATABASE_URL if not set (for local testing)
if not os.environ.get('DATABASE_URL'):
    print("⚠️  DATABASE_URL not set - will try to connect to Railway")

from bot_database import BotAPIKeysDB, BotConfigDB
from bot_engine import TradingEngine

def test_close_btc():
    """Test closing a Bitcoin position"""
    
    # Get user ID (assume user 1 for testing, adjust if needed)
    user_id = 1
    
    print(f"\n{'='*60}")
    print(f"Testing CLOSE position for BTC/USD (User: {user_id})")
    print(f"{'='*60}\n")
    
    # Check if API keys exist
    keys = BotAPIKeysDB.get_api_keys(user_id)
    if not keys:
        print("❌ No Alpaca API keys found for user. Please configure API keys first.")
        return
    
    print(f"✅ Found API keys for user {user_id} (mode: {keys['mode']})")
    
    # Initialize trading engine
    try:
        engine = TradingEngine(user_id)
        print("✅ Trading engine initialized")
    except Exception as e:
        print(f"❌ Failed to initialize trading engine: {e}")
        return
    
    # Check current position for BTC/USD
    print("\n📊 Checking current BTC/USD position...")
    
    # Try both formats
    for symbol in ['BTC/USD', 'BTCUSD']:
        print(f"\n  Checking {symbol}...")
        position = engine.get_current_position(symbol)
        if position:
            print(f"  Position: {position}")
            if position.get('side') != 'FLAT':
                print(f"\n✅ Found open position: {position['side']} {position.get('qty', 'N/A')} BTC")
                break
    else:
        print("\n⚠️  No open BTC position found")
        return
    
    # Attempt to close the position
    print(f"\n🔴 Attempting to close BTC/USD position...")
    
    result = engine.close_position('BTC/USD')
    
    print(f"\n{'='*60}")
    print(f"Result: {result}")
    print(f"{'='*60}\n")
    
    if result.get('status') == 'success':
        print("✅ Position closed successfully!")
    else:
        print(f"❌ Failed to close position: {result.get('message', 'Unknown error')}")
    
    # Verify position is closed
    print("\n📊 Verifying position is closed...")
    position = engine.get_current_position('BTC/USD')
    if position and position.get('side') == 'FLAT':
        print("✅ Position confirmed FLAT")
    else:
        print(f"⚠️  Position status: {position}")

if __name__ == '__main__':
    test_close_btc()

