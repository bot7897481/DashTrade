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
from comparison_analyzer import ComparisonAnalyzer
from backtester import Backtester, BacktestResults
from strategy_builder import CustomStrategy, StrategyCondition, StrategyTemplates, StrategyBuilder
from alert_system import AlertMonitor
from alpha_vantage_data import AlphaVantageProvider, fetch_alpha_vantage_data

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
def fetch_stock_data(symbol: str, period: str, interval: str, use_alpha_vantage: bool = False):
    """Fetch stock data from Yahoo Finance or Alpha Vantage"""
    if use_alpha_vantage:
        return fetch_alpha_vantage_data(symbol, interval, period)
    
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
        mode = st.radio("Mode", ["Single Stock Analysis", "Portfolio Dashboard", "Multi-Stock Comparison", "Backtesting", "Strategy Builder", "Alert Manager"], index=0)
        
        st.markdown("---")
        
        if mode == "Single Stock Analysis":
            st.title("⚙️ Analysis Settings")
            
            # Data source selection
            st.subheader("📡 Data Source")
            data_source = st.radio("Select Data Provider", 
                                  ["Yahoo Finance (Free, 15-min delay)", 
                                   "Alpha Vantage (Real-time, API key required)"],
                                  index=0)
            use_alpha_vantage = "Alpha Vantage" in data_source
            
            # Stock symbol input
            symbol = st.text_input("Stock Symbol", value="AAPL").upper()
            
            # Timeframe selection
            st.subheader("📅 Timeframe")
            period = st.selectbox("Period", 
                                 ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"],
                                 index=5)
            interval = st.selectbox("Interval",
                                   ["1m", "5m", "15m", "30m", "45m", "1h", "1d", "1wk"],
                                   index=6)
            
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
        period = '3mo'
        interval = '1d'
        fetch_button = True
        st.session_state['switch_to_analysis'] = False
    
    # Main content
    if mode == "Single Stock Analysis":
        # Run single stock analysis (same as original app)
        if fetch_button or 'analysis_results' in st.session_state:
            if fetch_button:
                with st.spinner(f"Fetching data for {symbol}..."):
                    df, error = fetch_stock_data(symbol, period, interval, use_alpha_vantage)
                    
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
            
            # News Sentiment Analysis (if using Alpha Vantage)
            if use_alpha_vantage:
                st.markdown("---")
                st.subheader("📰 News Sentiment Analysis")
                
                with st.spinner(f"Analyzing news sentiment for {symbol}..."):
                    try:
                        av_provider = AlphaVantageProvider()
                        combined_signal = av_provider.get_combined_signal(symbol)
                        
                        if 'error' not in combined_signal:
                            col1, col2, col3, col4 = st.columns(4)
                            
                            col1.metric("News Signal", combined_signal['news_signal'],
                                       help="Based on recent news sentiment")
                            col2.metric("Combined Signal", combined_signal['combined_signal'],
                                       help="Price + News combined")
                            col3.metric("Confidence", f"{combined_signal['confidence']*100:.0f}%",
                                       help="Signal strength confidence")
                            col4.metric("News Articles", combined_signal['article_count'],
                                       help="Number of articles analyzed")
                            
                            sentiment_score = combined_signal['news_sentiment_score']
                            if sentiment_score > 0.15:
                                st.success(f"📈 **Bullish News Sentiment** ({sentiment_score:.2f}) - Positive media coverage")
                            elif sentiment_score < -0.15:
                                st.error(f"📉 **Bearish News Sentiment** ({sentiment_score:.2f}) - Negative media coverage")
                            else:
                                st.info(f"⚖️ **Neutral News Sentiment** ({sentiment_score:.2f}) - Mixed or neutral coverage")
                            
                            if combined_signal['top_articles']:
                                with st.expander("📄 Top Recent News Articles"):
                                    for article in combined_signal['top_articles']:
                                        sentiment_emoji = "📈" if article['sentiment_score'] > 0.15 else ("📉" if article['sentiment_score'] < -0.15 else "⚖️")
                                        st.markdown(f"**{sentiment_emoji} {article['title']}**")
                                        st.caption(f"Source: {article['source']} | Sentiment: {article['sentiment_label']} ({article['sentiment_score']:.2f}) | Relevance: {article['relevance']:.2f}")
                                        if article.get('url'):
                                            st.markdown(f"[Read article]({article['url']})")
                                        st.markdown("---")
                    except Exception as e:
                        st.warning(f"⚠️ News sentiment analysis unavailable: {str(e)}")
        
        else:
            st.info("👈 Enter a stock symbol and click 'Fetch & Analyze' to get started!")
    
    elif mode == "Portfolio Dashboard":
        st.subheader("💼 Portfolio Dashboard")
        st.info("📡 **Data Source:** Yahoo Finance (15-min delay for free tier) | **Analysis:** Last 5 days, 1-day interval")
        
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
            
            # Alert Monitoring - check database-configured alerts
            st.markdown("### 🔔 Alert Status")
            
            triggered_alerts = []
            
            for stock in watchlist:
                stock_alerts = AlertsDB.get_active_alerts(stock['symbol'])
                
                if stock_alerts:
                    df, error = fetch_stock_data(stock['symbol'], '5d', '1d')
                    
                    if df is not None and len(df) >= 20:
                        try:
                            analyzer = TechnicalAnalyzer(df)
                            analyzer.calculate_emas()
                            analyzer.calculate_ma_cloud()
                            analyzer.calculate_qqe()
                            
                            latest = analyzer.df.iloc[-1]
                            
                            prev = analyzer.df.iloc[-2] if len(analyzer.df) > 1 else latest
                            
                            for db_alert in stock_alerts:
                                alert_type = db_alert['alert_type']
                                triggered = False
                                
                                if alert_type == 'qqe_long_signal' and latest.get('qqe_long', False):
                                    triggered = True
                                elif alert_type == 'qqe_short_signal' and latest.get('qqe_short', False):
                                    triggered = True
                                elif alert_type == 'trend_change_bullish' and latest.get('ma_cloud_trend') == 'bullish':
                                    triggered = True
                                elif alert_type == 'trend_change_bearish' and latest.get('ma_cloud_trend') == 'bearish':
                                    triggered = True
                                elif alert_type == 'ema_crossover' and 'ema_20' in latest and 'ema_50' in latest:
                                    if latest['ema_20'] > latest['ema_50'] and prev.get('ema_20', 0) <= prev.get('ema_50', 0):
                                        triggered = True
                                elif alert_type == 'ema_crossunder' and 'ema_20' in latest and 'ema_50' in latest:
                                    if latest['ema_20'] < latest['ema_50'] and prev.get('ema_20', 0) >= prev.get('ema_50', 0):
                                        triggered = True
                                elif ':' in alert_type:
                                    parts = alert_type.split(':')
                                    price_alert_type = parts[0]
                                    price_level = float(parts[1])
                                    current_price = latest['close']
                                    prev_price = prev['close']
                                    
                                    if price_alert_type == 'price_above' and current_price > price_level:
                                        triggered = True
                                    elif price_alert_type == 'price_below' and current_price < price_level:
                                        triggered = True
                                    elif price_alert_type == 'price_crosses_above' and prev_price <= price_level and current_price > price_level:
                                        triggered = True
                                    elif price_alert_type == 'price_crosses_below' and prev_price >= price_level and current_price < price_level:
                                        triggered = True
                                
                                if triggered:
                                    triggered_alerts.append({
                                        'symbol': stock['symbol'],
                                        'type': alert_type,
                                        'condition': db_alert['condition_text'],
                                        'id': db_alert['id']
                                    })
                                    
                                    if not db_alert['triggered_at']:
                                        AlertsDB.trigger_alert(db_alert['id'])
                        except:
                            pass
            
            if triggered_alerts:
                st.warning(f"🔔 {len(triggered_alerts)} alert(s) triggered!")
                for alert in triggered_alerts:
                    st.info(f"**{alert['symbol']}** - {alert['condition']}")
            else:
                active_count = len(AlertsDB.get_active_alerts())
                if active_count > 0:
                    st.success(f"✅ {active_count} active alert(s) - No triggers")
                else:
                    st.info("No alerts configured. Go to Alert Manager to create alerts.")
    
    elif mode == "Multi-Stock Comparison":
        st.subheader("📊 Multi-Stock Comparison")
        
        watchlist = WatchlistDB.get_all_stocks()
        
        if len(watchlist) < 2:
            st.info("📋 Add at least 2 stocks to your watchlist to use the comparison feature.")
            return
        
        # Stock selection
        st.markdown("### Select Stocks to Compare")
        
        available_symbols = [stock['symbol'] for stock in watchlist]
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_stocks = st.multiselect(
                "Choose stocks to compare (2-10 stocks recommended)",
                options=available_symbols,
                default=available_symbols[:min(5, len(available_symbols))]
            )
        
        with col2:
            comparison_period = st.selectbox(
                "Analysis Period",
                ["1d", "7d", "1mo", "3mo", "6mo", "1y", "2y"],
                index=3
            )
            
            benchmark_stock = st.selectbox(
                "Benchmark",
                selected_stocks if selected_stocks else available_symbols,
                index=0
            ) if selected_stocks else None
        
        if not selected_stocks or len(selected_stocks) < 2:
            st.warning("⚠️ Please select at least 2 stocks to compare")
            return
        
        if st.button("🔍 Run Comparison Analysis", type="primary"):
            with st.spinner("Fetching and analyzing stocks..."):
                # Create comparison analyzer
                analyzer = ComparisonAnalyzer(selected_stocks, period=comparison_period, interval='1d')
                
                if not analyzer.fetch_all_data():
                    st.error("Failed to fetch data for selected stocks")
                    return
                
                # Tabs for different analysis views
                tab1, tab2, tab3, tab4 = st.tabs([
                    "📈 Price Comparison",
                    "📊 Performance Metrics",
                    "🔗 Correlation Analysis",
                    "💪 Relative Strength"
                ])
                
                with tab1:
                    st.markdown("### Normalized Price Chart")
                    st.caption("All stocks normalized to 100 at the start of the period")
                    
                    normalized_prices = analyzer.get_normalized_prices()
                    
                    fig = go.Figure()
                    
                    for symbol in normalized_prices.columns:
                        fig.add_trace(go.Scatter(
                            x=normalized_prices.index,
                            y=normalized_prices[symbol],
                            name=symbol,
                            mode='lines',
                            line=dict(width=2)
                        ))
                    
                    fig.update_layout(
                        title="Normalized Price Performance",
                        xaxis_title="Date",
                        yaxis_title="Normalized Price (Base=100)",
                        hovermode='x unified',
                        height=500,
                        template='plotly_white'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                with tab2:
                    st.markdown("### Performance Metrics")
                    
                    metrics_df = analyzer.get_performance_metrics()
                    
                    # Display metrics
                    st.dataframe(
                        metrics_df.style.format({
                            'Total Return (%)': '{:.2f}%',
                            'Volatility (%)': '{:.2f}%',
                            'Sharpe Ratio': '{:.3f}',
                            'Max Drawdown (%)': '{:.2f}%',
                            'Current Price': '${:.2f}',
                            'Period High': '${:.2f}',
                            'Period Low': '${:.2f}'
                        }).background_gradient(subset=['Total Return (%)'], cmap='RdYlGn', vmin=-20, vmax=20),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Best/Worst performers
                    st.markdown("### 🏆 Top Performers")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    sorted_by_return = metrics_df.sort_values('Total Return (%)', ascending=False)
                    sorted_by_sharpe = metrics_df.sort_values('Sharpe Ratio', ascending=False)
                    sorted_by_volatility = metrics_df.sort_values('Volatility (%)')
                    
                    with col1:
                        st.success(f"**Best Return**: {sorted_by_return.iloc[0]['Symbol']}")
                        st.write(f"{sorted_by_return.iloc[0]['Total Return (%)']:.2f}%")
                    
                    with col2:
                        st.success(f"**Best Sharpe**: {sorted_by_sharpe.iloc[0]['Symbol']}")
                        st.write(f"{sorted_by_sharpe.iloc[0]['Sharpe Ratio']:.3f}")
                    
                    with col3:
                        st.info(f"**Lowest Volatility**: {sorted_by_volatility.iloc[0]['Symbol']}")
                        st.write(f"{sorted_by_volatility.iloc[0]['Volatility (%)']:.2f}%")
                
                with tab3:
                    st.markdown("### Correlation Matrix")
                    st.caption("Shows how stocks move together (1 = perfect correlation, -1 = perfect inverse)")
                    
                    corr_matrix = analyzer.calculate_correlation_matrix()
                    
                    if not corr_matrix.empty:
                        # Heatmap
                        fig = go.Figure(data=go.Heatmap(
                            z=corr_matrix.values,
                            x=corr_matrix.columns,
                            y=corr_matrix.columns,
                            colorscale='RdBu',
                            zmid=0,
                            zmin=-1,
                            zmax=1,
                            text=corr_matrix.values,
                            texttemplate='%{text:.2f}',
                            textfont={"size": 10},
                            colorbar=dict(title="Correlation")
                        ))
                        
                        fig.update_layout(
                            title="Stock Correlation Heatmap",
                            height=500,
                            template='plotly_white'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Highly correlated pairs
                        st.markdown("### 🔗 Highly Correlated Pairs")
                        
                        corr_pairs = analyzer.find_correlated_pairs(threshold=0.6)
                        
                        if corr_pairs:
                            for stock1, stock2, corr in corr_pairs[:5]:
                                color = "green" if corr > 0 else "red"
                                st.markdown(f"**{stock1}** ↔ **{stock2}**: :{color}[{corr:.3f}]")
                        else:
                            st.info("No highly correlated pairs found (threshold: 0.6)")
                    else:
                        st.warning("Unable to calculate correlation matrix")
                
                with tab4:
                    st.markdown("### Relative Strength Analysis")
                    st.caption(f"Performance relative to benchmark: {benchmark_stock}")
                    
                    # Get relative strength
                    rel_strength = analyzer.calculate_relative_strength(benchmark=benchmark_stock)
                    
                    if rel_strength:
                        # Create bar chart
                        symbols = list(rel_strength.keys())
                        values = list(rel_strength.values())
                        
                        colors = ['green' if v > 100 else 'red' for v in values]
                        
                        fig = go.Figure(data=[
                            go.Bar(
                                x=symbols,
                                y=values,
                                marker_color=colors,
                                text=[f"{v:.1f}" for v in values],
                                textposition='auto',
                            )
                        ])
                        
                        fig.add_hline(y=100, line_dash="dash", line_color="gray", 
                                     annotation_text="Benchmark (100)")
                        
                        fig.update_layout(
                            title=f"Relative Strength vs {benchmark_stock}",
                            xaxis_title="Stock",
                            yaxis_title="Relative Strength Index",
                            height=400,
                            template='plotly_white'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Rankings
                        st.markdown("### 📊 Strength Rankings")
                        
                        rankings = analyzer.get_sector_strength_ranking()
                        
                        if not rankings.empty:
                            st.dataframe(
                                rankings.style.format({
                                    'Strength Score': '{:.2f}',
                                    'Total Return %': '{:.2f}%',
                                    'Recent Return %': '{:.2f}%',
                                    'Momentum': '{:.2f}%',
                                    'From High %': '{:.2f}%'
                                }).background_gradient(subset=['Strength Score'], cmap='RdYlGn'),
                                use_container_width=True,
                                hide_index=True
                            )
    
    elif mode == "Backtesting":
        st.subheader("🔬 Strategy Backtesting")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            bt_symbol = st.text_input("Stock Symbol for Backtest", value="AAPL").upper()
        
        with col2:
            bt_period = st.selectbox("Historical Period", ["1d", "7d", "1mo", "3mo", "6mo", "1y", "2y", "5y"], index=5)
        
        st.markdown("### Backtest Parameters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            initial_capital = st.number_input("Initial Capital ($)", value=10000.0, step=1000.0)
            position_size = st.slider("Position Size (%)", 5, 50, 10)
        
        with col2:
            use_stop_loss = st.checkbox("Use Stop Loss", value=True)
            stop_loss_pct = st.slider("Stop Loss (%)", 1.0, 10.0, 2.0, 0.5) if use_stop_loss else 2.0
        
        with col3:
            use_take_profit = st.checkbox("Use Take Profit", value=False)
            take_profit_pct = st.slider("Take Profit (%)", 2.0, 20.0, 5.0, 0.5) if use_take_profit else 5.0
        
        st.markdown("### Strategy Selection")
        
        strategy_type = st.radio("Strategy", ["QQE Signals", "EMA Crossover", "MA Cloud Trend"], horizontal=True)
        
        if st.button("🚀 Run Backtest", type="primary"):
            with st.spinner(f"Running backtest for {bt_symbol}..."):
                df, error = fetch_stock_data(bt_symbol, bt_period, '1d')
                
                if error or df is None or len(df) < 50:
                    st.error("❌ Error fetching data or insufficient data for backtesting")
                    return
                
                analyzer = TechnicalAnalyzer(df)
                analyzer.calculate_emas()
                analyzer.calculate_ma_cloud()
                analyzer.calculate_qqe()
                
                backtester = Backtester(
                    analyzer.df,
                    initial_capital=initial_capital,
                    position_size_pct=position_size,
                    use_stop_loss=use_stop_loss,
                    stop_loss_pct=stop_loss_pct,
                    use_take_profit=use_take_profit,
                    take_profit_pct=take_profit_pct
                )
                
                if strategy_type == "QQE Signals":
                    results = backtester.run_simple_strategy(
                        long_signal_col='qqe_long',
                        short_signal_col='qqe_short',
                        exit_on_opposite=True
                    )
                elif strategy_type == "EMA Crossover":
                    def ema_entry(row):
                        if 'ema_20' in row and 'ema_50' in row:
                            if row['ema_20'] > row['ema_50']:
                                return 'long'
                        return None
                    
                    def ema_exit(row, trade):
                        if 'ema_20' in row and 'ema_50' in row:
                            if trade.position_type == 'long' and row['ema_20'] < row['ema_50']:
                                return True
                        return False
                    
                    results = backtester.run_custom_strategy(ema_entry, ema_exit)
                else:
                    def cloud_entry(row):
                        if row.get('ma_cloud_trend') == 'bullish':
                            return 'long'
                        return None
                    
                    def cloud_exit(row, trade):
                        if trade.position_type == 'long' and row.get('ma_cloud_trend') == 'bearish':
                            return True
                        return False
                    
                    results = backtester.run_custom_strategy(cloud_entry, cloud_exit)
                
                st.success(f"✅ Backtest complete! Total trades: {results.total_trades()}")
                
                tab1, tab2, tab3 = st.tabs(["📊 Performance", "💰 Equity Curve", "📝 Trade Log"])
                
                with tab1:
                    st.markdown("### Performance Summary")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    total_return = ((results.final_capital - results.initial_capital) / results.initial_capital) * 100
                    
                    col1.metric("Initial Capital", f"${results.initial_capital:,.2f}")
                    col2.metric("Final Capital", f"${results.final_capital:,.2f}", 
                               f"{total_return:+.2f}%")
                    col3.metric("Total Return", f"{total_return:+.2f}%")
                    col4.metric("Total Trades", results.total_trades())
                    
                    st.markdown("---")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    col1.metric("Win Rate", f"{results.win_rate():.1f}%")
                    col2.metric("Profit Factor", f"{results.profit_factor():.2f}")
                    col3.metric("Max Drawdown", f"{results.max_drawdown():.2f}%")
                    col4.metric("Sharpe Ratio", f"{results.sharpe_ratio():.2f}")
                    
                    st.markdown("---")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    col1.metric("Winning Trades", results.winning_trades())
                    col2.metric("Losing Trades", results.losing_trades())
                    col3.metric("Avg Trade Duration", f"{results.average_trade_duration():.1f} days")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    col1.metric("Average Win", f"${results.average_win():,.2f}")
                    col2.metric("Average Loss", f"${results.average_loss():,.2f}")
                    col3.metric("Total P&L", f"${results.total_pnl():,.2f}")
                
                with tab2:
                    st.markdown("### Equity Curve")
                    
                    if not results.equity_curve.empty:
                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatter(
                            x=results.equity_curve.index,
                            y=results.equity_curve.values,
                            name='Portfolio Value',
                            line=dict(color='blue', width=2),
                            fill='tozeroy',
                            fillcolor='rgba(0,100,255,0.1)'
                        ))
                        
                        fig.add_hline(y=initial_capital, line_dash="dash", 
                                     line_color="gray", 
                                     annotation_text="Initial Capital")
                        
                        fig.update_layout(
                            title="Portfolio Equity Over Time",
                            xaxis_title="Date",
                            yaxis_title="Portfolio Value ($)",
                            hovermode='x unified',
                            height=500,
                            template='plotly_white',
                            xaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray'),
                            yaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray', tickformat='$,.0f'),
                            showlegend=True
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        drawdown = (results.equity_curve - results.equity_curve.expanding().max()) / results.equity_curve.expanding().max() * 100
                        
                        fig2 = go.Figure()
                        
                        fig2.add_trace(go.Scatter(
                            x=drawdown.index,
                            y=drawdown.values,
                            name='Drawdown',
                            line=dict(color='red', width=2),
                            fill='tozeroy',
                            fillcolor='rgba(255,0,0,0.1)'
                        ))
                        
                        fig2.update_layout(
                            title="Drawdown Over Time",
                            xaxis_title="Date",
                            yaxis_title="Drawdown (%)",
                            hovermode='x unified',
                            height=300,
                            template='plotly_white'
                        )
                        
                        st.plotly_chart(fig2, use_container_width=True)
                
                with tab3:
                    st.markdown("### Trade Log")
                    
                    if results.total_trades() > 0:
                        trade_data = []
                        
                        for trade in results.trades:
                            if not trade.is_open():
                                trade_data.append({
                                    'Entry Date': trade.entry_date.strftime('%Y-%m-%d %H:%M'),
                                    'Exit Date': trade.exit_date.strftime('%Y-%m-%d %H:%M'),
                                    'Type': trade.position_type.upper(),
                                    'Entry Price': f"${trade.entry_price:.2f}",
                                    'Exit Price': f"${trade.exit_price:.2f}",
                                    'Shares': trade.shares,
                                    'P&L': f"${trade.pnl():.2f}",
                                    'P&L %': f"{trade.pnl_percent():.2f}%",
                                    'Duration': f"{trade.duration_days()} days",
                                    'Exit Reason': trade.exit_reason
                                })
                        
                        trade_df = pd.DataFrame(trade_data)
                        
                        st.dataframe(trade_df, use_container_width=True, hide_index=True)
                        
                        csv = trade_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Trade Log (CSV)",
                            data=csv,
                            file_name=f"{bt_symbol}_backtest_trades.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("No completed trades in this backtest")
    
    elif mode == "Strategy Builder":
        st.subheader("🔧 Custom Strategy Builder")
        st.caption("Build your own trading strategy by combining technical indicators")
        
        if 'custom_strategy' not in st.session_state:
            st.session_state.custom_strategy = CustomStrategy(name="My Strategy")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            strategy_name = st.text_input("Strategy Name", value=st.session_state.custom_strategy.name)
            st.session_state.custom_strategy.name = strategy_name
        
        with col2:
            load_template = st.selectbox("Load Template", 
                                        ["None"] + [t.name for t in StrategyTemplates.get_all_templates()])
            
            if load_template != "None":
                templates = {t.name: t for t in StrategyTemplates.get_all_templates()}
                st.session_state.custom_strategy = templates[load_template]
                st.rerun()
        
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Long Entry", "📉 Short Entry", "🚪 Exit Rules", "🧪 Test Strategy"])
        
        with tab1:
            st.markdown("### Long Entry Conditions")
            st.caption("All conditions must be met (AND logic) or any condition (OR logic)")
            
            long_logic = st.radio("Logic", ["AND", "OR"], 
                                 index=0 if st.session_state.custom_strategy.long_logic == 'AND' else 1,
                                 key="long_logic_radio")
            st.session_state.custom_strategy.long_logic = long_logic
            
            num_long_conditions = st.number_input("Number of conditions", 1, 10, 
                                                 len(st.session_state.custom_strategy.long_conditions) or 1,
                                                 key="num_long")
            
            long_conditions = []
            
            for i in range(int(num_long_conditions)):
                st.markdown(f"**Condition {i+1}**")
                
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    indicator = st.selectbox(f"Indicator", 
                                           StrategyBuilder.get_indicator_list(),
                                           key=f"long_ind_{i}")
                
                ind_type = StrategyBuilder.get_indicator_type(indicator)
                
                with col2:
                    if ind_type == 'boolean':
                        operator = st.selectbox(f"Op", ['=='], key=f"long_op_{i}")
                    else:
                        operator = st.selectbox(f"Op", ['>', '<', '>=', '<=', '==', '!='], 
                                              key=f"long_op_{i}")
                
                with col3:
                    compare_to = st.selectbox("Compare to", ["Value", "Indicator"], key=f"long_cmp_{i}")
                
                with col4:
                    if compare_to == "Value":
                        if ind_type == 'boolean':
                            value = st.selectbox("Value", [True, False], key=f"long_val_{i}")
                            indicator2 = None
                        elif ind_type == 'string':
                            value = st.selectbox("Value", ['bullish', 'bearish', 'neutral'], 
                                               key=f"long_val_{i}")
                            indicator2 = None
                        else:
                            value = st.number_input("Value", value=0.0, key=f"long_val_{i}")
                            indicator2 = None
                    else:
                        indicator2 = st.selectbox("Indicator", 
                                                StrategyBuilder.get_indicator_list(),
                                                key=f"long_ind2_{i}")
                        value = 0
                
                long_conditions.append(StrategyCondition(indicator, operator, value, indicator2))
            
            st.session_state.custom_strategy.long_conditions = long_conditions
        
        with tab2:
            st.markdown("### Short Entry Conditions")
            
            short_logic = st.radio("Logic", ["AND", "OR"], 
                                  index=0 if st.session_state.custom_strategy.short_logic == 'AND' else 1,
                                  key="short_logic_radio")
            st.session_state.custom_strategy.short_logic = short_logic
            
            num_short_conditions = st.number_input("Number of conditions", 0, 10, 
                                                  len(st.session_state.custom_strategy.short_conditions),
                                                  key="num_short")
            
            short_conditions = []
            
            for i in range(int(num_short_conditions)):
                st.markdown(f"**Condition {i+1}**")
                
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    indicator = st.selectbox(f"Indicator", 
                                           StrategyBuilder.get_indicator_list(),
                                           key=f"short_ind_{i}")
                
                ind_type = StrategyBuilder.get_indicator_type(indicator)
                
                with col2:
                    if ind_type == 'boolean':
                        operator = st.selectbox(f"Op", ['=='], key=f"short_op_{i}")
                    else:
                        operator = st.selectbox(f"Op", ['>', '<', '>=', '<=', '==', '!='], 
                                              key=f"short_op_{i}")
                
                with col3:
                    compare_to = st.selectbox("Compare to", ["Value", "Indicator"], key=f"short_cmp_{i}")
                
                with col4:
                    if compare_to == "Value":
                        if ind_type == 'boolean':
                            value = st.selectbox("Value", [True, False], key=f"short_val_{i}")
                            indicator2 = None
                        elif ind_type == 'string':
                            value = st.selectbox("Value", ['bullish', 'bearish', 'neutral'], 
                                               key=f"short_val_{i}")
                            indicator2 = None
                        else:
                            value = st.number_input("Value", value=0.0, key=f"short_val_{i}")
                            indicator2 = None
                    else:
                        indicator2 = st.selectbox("Indicator", 
                                                StrategyBuilder.get_indicator_list(),
                                                key=f"short_ind2_{i}")
                        value = 0
                
                short_conditions.append(StrategyCondition(indicator, operator, value, indicator2))
            
            st.session_state.custom_strategy.short_conditions = short_conditions
        
        with tab3:
            st.markdown("### Exit Conditions")
            
            exit_logic = st.radio("Logic", ["AND", "OR"], 
                                 index=0 if st.session_state.custom_strategy.exit_logic == 'AND' else 1,
                                 key="exit_logic_radio")
            st.session_state.custom_strategy.exit_logic = exit_logic
            
            num_exit_conditions = st.number_input("Number of conditions", 0, 10, 
                                                 len(st.session_state.custom_strategy.exit_conditions),
                                                 key="num_exit")
            
            exit_conditions = []
            
            for i in range(int(num_exit_conditions)):
                st.markdown(f"**Condition {i+1}**")
                
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    indicator = st.selectbox(f"Indicator", 
                                           StrategyBuilder.get_indicator_list(),
                                           key=f"exit_ind_{i}")
                
                ind_type = StrategyBuilder.get_indicator_type(indicator)
                
                with col2:
                    if ind_type == 'boolean':
                        operator = st.selectbox(f"Op", ['=='], key=f"exit_op_{i}")
                    else:
                        operator = st.selectbox(f"Op", ['>', '<', '>=', '<=', '==', '!='], 
                                              key=f"exit_op_{i}")
                
                with col3:
                    compare_to = st.selectbox("Compare to", ["Value", "Indicator"], key=f"exit_cmp_{i}")
                
                with col4:
                    if compare_to == "Value":
                        if ind_type == 'boolean':
                            value = st.selectbox("Value", [True, False], key=f"exit_val_{i}")
                            indicator2 = None
                        elif ind_type == 'string':
                            value = st.selectbox("Value", ['bullish', 'bearish', 'neutral'], 
                                               key=f"exit_val_{i}")
                            indicator2 = None
                        else:
                            value = st.number_input("Value", value=0.0, key=f"exit_val_{i}")
                            indicator2 = None
                    else:
                        indicator2 = st.selectbox("Indicator", 
                                                StrategyBuilder.get_indicator_list(),
                                                key=f"exit_ind2_{i}")
                        value = 0
                
                exit_conditions.append(StrategyCondition(indicator, operator, value, indicator2))
            
            st.session_state.custom_strategy.exit_conditions = exit_conditions
        
        with tab4:
            st.markdown("### Test Your Strategy")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                test_symbol = st.text_input("Test Symbol", value="AAPL").upper()
            
            with col2:
                test_period = st.selectbox("Period", ["6mo", "1y", "2y"], index=1)
            
            if st.button("🧪 Test Strategy", type="primary"):
                if not st.session_state.custom_strategy.long_conditions:
                    st.error("Please add at least one long entry condition")
                else:
                    with st.spinner(f"Testing strategy on {test_symbol}..."):
                        df, error = fetch_stock_data(test_symbol, test_period, '1d')
                        
                        if error or df is None:
                            st.error("Error fetching data")
                        else:
                            analyzer = TechnicalAnalyzer(df)
                            analyzer.calculate_emas()
                            analyzer.calculate_ma_cloud()
                            analyzer.calculate_qqe()
                            analyzer.calculate_vwap()
                            
                            df_signals = st.session_state.custom_strategy.generate_signals(analyzer.df)
                            
                            backtester = Backtester(df_signals, initial_capital=10000.0)
                            
                            def custom_entry(row):
                                if st.session_state.custom_strategy.should_enter_long(row):
                                    return 'long'
                                elif st.session_state.custom_strategy.should_enter_short(row):
                                    return 'short'
                                return None
                            
                            def custom_exit(row, trade):
                                return st.session_state.custom_strategy.should_exit(row)
                            
                            results = backtester.run_custom_strategy(custom_entry, custom_exit)
                            
                            st.success(f"✅ Test complete! Total trades: {results.total_trades()}")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            
                            total_return = ((results.final_capital - results.initial_capital) / results.initial_capital) * 100
                            
                            col1.metric("Total Return", f"{total_return:+.2f}%")
                            col2.metric("Win Rate", f"{results.win_rate():.1f}%")
                            col3.metric("Total Trades", results.total_trades())
                            col4.metric("Profit Factor", f"{results.profit_factor():.2f}")
                            
                            if not results.equity_curve.empty:
                                fig = go.Figure()
                                
                                fig.add_trace(go.Scatter(
                                    x=results.equity_curve.index,
                                    y=results.equity_curve.values,
                                    name='Equity',
                                    line=dict(color='blue', width=2)
                                ))
                                
                                fig.update_layout(
                                    title=f"{strategy_name} - Equity Curve",
                                    xaxis_title="Date",
                                    yaxis_title="Portfolio Value ($)",
                                    height=400,
                                    template='plotly_white'
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
    
    elif mode == "Alert Manager":
        st.subheader("🔔 Alert Manager")
        st.caption("Create and manage custom alerts for your watchlist")
        
        watchlist = WatchlistDB.get_all_stocks()
        
        if not watchlist:
            st.warning("📋 No stocks in watchlist. Add stocks first to create alerts.")
            return
        
        tab1, tab2 = st.tabs(["➕ Create Alert", "📋 Manage Alerts"])
        
        with tab1:
            st.markdown("### Create New Alert")
            
            col1, col2 = st.columns(2)
            
            with col1:
                alert_symbol = st.selectbox("Stock Symbol", 
                                           [stock['symbol'] for stock in watchlist])
            
            with col2:
                alert_category = st.selectbox("Alert Type", 
                                            ["Indicator Signal", "Trend Change", "Price Level", "EMA Crossover"])
            
            if alert_category == "Indicator Signal":
                signal_type = st.selectbox("Signal", 
                                          ["QQE Long Signal", "QQE Short Signal"])
                
                if st.button("Create Alert", type="primary"):
                    alert_type = 'qqe_long_signal' if signal_type == "QQE Long Signal" else 'qqe_short_signal'
                    condition_text = f"{signal_type} on {alert_symbol}"
                    
                    if AlertsDB.add_alert(alert_symbol, alert_type, condition_text):
                        st.success(f"✅ Alert created for {alert_symbol}")
                        st.rerun()
                    else:
                        st.error("Failed to create alert")
            
            elif alert_category == "Trend Change":
                trend_direction = st.selectbox("Direction", ["Bullish", "Bearish"])
                
                if st.button("Create Alert", type="primary"):
                    alert_type = 'trend_change_bullish' if trend_direction == "Bullish" else 'trend_change_bearish'
                    condition_text = f"Trend changes to {trend_direction} on {alert_symbol}"
                    
                    if AlertsDB.add_alert(alert_symbol, alert_type, condition_text):
                        st.success(f"✅ Alert created for {alert_symbol}")
                        st.rerun()
                    else:
                        st.error("Failed to create alert")
            
            elif alert_category == "Price Level":
                price_level = st.number_input("Price Level ($)", min_value=0.0, value=100.0, step=0.01)
                price_condition = st.selectbox("Condition", ["Above", "Below", "Crosses Above", "Crosses Below"])
                
                if st.button("Create Alert", type="primary"):
                    alert_type_map = {
                        "Above": "price_above",
                        "Below": "price_below",
                        "Crosses Above": "price_crosses_above",
                        "Crosses Below": "price_crosses_below"
                    }
                    alert_type = alert_type_map[price_condition]
                    condition_text = f"Price {price_condition.lower()} ${price_level:.2f} on {alert_symbol}"
                    
                    if AlertsDB.add_alert(alert_symbol, f"{alert_type}:{price_level}", condition_text):
                        st.success(f"✅ Alert created for {alert_symbol}")
                        st.rerun()
                    else:
                        st.error("Failed to create alert")
            
            elif alert_category == "EMA Crossover":
                cross_direction = st.selectbox("Crossover Type", ["EMA 20 crosses above EMA 50", "EMA 20 crosses below EMA 50"])
                
                if st.button("Create Alert", type="primary"):
                    alert_type = 'ema_crossover' if 'above' in cross_direction else 'ema_crossunder'
                    condition_text = f"{cross_direction} on {alert_symbol}"
                    
                    if AlertsDB.add_alert(alert_symbol, alert_type, condition_text):
                        st.success(f"✅ Alert created for {alert_symbol}")
                        st.rerun()
                    else:
                        st.error("Failed to create alert")
        
        with tab2:
            st.markdown("### Active Alerts")
            
            all_alerts = AlertsDB.get_active_alerts()
            
            if all_alerts:
                alert_data = []
                
                for alert in all_alerts:
                    alert_data.append({
                        'ID': alert['id'],
                        'Symbol': alert['symbol'],
                        'Type': alert['alert_type'],
                        'Condition': alert['condition_text'],
                        'Created': alert['created_at'].strftime('%Y-%m-%d %H:%M') if alert['created_at'] else 'N/A',
                        'Triggered': 'Yes' if alert['triggered_at'] else 'No'
                    })
                
                alert_df = pd.DataFrame(alert_data)
                
                st.dataframe(alert_df, use_container_width=True, hide_index=True)
                
                st.markdown("### Delete Alerts")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    alert_to_delete = st.selectbox("Select alert to delete",
                                                  options=[f"{a['Symbol']} - {a['Condition']}" for a in alert_data],
                                                  key="delete_alert_select")
                
                with col2:
                    if st.button("🗑️ Delete", type="secondary"):
                        idx = [f"{a['Symbol']} - {a['Condition']}" for a in alert_data].index(alert_to_delete)
                        alert_id = alert_data[idx]['ID']
                        
                        if AlertsDB.delete_alert(alert_id):
                            st.success("Alert deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete alert")
            else:
                st.info("No alerts configured. Create your first alert using the form above.")

if __name__ == "__main__":
    main()
