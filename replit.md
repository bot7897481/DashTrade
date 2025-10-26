# NovAlgo Trading Signal Dashboard

## Project Overview
Comprehensive stock trading signal application built with Streamlit and Python. This dashboard transforms your PinScript technical analysis into an advanced Python application with 100% technical analysis coverage.

## Last Updated
October 26, 2025 - Added Alpha Vantage integration with news sentiment analysis

## Features Implemented

### Core PineScript Features (20% - From Original)
1. **5 EMAs** - 9, 20, 50, 100, 200 period exponential moving averages
2. **MA Cloud** - Short/Long EMA cloud for trend visualization
3. **QQE Signals** - Quantified Qualitative Estimation momentum indicator
   - Configurable RSI period (default: 8)
   - RSI smoothing (default: 3)
   - QQE factor (default: 3.2)
4. **VWAP** - Volume Weighted Average Price with 3 standard deviation bands

### Advanced Features (80% - NEW)
5. **15+ Candlestick Patterns**
   - Doji, Hammer, Shooting Star
   - Bullish/Bearish Engulfing
   - Morning Star, Evening Star
   - Auto-detection with visual markers

6. **Chart Patterns (Bulkowski Method)**
   - Double Tops/Bottoms with measure rules
   - Head & Shoulders (regular and inverse)
   - Ascending/Descending Triangles
   - Statistical success rate tracking

7. **Support & Resistance**
   - Automatic pivot point detection
   - Level clustering algorithm
   - Distance calculations from current price

8. **Volume Analysis**
   - Volume trend detection (rising/falling/unchanged)
   - Volume shape analysis (U-shaped, Dome-shaped)
   - Breakout volume confirmation

9. **Risk Management System**
   - ATR-based stop loss calculation
   - Position sizing calculator
   - Risk/reward ratio analysis
   - Multiple price target projections (1:2, 1:3)

10. **Signal Generation**
    - Combined indicator signals
    - Trend alignment verification
    - Strength scoring
    - Pattern confirmation

## Project Structure
```
/
├── app.py                      # Main Streamlit dashboard with 6 modes
├── technical_analyzer.py       # Complete technical analysis engine
├── database.py                 # PostgreSQL database operations (watchlist, portfolio, alerts, preferences)
├── comparison_analyzer.py      # Multi-stock comparison and correlation analysis
├── backtester.py              # Backtesting framework with performance metrics
├── strategy_builder.py        # Custom strategy builder with template system
├── alert_system.py            # Alert monitoring and evaluation helpers
├── replit.md                  # Project documentation (this file)
├── attached_assets/           # Original PinScript and documentation
│   ├── PinChart Code_*.pdf
│   ├── novalgo_complete_*.py
│   ├── USAGE_GUIDE.md_*.pdf
│   ├── QUICK_COMPARISON.md_*.pdf
│   └── technical_analysis_comparison.md_*.pdf
```

## How to Use

### 1. Basic Usage
1. Enter a stock symbol (e.g., AAPL, TSLA, NVDA, BTC-USD)
2. Select timeframe and interval
3. Click "Fetch & Analyze"
4. View comprehensive analysis across multiple tabs

### 2. Dashboard Tabs
- **Chart** - Interactive candlestick chart with all indicators
- **Chart Patterns** - Detected patterns with targets
- **Candlestick Patterns** - Recent reversal patterns
- **Support & Resistance** - Key price levels
- **Risk Management** - Position sizing calculator

### 3. Customization
In the sidebar, you can adjust:
- QQE Parameters (RSI Period, Smoothing, Factor)
- Account Balance for risk calculations
- Timeframe and interval selections

## Technical Settings

### QQE Parameters (Optimized for Fast Signals)
- **RSI Period**: 8 (faster than traditional 14)
- **RSI Smoothing**: 3 
- **QQE Factor**: 3.2 (controls band width)

### Risk Management
- **Default Account**: $10,000
- **Default Risk**: 1% per trade
- **Stop Loss Method**: ATR-based (2x multiplier)

## Example Stocks to Analyze
- **Tech**: AAPL, MSFT, GOOGL, NVDA, TSLA
- **Crypto**: BTC-USD, ETH-USD
- **Indices**: SPY, QQQ, DIA
- **Commodities**: GLD, SLV, USO

## Data Sources

### Dual Provider System (Toggle Between Sources)
The application now supports **both Yahoo Finance and Alpha Vantage** with seamless switching via sidebar toggle.

#### Yahoo Finance (Default)
- **Provider**: Yahoo Finance (yfinance library)
- **Advantages**: 
  - Unlimited API calls
  - No API key required
  - Stable and reliable
- **Limitations**:
  - 15-minute delay for free tier
  - No real-time data
  - No news sentiment analysis
- **Intervals Supported**: 1m, 5m, 15m, 30m, 60m, 1h, 1d, 1wk
- **Best for**: Development, testing, backtesting, unlimited analysis

#### Alpha Vantage (Real-time)
- **Provider**: Alpha Vantage API
- **Advantages**:
  - Real-time stock quotes
  - News sentiment analysis (last 24 hours)
  - Combined price + news signals
  - Confidence scoring
- **Limitations**:
  - 25 API calls/day (free tier)
  - 5 requests/minute rate limit
  - Requires ALPHA_VANTAGE_API_KEY
