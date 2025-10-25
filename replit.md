# NovAlgo Trading Signal Dashboard

## Project Overview
Comprehensive stock trading signal application built with Streamlit and Python. This dashboard transforms your PinScript technical analysis into an advanced Python application with 100% technical analysis coverage.

## Last Updated
October 25, 2025

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
├── app.py                    # Main Streamlit dashboard
├── technical_analyzer.py     # Complete technical analysis engine
├── replit.md                # Project documentation (this file)
├── attached_assets/         # Original PinScript and documentation
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

## Data Source
- **Provider**: Yahoo Finance (yfinance library)
- **Real-time**: 15-minute delay for free tier
- **History**: Up to 5 years available

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

## Future Enhancements (User Requested)
- Portfolio tracking with multiple stock watchlist
- Backtesting framework with historical performance
- Alert system for pattern formations
- Custom strategy builder
- Multi-stock comparison tool
- Real-time monitoring dashboard

## Dependencies
```python
streamlit==1.40.2
pandas
numpy
yfinance
plotly==6.3.1
ta==0.11.0
scipy
```

## Known Issues
None currently reported.

## Support & Documentation
- Complete usage guide in `attached_assets/USAGE_GUIDE.md_*.pdf`
- Quick comparison in `attached_assets/QUICK_COMPARISON.md_*.pdf`
- Technical analysis comparison in `attached_assets/technical_analysis_comparison.md_*.pdf`
