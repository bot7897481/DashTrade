"""
NovAlgo - Stock Trading Signal Dashboard
=========================================
Comprehensive technical analysis dashboard with:
- All PineScript indicators (EMAs, MA Cloud, QQE, VWAP)
- Chart pattern recognition (20+ patterns)
- Candlestick pattern detection (15+ patterns)
- Support/Resistance identification
- Volume analysis & Risk management
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

# Page configuration
st.set_page_config(
    page_title="NovAlgo Trading Signals",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
    .signal-high {
        background-color: #4caf50;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
    }
    .signal-medium {
        background-color: #ff9800;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
@st.cache_data(ttl=300)
def fetch_stock_data(symbol: str, period: str, interval: str):
    """Fetch stock data from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            return None, f"No data found for {symbol}"
        
        # Ensure column names are lowercase
        df.columns = [col.lower() for col in df.columns]
        df = df[['open', 'high', 'low', 'close', 'volume']]
        
        return df, None
    except Exception as e:
        return None, str(e)

def create_candlestick_chart(df, analyzer, patterns, support, resistance):
    """Create comprehensive candlestick chart with all indicators"""
    
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=('Price & Indicators', 'Volume', 'QQE Trend')
    )
    
    # Candlesticks
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Price',
            increasing_line_color='#00c853',
            decreasing_line_color='#ff1744'
        ),
        row=1, col=1
    )
    
    # EMAs
    ema_colors = {'ema_9': '#FFD700', 'ema_20': '#FF4500', 'ema_50': '#FFA500', 
                  'ema_100': '#00FA9A', 'ema_200': '#FFFFFF'}
    for ema, color in ema_colors.items():
        if ema in df.columns:
            fig.add_trace(
                go.Scatter(x=df.index, y=df[ema], name=ema.upper(), 
                          line=dict(color=color, width=1.5)),
                row=1, col=1
            )
    
    # VWAP
    if 'vwap' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['vwap'], name='VWAP',
                      line=dict(color='#2962FF', width=2, dash='dash')),
            row=1, col=1
        )
        # VWAP Bands
        fig.add_trace(
            go.Scatter(x=df.index, y=df['vwap_upper_1'], name='VWAP +1σ',
                      line=dict(color='#4CAF50', width=1, dash='dot'),
                      showlegend=False),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['vwap_lower_1'], name='VWAP -1σ',
                      line=dict(color='#4CAF50', width=1, dash='dot'),
                      fill='tonexty', fillcolor='rgba(76, 175, 80, 0.1)'),
            row=1, col=1
        )
    
    # Support & Resistance levels
    for level in support[:5]:  # Top 5 support levels
        fig.add_hline(y=level, line_dash="dash", line_color="green", 
                     opacity=0.5, row=1, col=1,
                     annotation_text=f"S: ${level:.2f}", annotation_position="right")
    
    for level in resistance[:5]:  # Top 5 resistance levels
        fig.add_hline(y=level, line_dash="dash", line_color="red", 
                     opacity=0.5, row=1, col=1,
                     annotation_text=f"R: ${level:.2f}", annotation_position="right")
    
    # QQE Signals
    if 'qqe_long' in df.columns:
        long_signals = df[df['qqe_long'] == True]
        if not long_signals.empty:
            fig.add_trace(
                go.Scatter(
                    x=long_signals.index,
                    y=long_signals['low'] * 0.995,
                    mode='markers',
                    name='QQE Long',
                    marker=dict(symbol='triangle-up', size=15, color='green'),
                    text='LONG',
                    hovertemplate='<b>QQE Long Signal</b><br>Price: $%{y:.2f}<extra></extra>'
                ),
                row=1, col=1
            )
    
    if 'qqe_short' in df.columns:
        short_signals = df[df['qqe_short'] == True]
        if not short_signals.empty:
            fig.add_trace(
                go.Scatter(
                    x=short_signals.index,
                    y=short_signals['high'] * 1.005,
                    mode='markers',
                    name='QQE Short',
                    marker=dict(symbol='triangle-down', size=15, color='red'),
                    text='SHORT',
                    hovertemplate='<b>QQE Short Signal</b><br>Price: $%{y:.2f}<extra></extra>'
                ),
                row=1, col=1
            )
    
    # Candlestick patterns
    bullish_patterns = []
    bearish_patterns = []
    
    for col in df.columns:
        if col.startswith('pattern_'):
            pattern_data = df[df[col] == True]
            if not pattern_data.empty:
                pattern_name = col.replace('pattern_', '').replace('_', ' ').title()
                if any(x in col for x in ['bullish', 'hammer', 'morning']):
                    bullish_patterns.append((pattern_name, pattern_data))
                elif any(x in col for x in ['bearish', 'shooting', 'evening']):
                    bearish_patterns.append((pattern_name, pattern_data))
    
    for name, data in bullish_patterns:
        fig.add_trace(
            go.Scatter(
                x=data.index, y=data['low'] * 0.998,
                mode='markers',
                name=name,
                marker=dict(symbol='star', size=10, color='lightgreen'),
                hovertemplate=f'<b>{name}</b><br>Price: $' + '%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
    
    for name, data in bearish_patterns:
        fig.add_trace(
            go.Scatter(
                x=data.index, y=data['high'] * 1.002,
                mode='markers',
                name=name,
                marker=dict(symbol='star', size=10, color='lightcoral'),
                hovertemplate=f'<b>{name}</b><br>Price: $' + '%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
    
    # Volume
    colors = ['red' if df['close'].iloc[i] < df['open'].iloc[i] else 'green' 
              for i in range(len(df))]
    fig.add_trace(
        go.Bar(x=df.index, y=df['volume'], name='Volume',
               marker_color=colors, showlegend=False),
        row=2, col=1
    )
    
    # QQE Trend
    if 'qqe_trend' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['qqe_trend'], name='QQE Trend',
                      line=dict(color='purple', width=2),
                      fill='tozeroy'),
            row=3, col=1
        )
    
    # Layout
    fig.update_layout(
        title=f"{st.session_state.symbol} - Technical Analysis",
        xaxis_rangeslider_visible=False,
        height=900,
        template='plotly_dark',
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_xaxes(title_text="Date", row=3, col=1)
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="Trend", row=3, col=1)
    
    return fig

def display_patterns(patterns):
    """Display detected chart patterns"""
    total_patterns = sum(len(v) for v in patterns.values())
    
    if total_patterns == 0:
        st.info("No chart patterns detected in the current timeframe.")
        return
    
    for pattern_type, pattern_list in patterns.items():
        if pattern_list:
            st.subheader(f"📐 {pattern_type.replace('_', ' ').title()} ({len(pattern_list)})")
            
            for idx, pattern in enumerate(pattern_list[:3]):  # Show top 3
                with st.expander(f"Pattern #{idx + 1} - {pattern.get('type', 'Unknown').replace('_', ' ').title()}"):
                    cols = st.columns(3)
                    
                    if 'double_top' in pattern.get('type', ''):
                        cols[0].metric("Peak 1", f"${pattern.get('peak1', 0):.2f}")
                        cols[1].metric("Peak 2", f"${pattern.get('peak2', 0):.2f}")
                        cols[2].metric("Target", f"${pattern.get('target', 0):.2f}")
                        st.warning("⚠️ Bearish pattern - expect decline")
                        
                    elif 'double_bottom' in pattern.get('type', ''):
                        cols[0].metric("Trough 1", f"${pattern.get('trough1', 0):.2f}")
                        cols[1].metric("Trough 2", f"${pattern.get('trough2', 0):.2f}")
                        cols[2].metric("Target", f"${pattern.get('target', 0):.2f}")
                        st.success("✅ Bullish pattern - expect rise")
                        
                    elif 'head_and_shoulders' in pattern.get('type', ''):
                        cols[0].metric("Left Shoulder", f"${pattern.get('left_shoulder', 0):.2f}")
                        cols[1].metric("Head", f"${pattern.get('head', 0):.2f}")
                        cols[2].metric("Right Shoulder", f"${pattern.get('right_shoulder', 0):.2f}")
                        
                        neckline_col, target_col = st.columns(2)
                        neckline_col.metric("Neckline", f"${pattern.get('neckline', 0):.2f}")
                        target_col.metric("Target", f"${pattern.get('target', 0):.2f}")
                        
                        if pattern.get('bearish'):
                            st.warning("⚠️ Bearish pattern")
                        else:
                            st.success("✅ Bullish pattern")

def display_candlestick_patterns(df):
    """Display detected candlestick patterns"""
    pattern_cols = [col for col in df.columns if col.startswith('pattern_')]
    
    if not pattern_cols:
        st.info("No candlestick patterns detected.")
        return
    
    # Get latest patterns (last 10 bars)
    recent_df = df.tail(10)
    patterns_found = []
    
    for col in pattern_cols:
        if recent_df[col].any():
            pattern_name = col.replace('pattern_', '').replace('_', ' ').title()
            last_occurrence = recent_df[recent_df[col] == True].index[-1]
            patterns_found.append((pattern_name, last_occurrence, col))
    
    if patterns_found:
        st.subheader("🕯️ Recent Candlestick Patterns")
        
        for pattern_name, date, col_name in sorted(patterns_found, key=lambda x: x[1], reverse=True):
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                # Determine if bullish or bearish
                is_bullish = any(x in col_name for x in ['bullish', 'hammer', 'morning'])
                is_bearish = any(x in col_name for x in ['bearish', 'shooting', 'evening'])
                
                if is_bullish:
                    col1.markdown(f"**🟢 {pattern_name}**")
                    col2.success("Bullish")
                elif is_bearish:
                    col1.markdown(f"**🔴 {pattern_name}**")
                    col2.error("Bearish")
                else:
                    col1.markdown(f"**⚪ {pattern_name}**")
                    col2.info("Neutral")
                
                col3.write(f"{date.strftime('%Y-%m-%d')}")
    else:
        st.info("No recent candlestick patterns detected.")

def display_risk_management(analyzer, df, account_balance):
    """Display risk management calculator"""
    st.subheader("💼 Risk Management Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Position Parameters**")
        risk_percent = st.slider("Risk Per Trade (%)", 0.5, 5.0, 1.0, 0.5)
        direction = st.radio("Direction", ["Long", "Short"])
        entry_price = st.number_input("Entry Price ($)", 
                                     value=float(df['close'].iloc[-1]),
                                     step=0.01)
    
    with col2:
        st.write("**Stop Loss Settings**")
        atr_multiplier = st.slider("ATR Multiplier", 1.0, 3.0, 2.0, 0.5)
        
        # Calculate stop loss
        stop_loss = analyzer.calculate_stop_loss(
            entry_price=entry_price,
            direction=direction.lower(),
            method='atr',
            atr_multiplier=atr_multiplier
        )
        
        st.metric("Calculated Stop Loss", f"${stop_loss:.2f}")
        
        # Calculate position size
        position_size = analyzer.calculate_position_size(
            account_balance=account_balance,
            risk_per_trade=risk_percent / 100,
            entry_price=entry_price,
            stop_loss=stop_loss
        )
    
    # Display results
    st.write("---")
    st.subheader("📊 Trade Summary")
    
    risk_amount = account_balance * (risk_percent / 100)
    risk_per_share = abs(entry_price - stop_loss)
    position_value = entry_price * position_size
    
    # Calculate potential targets
    target_1 = entry_price + (2 * risk_per_share) if direction == "Long" else entry_price - (2 * risk_per_share)
    target_2 = entry_price + (3 * risk_per_share) if direction == "Long" else entry_price - (3 * risk_per_share)
    
    cols = st.columns(4)
    cols[0].metric("Position Size", f"{position_size} shares")
    cols[1].metric("Position Value", f"${position_value:,.2f}")
    cols[2].metric("Risk Amount", f"${risk_amount:.2f}")
    cols[3].metric("Risk/Share", f"${risk_per_share:.2f}")
    
    st.write("**Price Targets:**")
    target_cols = st.columns(3)
    target_cols[0].metric("Entry", f"${entry_price:.2f}")
    target_cols[1].metric("Target 1 (1:2)", f"${target_1:.2f}")
    target_cols[2].metric("Target 2 (1:3)", f"${target_2:.2f}")
    
    # Visual representation
    if direction == "Long":
        st.success(f"✅ **LONG Setup**: Buy at ${entry_price:.2f}, Stop at ${stop_loss:.2f}")
    else:
        st.error(f"⚠️ **SHORT Setup**: Sell at ${entry_price:.2f}, Stop at ${stop_loss:.2f}")

# Main App
def main():
    # Header
    st.markdown('<h1 class="main-header">📈 NovAlgo Trading Signals</h1>', unsafe_allow_html=True)
    st.markdown("### Comprehensive Stock Technical Analysis Dashboard")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.title("📈 NovAlgo")
        st.markdown("---")
        st.title("⚙️ Settings")
        
        # Stock symbol input
        symbol = st.text_input("Stock Symbol", value="AAPL", key='symbol').upper()
        
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
                                            value=10000.0, 
                                            step=1000.0)
        
        # Fetch button
        fetch_button = st.button("🔄 Fetch & Analyze", type="primary", use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 📊 Coverage")
        st.success("✅ EMAs (9, 20, 50, 100, 200)")
        st.success("✅ MA Cloud & QQE Signals")
        st.success("✅ VWAP with Bands")
        st.success("✅ 15+ Candlestick Patterns")
        st.success("✅ Chart Patterns")
        st.success("✅ Support & Resistance")
        st.success("✅ Volume Analysis")
        st.success("✅ Risk Management")
    
    # Main content
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
                    
                    # Calculate all indicators with custom QQE parameters
                    analyzer.calculate_emas()
                    analyzer.calculate_ma_cloud()
                    analyzer.calculate_qqe(rsi_period=rsi_period, 
                                         smoothing=rsi_smoothing,
                                         qqe_factor=qqe_factor)
                    analyzer.calculate_vwap()
                    analyzer.analyze_all_candlestick_patterns()
                    
                    # Get patterns and levels
                    chart_patterns = analyzer.detect_all_chart_patterns()
                    sr_levels = analyzer.identify_support_resistance()
                    
                    # Store in session state
                    st.session_state.analysis_results = {
                        'df': analyzer.df,
                        'analyzer': analyzer,
                        'patterns': chart_patterns,
                        'support': sr_levels['support'],
                        'resistance': sr_levels['resistance']
                    }
                    
                st.success(f"✅ Analysis complete for {symbol}!")
        
        # Get results from session state
        results = st.session_state.analysis_results
        df = results['df']
        analyzer = results['analyzer']
        patterns = results['patterns']
        support = results['support']
        resistance = results['resistance']
        
        # Overview metrics
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        price_change = latest['close'] - prev['close']
        price_change_pct = (price_change / prev['close']) * 100
        
        st.subheader(f"📊 {symbol} Overview")
        
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
        
        # Count signals
        bullish_signals = 0
        bearish_signals = 0
        
        if latest.get('qqe_long', False):
            bullish_signals += 1
        if latest.get('qqe_short', False):
            bearish_signals += 1
        
        for col in df.columns:
            if col.startswith('pattern_') and latest.get(col, False):
                if any(x in col for x in ['bullish', 'hammer', 'morning']):
                    bullish_signals += 1
                elif any(x in col for x in ['bearish', 'shooting', 'evening']):
                    bearish_signals += 1
        
        cols[3].metric("Bullish Signals", bullish_signals)
        cols[4].metric("Bearish Signals", bearish_signals)
        
        # Tabs
        tabs = st.tabs(["📈 Chart", "📐 Chart Patterns", "🕯️ Candlestick Patterns", 
                       "🎯 Support & Resistance", "💼 Risk Management"])
        
        with tabs[0]:
            st.plotly_chart(
                create_candlestick_chart(df, analyzer, patterns, support, resistance),
                use_container_width=True
            )
            
            # Latest signals
            st.subheader("🚦 Latest Signals")
            if latest.get('qqe_long', False):
                st.success("🟢 **QQE LONG SIGNAL** - Momentum turning bullish")
            elif latest.get('qqe_short', False):
                st.error("🔴 **QQE SHORT SIGNAL** - Momentum turning bearish")
            else:
                st.info("ℹ️ No active QQE signals")
        
        with tabs[1]:
            display_patterns(patterns)
        
        with tabs[2]:
            display_candlestick_patterns(df)
        
        with tabs[3]:
            st.subheader("🎯 Support & Resistance Levels")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**📉 Support Levels**")
                current_price = latest['close']
                support_below = [s for s in support if s < current_price]
                
                if support_below:
                    for i, level in enumerate(sorted(support_below, reverse=True)[:5], 1):
                        distance = ((current_price - level) / current_price) * 100
                        st.success(f"{i}. ${level:.2f} ({distance:.2f}% below)")
                else:
                    st.info("No support levels found below current price")
            
            with col2:
                st.write("**📈 Resistance Levels**")
                resistance_above = [r for r in resistance if r > current_price]
                
                if resistance_above:
                    for i, level in enumerate(sorted(resistance_above)[:5], 1):
                        distance = ((level - current_price) / current_price) * 100
                        st.error(f"{i}. ${level:.2f} ({distance:.2f}% above)")
                else:
                    st.info("No resistance levels found above current price")
            
            # Nearest levels
            st.write("---")
            st.subheader("🎯 Key Levels")
            
            nearest_support = max(support_below) if support_below else None
            nearest_resistance = min(resistance_above) if resistance_above else None
            
            level_cols = st.columns(3)
            level_cols[0].metric("Current Price", f"${current_price:.2f}")
            
            if nearest_support:
                level_cols[1].metric("Nearest Support", f"${nearest_support:.2f}",
                                   f"{((current_price - nearest_support) / current_price * 100):.2f}% below")
            
            if nearest_resistance:
                level_cols[2].metric("Nearest Resistance", f"${nearest_resistance:.2f}",
                                    f"{((nearest_resistance - current_price) / current_price * 100):.2f}% above")
        
        with tabs[4]:
            display_risk_management(analyzer, df, account_balance)
    
    else:
        # Welcome screen
        st.info("👈 Enter a stock symbol and click 'Fetch & Analyze' to get started!")
        
        st.subheader("🎯 What This Dashboard Offers")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **From Your PineScript (20%):**
            - ✅ 5 EMAs (9, 20, 50, 100, 200)
            - ✅ MA Cloud (trend visualization)
            - ✅ QQE Signals (momentum)
            - ✅ VWAP with Bands
            """)
            
            st.markdown("""
            **Advanced Features (80%):**
            - ✅ 15+ Candlestick Patterns
            - ✅ Chart Patterns (Double Tops/Bottoms, H&S, Triangles)
            - ✅ Automatic Support & Resistance
            - ✅ Volume Analysis (Bulkowski Method)
            """)
        
        with col2:
            st.markdown("""
            **Risk Management:**
            - ✅ ATR-based Stop Loss
            - ✅ Position Sizing Calculator
            - ✅ Price Target Projections
            - ✅ Risk/Reward Ratios
            """)
            
            st.markdown("""
            **Signal Generation:**
            - ✅ Pattern-based Entries
            - ✅ Trend Confirmation
            - ✅ Strength Scoring
            - ✅ Multi-timeframe Analysis
            """)
        
        st.markdown("---")
        st.subheader("📚 Example Stocks to Try")
        example_cols = st.columns(4)
        example_cols[0].code("AAPL")
        example_cols[1].code("TSLA")
        example_cols[2].code("NVDA")
        example_cols[3].code("BTC-USD")

if __name__ == "__main__":
    main()