- **Intervals Supported**: 1m, 5m, 15m, 30m, 45m (mapped to 60m), 1h, 1d, 1wk (mapped to daily)
- **Best for**: Real-time trading, news-driven strategies, sentiment analysis

### How to Switch Data Sources
1. In the sidebar, find the **"Data Source"** section
2. Select either **"Yahoo Finance"** or **"Alpha Vantage"**
3. The active source badge appears in the main content area
4. Cache automatically clears when switching sources
5. All features work identically regardless of source

## Performance Notes
- First analysis may take 10-20 seconds
- Subsequent analyses are faster (caching enabled)
- Recommended: Use 1d interval for daily trading
- Pattern detection works best with 3+ months of data

## Deployment
Currently running on Replit.
Port: 5000 (configured for Streamlit)

## User Preferences
- **Focus**: Stock trading with technical analysis
- **Style**: Comprehensive analysis with visual signals
- **Priority**: Pattern recognition and risk management

## Recent Changes
- Initial implementation (Oct 25, 2025)
- Complete dashboard with all PinScript features
- Added 80% new functionality (patterns, S/R, risk management)
- Interactive Plotly charts
- Multi-tab interface for organized analysis

## Completed Enhancements (NEW - October 26, 2025)
All major requested features have been implemented:

### 11. **Portfolio Tracking & Watchlist** ✅
- PostgreSQL database-backed watchlist management
- Add/remove stocks dynamically
- Real-time monitoring of all watchlist stocks
- Combined signal dashboard showing long/short signals across portfolio
- Trend analysis aggregation

### 12. **Multi-Stock Comparison** ✅
- Side-by-side comparison of up to 10 stocks
- Normalized price charts for performance comparison
- Correlation matrix with color-coded heatmap
- Performance metrics (returns, volatility, Sharpe ratio)
- Relative strength rankings

### 13. **Backtesting Framework** ✅
- Complete historical performance analysis
- Multiple pre-built strategies (QQE, Trend Following, Combined)
- Win rate, profit factor, max drawdown tracking
- Equity curve visualization
- Detailed trade log with entry/exit prices
- Customizable initial capital and position sizing

### 14. **Custom Strategy Builder** ✅
- Visual strategy builder with no-code interface
- Combine multiple indicators with AND/OR logic
- Separate entry/exit conditions for long and short positions
- Pre-built strategy templates (QQE Aggressive, Trend Rider, etc.)
- Real-time strategy testing with backtesting integration
- Performance metrics for custom strategies

### 15. **Alert System** ✅
- Database-backed alert configuration
- Multiple alert types:
  - QQE long/short signals
  - Trend changes (bullish/bearish)
  - Price levels (above, below, crosses)
  - EMA crossovers (20/50 cross)
- Alert Manager UI for creating/managing/deleting alerts
- Active alert monitoring in Portfolio Dashboard
- Alert lifecycle tracking (created, triggered, timestamp)
- Real-time alert evaluation against live market data

### 16. **News Sentiment Analysis** ⭐ NEW
- Real-time news sentiment using Alpha Vantage News Intelligence API
- Sentiment scoring for individual stocks (-1 to +1 scale)
- Combined price + news signals for stronger conviction
- Confidence scoring based on sentiment strength and relevance
- Top news articles display with:
  - Sentiment labels (Bullish/Bearish/Neutral)
  - Relevance scores
  - Source attribution
  - Direct links to articles
- Analyzes last 24 hours of news coverage
- Supports news-driven long/short signal generation

### 17. **Signal Activity Dashboard** ⭐ NEW
- Real-time signal counting for LONG and SHORT signals
- Multi-timeframe analysis:
  - Past 1 hour signal counts
  - Past 4 hours signal counts
  - Past 24 hours signal counts
- Current signal status display with:
  - Signal type (LONG/SHORT)
  - Time elapsed since signal
  - Price at signal
  - Signal strength (STRONG/NORMAL)
- Detailed signal timeline table showing:
  - Exact timestamp
  - Time ago (e.g., "23 minutes ago")
  - Signal type
  - Price at signal
  - Indicator source
  - Strength classification

### 18. **Visual Signal Markers (TradingView-style)** ⭐ NEW
- Interactive candlestick chart with text annotations
- Green "Long" labels for buy signals
- Red "Short" labels for sell signals
- Direct signal markers on price candles
- Includes:
  - 5 EMAs (9, 20, 50, 100, 200)
  - MA Cloud visualization
  - VWAP with bands
  - Volume bars
  - QQE trend subplot
- Fully interactive with zoom and pan
- Professional dark theme

## Future Enhancements
- Email/SMS notifications for triggered alerts
- Advanced chart pattern recognition (Fibonacci retracements, harmonic patterns)
- Machine learning-based signal predictions
- Export functionality for strategies and backtest results
- Mobile-optimized interface

## Dependencies
```python
streamlit==1.40.2
pandas
numpy
yfinance
plotly==6.3.1
ta==0.11.0
scipy
matplotlib
requests
psycopg2-binary
sqlalchemy
```

## Known Issues
None currently reported.

## Support & Documentation
- Complete usage guide in `attached_assets/USAGE_GUIDE.md_*.pdf`
- Quick comparison in `attached_assets/QUICK_COMPARISON.md_*.pdf`
- Technical analysis comparison in `attached_assets/technical_analysis_comparison.md_*.pdf`
