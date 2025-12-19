
import os
import sys
import time
import logging
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot_database import BotConfigDB, BotAPIKeysDB
from bot_engine import TradingEngine
from technical_analyzer import TechnicalAnalyzer
from alpha_vantage_data import fetch_alpha_vantage_data
from yahoo_finance_data import fetch_yahoo_data

# Alpaca Data Imports
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from datetime import datetime, timedelta

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BotRunner")

# Mapping from UI timeframe to Yahoo/provider interval
TIMEFRAME_MAPPING = {
    "5 Min": "5m",
    "15 Min": "15m",
    "30 Min": "30m",
    "45 Min": "45m",
    "1 Hour": "1h",
    "4 Hour": "1h", # Yahoo might not support 4h directly in some contexts, but 1h is safe
    "1 Day": "1d"
}

def get_interval(timeframe):
    return TIMEFRAME_MAPPING.get(timeframe, "15m")

def get_alpaca_timeframe(timeframe_str):
    """Convert UI timeframe to Alpaca TimeFrame object"""
    mapping = {
        "5 Min": TimeFrame(5, TimeFrameUnit.Minute),
        "15 Min": TimeFrame(15, TimeFrameUnit.Minute),
        "30 Min": TimeFrame(30, TimeFrameUnit.Minute),
        "45 Min": TimeFrame(45, TimeFrameUnit.Minute),
        "1 Hour": TimeFrame(1, TimeFrameUnit.Hour),
        "4 Hour": TimeFrame(4, TimeFrameUnit.Hour),
        "1 Day": TimeFrame(1, TimeFrameUnit.Day)
    }
    return mapping.get(timeframe_str, TimeFrame(1, TimeFrameUnit.Minute))

def fetch_alpaca_data(symbol, timeframe_str, user_id):
    """Fetch recent data using Alpaca Historical Data API"""
    try:
        keys = BotAPIKeysDB.get_api_keys(user_id)
        if not keys:
            return None, "No Alpaca keys found"
            
        client = StockHistoricalDataClient(keys['api_key'], keys['secret_key'])
        
        # Calculate start time (5 days ago)
        start_time = datetime.now() - timedelta(days=5)
        
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=get_alpaca_timeframe(timeframe_str),
            start=start_time
        )
        
        bars = client.get_stock_bars(request_params)
        df = bars.df
        
        if df is None or df.empty:
            return None, "No data returned from Alpaca"
            
        # Reset index if multi-index (Alpaca returns [symbol, timestamp])
        if isinstance(df.index, pd.MultiIndex):
            df = df.xs(symbol, level=0)
            
        # Ensure column names are lowercase to match DashTrade expectations
        df.columns = [col.lower() for col in df.columns]
        
        return df, None
    except Exception as e:
        return None, str(e)

def run_bot_cycle():
    """Single cycle of checking internal bots and executing trades"""
    logger.info("Checking all active internal bots...")
    
    try:
        active_bots = BotConfigDB.get_all_active_internal_bots()
        logger.info(f"Found {len(active_bots)} active internal bots.")
        
        for bot in active_bots:
            try:
                process_bot(bot)
            except Exception as e:
                logger.error(f"Error processing bot {bot['id']} ({bot['symbol']}): {e}")
                
    except Exception as e:
        logger.error(f"Error fetching active bots: {e}")

def process_bot(bot):
    """Analyze and execute for a single bot"""
    symbol = bot['symbol']
    timeframe = bot['timeframe']
    strategy = bot['strategy_type']
    user_id = bot['user_id']
    
    logger.info(f"Analyzing {symbol} ({timeframe}) for User {user_id} using {strategy} (Source: {bot['signal_source']})")
    
    # 1. Fetch data based on source
    source = bot.get('signal_source', 'webhook').lower()
    
    if 'alpaca' in source:
        df, error = fetch_alpaca_data(symbol, timeframe, user_id)
    else:
        # Default to Yahoo for 'internal (yahoo)' or standard 'internal'
        interval = get_interval(timeframe)
        df, error = fetch_yahoo_data(symbol, period='5d', interval=interval)
    
    if error or df is None or len(df) < 20:
        logger.warning(f"Insufficient data for {symbol} ({timeframe}): {error}")
        return

    # 2. Analyze
    analyzer = TechnicalAnalyzer(df)
    
    if strategy == "NovAlgo Fast Signals [Custom]":
        analyzer.add_novalgo_fast_signals()
    elif strategy == "none":
        logger.warning(f"⚠️ Bot {symbol} ({timeframe}) has strategy 'none'. Falling back to standard QQE, but this may not be what's intended.")
        analyzer.calculate_qqe()
    else:
        # Default analysis (QQE)
        analyzer.calculate_qqe()
    
    latest = analyzer.df.iloc[-1]
    prev = analyzer.df.iloc[-2]
    
    # 3. Check for signals
    action = None
    if latest.get('qqe_long') and not prev.get('qqe_long'):
        action = 'BUY'
    elif latest.get('qqe_short') and not prev.get('qqe_short'):
        action = 'SELL'
        
    if action:
        logger.info(f"🎯 SIGNAL DETECTED: {action} {symbol} ({timeframe})")
        
        # 4. Execute
        try:
            engine = TradingEngine(user_id)
            result = engine.execute_trade(bot, action)
            logger.info(f"Execution result for {symbol}: {result}")
        except Exception as e:
            logger.error(f"Failed to execute trade for {symbol}: {e}")
    else:
        logger.info(f"No new signal for {symbol}.")

def main():
    logger.info("=" * 60)
    logger.info("🚀 DashTrade Internal Bot Runner Starting")
    logger.info("=" * 60)
    
    while True:
        try:
            run_bot_cycle()
        except KeyboardInterrupt:
            logger.info("Bot runner stopped by user.")
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            
        # Wait for 1 minute before next cycle
        time.sleep(60)

if __name__ == "__main__":
    main()
