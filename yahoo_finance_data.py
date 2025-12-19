
import yfinance as yf
import pandas as pd

def fetch_yahoo_data(symbol: str, period: str, interval: str):
    """Fetch stock data from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            return None, f"No data found for {symbol}"
        
        # Ensure column names are lowercase
        df.columns = [col.lower() for col in df.columns]
        
        # Select required columns if they exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        # Filter columns to only those that exist
        df = df[[col for col in required_cols if col in df.columns]]
        
        return df, None
    except Exception as e:
        return None, str(e)
