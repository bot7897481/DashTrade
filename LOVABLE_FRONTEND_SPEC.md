# DashTrade (NovAlgo) - Frontend Design Specification for Lovable

## Document Purpose
This document provides all the information needed to design a modern, professional trading platform frontend. The backend is fully functional - this spec describes all features, data structures, and API endpoints for frontend integration.

---

## 1. APPLICATION OVERVIEW

### What is DashTrade?
DashTrade (branded as "NovAlgo") is a **multi-user stock trading technical analysis platform** that combines:
- Professional-grade technical analysis with 35+ indicators
- Automated trading bot with Alpaca broker integration
- TradingView webhook integration for signal execution
- Portfolio management and watchlist tracking
- Strategy backtesting engine
- Custom strategy builder
- Real-time alerts system
- AI assistant powered by Claude

### Target Users
- Day traders and swing traders
- Technical analysis enthusiasts
- Algorithmic trading beginners
- Portfolio managers tracking multiple stocks

### Brand Identity
- **App Name:** NovAlgo (or DashTrade)
- **Primary Colors:** Purple gradient (#667eea to #764ba2)
- **Accent Colors:** Green (#00c853) for bullish/positive, Red (#ff1744) for bearish/negative
- **Style:** Modern, professional, dark mode preferred for trading

---

## 2. USER AUTHENTICATION SYSTEM

### User Roles
| Role | Access Level |
|------|--------------|
| **User** | All trading features, personal dashboard |
| **Admin** | User management + all user features |
| **Superadmin** | Full system control |

### Authentication Screens Needed

#### 2.1 Login Screen
```
Fields:
- Username (text input)
- Password (password input)
- "Remember me" checkbox
- Login button
- Link to Register page
- "Forgot password" link
```

#### 2.2 Registration Screen
```
Fields:
- Username (3+ characters, unique)
- Email (valid format, unique)
- Password (6+ characters)
- Confirm Password
- Full Name (optional)
- Admin Code (optional, for admin registration - 16 digits like "1234-5678-9012-3456")
- Register button
- Link to Login page
```

#### 2.3 User Session Data (stored after login)
```json
{
  "user_id": 123,
  "username": "trader1",
  "email": "trader1@email.com",
  "role": "user",
  "full_name": "John Trader",
  "is_active": true,
  "last_login": "2024-01-15T10:30:00Z"
}
```

---

## 3. MAIN NAVIGATION STRUCTURE

### Sidebar Navigation (7 Main Sections)
```
1. 📈 Single Stock Analysis (default)
2. 📊 Portfolio Dashboard
3. 🔄 Multi-Stock Comparison
4. 📉 Backtesting
5. 🛠️ Strategy Builder
6. 🔔 Alert Manager
7. 🤖 Trading Bot
8. 👤 Admin Panel (admins only)
9. ⚙️ Settings/Profile
```

---

## 4. FEATURE SCREENS - DETAILED SPECIFICATIONS

---

### 4.1 SINGLE STOCK ANALYSIS (Main Dashboard)

**Purpose:** Comprehensive technical analysis for one stock at a time

#### Input Controls
```
- Symbol input (text, e.g., "AAPL", "TSLA", "SPY")
- Time Period selector:
  - Options: 1 Month, 3 Months, 6 Months, 1 Year, 2 Years, 5 Years
- Interval selector:
  - Options: 1 Min, 5 Min, 15 Min, 30 Min, 1 Hour, 1 Day
- Data Source toggle:
  - Yahoo Finance (default, free)
  - Alpha Vantage (requires API key)
- "Analyze" button
```

#### Output Display - 4 Tabs

**Tab 1: Overview**
```
Main Chart (Interactive Candlestick):
- OHLC candlesticks (green=up, red=down)
- 5 EMA lines overlay (9, 20, 50, 100, 200 period)
- MA Cloud shading (bullish=green, bearish=red)
- VWAP line with bands
- Volume histogram below chart
- Signal markers (buy/sell arrows)

Chart Controls:
- Zoom in/out
- Pan left/right
- Reset view
- Download as image
- Toggle indicators on/off

Summary Cards:
- Current Price with change %
- Signal (BULLISH/BEARISH/NEUTRAL)
- Trend strength (1-5 scale)
- Volume vs Average
```

**Tab 2: Patterns**
```
Candlestick Patterns Detected:
- Pattern name (e.g., "Bullish Engulfing")
- Location on chart (date/price)
- Reliability score (%)
- Historical success rate

Chart Patterns Detected:
- Pattern name (e.g., "Double Bottom", "Head & Shoulders")
- Pattern visualization on chart
- Price target (measure rule)
- Breakout level
```

**Tab 3: Support & Resistance**
```
Key Levels Table:
| Level Type | Price | Strength | Touches | Distance from Current |
|------------|-------|----------|---------|----------------------|
| Resistance | $150.50 | Strong | 4 | +2.3% |
| Support    | $142.20 | Medium | 2 | -3.1% |

Visual: Horizontal lines on chart at each S&R level
```

**Tab 4: Metrics**
```
Technical Indicators Panel:
- RSI (14): 65.4 (Overbought/Oversold/Neutral)
- MACD: Bullish/Bearish crossover
- Stochastic: 72.3
- ATR (Average True Range): $2.45
- 52-Week High/Low
- Average Volume
- Beta (vs SPY)
- Volatility %
```

#### API Data Structure - Stock Analysis Response
```json
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "current_price": 175.50,
  "change_percent": 2.34,
  "signal": "BULLISH",
  "trend_strength": 4,

  "ohlcv_data": [
    {
      "timestamp": "2024-01-15T09:30:00",
      "open": 174.20,
      "high": 176.80,
      "low": 173.90,
      "close": 175.50,
      "volume": 45000000
    }
  ],

  "indicators": {
    "ema_9": 174.80,
    "ema_20": 173.50,
    "ema_50": 170.20,
    "ema_100": 168.00,
    "ema_200": 165.50,
    "vwap": 175.10,
    "rsi_14": 65.4,
    "macd": {"value": 1.2, "signal": 0.8, "histogram": 0.4},
    "atr_14": 2.45
  },

  "candlestick_patterns": [
    {
      "name": "Bullish Engulfing",
      "date": "2024-01-14",
      "reliability": 78,
      "type": "bullish"
    }
  ],

  "chart_patterns": [
    {
      "name": "Cup and Handle",
      "start_date": "2024-01-01",
      "end_date": "2024-01-15",
      "target_price": 185.00,
      "breakout_level": 176.50
    }
  ],

  "support_resistance": [
    {"type": "resistance", "price": 180.00, "strength": "strong", "touches": 4},
    {"type": "support", "price": 170.00, "strength": "medium", "touches": 2}
  ]
}
```

---

### 4.2 PORTFOLIO DASHBOARD

**Purpose:** Manage watchlist and track multiple stocks at once

#### Watchlist Management
```
Add Stock Form:
- Symbol input
- Notes (optional textarea)
- "Add to Watchlist" button

Watchlist Table:
| Symbol | Name | Current Price | Change % | Signal | Notes | Actions |
|--------|------|---------------|----------|--------|-------|---------|
| AAPL   | Apple| $175.50       | +2.3%    | BULL   | Tech  | [Analyze] [Remove] |
| TSLA   | Tesla| $245.20       | -1.2%    | BEAR   | EV    | [Analyze] [Remove] |

Batch Analysis:
- "Analyze All" button (full analysis on all watchlist stocks)
- "Quick Scan" button (just signals, no deep analysis)
```

#### Portfolio Summary Cards
```
- Total Stocks in Watchlist: 12
- Bullish Signals: 7
- Bearish Signals: 3
- Neutral Signals: 2
- Active Alerts: 5
- Triggered Alerts Today: 2
```

#### API Endpoints
```
GET /api/watchlist
Response: [{"symbol": "AAPL", "name": "Apple", "notes": "Tech leader", "added_at": "2024-01-10"}]

POST /api/watchlist
Body: {"symbol": "AAPL", "notes": "Tech leader"}

DELETE /api/watchlist/{symbol}
```

---

### 4.3 MULTI-STOCK COMPARISON

**Purpose:** Compare 2-10 stocks side by side

#### Input Controls
```
- Multi-select stock input (comma separated or chips)
- Comparison period selector (1mo, 3mo, 6mo, 1yr)
- Benchmark selector (SPY, QQQ, IWM, or none)
- "Compare" button
```

#### Output Displays

**Normalized Performance Chart**
```
Line chart showing all stocks normalized to 100% at start date
- Each stock as different colored line
- Benchmark as dashed line
- Hover shows exact values
```

**Correlation Matrix Heatmap**
```
Grid showing correlation coefficients between each pair
- Color scale: -1 (red) to +1 (green)
- Values shown in each cell
```

**Comparison Table**
```
| Metric          | AAPL   | TSLA   | MSFT   | GOOGL  |
|-----------------|--------|--------|--------|--------|
| Return %        | +15.2% | +8.4%  | +12.1% | +10.5% |
| Volatility      | 22%    | 45%    | 20%    | 25%    |
| Sharpe Ratio    | 1.2    | 0.8    | 1.1    | 0.9    |
| Beta            | 1.1    | 1.8    | 0.9    | 1.2    |
| Max Drawdown    | -12%   | -25%   | -10%   | -15%   |
| Relative Strength| 1.05   | 0.92   | 1.02   | 0.98   |
| Signal          | BULL   | NEUTRAL| BULL   | BULL   |
```

**Sector Strength Rankings** (if multiple sectors)
```
1. Technology: +12.5% avg return
2. Healthcare: +8.2% avg return
3. Financials: +5.1% avg return
```

---

### 4.4 BACKTESTING ENGINE

**Purpose:** Test trading strategies on historical data

#### Strategy Selection
```
Pre-built Strategies:
1. QQE Crossover - Momentum-based entries
2. EMA Crossover (9/20) - Trend following
3. MA Cloud Trend - Cloud-based signals
4. Custom Strategy - (from Strategy Builder)
```

#### Configuration Panel
```
Stock Settings:
- Symbol input
- Start Date picker
- End Date picker

Risk Management:
- Initial Capital: $10,000 (number input)
- Position Size: Fixed $ or % of account (radio)
- Stop Loss %: 2% (slider 0.5-10%)
- Take Profit %: 6% (slider 1-20%)
- ATR Multiplier for stops: 2.0 (slider 1-4)

Advanced Options:
- Allow short selling (checkbox)
- Commission per trade: $0 (number input)
- Slippage %: 0.1% (number input)
```

#### Results Display

**Performance Summary Cards**
```
- Total Return: +45.2% ($4,520)
- CAGR: 32.1%
- Win Rate: 62%
- Profit Factor: 2.3
- Sharpe Ratio: 1.85
- Max Drawdown: -12.4%
- Total Trades: 48
- Avg Win: $245.50
- Avg Loss: -$112.30
- Best Trade: +$890
- Worst Trade: -$450
```

**Equity Curve Chart**
```
Line chart showing account value over time
- Starting value line (horizontal)
- Drawdown shading
- Trade entry/exit markers
```

**Trade Log Table**
```
| # | Entry Date | Exit Date | Side | Entry Price | Exit Price | P&L | P&L % |
|---|------------|-----------|------|-------------|------------|-----|-------|
| 1 | 2024-01-05 | 2024-01-08| LONG | $170.50     | $175.20    | +$470| +2.8%|
| 2 | 2024-01-10 | 2024-01-12| SHORT| $176.00     | $172.50    | +$350| +2.0%|

Export to CSV button
```

#### API Data Structure - Backtest Results
```json
{
  "strategy_name": "EMA Crossover",
  "symbol": "AAPL",
  "period": {"start": "2023-01-01", "end": "2024-01-15"},

  "metrics": {
    "total_return_pct": 45.2,
    "total_return_dollars": 4520,
    "cagr": 32.1,
    "win_rate": 62,
    "profit_factor": 2.3,
    "sharpe_ratio": 1.85,
    "max_drawdown_pct": 12.4,
    "total_trades": 48,
    "winning_trades": 30,
    "losing_trades": 18,
    "avg_win": 245.50,
    "avg_loss": 112.30,
    "best_trade": 890,
    "worst_trade": -450,
    "avg_trade_duration_days": 3.2
  },

  "equity_curve": [
    {"date": "2023-01-01", "equity": 10000},
    {"date": "2023-01-05", "equity": 10470},
    {"date": "2023-01-08", "equity": 10350}
  ],

  "trades": [
    {
      "id": 1,
      "entry_date": "2024-01-05",
      "exit_date": "2024-01-08",
      "side": "LONG",
      "entry_price": 170.50,
      "exit_price": 175.20,
      "shares": 100,
      "pnl_dollars": 470,
      "pnl_percent": 2.8,
      "exit_reason": "take_profit"
    }
  ]
}
```

---

### 4.5 STRATEGY BUILDER

**Purpose:** Create custom trading strategies with visual rule builder

#### Strategy Configuration
```
Strategy Name: (text input)
Description: (textarea)
```

#### Condition Builder (Visual Interface)

**Entry Conditions (Long)**
```
Rule Builder Interface:
┌─────────────────────────────────────────────────┐
│ IF [Indicator ▼] [Operator ▼] [Value/Indicator] │
│    EMA_9         crosses above    EMA_20        │
│                                                 │
│ [AND ▼]                                         │
│                                                 │
│ IF [Indicator ▼] [Operator ▼] [Value/Indicator] │
│    RSI_14        is below         70            │
│                                                 │
│ [+ Add Condition]                               │
└─────────────────────────────────────────────────┘

Logic Operator: AND / OR (radio buttons)
```

**Available Indicators for Conditions:**
```
Price-based:
- Close, Open, High, Low
- Price crosses above/below level

Moving Averages:
- EMA (9, 20, 50, 100, 200)
- SMA (any period)
- MA Cloud (short, long)

Momentum:
- RSI (oversold <30, overbought >70)
- MACD (line, signal, histogram)
- QQE (fast, slow)
- Stochastic (%K, %D)

Volume:
- Volume > Average Volume
- VWAP position

Patterns:
- Bullish pattern detected
- Bearish pattern detected
```

**Operators Available:**
```
- crosses above
- crosses below
- is greater than (>)
- is less than (<)
- is equal to (==)
- is between (range)
```

**Exit Conditions**
```
Same builder interface as entry
Common exits:
- Opposite signal
- Stop loss hit
- Take profit hit
- Time-based (X bars)
```

#### Strategy Templates (Quick Start)
```
1. QQE Momentum
   - Entry: QQE crosses above threshold
   - Exit: QQE crosses below threshold

2. EMA Trend Following
   - Entry: EMA9 crosses above EMA20 AND price > VWAP
   - Exit: EMA9 crosses below EMA20

3. RSI Mean Reversion
   - Entry: RSI < 30 AND bullish candle pattern
   - Exit: RSI > 70 OR stop loss

4. Breakout Strategy
   - Entry: Price breaks above resistance
   - Exit: Price falls below entry - ATR*2
```

#### Save & Test
```
- "Save Strategy" button
- "Backtest Now" button (redirects to backtesting with this strategy)
- "Export Strategy" (JSON download)
```

#### API Data Structure - Custom Strategy
```json
{
  "id": 1,
  "name": "My EMA Strategy",
  "description": "Trend following with EMA crossover",
  "user_id": 123,
  "created_at": "2024-01-15T10:00:00Z",

  "entry_long": {
    "logic": "AND",
    "conditions": [
      {"indicator": "ema_9", "operator": "crosses_above", "value": "ema_20"},
      {"indicator": "rsi_14", "operator": "less_than", "value": 70},
      {"indicator": "close", "operator": "greater_than", "value": "vwap"}
    ]
  },

  "entry_short": {
    "logic": "AND",
    "conditions": [
      {"indicator": "ema_9", "operator": "crosses_below", "value": "ema_20"},
      {"indicator": "rsi_14", "operator": "greater_than", "value": 30}
    ]
  },

  "exit": {
    "logic": "OR",
    "conditions": [
      {"indicator": "opposite_signal", "operator": "equals", "value": true},
      {"indicator": "stop_loss_pct", "operator": "equals", "value": 2},
      {"indicator": "take_profit_pct", "operator": "equals", "value": 6}
    ]
  }
}
```

---

### 4.6 ALERT MANAGER

**Purpose:** Set price and technical alerts with notifications

#### Create Alert Form
```
Alert Type (tabs or dropdown):
1. Price Alert
   - Symbol
   - Condition: Above / Below / Crosses
   - Price level

2. Indicator Alert
   - Symbol
   - Indicator: RSI, MACD, etc.
   - Condition: Above / Below / Crosses
   - Threshold value

3. Trend Alert
   - Symbol
   - Condition: EMA crossover, QQE signal change, etc.

4. Pattern Alert
   - Symbol
   - Pattern type: Bullish engulfing, Head & shoulders, etc.
```

#### Alert Notification Settings
```
- Email notifications (toggle)
- Email address (if enabled)
- Push notifications (future feature)
```

#### Active Alerts Table
```
| Symbol | Type | Condition | Created | Status | Actions |
|--------|------|-----------|---------|--------|---------|
| AAPL | Price | Above $180 | Jan 10 | Active | [Edit] [Delete] |
| TSLA | RSI | Below 30 | Jan 12 | Active | [Edit] [Delete] |
| MSFT | Trend | EMA Bullish | Jan 14 | Triggered | [Reset] [Delete] |
```

#### Triggered Alerts History
```
| Symbol | Type | Condition | Triggered At | Price at Trigger |
|--------|------|-----------|--------------|------------------|
| AAPL | Price | Above $175 | Jan 15 10:30 | $175.25 |
```

#### API Endpoints
```
GET /api/alerts
POST /api/alerts
Body: {
  "symbol": "AAPL",
  "alert_type": "price",
  "condition": "above",
  "value": 180.00
}

PUT /api/alerts/{id}
DELETE /api/alerts/{id}

POST /api/alerts/{id}/reset (reactivate triggered alert)
```

---

### 4.7 TRADING BOT (Most Complex Feature)

**Purpose:** Automated trading with Alpaca broker integration

#### Tab Structure (6 Tabs)
```
1. Setup - API keys and webhook configuration
2. My Bots - Create and manage trading bots
3. Live Positions - Current open positions from Alpaca
4. Trade History - All executed trades
5. Performance - Analytics and P&L tracking
6. Risk Events - Risk limit triggers and safety stops
```

---

#### Tab 1: Setup

**Alpaca API Connection**
```
If NOT connected:
┌─────────────────────────────────────────┐
│ Connect Alpaca Account                  │
│                                         │
│ API Key: [________________] (password)  │
│ Secret:  [________________] (password)  │
│                                         │
│ Mode: ○ Paper Trading (recommended)     │
│       ○ Live Trading ⚠️                 │
│                                         │
│ [Connect Account]                       │
└─────────────────────────────────────────┘

If connected:
┌─────────────────────────────────────────┐
│ ✅ Alpaca Connected (PAPER mode)        │
│                                         │
│ [Update Keys] [Disconnect]              │
└─────────────────────────────────────────┘
```

**Webhook URL Section**
```
┌─────────────────────────────────────────┐
│ TradingView Webhook URL                 │
│                                         │
│ https://yourapp.com/webhook?token=abc123│
│ [Copy URL]                              │
│                                         │
│ Webhook Message Format:                 │
│ {                                       │
│   "action": "{{strategy.order.action}}" │
│   "symbol": "{{ticker}}",               │
│   "timeframe": "15 Min"                 │
│ }                                       │
└─────────────────────────────────────────┘
```

---

#### Tab 2: My Bots

**Add New Bot Form**
```
┌─────────────────────────────────────────────────────┐
│ ➕ Create New Bot                                    │
│                                                     │
│ Symbol: [AAPL____]  Timeframe: [15 Min ▼]          │
│                                                     │
│ Position Size: [$5,000___]                          │
│                                                     │
│ Signal Source:                                      │
│ ○ Webhook (TradingView)                            │
│ ○ Internal - Yahoo (15min delay)                   │
│ ○ Internal - Alpaca (real-time)                    │
│                                                     │
│ Strategy (for Internal): [NovAlgo Fast Signals ▼]  │
│                                                     │
│ Risk Management:                                    │
│ Risk Limit: [10__]%  Daily Loss Limit: [$500__]   │
│                                                     │
│ Strategy Name (optional): [______________]          │
│                                                     │
│ [Create Bot]                                        │
└─────────────────────────────────────────────────────┘
```

**Bot Cards Grid**
```
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ AAPL - 15 Min    │ │ TSLA - 1 Hour    │ │ SPY - 5 Min      │
│ ────────────────│ │ ────────────────│ │ ────────────────│
│ Status: IDLE     │ │ Status: IN_TRADE │ │ Status: IDLE     │
│ Position: FLAT   │ │ Position: LONG   │ │ Position: FLAT   │
│ Size: $5,000     │ │ Size: $10,000    │ │ Size: $3,000     │
│ P&L: +$234.50    │ │ P&L: -$45.20     │ │ P&L: +$0.00      │
│ Trades: 12       │ │ Trades: 8        │ │ Trades: 0        │
│                  │ │                  │ │                  │
│ [🟢 Active]      │ │ [🟢 Active]      │ │ [🔴 Disabled]    │
│ [Disable] [Delete]│ │ [Disable] [Delete]│ │ [Enable] [Delete]│
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

**Bots Summary Table**
```
| Symbol | Timeframe | Source | Strategy | Size | Active | Status | P&L | Trades |
|--------|-----------|--------|----------|------|--------|--------|-----|--------|
| AAPL | 15 Min | Webhook | - | $5,000 | ✅ | IDLE | +$234 | 12 |
| TSLA | 1 Hour | Internal | NovAlgo | $10,000 | ✅ | LONG | -$45 | 8 |
```

---

#### Tab 3: Live Positions

**Account Overview Cards**
```
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Equity      │ │ Cash        │ │ Buying Power│ │ Day P&L     │
│ $52,450.00  │ │ $12,450.00  │ │ $48,900.00  │ │ +$450.25    │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

**Open Positions Table**
```
| Symbol | Qty | Side | Entry Price | Current | Market Value | Unrealized P&L | P&L % |
|--------|-----|------|-------------|---------|--------------|----------------|-------|
| AAPL | 28 | LONG | $173.50 | $175.80 | $4,922.40 | +$64.40 | +1.33% |
| MSFT | 15 | LONG | $380.20 | $378.50 | $5,677.50 | -$25.50 | -0.45% |

[Refresh Positions]
```

**Manual Trading Controls** (Optional)
```
Quick Order:
Symbol: [____] Qty: [__] Side: [Buy ▼] Type: [Market ▼]
[Place Order]
```

---

#### Tab 4: Trade History

**Filters**
```
Date Range: [Start] to [End]
Symbol: [All ▼]
Status: [All ▼] (Filled, Cancelled, Rejected)
[Apply Filters]
```

**Trades Table**
```
| Date/Time | Symbol | Timeframe | Action | Status | Notional | Qty | Avg Price | Order ID |
|-----------|--------|-----------|--------|--------|----------|-----|-----------|----------|
| Jan 15 10:32 | AAPL | 15 Min | BUY | FILLED | $5,000 | 28.5 | $175.44 | abc123 |
| Jan 15 14:15 | AAPL | 15 Min | SELL | FILLED | $5,080 | 28.5 | $178.25 | def456 |

[Export CSV]
```

---

#### Tab 5: Performance

**Summary Metrics**
```
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Total P&L   │ │ Total Trades│ │ Active Bots │ │ Win Rate    │
│ +$1,245.80  │ │ 48          │ │ 3 / 5       │ │ 62%         │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

**Per-Symbol Performance Table**
```
| Symbol | Timeframe | P&L | Trades | Win Rate | Avg Win | Avg Loss | Status |
|--------|-----------|-----|--------|----------|---------|----------|--------|
| AAPL | 15 Min | +$890 | 24 | 67% | $78 | -$45 | IDLE |
| TSLA | 1 Hour | +$355 | 18 | 56% | $92 | -$68 | LONG |
| SPY | 5 Min | +$0 | 0 | - | - | - | IDLE |
```

**Equity Curve Chart**
```
Line chart showing cumulative P&L over time
- X-axis: Date
- Y-axis: Cumulative P&L ($)
- Trade markers on chart
```

---

#### Tab 6: Risk Events

**Risk Events Log**
```
| Date/Time | Event Type | Symbol | Timeframe | Threshold | Actual | Action Taken |
|-----------|------------|--------|-----------|-----------|--------|--------------|
| Jan 14 15:30 | DAILY_LOSS_LIMIT | TSLA | 1 Hour | $500 | -$520 | Bot disabled |
| Jan 12 11:15 | RISK_LIMIT_HIT | AAPL | 15 Min | 10% | -11.2% | Position closed |
```

**Risk Event Types:**
```
- DAILY_LOSS_LIMIT - Daily loss exceeded threshold
- RISK_LIMIT_HIT - Single position loss exceeded threshold
- POSITION_SIZE_EXCEEDED - Attempted order too large
- CONNECTION_ERROR - API connection lost
```

---

### 4.8 ADMIN PANEL (Admin/Superadmin Only)

**User Management Table**
```
| ID | Username | Email | Role | Status | Last Login | Actions |
|----|----------|-------|------|--------|------------|---------|
| 1 | admin | admin@test.com | admin | Active | Jan 15 | [Edit] |
| 2 | trader1 | t1@test.com | user | Active | Jan 14 | [Edit] [Deactivate] |
| 3 | trader2 | t2@test.com | user | Inactive | Dec 20 | [Activate] [Delete] |

[+ Add User]
```

**Edit User Modal**
```
Username: [readonly]
Email: [editable]
Full Name: [editable]
Role: [user ▼] (user/admin, superadmin can't be changed)
Status: ○ Active ○ Inactive
[Save Changes]
```

**System Statistics**
```
- Total Users: 45
- Active Users (last 7 days): 28
- Total Bots Running: 67
- Total Trades Today: 234
- System Uptime: 99.9%
```

---

### 4.9 SETTINGS / PROFILE

**Profile Section**
```
Username: [readonly]
Email: [editable]
Full Name: [editable]
[Save Profile]
```

**Change Password**
```
Current Password: [______]
New Password: [______]
Confirm New Password: [______]
[Change Password]
```

**Notification Preferences**
```
☑ Email alerts for triggered price alerts
☑ Email alerts for bot trades
☑ Daily performance summary email
☐ Marketing emails
[Save Preferences]
```

**API Keys Management**
```
Alpha Vantage API Key: [*************] [Show] [Update]
Claude API Key (AI Assistant): [*************] [Show] [Update]
```

**Theme Preferences**
```
○ Light Mode
● Dark Mode (recommended for trading)
○ System Default
```

---

## 5. DATA FLOW & API STRUCTURE

### Base URL Structure
```
Production: https://your-domain.com/api
Development: http://localhost:8501/api

Authentication: Session-based (cookie) or JWT token in header
```

### Core API Endpoints Summary

```
AUTHENTICATION
--------------
POST /api/auth/login
POST /api/auth/register
POST /api/auth/logout
GET  /api/auth/me

STOCK ANALYSIS
--------------
GET  /api/analyze/{symbol}?period=1y&interval=1d
GET  /api/quote/{symbol}

WATCHLIST
---------
GET    /api/watchlist
POST   /api/watchlist
DELETE /api/watchlist/{symbol}
PUT    /api/watchlist/{symbol}/notes

ALERTS
------
GET    /api/alerts
POST   /api/alerts
PUT    /api/alerts/{id}
DELETE /api/alerts/{id}
POST   /api/alerts/{id}/reset

BACKTESTING
-----------
POST /api/backtest
Body: {symbol, strategy, start_date, end_date, config}

STRATEGIES
----------
GET    /api/strategies
POST   /api/strategies
PUT    /api/strategies/{id}
DELETE /api/strategies/{id}

TRADING BOT
-----------
GET    /api/bot/account
GET    /api/bot/positions
GET    /api/bot/orders
POST   /api/bot/keys
DELETE /api/bot/keys

GET    /api/bot/configs
POST   /api/bot/configs
PUT    /api/bot/configs/{id}
DELETE /api/bot/configs/{id}
PUT    /api/bot/configs/{id}/toggle

GET    /api/bot/trades?limit=100
GET    /api/bot/performance
GET    /api/bot/risk-events

POST   /webhook?token={token}  (external webhook endpoint)

ADMIN
-----
GET    /api/admin/users
PUT    /api/admin/users/{id}
DELETE /api/admin/users/{id}
GET    /api/admin/stats

PREFERENCES
-----------
GET  /api/preferences
PUT  /api/preferences
```

---

## 6. UI/UX DESIGN GUIDELINES

### Color Palette
```
Primary Gradient: #667eea → #764ba2 (Purple)
Success/Bullish: #00c853 (Green)
Error/Bearish: #ff1744 (Red)
Warning: #ff9100 (Orange)
Info: #2196f3 (Blue)
Neutral: #9e9e9e (Gray)

Background (Dark Mode):
- Primary: #121212
- Surface: #1e1e1e
- Card: #2d2d2d

Background (Light Mode):
- Primary: #ffffff
- Surface: #f5f5f5
- Card: #ffffff
```

### Typography
```
Headings: Inter or SF Pro Display (bold)
Body: Inter or SF Pro Text (regular)
Monospace (prices, code): JetBrains Mono or SF Mono
Numbers: Tabular figures for alignment
```

### Component Styling
```
Cards:
- Border radius: 12px
- Shadow: 0 4px 6px rgba(0,0,0,0.1)
- Padding: 20px

Buttons:
- Primary: Gradient background, white text
- Secondary: Outlined, primary color
- Danger: Red background, white text
- Border radius: 8px

Inputs:
- Border radius: 8px
- Border: 2px solid gray
- Focus: Primary color border with glow

Tables:
- Alternating row colors
- Sticky header
- Hover highlight
- Sortable columns
```

### Chart Styling
```
Candlesticks:
- Bullish: #00c853 (filled green)
- Bearish: #ff1744 (filled red)
- Wick same color as body

Background: Transparent or match theme
Grid: Subtle, low opacity
Crosshair: White with price label
```

### Responsive Breakpoints
```
Mobile: < 768px (single column, collapsed sidebar)
Tablet: 768px - 1024px (condensed layout)
Desktop: > 1024px (full layout)
Large: > 1440px (expanded charts)
```

### Animations
```
- Page transitions: Fade 200ms
- Card hover: Scale 1.02, shadow increase
- Button press: Scale 0.98
- Loading: Skeleton shimmer or spinner
- Charts: Smooth data transitions
- Notifications: Slide in from right
```

---

## 7. MOBILE CONSIDERATIONS

### Priority Features for Mobile
```
1. Quick stock lookup and price check
2. View watchlist with signals
3. Check bot status and P&L
4. Receive and view alerts
5. Basic chart viewing (simplified)
```

### Mobile-Specific UI
```
- Bottom navigation bar instead of sidebar
- Swipe gestures for tabs
- Pull-to-refresh
- Simplified charts (no overlays toggle)
- Large touch targets (44px minimum)
- Floating action button for quick actions
```

---

## 8. REAL-TIME FEATURES

### WebSocket Connections (Future Enhancement)
```
- Live price updates for watchlist
- Real-time bot status changes
- Instant alert notifications
- Position P&L updates
```

### Polling Fallback
```
- Watchlist prices: Every 30 seconds
- Bot positions: Every 10 seconds
- Active trades: Every 5 seconds during market hours
```

---

## 9. ERROR HANDLING

### Error States to Design
```
1. Network Error
   - Message: "Unable to connect. Check your internet."
   - Action: Retry button

2. Authentication Error
   - Message: "Session expired. Please log in again."
   - Action: Redirect to login

3. Not Found
   - Message: "Symbol not found"
   - Action: Search suggestions

4. Rate Limited
   - Message: "Too many requests. Please wait."
   - Action: Auto-retry countdown

5. Server Error
   - Message: "Something went wrong. We're on it."
   - Action: Report issue link

6. Empty State
   - Watchlist: "No stocks yet. Add your first!"
   - Bots: "No bots configured. Create one!"
   - Trades: "No trades yet. Your history will appear here."
```

---

## 10. NOTIFICATIONS

### Notification Types
```
Toast Notifications (temporary):
- Success: Green, 3 seconds
- Error: Red, 5 seconds (or until dismissed)
- Warning: Orange, 4 seconds
- Info: Blue, 3 seconds

Alert Banners (persistent):
- At top of page for important messages
- Dismissible with X button

Push Notifications (mobile):
- Price alerts triggered
- Bot trade executed
- Risk event occurred
```

---

## 11. LOADING STATES

### Skeleton Screens
```
- Tables: Row skeletons
- Cards: Card-shaped skeletons
- Charts: Chart area with shimmer
- Profile: Avatar + text skeletons
```

### Spinners
```
- Full page: Centered with app logo
- Inline: Small spinner next to text
- Button: Replace button text while loading
```

---

## 12. SUGGESTED TECH STACK FOR LOVABLE

```
Framework: React or Next.js
State Management: Zustand or React Query
UI Components: Tailwind CSS + Shadcn/ui
Charts: TradingView Lightweight Charts or Recharts
Forms: React Hook Form + Zod validation
Tables: TanStack Table
Icons: Lucide React
Animations: Framer Motion
Date Handling: date-fns
HTTP Client: Axios or fetch with React Query
```

---

## 13. SAMPLE SCREENS PRIORITY ORDER

### Phase 1 - Core (MVP)
1. Login / Register
2. Single Stock Analysis (main chart)
3. Portfolio Dashboard (watchlist)
4. Navigation / Layout

### Phase 2 - Analysis
5. Multi-Stock Comparison
6. Alert Manager
7. Backtesting

### Phase 3 - Automation
8. Trading Bot (all tabs)
9. Strategy Builder

### Phase 4 - Admin
10. Admin Panel
11. Settings / Profile

---

## 14. ACCESSIBILITY REQUIREMENTS

```
- WCAG 2.1 AA compliance
- Keyboard navigation for all features
- Screen reader support
- Color contrast ratios (4.5:1 minimum)
- Focus indicators
- Alt text for charts (data table alternative)
- Reduced motion option
```

---

## APPENDIX A: SAMPLE API RESPONSES

### Stock Analysis Response
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "current_price": 175.50,
    "change": 3.25,
    "change_percent": 1.89,
    "signal": "BULLISH",
    "signal_strength": 4,
    "last_updated": "2024-01-15T16:00:00Z",

    "price_data": [...],
    "indicators": {...},
    "patterns": [...],
    "support_resistance": [...]
  }
}
```

### Login Response
```json
{
  "success": true,
  "user": {
    "id": 123,
    "username": "trader1",
    "email": "trader1@email.com",
    "role": "user",
    "full_name": "John Trader"
  },
  "token": "jwt_token_here"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "INVALID_SYMBOL",
    "message": "Stock symbol 'XYZ' not found",
    "details": null
  }
}
```

---

## APPENDIX B: KEYBOARD SHORTCUTS (Optional Enhancement)

```
Global:
- Cmd/Ctrl + K: Quick search
- Cmd/Ctrl + /: Toggle sidebar
- Escape: Close modal/dialog

Analysis:
- A: Add to watchlist
- R: Refresh data
- 1-4: Switch tabs

Trading Bot:
- N: New bot
- E: Toggle bot enable/disable
```

---

## END OF SPECIFICATION

This document provides complete specifications for building a modern frontend for the DashTrade trading platform. The backend is fully functional with PostgreSQL database, authentication, real trading integration, and comprehensive analysis features.

For questions about the backend API or clarification on any feature, refer to the Python codebase or contact the development team.
