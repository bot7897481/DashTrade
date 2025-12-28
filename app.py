"""
NovAlgo - Enhanced Stock Trading Signal Dashboard with Portfolio Tracking
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')
import yfinance as yf

from technical_analyzer import TechnicalAnalyzer
from database import WatchlistDB, AlertsDB, PreferencesDB
from comparison_analyzer import ComparisonAnalyzer
from backtester import Backtester, BacktestResults
from strategy_builder import CustomStrategy, StrategyCondition, StrategyTemplates, StrategyBuilder
from alert_system import AlertMonitor
from alpha_vantage_data import AlphaVantageProvider, fetch_alpha_vantage_data
from yahoo_finance_data import fetch_yahoo_data
from auth import UserDB
from ai_assistant import AIAssistant, LLMKeysDB

# Page configuration
st.set_page_config(
    page_title="NovAlgo - Automated Trading Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main header */
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Login/Register Page Styles */
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
    }
    
    .login-card {
        background: white;
        border-radius: 20px;
        padding: 3rem;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        max-width: 450px;
        width: 100%;
        animation: slideUp 0.5s ease-out;
    }
    
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .login-title {
        font-size: 2rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
        color: #1a1a1a;
    }
    
    .login-subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
        font-size: 0.95rem;
    }
    
    .form-input {
        margin-bottom: 1.5rem;
    }
    
    .login-button {
        width: 100%;
        padding: 0.75rem;
        border-radius: 10px;
        font-weight: 600;
        font-size: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .login-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    .register-link {
        text-align: center;
        margin-top: 1.5rem;
        color: #666;
        font-size: 0.9rem;
    }
    
    .register-link a {
        color: #667eea;
        text-decoration: none;
        font-weight: 600;
    }
    
    .register-link a:hover {
        text-decoration: underline;
    }
    
    .error-message {
        background-color: #fee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #c62828;
    }
    
    .success-message {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #2e7d32;
    }
    
    .info-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #1565c0;
    }
    
    /* Metric cards */
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
    
    /* Styling for Streamlit form inputs */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem;
        transition: border-color 0.3s;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Styling for buttons */
    .stButton > button {
        border-radius: 10px;
        transition: all 0.3s;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
@st.cache_data(ttl=300)
def fetch_stock_data(symbol: str, period: str, interval: str, source: str = "yahoo"):
    """Unified data fetcher - routes to Yahoo Finance or Alpha Vantage based on selection"""
    if source == "yahoo":
        return fetch_yahoo_data(symbol, period, interval)
    else:  # alpha_vantage
        return fetch_alpha_vantage_data(symbol, interval, period)

def get_stock_info(symbol: str, source: str = "yahoo"):
    """Get stock name from selected data source"""
    if source == "yahoo":
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info.get('longName', symbol)
        except:
            return symbol
    else:  # alpha_vantage
        try:
            provider = AlphaVantageProvider()
            quote = provider.get_quote(symbol)
            if quote:
                return quote['symbol']
            return symbol
        except:
            return symbol

def create_candlestick_chart_with_signals(df, symbol: str):
    """Create candlestick chart with signal annotations like TradingView"""
    
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
    
    # MA Cloud
    if 'ma_cloud_short' in df.columns and 'ma_cloud_long' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['ma_cloud_short'], name='Cloud Short',
                      line=dict(color='#00c853', width=1), showlegend=False),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['ma_cloud_long'], name='Cloud Long',
                      line=dict(color='#ff1744', width=1), 
                      fill='tonexty', fillcolor='rgba(0, 200, 83, 0.2)'),
            row=1, col=1
        )
    
    # VWAP
    if 'vwap' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['vwap'], name='VWAP',
                      line=dict(color='#2962FF', width=2, dash='dash')),
            row=1, col=1
        )
    
    # QQE LONG Signals with text annotations (like TradingView)
    if 'qqe_long' in df.columns:
        long_signals = df[df['qqe_long'] == True]
        if not long_signals.empty:
            for idx in long_signals.index:
                fig.add_annotation(
                    x=idx,
                    y=long_signals.loc[idx, 'low'] * 0.995,
                    text="Long",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="#00c853",
                    arrowsize=1.5,
                    arrowwidth=2,
                    ax=0,
                    ay=30,
                    font=dict(size=10, color="white"),
                    bgcolor="#00c853",
                    bordercolor="#00c853",
                    borderwidth=2,
                    borderpad=3,
                    opacity=0.9,
                    row=1, col=1
                )
    
    # QQE SHORT Signals with text annotations (like TradingView)
    if 'qqe_short' in df.columns:
        short_signals = df[df['qqe_short'] == True]
        if not short_signals.empty:
            for idx in short_signals.index:
                fig.add_annotation(
                    x=idx,
                    y=short_signals.loc[idx, 'high'] * 1.005,
                    text="Short",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="#ff1744",
                    arrowsize=1.5,
                    arrowwidth=2,
                    ax=0,
                    ay=-30,
                    font=dict(size=10, color="white"),
                    bgcolor="#ff1744",
                    bordercolor="#ff1744",
                    borderwidth=2,
                    borderpad=3,
                    opacity=0.9,
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
        title=f"{symbol} - Technical Analysis with Signal Markers",
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

# Main App
def show_landing_page():
    """Display NovAlgo landing page - Robinhood Gold inspired design with inline styles"""
    
    # Hide sidebar and Streamlit elements + base styles
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');
        
        [data-testid="stSidebar"] {display: none !important;}
        [data-testid="stSidebarNav"] {display: none !important;}
        section[data-testid="stSidebar"] {display: none !important;}
        [data-testid="collapsedControl"] {display: none !important;}
        .block-container {padding-top: 0 !important; max-width: 100% !important; padding-left: 0 !important; padding-right: 0 !important;}
        header {visibility: hidden !important;}
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        .stApp {background: #0a0b10 !important;}
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # =========================================================================
    # NAVIGATION BAR
    # =========================================================================
    st.markdown("""
    <div style="
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 72px;
        background: rgba(10, 11, 16, 0.95);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 5%;
        z-index: 1000;
        box-sizing: border-box;
    ">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="
                width: 36px;
                height: 36px;
                background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.2rem;
            ">⚡</div>
            <span style="
                font-family: 'Playfair Display', Georgia, serif;
                font-size: 1.5rem;
                font-weight: 600;
                color: #f5f0e8;
            ">NovAlgo</span>
        </div>
        <div style="display: flex; gap: 2.5rem;">
            <a href="#features" style="color: rgba(245, 240, 232, 0.7); text-decoration: none; font-family: 'Inter', sans-serif; font-size: 0.95rem; font-weight: 500;">Features</a>
            <a href="#how-it-works" style="color: rgba(245, 240, 232, 0.7); text-decoration: none; font-family: 'Inter', sans-serif; font-size: 0.95rem; font-weight: 500;">How it Works</a>
            <a href="#pricing" style="color: rgba(245, 240, 232, 0.7); text-decoration: none; font-family: 'Inter', sans-serif; font-size: 0.95rem; font-weight: 500;">Pricing</a>
            <a href="#faq" style="color: rgba(245, 240, 232, 0.7); text-decoration: none; font-family: 'Inter', sans-serif; font-size: 0.95rem; font-weight: 500;">FAQ</a>
        </div>
        <div style="display: flex; gap: 1rem; align-items: center;">
            <a href="#get-started" style="
                background: transparent;
                border: 1px solid rgba(255, 255, 255, 0.2);
                color: #f5f0e8;
                padding: 10px 24px;
                border-radius: 9999px;
                font-family: 'Inter', sans-serif;
                font-size: 0.9rem;
                font-weight: 500;
                text-decoration: none;
            ">Log in</a>
            <a href="#get-started" style="
                background: #f5f0e8;
                color: #0a0b10;
                padding: 10px 24px;
                border-radius: 9999px;
                font-family: 'Inter', sans-serif;
                font-size: 0.9rem;
                font-weight: 600;
                text-decoration: none;
            ">Get Started</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # =========================================================================
    # HERO SECTION
    # =========================================================================
    st.markdown("""
    <div style="
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 140px 5% 100px;
        background: #0a0b10;
        position: relative;
    ">
        <!-- Badge -->
        <div style="
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid rgba(0, 212, 255, 0.3);
            padding: 10px 20px;
            border-radius: 9999px;
            margin-bottom: 2rem;
        ">
            <div style="
                width: 8px;
                height: 8px;
                background: #00d4ff;
                border-radius: 50%;
                animation: pulse 2s ease-in-out infinite;
            "></div>
            <span style="font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #00d4ff;">
                Now in Public Beta — Free to Use
            </span>
        </div>
        
        <!-- Title -->
        <h1 style="
            font-family: 'Playfair Display', Georgia, serif;
            font-size: clamp(3rem, 8vw, 5rem);
            font-weight: 600;
            line-height: 1.1;
            color: #f5f0e8;
            margin: 0 0 1.5rem 0;
        ">
            <span style="background: linear-gradient(135deg, #f5f0e8 0%, #d4a84b 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">Trade</span> Smarter,<br>
            Not <span style="background: linear-gradient(135deg, #f5f0e8 0%, #d4a84b 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">Harder</span>
        </h1>
        
        <!-- Subtitle -->
        <p style="
            font-family: 'Inter', sans-serif;
            font-size: 1.25rem;
            color: #7a7a8c;
            max-width: 600px;
            margin: 0 auto 2.5rem;
            line-height: 1.7;
        ">
            Connect TradingView to Alpaca and execute your strategies automatically.
            No coding required. Set up once, trade 24/7.
        </p>
        
        <!-- CTA Buttons -->
        <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; margin-bottom: 4rem;">
            <a href="#get-started" style="
                background: #f5f0e8;
                color: #0a0b10;
                padding: 16px 32px;
                border-radius: 9999px;
                font-family: 'Inter', sans-serif;
                font-size: 1rem;
                font-weight: 600;
                text-decoration: none;
                display: inline-block;
            ">Start Trading Free →</a>
            <a href="#how-it-works" style="
                background: transparent;
                border: 1px solid rgba(255, 255, 255, 0.2);
                color: #f5f0e8;
                padding: 16px 32px;
                border-radius: 9999px;
                font-family: 'Inter', sans-serif;
                font-size: 1rem;
                font-weight: 500;
                text-decoration: none;
                display: inline-block;
            ">Watch Demo</a>
        </div>
        
        <!-- Stats -->
        <div style="display: flex; gap: 3rem; justify-content: center; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 10px; font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #7a7a8c;">
                <span style="color: #00d4ff;">⚡</span>
                <span>24/7 Automated Trading</span>
            </div>
            <div style="display: flex; align-items: center; gap: 10px; font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #7a7a8c;">
                <span style="color: #00d4ff;">🚀</span>
                <span>0.1s Execution Speed</span>
            </div>
            <div style="display: flex; align-items: center; gap: 10px; font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #7a7a8c;">
                <span style="color: #00d4ff;">✓</span>
                <span>100% Strategy Compliant</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # =========================================================================
    # FEATURES SECTION
    # =========================================================================
    st.markdown('<div id="features"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="padding: 100px 5%; max-width: 1200px; margin: 0 auto;">
        <div style="text-align: center; margin-bottom: 4rem;">
            <div style="font-family: 'Inter', sans-serif; font-size: 0.85rem; color: #d4a84b; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 1rem;">Features</div>
            <h2 style="font-family: 'Playfair Display', Georgia, serif; font-size: clamp(2rem, 5vw, 3rem); font-weight: 600; color: #f5f0e8; margin: 0 0 1rem 0;">
                Start trading <span style="background: linear-gradient(135deg, #f5f0e8 0%, #d4a84b 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">like a pro</span>
            </h2>
            <p style="font-family: 'Inter', sans-serif; font-size: 1.1rem; color: #7a7a8c; max-width: 600px; margin: 0 auto;">
                Everything you need to automate your trading strategies
            </p>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 2rem;">
            <!-- Feature 1 -->
            <div style="background: linear-gradient(180deg, #12131a 0%, #0a0b10 100%); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 2.5rem;">
                <div style="width: 56px; height: 56px; background: #1a1b24; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.8rem; margin-bottom: 1.5rem;">🤖</div>
                <h3 style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.4rem; font-weight: 600; color: #f5f0e8; margin: 0 0 1rem 0;">Automated Execution</h3>
                <p style="font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #7a7a8c; line-height: 1.7; margin: 0 0 1.5rem 0;">
                    Connect your TradingView alerts to Alpaca and let NovAlgo execute trades automatically. No manual intervention needed.
                </p>
                <a href="#" style="display: inline-flex; align-items: center; gap: 8px; font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #00d4ff; text-decoration: none;">Learn more →</a>
            </div>
            
            <!-- Feature 2 -->
            <div style="background: linear-gradient(180deg, #12131a 0%, #0a0b10 100%); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 2.5rem;">
                <div style="width: 56px; height: 56px; background: #1a1b24; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.8rem; margin-bottom: 1.5rem;">⚡</div>
                <h3 style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.4rem; font-weight: 600; color: #f5f0e8; margin: 0 0 1rem 0;">Lightning Fast</h3>
                <p style="font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #7a7a8c; line-height: 1.7; margin: 0 0 1.5rem 0;">
                    Trades execute in under 100 milliseconds. Never miss an entry or exit again with our high-speed infrastructure.
                </p>
                <a href="#" style="display: inline-flex; align-items: center; gap: 8px; font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #00d4ff; text-decoration: none;">Learn more →</a>
            </div>
            
            <!-- Feature 3 -->
            <div style="background: linear-gradient(180deg, #12131a 0%, #0a0b10 100%); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 2.5rem;">
                <div style="width: 56px; height: 56px; background: #1a1b24; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.8rem; margin-bottom: 1.5rem;">🛡️</div>
                <h3 style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.4rem; font-weight: 600; color: #f5f0e8; margin: 0 0 1rem 0;">Bank-Grade Security</h3>
                <p style="font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #7a7a8c; line-height: 1.7; margin: 0 0 1.5rem 0;">
                    Your API keys are encrypted with 256-bit encryption. We never have withdrawal access to your funds.
                </p>
                <a href="#" style="display: inline-flex; align-items: center; gap: 8px; font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #00d4ff; text-decoration: none;">Learn more →</a>
            </div>
            
            <!-- Feature 4 -->
            <div style="background: linear-gradient(180deg, #12131a 0%, #0a0b10 100%); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 2.5rem;">
                <div style="width: 56px; height: 56px; background: #1a1b24; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.8rem; margin-bottom: 1.5rem;">📊</div>
                <h3 style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.4rem; font-weight: 600; color: #f5f0e8; margin: 0 0 1rem 0;">Real-Time Dashboard</h3>
                <p style="font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #7a7a8c; line-height: 1.7; margin: 0 0 1.5rem 0;">
                    Monitor all your positions, P&L, and trade history in real-time with our beautiful analytics dashboard.
                </p>
                <a href="#" style="display: inline-flex; align-items: center; gap: 8px; font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #00d4ff; text-decoration: none;">Learn more →</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # =========================================================================
    # HOW IT WORKS SECTION
    # =========================================================================
    st.markdown('<div id="how-it-works"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="padding: 100px 5%; background: #08090d;">
        <div style="max-width: 1200px; margin: 0 auto;">
            <div style="text-align: center; margin-bottom: 4rem;">
                <div style="font-family: 'Inter', sans-serif; font-size: 0.85rem; color: #d4a84b; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 1rem;">Process</div>
                <h2 style="font-family: 'Playfair Display', Georgia, serif; font-size: clamp(2rem, 5vw, 3rem); font-weight: 600; color: #f5f0e8; margin: 0 0 1rem 0;">
                    How it <span style="background: linear-gradient(135deg, #f5f0e8 0%, #d4a84b 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">works</span>
                </h2>
                <p style="font-family: 'Inter', sans-serif; font-size: 1.1rem; color: #7a7a8c; max-width: 600px; margin: 0 auto;">
                    Get started in minutes with our simple 4-step process
                </p>
            </div>
            
            <div style="display: flex; justify-content: space-between; position: relative; gap: 2rem;">
                <!-- Connecting line -->
                <div style="position: absolute; top: 40px; left: 15%; right: 15%; height: 2px; background: linear-gradient(90deg, #00d4ff, #d4a84b); z-index: 0;"></div>
                
                <!-- Step 1 -->
                <div style="flex: 1; text-align: center; position: relative; z-index: 1;">
                    <div style="width: 80px; height: 80px; background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-family: 'Playfair Display', serif; font-size: 1.8rem; font-weight: 600; color: #0a0b10; margin: 0 auto 1.5rem; box-shadow: 0 0 30px rgba(0, 212, 255, 0.3);">1</div>
                    <div style="width: 60px; height: 60px; background: rgba(212, 168, 75, 0.15); border: 1px solid rgba(212, 168, 75, 0.3); border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; margin: 0 auto 1rem;">👤</div>
                    <h4 style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.2rem; font-weight: 600; color: #f5f0e8; margin: 0 0 0.75rem 0;">Create Account</h4>
                    <p style="font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #7a7a8c; line-height: 1.6; margin: 0;">Sign up for free in seconds. No credit card required.</p>
                </div>
                
                <!-- Step 2 -->
                <div style="flex: 1; text-align: center; position: relative; z-index: 1;">
                    <div style="width: 80px; height: 80px; background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-family: 'Playfair Display', serif; font-size: 1.8rem; font-weight: 600; color: #0a0b10; margin: 0 auto 1.5rem; box-shadow: 0 0 30px rgba(0, 212, 255, 0.3);">2</div>
                    <div style="width: 60px; height: 60px; background: rgba(212, 168, 75, 0.15); border: 1px solid rgba(212, 168, 75, 0.3); border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; margin: 0 auto 1rem;">🔗</div>
                    <h4 style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.2rem; font-weight: 600; color: #f5f0e8; margin: 0 0 0.75rem 0;">Connect Alpaca</h4>
                    <p style="font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #7a7a8c; line-height: 1.6; margin: 0;">Link your Alpaca brokerage account with API keys.</p>
                </div>
                
                <!-- Step 3 -->
                <div style="flex: 1; text-align: center; position: relative; z-index: 1;">
                    <div style="width: 80px; height: 80px; background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-family: 'Playfair Display', serif; font-size: 1.8rem; font-weight: 600; color: #0a0b10; margin: 0 auto 1.5rem; box-shadow: 0 0 30px rgba(0, 212, 255, 0.3);">3</div>
                    <div style="width: 60px; height: 60px; background: rgba(212, 168, 75, 0.15); border: 1px solid rgba(212, 168, 75, 0.3); border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; margin: 0 auto 1rem;">🤖</div>
                    <h4 style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.2rem; font-weight: 600; color: #f5f0e8; margin: 0 0 0.75rem 0;">Configure Bots</h4>
                    <p style="font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #7a7a8c; line-height: 1.6; margin: 0;">Set up trading bots with your symbols and position sizes.</p>
                </div>
                
                <!-- Step 4 -->
                <div style="flex: 1; text-align: center; position: relative; z-index: 1;">
                    <div style="width: 80px; height: 80px; background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-family: 'Playfair Display', serif; font-size: 1.8rem; font-weight: 600; color: #0a0b10; margin: 0 auto 1.5rem; box-shadow: 0 0 30px rgba(0, 212, 255, 0.3);">4</div>
                    <div style="width: 60px; height: 60px; background: rgba(212, 168, 75, 0.15); border: 1px solid rgba(212, 168, 75, 0.3); border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; margin: 0 auto 1rem;">🚀</div>
                    <h4 style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.2rem; font-weight: 600; color: #f5f0e8; margin: 0 0 0.75rem 0;">Automate Trading</h4>
                    <p style="font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #7a7a8c; line-height: 1.6; margin: 0;">Add webhook to TradingView and start trading automatically!</p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # =========================================================================
    # PRICING SECTION
    # =========================================================================
    st.markdown('<div id="pricing"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="padding: 100px 5%; max-width: 1200px; margin: 0 auto;">
        <div style="text-align: center; margin-bottom: 4rem;">
            <div style="font-family: 'Inter', sans-serif; font-size: 0.85rem; color: #d4a84b; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 1rem;">Pricing</div>
            <h2 style="font-family: 'Playfair Display', Georgia, serif; font-size: clamp(2rem, 5vw, 3rem); font-weight: 600; color: #f5f0e8; margin: 0 0 1rem 0;">
                Simple, <span style="background: linear-gradient(135deg, #f5f0e8 0%, #d4a84b 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">transparent</span> pricing
            </h2>
            <p style="font-family: 'Inter', sans-serif; font-size: 1.1rem; color: #7a7a8c; max-width: 600px; margin: 0 auto;">
                Start for free, upgrade when you need more
            </p>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 2rem; max-width: 900px; margin: 0 auto;">
            <!-- Free Beta Card -->
            <div style="background: #0e0f14; border: 1px solid #00d4ff; border-radius: 24px; padding: 3rem 2rem; text-align: center; position: relative; box-shadow: 0 0 40px rgba(0, 212, 255, 0.2);">
                <div style="position: absolute; top: -14px; left: 50%; transform: translateX(-50%); background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%); color: #0a0b10; padding: 6px 16px; border-radius: 9999px; font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">✨ Popular</div>
                <div style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.5rem; font-weight: 600; color: #f5f0e8; margin-bottom: 1rem;">Free Beta</div>
                <div style="font-family: 'Playfair Display', Georgia, serif; font-size: 4rem; font-weight: 600; color: #f5f0e8; margin-bottom: 0.5rem;">$0<span style="font-size: 1rem; color: #7a7a8c; font-family: 'Inter', sans-serif;">/month</span></div>
                <div style="margin: 2rem 0; text-align: left;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem; font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #b0b0c0;">
                        <span style="color: #00d4ff;">✓</span>
                        <span>Unlimited paper trades</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem; font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #b0b0c0;">
                        <span style="color: #00d4ff;">✓</span>
                        <span>Live market execution</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem; font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #b0b0c0;">
                        <span style="color: #00d4ff;">✓</span>
                        <span>TradingView webhooks</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem; font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #b0b0c0;">
                        <span style="color: #00d4ff;">✓</span>
                        <span>Real-time dashboard</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem; font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #b0b0c0;">
                        <span style="color: #00d4ff;">✓</span>
                        <span>Bank-grade encryption</span>
                    </div>
                </div>
                <a href="#get-started" style="display: block; width: 100%; padding: 14px; border-radius: 9999px; font-family: 'Inter', sans-serif; font-size: 0.95rem; font-weight: 600; background: #f5f0e8; color: #0a0b10; text-decoration: none; text-align: center; box-sizing: border-box;">Start Free</a>
            </div>
            
            <!-- Pro Card -->
            <div style="background: #0e0f14; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 24px; padding: 3rem 2rem; text-align: center; position: relative;">
                <div style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.5rem; font-weight: 600; color: #f5f0e8; margin-bottom: 1rem;">Pro</div>
                <div style="font-family: 'Playfair Display', Georgia, serif; font-size: 4rem; font-weight: 600; color: #f5f0e8; margin-bottom: 0.5rem;">$29<span style="font-size: 1rem; color: #7a7a8c; font-family: 'Inter', sans-serif;">/month</span></div>
                <div style="margin: 2rem 0; text-align: left;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem; font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #b0b0c0;">
                        <span style="color: #00d4ff;">✓</span>
                        <span>Everything in Free</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem; font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #b0b0c0;">
                        <span style="color: #00d4ff;">✓</span>
                        <span>Priority execution</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem; font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #b0b0c0;">
                        <span style="color: #00d4ff;">✓</span>
                        <span>Advanced analytics</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem; font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #b0b0c0;">
                        <span style="color: #00d4ff;">✓</span>
                        <span>Outgoing webhooks</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem; font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #b0b0c0;">
                        <span style="color: #00d4ff;">✓</span>
                        <span>Priority support</span>
                    </div>
                </div>
                <button style="display: block; width: 100%; padding: 14px; border-radius: 9999px; font-family: 'Inter', sans-serif; font-size: 0.95rem; font-weight: 600; background: #1a1b24; color: #7a7a8c; border: none; cursor: not-allowed;">Coming Soon</button>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # =========================================================================
    # FAQ SECTION
    # =========================================================================
    st.markdown('<div id="faq"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="padding: 100px 5%; background: #08090d;">
        <div style="max-width: 800px; margin: 0 auto;">
            <div style="text-align: center; margin-bottom: 4rem;">
                <div style="font-family: 'Inter', sans-serif; font-size: 0.85rem; color: #d4a84b; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 1rem;">FAQ</div>
                <h2 style="font-family: 'Playfair Display', Georgia, serif; font-size: clamp(2rem, 5vw, 3rem); font-weight: 600; color: #f5f0e8; margin: 0;">
                    Get to know all <span style="background: linear-gradient(135deg, #f5f0e8 0%, #d4a84b 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">the benefits</span>
                </h2>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # FAQ using Streamlit expanders
    with st.container():
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            with st.expander("What is NovAlgo?"):
                st.write("""
                NovAlgo is an automated trading platform that connects TradingView to Alpaca brokerage.
                When your TradingView strategy generates a signal, NovAlgo receives the webhook and 
                automatically executes the trade through your Alpaca account.
                """)
            
            with st.expander("Is my money safe? Can you withdraw my funds?"):
                st.write("""
                Your money is completely safe. NovAlgo never has access to withdraw your funds. 
                We only store encrypted API keys with trading permissions - no withdrawal access.
                Your money stays in your SIPC-protected Alpaca account.
                """)
            
            with st.expander("Do I need any coding experience?"):
                st.write("""
                No coding required! If you can create an alert in TradingView, you can use NovAlgo.
                Just copy your webhook URL and paste it into TradingView's alert settings.
                """)
            
            with st.expander("Can I practice with paper trading first?"):
                st.write("""
                Absolutely! We recommend starting with paper trading. Alpaca provides free paper
                trading accounts with real-time data so you can test your strategies risk-free.
                """)
            
            with st.expander("How fast are trade executions?"):
                st.write("""
                Trades typically execute in under 100 milliseconds from when we receive the webhook.
                Market orders fill immediately at the best available price through Alpaca.
                """)
            
            with st.expander("What happens if NovAlgo goes down?"):
                st.write("""
                Your existing positions remain safely in your Alpaca account. You can always 
                manage your positions directly through Alpaca's app or website. We maintain 
                99.9% uptime with redundant infrastructure.
                """)
    
    # =========================================================================
    # CTA SECTION
    # =========================================================================
    st.markdown("""
    <div style="text-align: center; padding: 100px 5%; background: #08090d; position: relative; overflow: hidden;">
        <h2 style="font-family: 'Playfair Display', Georgia, serif; font-size: clamp(2rem, 5vw, 3rem); font-weight: 600; color: #f5f0e8; margin: 0 0 1rem 0;">Discover the power of automation</h2>
        <p style="font-family: 'Inter', sans-serif; font-size: 1.1rem; color: #7a7a8c; margin: 0 0 2rem 0;">Join thousands of traders automating their strategies with NovAlgo</p>
        <a href="#get-started" style="background: #f5f0e8; color: #0a0b10; padding: 16px 32px; border-radius: 9999px; font-family: 'Inter', sans-serif; font-size: 1rem; font-weight: 600; text-decoration: none; display: inline-block;">Start Trading Free →</a>
    </div>
    """, unsafe_allow_html=True)
    
    # =========================================================================
    # AUTH SECTION
    # =========================================================================
    st.markdown('<div id="get-started"></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="font-family: 'Playfair Display', Georgia, serif; font-size: 2rem; color: #f5f0e8; margin-bottom: 0.5rem;">
                Get Started
            </h2>
            <p style="font-family: 'Inter', sans-serif; color: #7a7a8c;">
                Create your account or sign in
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Sign In", "Create Account"])
        
        with tab1:
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                submit = st.form_submit_button("Sign In", use_container_width=True, type="primary")
                
                if submit:
                    if not username or not password:
                        st.error("Please enter both username and password")
                    else:
                        with st.spinner("Signing in..."):
                            result = UserDB.authenticate_user(username, password)
                            if result['success']:
                                st.session_state['authenticated'] = True
                                st.session_state['user'] = result['user']
                                st.success(f"Welcome back, {result['user']['username']}!")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(result.get('error', 'Invalid credentials'))
        
        with tab2:
            with st.form("register_form", clear_on_submit=False):
                new_username = st.text_input("Username", placeholder="Choose a username", key="reg_user")
                new_email = st.text_input("Email", placeholder="your@email.com", key="reg_email")
                new_password = st.text_input("Password", type="password", placeholder="Create a password", key="reg_pass")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password", key="reg_confirm")
                
                agree = st.checkbox("I agree to the Terms of Service and Privacy Policy")
                
                register = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                
                if register:
                    if not all([new_username, new_email, new_password, confirm_password]):
                        st.error("Please fill in all fields")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif not agree:
                        st.error("Please agree to the Terms of Service")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        with st.spinner("Creating account..."):
                            result = UserDB.register_user(new_username, new_email, new_password)
                            if result['success']:
                                st.success("Account created! Please sign in.")
                                st.balloons()
                            else:
                                st.error(result.get('error', 'Registration failed'))
    
    # =========================================================================
    # FOOTER
    # =========================================================================
    st.markdown("""
    <div style="background: #0a0b10; border-top: 1px solid rgba(255, 255, 255, 0.1); padding: 60px 5% 30px;">
        <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 4rem; max-width: 1200px; margin: 0 auto 3rem;">
            <div>
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem;">
                    <div style="width: 36px; height: 36px; background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">⚡</div>
                    <span style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.5rem; font-weight: 600; color: #f5f0e8;">NovAlgo</span>
                </div>
                <p style="font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #7a7a8c; line-height: 1.7;">
                    Automated trading platform connecting TradingView strategies to Alpaca execution. Trade smarter, not harder.
                </p>
            </div>
            <div>
                <div style="font-family: 'Inter', sans-serif; font-size: 0.9rem; font-weight: 600; color: #f5f0e8; margin-bottom: 1.5rem; text-transform: uppercase; letter-spacing: 1px;">Product</div>
                <ul style="list-style: none; padding: 0; margin: 0;">
                    <li style="margin-bottom: 0.75rem;"><a href="#features" style="font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #7a7a8c; text-decoration: none;">Features</a></li>
                    <li style="margin-bottom: 0.75rem;"><a href="#pricing" style="font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #7a7a8c; text-decoration: none;">Pricing</a></li>
                    <li style="margin-bottom: 0.75rem;"><a href="#how-it-works" style="font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #7a7a8c; text-decoration: none;">How it Works</a></li>
                    <li style="margin-bottom: 0.75rem;"><a href="#faq" style="font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #7a7a8c; text-decoration: none;">FAQ</a></li>
                </ul>
            </div>
            <div>
                <div style="font-family: 'Inter', sans-serif; font-size: 0.9rem; font-weight: 600; color: #f5f0e8; margin-bottom: 1.5rem; text-transform: uppercase; letter-spacing: 1px;">Company</div>
                <ul style="list-style: none; padding: 0; margin: 0;">
                    <li style="margin-bottom: 0.75rem;"><a href="#" style="font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #7a7a8c; text-decoration: none;">About</a></li>
                    <li style="margin-bottom: 0.75rem;"><a href="#" style="font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #7a7a8c; text-decoration: none;">Blog</a></li>
                    <li style="margin-bottom: 0.75rem;"><a href="#" style="font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #7a7a8c; text-decoration: none;">Careers</a></li>
                    <li style="margin-bottom: 0.75rem;"><a href="#" style="font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #7a7a8c; text-decoration: none;">Contact</a></li>
                </ul>
            </div>
            <div>
                <div style="font-family: 'Inter', sans-serif; font-size: 0.9rem; font-weight: 600; color: #f5f0e8; margin-bottom: 1.5rem; text-transform: uppercase; letter-spacing: 1px;">Legal</div>
                <ul style="list-style: none; padding: 0; margin: 0;">
                    <li style="margin-bottom: 0.75rem;"><a href="#" style="font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #7a7a8c; text-decoration: none;">Terms of Service</a></li>
                    <li style="margin-bottom: 0.75rem;"><a href="#" style="font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #7a7a8c; text-decoration: none;">Privacy Policy</a></li>
                    <li style="margin-bottom: 0.75rem;"><a href="#" style="font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #7a7a8c; text-decoration: none;">Risk Disclosure</a></li>
                </ul>
            </div>
        </div>
        <div style="border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 2rem; max-width: 1200px; margin: 0 auto;">
            <p style="font-family: 'Inter', sans-serif; font-size: 0.85rem; color: #5a5a6c; margin-bottom: 1rem;">© 2024 NovAlgo. All rights reserved.</p>
            <p style="font-family: 'Inter', sans-serif; font-size: 0.8rem; color: #4a4a5c; line-height: 1.6;">
                Trading involves substantial risk of loss. Past performance is not indicative of future results. Automated trading systems carry additional risks. Only trade with money you can afford to lose.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_register_page():
    """Display modern registration page"""
    # Background gradient
    st.markdown("""
    <div style='position: fixed; top: 0; left: 0; right: 0; bottom: 0; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                z-index: -1;'></div>
    """, unsafe_allow_html=True)
    
    # Center the registration card
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Registration Card
        st.markdown("""
        <div style='background: white; border-radius: 20px; padding: 3rem; 
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3); margin: 2rem 0;'>
            <h1 style='text-align: center; font-size: 2.5rem; margin-bottom: 0.5rem; 
                       background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                       background-clip: text;'>
                📈 DashTrade
            </h1>
            <p style='text-align: center; color: #666; margin-bottom: 2rem; font-size: 1rem;'>
                Create your account and start trading today
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Registration Form
        with st.form("register_form", clear_on_submit=False):
            st.markdown("<div style='margin-bottom: 1.5rem;'>", unsafe_allow_html=True)
            username = st.text_input(
                "👤 Username", 
                help="Minimum 3 characters",
                placeholder="Choose a username"
            )
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div style='margin-bottom: 1.5rem;'>", unsafe_allow_html=True)
            email = st.text_input(
                "📧 Email",
                placeholder="your.email@example.com"
            )
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div style='margin-bottom: 1.5rem;'>", unsafe_allow_html=True)
            full_name = st.text_input(
                "👨‍💼 Full Name (optional)",
                placeholder="Your full name"
            )
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div style='margin-bottom: 1.5rem;'>", unsafe_allow_html=True)
            password = st.text_input(
                "🔒 Password", 
                type="password", 
                help="Minimum 6 characters",
                placeholder="Create a strong password"
            )
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div style='margin-bottom: 1.5rem;'>", unsafe_allow_html=True)
            password_confirm = st.text_input(
                "🔒 Confirm Password", 
                type="password",
                placeholder="Re-enter your password"
            )
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div style='margin-bottom: 1.5rem;'>", unsafe_allow_html=True)
            admin_code = st.text_input(
                "🔑 Admin Activation Code (optional)", 
                help="Enter a 16-digit admin code to create an admin account. Leave blank for regular user account.",
                placeholder="1234-5678-9012-3456",
                max_chars=19
            )
            st.markdown("</div>", unsafe_allow_html=True)
            
            submit = st.form_submit_button(
                "✨ Create Account", 
                use_container_width=True,
                type="primary"
            )

            if submit:
                if not username or not email or not password:
                    st.markdown("""
                    <div class='error-message'>
                        <strong>⚠️ Error:</strong> Please fill in all required fields (Username, Email, Password)
                    </div>
                    """, unsafe_allow_html=True)
                elif password != password_confirm:
                    st.markdown("""
                    <div class='error-message'>
                        <strong>⚠️ Error:</strong> Passwords do not match. Please try again.
                    </div>
                    """, unsafe_allow_html=True)
                elif len(password) < 6:
                    st.markdown("""
                    <div class='error-message'>
                        <strong>⚠️ Error:</strong> Password must be at least 6 characters long.
                    </div>
                    """, unsafe_allow_html=True)
                elif len(username) < 3:
                    st.markdown("""
                    <div class='error-message'>
                        <strong>⚠️ Error:</strong> Username must be at least 3 characters long.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Process admin code if provided
                    admin_code_to_use = None
                    if admin_code and admin_code.strip():
                        admin_code_clean = admin_code.strip().replace('-', '').replace(' ', '')
                        # Validate format
                        if len(admin_code_clean) != 16 or not admin_code_clean.isdigit():
                            st.markdown("""
                            <div class='error-message'>
                                <strong>⚠️ Error:</strong> Admin code must be exactly 16 digits (e.g., 1234-5678-9012-3456)
                            </div>
                            """, unsafe_allow_html=True)
                            admin_code_to_use = None  # Don't use invalid code
                        else:
                            # Format with dashes for consistency
                            admin_code_to_use = f"{admin_code_clean[:4]}-{admin_code_clean[4:8]}-{admin_code_clean[8:12]}-{admin_code_clean[12:16]}"
                    
                    # Create account
                    with st.spinner("✨ Creating your account..."):
                        try:
                            result = UserDB.register_user(
                                username, 
                                email, 
                                password, 
                                full_name,
                                admin_code=admin_code_to_use
                            )
                        except Exception as e:
                            error_msg = str(e)
                            # Check if it's a database connection error
                            if 'connection' in error_msg.lower() or 'localhost' in error_msg.lower():
                                st.markdown("""
                                <div class='error-message'>
                                    <strong>❌ Database Connection Error:</strong> Cannot connect to database.
                                    <br><br>This usually means:
                                    <br>• You're testing locally but DATABASE_URL is not set
                                    <br>• Railway deployment hasn't finished yet
                                    <br>• Database service is not running
                                    <br><br>💡 Make sure you're accessing the Railway-deployed app, not running locally.
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div class='error-message'>
                                    <strong>❌ Registration Failed:</strong> {error_msg}
                                </div>
                                """, unsafe_allow_html=True)
                            result = {'success': False, 'error': error_msg}
                        
                        if result['success']:
                            role_msg = "admin" if result.get('role') == 'admin' else "user"
                            st.markdown(f"""
                            <div class='success-message'>
                                <strong>✅ Success!</strong> Account created successfully as <strong>{role_msg}</strong>! 
                                <br>You can now login with your credentials.
                            </div>
                            """, unsafe_allow_html=True)
                            st.balloons()
                            st.session_state['show_register'] = False
                            # Small delay to show success message
                            import time
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            error_msg = result.get('error', 'Registration failed')
                            st.markdown(f"""
                            <div class='error-message'>
                                <strong>❌ Registration Failed:</strong> {error_msg}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Provide helpful hints
                            if 'already exists' in error_msg.lower():
                                st.markdown("""
                                <div class='info-message'>
                                    <strong>💡 Tip:</strong> This username or email is already registered. 
                                    Try logging in instead, or use a different username/email.
                                </div>
                                """, unsafe_allow_html=True)
                            elif 'admin code' in error_msg.lower() or 'activation' in error_msg.lower():
                                entered_code = admin_code if admin_code else '(none)'
                                st.markdown(f"""
                                <div class='info-message'>
                                    <strong>💡 Admin Code Help:</strong>
                                    <br>• You entered: <strong>{entered_code}</strong>
                                    <br>• Admin code must match the ADMIN_CODE variable in Railway
                                    <br>• If ADMIN_CODE is not set in Railway, use default: <strong>1234-5678-9012-3456</strong>
                                    <br>• Codes work with or without dashes (e.g., 1234-5678-9012-3456 or 1234567890123456)
                                    <br>• Leave blank to create a regular user account
                                    <br><br>🔍 Check Railway Variables tab to see what ADMIN_CODE is set to.
                                </div>
                                """, unsafe_allow_html=True)
        
        # Back to login link
        st.markdown("""
        <div style='text-align: center; margin-top: 2rem; padding-top: 1.5rem; 
                    border-top: 1px solid #e0e0e0;'>
            <p style='color: #666; margin-bottom: 0.5rem; font-size: 0.95rem;'>
                Already have an account?
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("← Back to Login", use_container_width=True, type="secondary"):
            st.session_state['show_register'] = False
            st.rerun()

def main():
    # Get user_id from session
    user_id = st.session_state['user']['id']
    username = st.session_state['user']['username']

    # Header
    st.markdown('<h1 class="main-header">🚀 NovAlgo</h1>', unsafe_allow_html=True)
    st.markdown("### AI-Powered Trading Signals & Automation")
    st.markdown("---")

    # Load user preferences
    prefs = PreferencesDB.get_all_preferences(user_id)

    # Sidebar
    with st.sidebar:
        st.title("🚀 NovAlgo")
        st.caption(f"👤 {username}")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        st.markdown("---")
        
        # Data Source Selection
        st.subheader("🔌 Data Source")
        data_source = st.radio(
            "Select Provider",
            ["Yahoo Finance", "Alpha Vantage"],
            index=0,
            help="Yahoo Finance: Unlimited usage, 15-min delay | Alpha Vantage: Real-time, 25 calls/day limit"
        )
        
        # Store in session state
        if 'data_source' not in st.session_state or st.session_state.data_source != data_source:
            st.session_state.data_source = data_source
            # Clear cache when switching sources
            if data_source != st.session_state.get('previous_source'):
                st.cache_data.clear()
                st.session_state.previous_source = data_source
        
        # Display source info
        source_key = "yahoo" if data_source == "Yahoo Finance" else "alpha_vantage"
        if source_key == "yahoo":
            st.info("📊 **Yahoo Finance** - Unlimited usage, 15-min delay for free tier")
        else:
            st.warning("⚡ **Alpha Vantage** - Real-time data, 25 API calls/day limit")
        
        st.markdown("---")

        # Mode selection - add Admin Panel if user is admin
        modes = ["Single Stock Analysis", "Portfolio Dashboard", "Multi-Stock Comparison", "Backtesting", "Strategy Builder", "Alert Manager", "🤖 AI Assistant"]

        # Check if user is admin
        if st.session_state['user'].get('role') in ['admin', 'superadmin']:
            modes.append("👑 Admin Panel")

        mode = st.radio("Mode", modes, index=0)
        
        st.markdown("---")
        
        if mode == "Single Stock Analysis":
            st.title("⚙️ Analysis Settings")
            
            # Stock symbol input
            st.subheader("📈 Stock Selection")
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
                stock_name = get_stock_info(symbol, source_key)
                if WatchlistDB.add_stock(user_id, symbol, stock_name):
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
        watchlist = WatchlistDB.get_all_stocks(user_id)

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
                        WatchlistDB.remove_stock(user_id, stock['symbol'])
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
        # Display active data source badge
        source_key = "yahoo" if st.session_state.data_source == "Yahoo Finance" else "alpha_vantage"
        if source_key == "yahoo":
            st.success(f"📊 **Data Source:** Yahoo Finance (Unlimited)")
        else:
            st.warning(f"⚡ **Data Source:** Alpha Vantage (Real-time, 25 calls/day)")
        
        st.markdown("---")
        
        # Run single stock analysis (same as original app)
        if fetch_button or 'analysis_results' in st.session_state:
            if fetch_button:
                with st.spinner(f"Fetching data for {symbol} from {st.session_state.data_source}..."):
                    df, error = fetch_stock_data(symbol, period, interval, source_key)
                    
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
            
            # Signal Activity Dashboard
            st.markdown("---")
            st.subheader("⚡ Signal Activity Dashboard")
            
            analyzer = results['analyzer']
            
            # Get signal counts for different periods
            signals_1h = analyzer.count_signals_by_period(hours_back=1)
            signals_4h = analyzer.count_signals_by_period(hours_back=4)
            signals_24h = analyzer.count_signals_by_period(hours_back=24)
            
            # Display signal counts in columns
            activity_cols = st.columns([2, 2, 2, 3])
            
            with activity_cols[0]:
                st.markdown("### 🟢 LONG Signals")
                st.metric("Past 1 Hour", signals_1h['long_count'])
                st.metric("Past 4 Hours", signals_4h['long_count'])
                st.metric("Past 24 Hours", signals_24h['long_count'])
            
            with activity_cols[1]:
                st.markdown("### 🔴 SHORT Signals")
                st.metric("Past 1 Hour", signals_1h['short_count'])
                st.metric("Past 4 Hours", signals_4h['short_count'])
                st.metric("Past 24 Hours", signals_24h['short_count'])
            
            with activity_cols[2]:
                st.markdown("### 📊 Total Activity")
                st.metric("Past 1 Hour", signals_1h['total_signals'])
                st.metric("Past 4 Hours", signals_4h['total_signals'])
                st.metric("Past 24 Hours", signals_24h['total_signals'])
            
            with activity_cols[3]:
                st.markdown("### ⚡ Current Signal")
                latest_signal = signals_24h['latest_signal']
                if latest_signal:
                    signal_type = latest_signal['type']
                    signal_time = latest_signal['timestamp']
                    signal_price = latest_signal['price']
                    
                    # Calculate how long ago
                    time_diff = df.index[-1] - signal_time
                    hours_ago = time_diff.total_seconds() / 3600
                    
                    if hours_ago < 1:
                        time_str = f"{int(hours_ago * 60)} minutes ago"
                    elif hours_ago < 24:
                        time_str = f"{int(hours_ago)} hours ago"
                    else:
                        time_str = f"{int(hours_ago / 24)} days ago"
                    
                    signal_color = "🟢" if signal_type == "LONG" else "🔴"
                    st.markdown(f"#### {signal_color} **{signal_type}**")
                    st.write(f"**{time_str}**")
                    st.write(f"Price: ${signal_price:.2f}")
                    st.write(f"Strength: {latest_signal['strength'].upper()}")
                else:
                    st.info("No recent signals")
            
            # Signal Timeline Table
            if signals_24h['signals']:
                with st.expander(f"📋 Detailed Signal Timeline (Last 24 Hours) - {len(signals_24h['signals'])} signals"):
                    timeline_data = []
                    for sig in reversed(signals_24h['signals']):  # Most recent first
                        time_diff = df.index[-1] - sig['timestamp']
                        hours_ago = time_diff.total_seconds() / 3600
                        
                        if hours_ago < 1:
                            time_ago = f"{int(hours_ago * 60)}m ago"
                        elif hours_ago < 24:
                            time_ago = f"{int(hours_ago)}h ago"
                        else:
                            time_ago = f"{int(hours_ago / 24)}d ago"
                        
                        timeline_data.append({
                            'Time': sig['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                            'Time Ago': time_ago,
                            'Signal': sig['type'],
                            'Price': f"${sig['price']:.2f}",
                            'Indicator': sig['indicator'],
                            'Strength': sig['strength'].upper()
                        })
                    
                    timeline_df = pd.DataFrame(timeline_data)
                    st.dataframe(timeline_df, use_container_width=True, hide_index=True)
            
            # News Sentiment Analysis
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
            
            # Tabs for detailed analysis
            st.markdown("---")
            st.subheader("📊 Detailed Analysis")
            
            tab1, tab2 = st.tabs(["📈 Interactive Chart", "📋 Summary"])
            
            with tab1:
                st.markdown("### Price Chart with Signal Markers")
                st.caption("Green 'Long' and Red 'Short' labels show QQE trading signals")
                
                # Create and display chart with signal annotations
                chart_fig = create_candlestick_chart_with_signals(df, results['symbol'])
                st.plotly_chart(chart_fig, use_container_width=True)
            
            with tab2:
                st.markdown("### Analysis Summary")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Trend Analysis")
                    trend_status = latest.get('ma_cloud_trend', 'unknown')
                    if trend_status == 'bullish':
                        st.success("📈 **Bullish Trend** - Price above MA Cloud")
                    elif trend_status == 'bearish':
                        st.error("📉 **Bearish Trend** - Price below MA Cloud")
                    else:
                        st.info("⚪ **Neutral Trend** - Unclear direction")
                    
                    # EMA positions
                    if 'ema_20' in latest and 'ema_50' in latest:
                        if latest['ema_20'] > latest['ema_50']:
                            st.success("✅ EMA 20 > EMA 50 (Bullish)")
                        else:
                            st.error("⚠️ EMA 20 < EMA 50 (Bearish)")
                
                with col2:
                    st.markdown("#### Signal Summary")
                    st.metric("Total Signals (24h)", signals_24h['total_signals'])
                    st.metric("Long Signals (24h)", signals_24h['long_count'])
                    st.metric("Short Signals (24h)", signals_24h['short_count'])
                    
                    if signals_24h['latest_signal']:
                        signal_type = signals_24h['latest_signal']['type']
                        if signal_type == 'LONG':
                            st.success(f"Most Recent: {signal_type}")
                        else:
                            st.error(f"Most Recent: {signal_type}")
        
        else:
            st.info("👈 Enter a stock symbol and click 'Fetch & Analyze' to get started!")
    
    elif mode == "Portfolio Dashboard":
        st.subheader("💼 Portfolio Dashboard")
        st.info("📡 **Data Source:** Yahoo Finance (15-min delay for free tier) | **Analysis:** Last 5 days, 1-day interval")

        watchlist = WatchlistDB.get_all_stocks(user_id)
        
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
                stock_alerts = AlertsDB.get_active_alerts(user_id, stock['symbol'])
                
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
                                        AlertsDB.trigger_alert(user_id, db_alert['id'])
                        except:
                            pass
            
            if triggered_alerts:
                st.warning(f"🔔 {len(triggered_alerts)} alert(s) triggered!")
                for alert in triggered_alerts:
                    st.info(f"**{alert['symbol']}** - {alert['condition']}")
            else:
                active_count = len(AlertsDB.get_active_alerts(user_id))
                if active_count > 0:
                    st.success(f"✅ {active_count} active alert(s) - No triggers")
                else:
                    st.info("No alerts configured. Go to Alert Manager to create alerts.")
    
    elif mode == "Multi-Stock Comparison":
        st.subheader("📊 Multi-Stock Comparison")

        watchlist = WatchlistDB.get_all_stocks(user_id)
        
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
                # Get data source from session state
                source_key = "yahoo" if st.session_state.get('data_source', 'Yahoo Finance') == "Yahoo Finance" else "alpha_vantage"
                
                # Create comparison analyzer with data source
                analyzer = ComparisonAnalyzer(selected_stocks, period=comparison_period, interval='1d', data_source=source_key)
                
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
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            bt_symbol = st.text_input("Stock Symbol for Backtest", value="AAPL").upper()
        
        with col2:
            bt_interval = st.selectbox(
                "Interval",
                ["5m", "15m", "30m", "45m", "1h", "1d"],
                index=5,
                help="Shorter intervals = more signals, longer data needed"
            )
        
        with col3:
            # Smart period recommendations based on interval
            if bt_interval == "5m":
                period_options = ["1d", "5d"]
                default_idx = 0
            elif bt_interval == "15m":
                period_options = ["1d", "5d", "1mo"]
                default_idx = 1
            elif bt_interval == "30m":
                period_options = ["5d", "1mo", "3mo"]
                default_idx = 1
            elif bt_interval == "45m":
                period_options = ["5d", "1mo", "3mo"]
                default_idx = 1
            elif bt_interval == "1h":
                period_options = ["1mo", "3mo", "6mo"]
                default_idx = 1
            else:  # 1d
                period_options = ["1mo", "3mo", "6mo", "1y", "2y", "5y"]
                default_idx = 3
            
            bt_period = st.selectbox(
                "Period",
                period_options,
                index=default_idx,
                help="Historical data to analyze"
            )
        
        
        st.markdown("### Backtest Parameters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            initial_capital = st.number_input("Initial Capital ($)", value=10000.0, step=1000.0)
            position_size = st.slider("Position Size (%)", 5, 100, 10, 
                                     help="Percentage of capital per trade (100% for long-only recommended)")
        
        with col2:
            use_stop_loss = st.checkbox("Use Stop Loss", value=True)
            stop_loss_pct = st.slider("Stop Loss (%)", 1.0, 10.0, 2.0, 0.5) if use_stop_loss else 2.0
        
        with col3:
            use_take_profit = st.checkbox("Use Take Profit", value=False)
            take_profit_pct = st.slider("Take Profit (%)", 2.0, 20.0, 5.0, 0.5) if use_take_profit else 5.0
        
        st.markdown("### Strategy Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            strategy_mode = st.radio(
                "Strategy Mode",
                ["Long Only", "Long & Short", "Short Only"],
                index=0,  # Default to Long Only (performs 22x better!)
                help="Long Only: Buy on long signals, sell on short signals (recommended for trending markets)"
            )
            
            # Map display names to internal values
            mode_map = {
                "Long Only": "long_only",
                "Long & Short": "long_short",
                "Short Only": "short_only"
            }
            strategy_mode_value = mode_map[strategy_mode]
        
        with col2:
            use_trend_filter = st.checkbox(
                "Use Trend Filter",
                value=False,
                help="Filter signals by 200 EMA trend (only long in uptrend, only short in downtrend)"
            )
            
            if use_trend_filter:
                trend_ema_period = st.slider("Trend EMA Period", 50, 200, 200, 10,
                                             help="EMA period for trend detection (200 is standard)")
            else:
                trend_ema_period = 200
        
        st.markdown("### Strategy Selection")
        
        strategy_type = st.radio("Strategy", ["QQE Signals", "NovAlgo Fast Signals [Custom]", "EMA Crossover", "MA Cloud Trend"], horizontal=True)

        
        # Show info about selected interval
        if bt_interval in ["5m", "15m", "30m", "45m"]:
            st.info(f"📊 **Intraday Backtesting**: Testing {bt_interval} signals over {bt_period}. More signals = more realistic results!")
        
        # Get data source from session state
        source_key = "yahoo" if st.session_state.get('data_source', 'Yahoo Finance') == "Yahoo Finance" else "alpha_vantage"
        
        if st.button("🚀 Run Backtest", type="primary"):
            with st.spinner(f"Running backtest for {bt_symbol} on {bt_interval} interval..."):
                df, error = fetch_stock_data(bt_symbol, bt_period, bt_interval, source_key)
                
                if error or df is None or len(df) < 50:
                    st.error("❌ Error fetching data or insufficient data for backtesting")
                    return
                
                analyzer = TechnicalAnalyzer(df)
                analyzer.calculate_emas()
                analyzer.calculate_ma_cloud()
                
                # Logic for strategy selection
                if strategy_type == "NovAlgo Fast Signals [Custom]":
                    st.toast("Running Custom Pine Script Logic...")
                    analyzer.add_novalgo_fast_signals()
                else:
                    # Default QQE
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

        watchlist = WatchlistDB.get_all_stocks(user_id)
        
        if not watchlist:
            st.warning("📋 No stocks in watchlist. Add stocks first to create alerts.")
            return
        
        tab1, tab2, tab3 = st.tabs(["➕ Create Alert", "📋 Manage Alerts", "⚙️ Notification Settings"])
        
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
                                          ["QQE Long Signal", "QQE Short Signal", "NovAlgo Fast Long [Custom]", "NovAlgo Fast Short [Custom]"])
                
                if st.button("Create Alert", type="primary"):
                    if "NovAlgo Fast" in signal_type:
                        alert_type = 'fast_qqe_long' if "Long" in signal_type else 'fast_qqe_short'
                    else:
                        alert_type = 'qqe_long_signal' if signal_type == "QQE Long Signal" else 'qqe_short_signal'
                    
                    condition_text = f"{signal_type} on {alert_symbol}"

                    if AlertsDB.add_alert(user_id, alert_symbol, alert_type, condition_text):
                        st.success(f"✅ Alert created for {alert_symbol}")
                        st.rerun()
                    else:
                        st.error("Failed to create alert")
            
            elif alert_category == "Trend Change":
                trend_direction = st.selectbox("Direction", ["Bullish", "Bearish"])
                
                if st.button("Create Alert", type="primary"):
                    alert_type = 'trend_change_bullish' if trend_direction == "Bullish" else 'trend_change_bearish'
                    condition_text = f"Trend changes to {trend_direction} on {alert_symbol}"

                    if AlertsDB.add_alert(user_id, alert_symbol, alert_type, condition_text):
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

                    if AlertsDB.add_alert(user_id, alert_symbol, f"{alert_type}:{price_level}", condition_text):
                        st.success(f"✅ Alert created for {alert_symbol}")
                        st.rerun()
                    else:
                        st.error("Failed to create alert")
            
            elif alert_category == "EMA Crossover":
                cross_direction = st.selectbox("Crossover Type", ["EMA 20 crosses above EMA 50", "EMA 20 crosses below EMA 50"])
                
                if st.button("Create Alert", type="primary"):
                    alert_type = 'ema_crossover' if 'above' in cross_direction else 'ema_crossunder'
                    condition_text = f"{cross_direction} on {alert_symbol}"

                    if AlertsDB.add_alert(user_id, alert_symbol, alert_type, condition_text):
                        st.success(f"✅ Alert created for {alert_symbol}")
                        st.rerun()
                    else:
                        st.error("Failed to create alert")
        
        with tab2:
            st.markdown("### Active Alerts")

            all_alerts = AlertsDB.get_active_alerts(user_id)
            
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
                        
                        if AlertsDB.delete_alert(user_id, alert_id):
                            st.success("Alert deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete alert")
            else:
                st.info("No alerts configured. Create your first alert using the form above.")

        with tab3:
            st.markdown("### 📧 Email Notifications")
            st.caption("Receive instant email alerts when your trading signals trigger.")
            
            # Fetch fresh user data to get current settings
            current_user = UserDB.get_user_by_id(user_id)
            
            if current_user:
                email = current_user.get('email', 'Unknown')
                is_enabled = current_user.get('email_enabled', False)
                
                st.info(f"Updates will be sent to: **{email}**")
                
                # Toggle
                new_state = st.toggle("Enable Email Alerts", value=is_enabled)
                
                if new_state != is_enabled:
                    if UserDB.update_email_preference(user_id, new_state):
                        st.success(f"Email notifications {'enabled' if new_state else 'disabled'}!")
                        st.rerun()
                    else:
                        st.error("Failed to update preference")
            else:
                st.error("Could not load user settings")


    # ==========================================
    # 7. AI ASSISTANT
    # ==========================================
    elif mode == "🤖 AI Assistant":
        st.header("🤖 AI Trading Assistant")
        st.caption("Powered by Claude 3.5 Sonnet with Alpaca Tool Integration")
        
        # User is guaranteed to be logged in if we are here (checked in main)
        user_id = st.session_state['user']['id']
        
        # Check if user has an API key configured
        existing_key = LLMKeysDB.get_key(user_id)
        
        # Tabs for Chat and Settings
        tab_chat, tab_settings = st.tabs(["💬 Chat", "🔑 API Login"])
        
        with tab_settings:
            st.subheader("Connect Your Claude Account")
            st.markdown("""
            To use the AI Assistant, please **login** with your Anthropic API Key.
            This connects DashTrade to your personal Claude account.
            
            [Get my API Key](https://console.anthropic.com/)
            """)
            
            with st.form("llm_key_form"):
                api_key_input = st.text_input("Enter Anthropic API Key (sk-ant-...)", 
                                             type="password", 
                                             value=existing_key if existing_key else "")
                save_btn = st.form_submit_button("Login / Save Key")
                
                if save_btn:
                    if api_key_input.startswith("sk-"):
                        if LLMKeysDB.save_key(user_id, api_key_input):
                            st.success("✅ Successfully connected to Claude! You can now use the Chat tab.")
                            st.rerun()
                        else:
                            st.error("Failed to save API Key.")
                    else:
                        st.error("Invalid API Key format.")
        
        with tab_chat:
            if not existing_key:
                st.info("👋 **Welcome to DashTrade AI!**")
                st.warning("🔒 **Login Required**: Please go to the **🔑 API Login** tab and enter your Anthropic API Key to start chatting.")
            else:
                # Add a sidebar for AI Capabilities
                with st.sidebar:
                    st.markdown("### 🤖 Help & Commands")
                    with st.expander("Show AI Capabilities", expanded=True):
                        st.markdown("""
                        **Account Tools:**
                        - "What's my balance?"
                        - "Am I in the green today?"
                        
                        **Market Data:**
                        - "What's the price of AAPL?"
                        - "Is the market open?"
                        
                        **Portfolio:**
                        - "Show my positions."
                        - "Which position is performing best?"
                        
                        **Trading (Paper):**
                        - "Buy 10 shares of SPY"
                        - "Close my position in TSLA"
                        """)
                    
                # Initialize chat history
                if "messages" not in st.session_state:
                    st.session_state.messages = []

                # Display chat messages
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

                # Chat input
                if prompt := st.chat_input("Ask about trading, indicators, or market concepts..."):
                    # Add user message to chat history
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)

                    # Display assistant response
                    with st.chat_message("assistant"):
                        message_placeholder = st.empty()
                        full_response = ""
                        
                        try:
                            # Initialize assistant with user_id for tool execution
                            assistant = AIAssistant(existing_key, user_id=user_id)
                            
                            # Prepare messages for API (convert streamlit format to anthropic format if needed)
                            # Simple pass-through for now
                            api_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                            
                            # Stream response
                            for chunk in assistant.chat_stream(api_messages):
                                full_response += chunk
                                message_placeholder.markdown(full_response + "▌")
                            
                            message_placeholder.markdown(full_response)
                            
                            # Add assistant response to chat history
                            st.session_state.messages.append({"role": "assistant", "content": full_response})
                            
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

    elif mode == "👑 Admin Panel":
        st.subheader("👑 Admin Panel")
        st.caption("Manage users and system settings")

        # Check if user is actually admin
        user_role = st.session_state['user'].get('role')
        if user_role not in ['admin', 'superadmin']:
            st.error("⛔ Access denied. Admin privileges required.")
            return

        # Show admin info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Your Role", user_role.upper())
        with col2:
            total_users = UserDB.get_all_users_count()
            st.metric("Total Users", total_users)
        with col3:
            st.metric("Status", "Active" if st.session_state['user'].get('is_active') else "Inactive")

        st.markdown("---")

        # Admin tabs
        tab1, tab2, tab3 = st.tabs(["👥 User Management", "📡 System Strategies", "📊 System Stats"])

        with tab1:
            st.markdown("### User Management")

            # Get all users
            all_users = UserDB.get_all_users()

            if all_users:
                # Create user table
                user_data = []
                for user in all_users:
                    # Helper function to format dates (handles both datetime objects and strings)
                    def format_date(date_value, format_str='%Y-%m-%d'):
                        if not date_value:
                            return 'N/A' if '%H' not in format_str else 'Never'
                        if isinstance(date_value, str):
                            # Already a string, try to parse and reformat
                            try:
                                from datetime import datetime
                                dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                                return dt.strftime(format_str)
                            except:
                                # If parsing fails, return as-is or truncated
                                return date_value[:10] if '%H' not in format_str else date_value[:16].replace('T', ' ')
                        else:
                            # It's a datetime object
                            return date_value.strftime(format_str)
                    
                    user_data.append({
                        'ID': user['id'],
                        'Username': user['username'],
                        'Email': user['email'],
                        'Full Name': user.get('full_name', 'N/A'),
                        'Role': user['role'].upper(),
                        'Status': '✅ Active' if user['is_active'] else '❌ Disabled',
                        'Created': format_date(user.get('created_at')),
                        'Last Login': format_date(user.get('last_login'), '%Y-%m-%d %H:%M')
                    })

                # Display as DataFrame
                df_users = pd.DataFrame(user_data)
                st.dataframe(df_users, use_container_width=True, hide_index=True)

                st.markdown("---")

                # User actions (only for superadmin)
                if user_role == 'superadmin':
                    st.markdown("### User Actions")

                    # Create new user
                    with st.expander("➕ Create New User"):
                        st.markdown("**Create a new user account with specific role**")
                        
                        with st.form("create_user_form"):
                            new_username = st.text_input("Username", help="Minimum 3 characters")
                            new_email = st.text_input("Email")
                            new_full_name = st.text_input("Full Name (optional)")
                            new_password = st.text_input("Password", type="password", help="Minimum 6 characters")
                            new_role = st.selectbox("Role", options=['user', 'admin', 'superadmin'], index=0)
                            
                            create_submit = st.form_submit_button("Create User", use_container_width=True)
                            
                            if create_submit:
                                if not new_username or not new_email or not new_password:
                                    st.error("❌ Please fill in all required fields")
                                elif len(new_username) < 3:
                                    st.error("❌ Username must be at least 3 characters")
                                elif len(new_password) < 6:
                                    st.error("❌ Password must be at least 6 characters")
                                else:
                                    # Create user with specific role
                                    result = UserDB.register_user(new_username, new_email, new_password, new_full_name or None)
                                    
                                    if result['success']:
                                        # Update role if not default
                                        if new_role != 'user':
                                            role_result = UserDB.update_user_role(result['user_id'], new_role)
                                            if role_result['success']:
                                                st.success(f"✅ User '{new_username}' created successfully with role '{new_role}'")
                                            else:
                                                st.warning(f"⚠️ User created but role update failed: {role_result['error']}")
                                        else:
                                            st.success(f"✅ User '{new_username}' created successfully")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Failed to create user: {result['error']}")

                    with st.expander("🔧 Manage User"):
                        selected_user = st.selectbox(
                            "Select User",
                            options=[f"{u['username']} ({u['email']})" for u in all_users],
                            key="manage_user_select"
                        )

                        if selected_user:
                            # Get selected user ID
                            selected_username = selected_user.split(' (')[0]
                            selected_user_obj = next((u for u in all_users if u['username'] == selected_username), None)

                            if selected_user_obj:
                                st.write(f"**Managing:** {selected_user_obj['username']}")

                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    new_role = st.selectbox(
                                        "Change Role",
                                        options=['user', 'admin', 'superadmin'],
                                        index=['user', 'admin', 'superadmin'].index(selected_user_obj['role']),
                                        key="role_select"
                                    )

                                    if st.button("Update Role", key="update_role_btn"):
                                        if selected_user_obj['id'] == user_id:
                                            st.warning("⚠️ Cannot change your own role")
                                        else:
                                            result = UserDB.update_user_role(selected_user_obj['id'], new_role)
                                            if result['success']:
                                                st.success(f"✅ Role updated to {new_role}")
                                                st.rerun()
                                            else:
                                                st.error(f"❌ {result['error']}")

                                with col2:
                                    if st.button("Toggle Active Status", key="toggle_status_btn"):
                                        if selected_user_obj['id'] == user_id:
                                            st.warning("⚠️ Cannot disable your own account")
                                        else:
                                            result = UserDB.toggle_user_status(selected_user_obj['id'])
                                            if result['success']:
                                                status = "enabled" if result['is_active'] else "disabled"
                                                st.success(f"✅ User {status}")
                                                st.rerun()
                                            else:
                                                st.error(f"❌ {result['error']}")

                                with col3:
                                    if selected_user_obj['role'] != 'superadmin':
                                        if st.button("🗑️ Delete User", key="delete_user_btn", type="secondary"):
                                            if st.session_state.get('confirm_delete'):
                                                result = UserDB.delete_user(selected_user_obj['id'])
                                                if result['success']:
                                                    st.success("✅ User deleted")
                                                    st.session_state['confirm_delete'] = False
                                                    st.rerun()
                                                else:
                                                    st.error(f"❌ {result['error']}")
                                            else:
                                                st.session_state['confirm_delete'] = True
                                                st.warning("⚠️ Click again to confirm deletion")
                                    else:
                                        st.info("Cannot delete superadmin")
                else:
                    st.info("👑 Only superadmins can manage users")

            else:
                st.info("No users found in the system")

        with tab2:
            st.markdown("### System TradingView Strategies")
            st.caption("Create and manage company TradingView alerts that users can subscribe to")

            # Import SystemStrategyDB
            try:
                from bot_database import SystemStrategyDB, UserStrategySubscriptionDB
                strategies_available = True
            except ImportError:
                strategies_available = False
                st.warning("⚠️ System strategies module not available. Run migration first.")

            if strategies_available:
                # Get webhook base URL - use dedicated webhook service
                import os
                webhook_base = os.getenv('WEBHOOK_BASE_URL', 'https://webhook.novalgo.org')

                # Create new strategy section
                with st.expander("➕ Create New System Strategy", expanded=False):
                    with st.form("create_strategy_form"):
                        st.markdown("**Create a TradingView strategy that users can subscribe to**")

                        strat_name = st.text_input("Strategy Name", placeholder="e.g., NovAlgo AAPL Scalper")
                        strat_symbol = st.text_input("Symbol", placeholder="e.g., AAPL").upper()
                        strat_timeframe = st.selectbox(
                            "Timeframe",
                            options=["5 Min", "15 Min", "30 Min", "1 Hour", "4 Hour", "1 Day"]
                        )
                        strat_description = st.text_area(
                            "Description",
                            placeholder="Describe this strategy for users..."
                        )
                        strat_risk_warning = st.text_area(
                            "Risk Warning",
                            value="Trading involves substantial risk. Past performance is not indicative of future results. NovAlgo is not responsible for any losses resulting from signals generated by this strategy.",
                            help="This warning will be shown to users before they subscribe"
                        )

                        create_strat = st.form_submit_button("Create Strategy", use_container_width=True)

                        if create_strat:
                            if not strat_name or not strat_symbol:
                                st.error("❌ Please fill in strategy name and symbol")
                            else:
                                strategy_id = SystemStrategyDB.create_strategy(
                                    name=strat_name,
                                    symbol=strat_symbol,
                                    timeframe=strat_timeframe,
                                    description=strat_description,
                                    risk_warning=strat_risk_warning
                                )
                                if strategy_id:
                                    st.success(f"✅ Strategy '{strat_name}' created successfully!")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to create strategy")

                # Display existing strategies
                st.markdown("---")
                strategies = SystemStrategyDB.get_all_strategies(active_only=False)

                if not strategies:
                    st.info("No system strategies created yet. Create your first strategy above!")
                else:
                    st.markdown(f"**Total Strategies:** {len(strategies)}")

                    for strat in strategies:
                        with st.container(border=True):
                            col1, col2, col3 = st.columns([3, 2, 1])

                            with col1:
                                status_icon = "🟢" if strat['is_active'] else "🔴"
                                st.markdown(f"### {status_icon} {strat['name']}")
                                st.caption(f"**{strat['symbol']}** | {strat['timeframe']}")
                                if strat.get('description'):
                                    st.write(strat['description'])

                            with col2:
                                subscriber_count = SystemStrategyDB.get_subscriber_count(strat['id'])
                                st.metric("Subscribers", subscriber_count)
                                st.metric("Total Signals", strat.get('total_signals', 0))
                                if strat.get('last_signal_at'):
                                    st.caption(f"Last signal: {strat['last_signal_at']}")

                            with col3:
                                # Toggle active status
                                if strat['is_active']:
                                    if st.button("🔴 Disable", key=f"disable_strat_{strat['id']}"):
                                        SystemStrategyDB.update_strategy(strat['id'], is_active=False)
                                        st.rerun()
                                else:
                                    if st.button("🟢 Enable", key=f"enable_strat_{strat['id']}"):
                                        SystemStrategyDB.update_strategy(strat['id'], is_active=True)
                                        st.rerun()

                                if st.button("🗑️ Delete", key=f"delete_strat_{strat['id']}", type="secondary"):
                                    if subscriber_count > 0:
                                        st.warning(f"⚠️ {subscriber_count} users subscribed!")
                                    else:
                                        SystemStrategyDB.delete_strategy(strat['id'])
                                        st.rerun()

                            # Webhook URL for TradingView
                            st.markdown("**TradingView Webhook URL:**")
                            webhook_url = f"{webhook_base}/system-webhook?token={strat['webhook_token']}"
                            st.code(webhook_url, language=None)

                            with st.expander("📋 TradingView Alert Setup"):
                                st.markdown(f"""
                                **In TradingView:**
                                1. Set up your strategy/indicator for **{strat['symbol']}** on **{strat['timeframe']}** timeframe
                                2. Create an alert
                                3. Set **Webhook URL** to the URL above
                                4. Use this **Message** format:
                                ```json
                                {{
                                  "action": "{{{{strategy.order.action}}}}",
                                  "symbol": "{strat['symbol']}",
                                  "timeframe": "{strat['timeframe']}"
                                }}
                                ```

                                When TradingView sends a signal, it will be executed for **all subscribed users**.
                                """)

        with tab3:
            st.markdown("### System Statistics")

            # Get stats from database
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### User Stats")
                try:
                    watchlist = WatchlistDB.get_all_stocks(user_id)
                    alerts = AlertsDB.get_active_alerts(user_id)

                    st.metric("Your Watchlist Stocks", len(watchlist))
                    st.metric("Your Active Alerts", len(alerts))

                except Exception as e:
                    st.error(f"Error loading stats: {e}")

            with col2:
                st.markdown("#### System Info")
                st.info("DashTrade v1.0\nAuthentication: Active\nRole-Based Access: Enabled")

                # Show role capabilities
                st.markdown("**Your Permissions:**")
                if user_role == 'superadmin':
                    st.success("✅ Full system access")
                    st.success("✅ User management")
                    st.success("✅ Role assignments")
                    st.success("✅ Delete users")
                elif user_role == 'admin':
                    st.success("✅ View all users")
                    st.success("✅ System statistics")
                    st.warning("⚠️ Limited user management")

if __name__ == "__main__":
    # Check database connection and show helpful error if needed
    import os
    from database import DATABASE_URL
    
    # Show database status (helpful for debugging)
    db_url_preview = DATABASE_URL[:50] + "..." if DATABASE_URL and len(DATABASE_URL) > 50 else (DATABASE_URL or "NOT SET")
    is_railway = os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RAILWAY_PROJECT_ID')
    
    # Initialize database tables on first run
    try:
        UserDB.create_users_table()

        # Auto-create admin if none exists
        try:
            from database import get_db_connection
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM users WHERE role IN ('admin', 'superadmin')")
                    result = cur.fetchone()
                    admin_count = result[0] if isinstance(result, tuple) else result.get('count', 0) if isinstance(result, dict) else 0

                    if admin_count == 0:
                        # No admin exists, create default one
                        print("No admin found. Creating default superadmin account...")
                        result = UserDB.register_user(
                            username='admin',
                            email='admin@dashtrade.app',
                            password='Admin123',
                            full_name='Administrator',
                            role='superadmin'
                        )
                        if result.get('success'):
                            print("Default superadmin created: admin / Admin123")
                        else:
                            print(f"Failed to create admin: {result.get('error')}")
        except Exception as admin_err:
            print(f"Admin check/creation error (non-fatal): {admin_err}")

    except ConnectionError as e:
        # Show helpful error for connection issues
        st.error("🚨 Database Connection Error")
        st.markdown(f"""
        <div class='error-message'>
            <strong>Cannot connect to database!</strong><br><br>
            {str(e)}<br><br>
            <strong>Quick Fix:</strong><br>
            • Make sure you're accessing your <strong>Railway app URL</strong>, not running locally<br>
            • Check Railway → Variables → DATABASE_URL is set<br>
            • Verify PostgreSQL service is running in Railway<br><br>
            <strong>Current Status:</strong><br>
            • Running on Railway: {'Yes' if is_railway else 'No (likely local)'}<br>
            • DATABASE_URL: {db_url_preview}
        </div>
        """, unsafe_allow_html=True)
        st.stop()
    except Exception as e:
        error_msg = str(e)
        if 'localhost' in error_msg.lower() or 'connection refused' in error_msg.lower():
            st.error("🚨 Database Connection Error")
            st.markdown(f"""
            <div class='error-message'>
                <strong>Database Connection Failed!</strong><br><br>
                The app is trying to connect to <strong>localhost</strong> instead of Railway's database.<br><br>
                <strong>This means:</strong><br>
                • You're likely running the app <strong>locally</strong> instead of using Railway URL<br>
                • Or DATABASE_URL is not set correctly in Railway<br><br>
                <strong>Solution:</strong><br>
                1. <strong>Don't run</strong> <code>streamlit run app.py</code> locally<br>
                2. Go to your <strong>Railway dashboard</strong> → Get your app URL<br>
                3. Access the app through that URL (e.g., https://your-app.railway.app)<br>
                4. Railway automatically sets DATABASE_URL for you<br><br>
                <strong>Current Status:</strong><br>
                • Running on Railway: {'Yes ✅' if is_railway else 'No ❌ (This is the problem!)'}<br>
                • DATABASE_URL: {db_url_preview}
            </div>
            """, unsafe_allow_html=True)
            st.stop()
        else:
            st.error(f"Database initialization error: {e}")

    # Check authentication
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    if st.session_state['authenticated']:
        # User is logged in, show main app
        main()
    else:
        # User not logged in, show landing page with login/register
        show_landing_page()
