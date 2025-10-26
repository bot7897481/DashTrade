"""
NovAlgo - Enhanced Stock Trading Signal Dashboard with Portfolio Tracking
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

from technical_analyzer import TechnicalAnalyzer
from database import WatchlistDB, AlertsDB, PreferencesDB

# Page configuration
st.set_page_config(
    page_title="NovAlgo Trading Signals",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (same as before)
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .bullish {
        color: #00c853;
        font-weight: bold;
    }
    .bearish {
        color: #ff1744;
        font-weight: bold;
    }
    .watchlist-item {
        padding: 0.5rem;
        margin: 0.25rem 0;
        background-color: #f8f9fa;
        border-radius: 0.25rem;
        cursor: pointer;
    }
    .watchlist-item:hover {
        background-color: #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions (reusing from original app.py)
@st.cache_data(ttl=300)
def fetch_stock_data(symbol: str, period: str, interval: str):
    """Fetch stock data from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            return None, f"No data found for {symbol}"
        
        df.columns = [col.lower() for col in df.columns]
        df = df[['open', 'high', 'low', 'close', 'volume']]
        
        return df, None
    except Exception as e:
        return None, str(e)

def get_stock_info(symbol: str):
    """Get stock name and info"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info.get('longName', symbol)
    except:
        return symbol

# Main App
def main():
    # Header
    st.markdown('<h1 class="main-header">📈 NovAlgo Trading Signals</h1>', unsafe_allow_html=True)
    st.markdown("### Comprehensive Stock Technical Analysis Dashboard with Portfolio Tracking")
    st.markdown("---")
    
    # Load preferences
    prefs = PreferencesDB.get_all_preferences()
    
    # Sidebar
    with st.sidebar:
        st.title("📈 NovAlgo")
        st.markdown("---")
        
        # Mode selection
        mode = st.radio("Mode", ["Single Stock Analysis", "Portfolio Dashboard"], index=0)
        
        st.markdown("---")
        
        if mode == "Single Stock Analysis":
            st.title("⚙️ Analysis Settings")
            
            # Stock symbol input
            symbol = st.text_input("Stock Symbol", value="AAPL").upper()
            
            # Timeframe selection
            st.subheader("📅 Timeframe")
            period = st.selectbox("Period", 
                                 ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"],
                                 index=5)
            interval = st.selectbox("Interval",
                                   ["1m", "5m", "15m", "30m", "1h", "1d", "1wk"],
                                   index=5)
            
            # Technical settings
            st.subheader("🔧 Technical Settings")
            
            with st.expander("QQE Parameters"):
                rsi_period = st.slider("RSI Period", 5, 20, 8)
                rsi_smoothing = st.slider("RSI Smoothing", 2, 10, 3)
                qqe_factor = st.slider("QQE Factor", 2.0, 5.0, 3.2, 0.1)
            
            with st.expander("Risk Management"):
                account_balance = st.number_input("Account Balance ($)", 
                                                value=float(prefs.get('account_balance', 10000)), 
                                                step=1000.0)
            
            # Fetch button
            fetch_button = st.button("🔄 Fetch & Analyze", type="primary", use_container_width=True)
            
            # Add to watchlist button
            if st.button("➕ Add to Watchlist", use_container_width=True):
                stock_name = get_stock_info(symbol)
                if WatchlistDB.add_stock(symbol, stock_name):
                    st.success(f"Added {symbol} to watchlist!")
                    st.rerun()
                else:
                    st.info(f"{symbol} already in watchlist")
        
        else:  # Portfolio Dashboard
            st.title("💼 Portfolio Settings")
            
            # Refresh interval
            refresh_interval = st.selectbox("Auto-refresh", 
                                          ["Off", "1 min", "5 min", "15 min"],
                                          index=0)
            
            # Analysis depth
            quick_mode = st.checkbox("Quick Mode (faster, less detailed)", value=True)
            
            st.markdown("---")
        
        # Watchlist Management
        st.subheader("📋 Watchlist")
        watchlist = WatchlistDB.get_all_stocks()
        
        if watchlist:
            st.write(f"**{len(watchlist)} stocks**")
            
            for stock in watchlist:
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button(f"📊 {stock['symbol']}", key=f"view_{stock['symbol']}", use_container_width=True):
                        st.session_state['symbol'] = stock['symbol']
                        st.session_state['switch_to_analysis'] = True
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_{stock['symbol']}"):
                        WatchlistDB.remove_stock(stock['symbol'])
                        st.rerun()
        else:
            st.info("No stocks in watchlist")
        
        st.markdown("---")
        st.markdown("### 📊 Coverage")
        st.success("✅ Portfolio Tracking")
        st.success("✅ Real-time Monitoring")
        st.success("✅ Technical Analysis")
        st.success("✅ Risk Management")
    
    # Handle mode switch from watchlist
    if st.session_state.get('switch_to_analysis'):
        mode = "Single Stock Analysis"
        symbol = st.session_state.get('symbol', 'AAPL')
        fetch_button = True
        st.session_state['switch_to_analysis'] = False
    
    # Main content
    if mode == "Single Stock Analysis":
        # Run single stock analysis (same as original app)
        if fetch_button or 'analysis_results' in st.session_state:
            if fetch_button:
                with st.spinner(f"Fetching data for {symbol}..."):
                    df, error = fetch_stock_data(symbol, period, interval)
                    
                    if error:
                        st.error(f"❌ Error fetching data: {error}")
                        return
                    
                    if df is None or len(df) < 50:
                        st.error("❌ Insufficient data for analysis. Try a different period.")
                        return
                    
                    # Run technical analysis
                    with st.spinner("Running comprehensive technical analysis..."):
                        analyzer = TechnicalAnalyzer(df)
                        
                        analyzer.calculate_emas()
                        analyzer.calculate_ma_cloud()
                        analyzer.calculate_qqe(rsi_period=rsi_period, 
                                             smoothing=rsi_smoothing,
                                             qqe_factor=qqe_factor)
                        analyzer.calculate_vwap()
                        analyzer.analyze_all_candlestick_patterns()
                        
                        chart_patterns = analyzer.detect_all_chart_patterns()
                        sr_levels = analyzer.identify_support_resistance()
                        
                        st.session_state.analysis_results = {
                            'symbol': symbol,
                            'df': analyzer.df,
                            'analyzer': analyzer,
                            'patterns': chart_patterns,
                            'support': sr_levels['support'],
                            'resistance': sr_levels['resistance']
                        }
                        
                    st.success(f"✅ Analysis complete for {symbol}!")
            
            # Display results
            results = st.session_state.analysis_results
            df = results['df']
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            price_change = latest['close'] - prev['close']
            price_change_pct = (price_change / prev['close']) * 100
            
            st.subheader(f"📊 {results['symbol']} Overview")
            
            cols = st.columns(5)
            cols[0].metric("Current Price", f"${latest['close']:.2f}", 
                          f"{price_change:+.2f} ({price_change_pct:+.2f}%)")
            cols[1].metric("Volume", f"{latest['volume']:,.0f}")
            
            trend = latest.get('ma_cloud_trend', 'unknown')
            if trend == 'bullish':
                cols[2].metric("Trend", "BULLISH 📈", delta="Up", delta_color="normal")
            elif trend == 'bearish':
                cols[2].metric("Trend", "BEARISH 📉", delta="Down", delta_color="inverse")
            else:
                cols[2].metric("Trend", "UNKNOWN", delta="Neutral", delta_color="off")
            
            # Quick signals summary
            bullish_signals = 0
            bearish_signals = 0
            
            if latest.get('qqe_long', False):
                bullish_signals += 1
            if latest.get('qqe_short', False):
                bearish_signals += 1
            
            cols[3].metric("Bullish Signals", bullish_signals)
            cols[4].metric("Bearish Signals", bearish_signals)
            
            # Show key signal
            if latest.get('qqe_long', False):
                st.success("🟢 **QQE LONG SIGNAL** - Momentum turning bullish")
            elif latest.get('qqe_short', False):
                st.error("🔴 **QQE SHORT SIGNAL** - Momentum turning bearish")
        
        else:
            st.info("👈 Enter a stock symbol and click 'Fetch & Analyze' to get started!")
    
    else:  # Portfolio Dashboard
        st.subheader("💼 Portfolio Dashboard")
        
        watchlist = WatchlistDB.get_all_stocks()
        
        if not watchlist:
            st.info("📋 Your watchlist is empty. Add stocks from the sidebar to start monitoring.")
            return
        
        st.write(f"Monitoring **{len(watchlist)} stocks** in your portfolio")
        
        # Fetch data for all stocks
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        portfolio_data = []
        
        for idx, stock in enumerate(watchlist):
            status_text.text(f"Fetching {stock['symbol']}...")
            progress_bar.progress((idx + 1) / len(watchlist))
            
            df, error = fetch_stock_data(stock['symbol'], '1mo', '1d')
            
            if df is not None and len(df) >= 20:
                try:
                    analyzer = TechnicalAnalyzer(df)
                    
                    if not quick_mode:
                        analyzer.calculate_emas()
                        analyzer.calculate_ma_cloud()
                        analyzer.calculate_qqe()
                        analyzer.calculate_vwap()
                        analyzer.analyze_all_candlestick_patterns()
                    else:
                        analyzer.calculate_emas(periods=[20, 50])
                        analyzer.calculate_ma_cloud()
                        analyzer.calculate_qqe()
                    
                    latest = analyzer.df.iloc[-1]
                    prev = analyzer.df.iloc[-2]
                    
                    portfolio_data.append({
                        'Symbol': stock['symbol'],
                        'Name': stock.get('name', stock['symbol']),
                        'Price': latest['close'],
                        'Change %': ((latest['close'] - prev['close']) / prev['close']) * 100,
                        'Volume': latest['volume'],
                        'Trend': latest.get('ma_cloud_trend', 'unknown'),
                        'QQE Long': latest.get('qqe_long', False),
                        'QQE Short': latest.get('qqe_short', False),
                        'EMA20': latest.get('ema_20', 0) if 'ema_20' in latest else 0,
                        'EMA50': latest.get('ema_50', 0) if 'ema_50' in latest else 0,
                    })
                except Exception as e:
                    st.warning(f"Error analyzing {stock['symbol']}: {str(e)}")
        
        progress_bar.empty()
        status_text.empty()
        
        if portfolio_data:
            # Create DataFrame
            portfolio_df = pd.DataFrame(portfolio_data)
            
            # Summary metrics
            st.markdown("### 📊 Portfolio Summary")
            
            sum_cols = st.columns(4)
            
            bullish_count = len(portfolio_df[portfolio_df['Trend'] == 'bullish'])
            bearish_count = len(portfolio_df[portfolio_df['Trend'] == 'bearish'])
            long_signals = portfolio_df['QQE Long'].sum()
            short_signals = portfolio_df['QQE Short'].sum()
            
            sum_cols[0].metric("Bullish Stocks", f"{bullish_count}/{len(portfolio_df)}")
            sum_cols[1].metric("Bearish Stocks", f"{bearish_count}/{len(portfolio_df)}")
            sum_cols[2].metric("Long Signals", long_signals)
            sum_cols[3].metric("Short Signals", short_signals)
            
            # Portfolio table
            st.markdown("### 📋 Stock Overview")
            
            # Format the display
            display_df = portfolio_df.copy()
            display_df['Price'] = display_df['Price'].apply(lambda x: f"${x:.2f}")
            display_df['Change %'] = display_df['Change %'].apply(lambda x: f"{x:+.2f}%")
            display_df['Volume'] = display_df['Volume'].apply(lambda x: f"{x:,.0f}")
            display_df['Trend'] = display_df['Trend'].apply(lambda x: "📈 Bullish" if x == 'bullish' else "📉 Bearish" if x == 'bearish' else "➖ Neutral")
            display_df['Signals'] = display_df.apply(lambda row: 
                "🟢 Long" if row['QQE Long'] else "🔴 Short" if row['QQE Short'] else "⚪ None", axis=1)
            
            # Show table
            st.dataframe(
                display_df[['Symbol', 'Name', 'Price', 'Change %', 'Volume', 'Trend', 'Signals']],
                use_container_width=True,
                hide_index=True
            )
            
            # Action items
            st.markdown("### 🎯 Action Items")
            
            if long_signals > 0:
                st.success(f"**{long_signals} Long Signal(s)**: " + ", ".join(portfolio_df[portfolio_df['QQE Long']]['Symbol'].tolist()))
            
            if short_signals > 0:
                st.error(f"**{short_signals} Short Signal(s)**: " + ", ".join(portfolio_df[portfolio_df['QQE Short']]['Symbol'].tolist()))
            
            if long_signals == 0 and short_signals == 0:
                st.info("No active signals across your portfolio")

if __name__ == "__main__":
    main()
