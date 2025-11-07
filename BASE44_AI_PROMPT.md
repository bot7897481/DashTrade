# Base44.AI Design Prompt - Stock Trading Technical Analysis Platform

## PROJECT OVERVIEW

Design a production-ready, multi-user stock trading technical analysis platform with the following specifications:

**Platform Name:** DashTrade (or similar professional trading platform)

**Primary Purpose:** Provide retail and professional traders with comprehensive technical analysis tools, backtesting capabilities, portfolio management, and custom strategy building in an intuitive web-based interface.

**Target Users:**
- Individual retail traders (primary)
- Trading teams and small investment firms
- Financial advisors
- Trading educators and students

**Core Value Proposition:**
- 35+ technical indicators and pattern recognition
- Real-time and historical market data from multiple sources
- Custom strategy building with visual tools
- Robust backtesting engine with detailed performance metrics
- Multi-user support with role-based access control
- Portfolio-wide monitoring and alerting

---

## TECHNICAL ARCHITECTURE

### 1. SYSTEM ARCHITECTURE

**Architecture Pattern:** Modular MVC-like with reactive UI paradigm

**Technology Stack:**

**Backend:**
- Language: Python 3.11+
- Web Framework: Streamlit 1.50.0 (for rapid reactive UI development)
- Database: PostgreSQL (latest stable)
- ORM/DB Adapter: psycopg2-binary or SQLAlchemy

**Data Processing:**
- Pandas (time series manipulation)
- NumPy (numerical computation)
- TA-Lib or TA library (technical indicators)
- SciPy (statistical analysis, correlation)

**Data Sources:**
- yfinance (Yahoo Finance API - primary, unlimited usage)
- Alpha Vantage API (optional, real-time data, news sentiment)
- Extensible to add more providers (Polygon.io, IEX Cloud, etc.)

**Visualization:**
- Plotly (interactive candlestick charts, equity curves)
- Matplotlib (supporting charts, heatmaps)

**Security:**
- bcrypt (password hashing)
- streamlit-authenticator or custom JWT (session management)

**Optional Enhancements:**
- Redis (caching, session store for scaling)
- Celery (background tasks, alert monitoring)
- Docker (containerization)
- Nginx (reverse proxy, load balancing)

### 2. APPLICATION LAYERS

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│  Technology: Streamlit (reactive web interface)             │
│  Components:                                                │
│  • Login/Registration UI                                    │
│  • Multi-mode dashboard (7 modes)                           │
│  • Interactive charts (Plotly)                              │
│  • Data tables (styled pandas DataFrames)                   │
│  • Forms and input widgets                                  │
│  • Sidebar navigation and configuration                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                      │
│  Modules:                                                   │
│                                                             │
│  1. TechnicalAnalyzer (technical_analyzer.py)               │
│     • Moving averages (EMAs: 9, 20, 50, 100, 200)          │
│     • MA Cloud visualization                                │
│     • QQE (Quantified Qualitative Estimation) signals       │
│     • VWAP with bands                                       │
│     • 15+ candlestick patterns                              │
│     • 20+ chart patterns                                    │
│     • Support/resistance detection                          │
│     • Volume analysis (Bulkowski methodology)               │
│     • Signal tracking and history                           │
│                                                             │
│  2. Backtester (backtester.py)                              │
│     • Trade execution simulation                            │
│     • Risk management (stop loss, take profit)              │
│     • Position sizing                                       │
│     • Performance metrics (Sharpe, max drawdown)            │
│     • Trade logging and CSV export                          │
│                                                             │
│  3. StrategyBuilder (strategy_builder.py)                   │
│     • Custom condition builder                              │
│     • Indicator comparison logic                            │
│     • AND/OR rule combinations                              │
│     • Pre-built templates                                   │
│     • Strategy testing interface                            │
│                                                             │
│  4. ComparisonAnalyzer (comparison_analyzer.py)             │
│     • Multi-stock performance comparison                    │
│     • Correlation matrix calculation                        │
│     • Relative strength analysis                            │
│     • Sector strength ranking                               │
│                                                             │
│  5. AlertMonitor (alert_system.py)                          │
│     • Condition evaluation engine                           │
│     • Alert triggering logic                                │
│     • Notification system                                   │
│                                                             │
│  6. DataProvider (alpha_vantage_data.py, etc.)              │
│     • Multi-source data fetching                            │
│     • API rate limit management                             │
│     • Data caching (5-minute TTL)                           │
│     • News sentiment integration                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    DATA ACCESS LAYER                        │
│  Modules:                                                   │
│                                                             │
│  1. UserDB (auth.py)                                        │
│     • User registration with validation                     │
│     • Authentication (bcrypt hashing)                       │
│     • Role-based access (user/admin/superadmin)             │
│     • Session management                                    │
│     • Last login tracking                                   │
│                                                             │
│  2. WatchlistDB (database.py)                               │
│     • Add/remove stocks from user watchlists                │
│     • Multi-user isolation                                  │
│     • Notes and metadata per stock                          │
│                                                             │
│  3. AlertsDB (database.py)                                  │
│     • Store user-defined alerts                             │
│     • Track trigger status                                  │
│     • Alert history                                         │
│                                                             │
│  4. PreferencesDB (database.py)                             │
│     • Key-value store for user settings                     │
│     • Theme preferences, default parameters, etc.           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   PERSISTENCE LAYER                         │
│  PostgreSQL Database Schema:                                │
│                                                             │
│  • users (authentication, roles, metadata)                  │
│  • watchlist (user stock lists)                             │
│  • alerts (price & technical alerts)                        │
│  • user_preferences (settings)                              │
│                                                             │
│  Indexes: user_id, symbol, alert_type for performance       │
│  Constraints: CASCADE DELETE, UNIQUE constraints            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  EXTERNAL DATA SOURCES                      │
│                                                             │
│  • Yahoo Finance (yfinance library)                         │
│    - Historical and recent data                             │
│    - 15-minute delay, unlimited usage                       │
│    - Intervals: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo         │
│                                                             │
│  • Alpha Vantage API (optional)                             │
│    - Real-time data                                         │
│    - News sentiment analysis                                │
│    - 25 API calls/day free tier                             │
│                                                             │
│  • Extensible for future providers                          │
│    - Polygon.io, IEX Cloud, Twelve Data, etc.               │
└─────────────────────────────────────────────────────────────┘
```

### 3. DATABASE SCHEMA

Design a PostgreSQL database with the following tables:

```sql
-- Authentication and User Management
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt hashed
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user' NOT NULL,  -- user, admin, superadmin
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- User Watchlists
CREATE TABLE watchlist (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,  -- Stock ticker
    name VARCHAR(255),  -- Company name
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    UNIQUE(user_id, symbol)  -- One symbol per user
);

-- Alert System
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    alert_type VARCHAR(100) NOT NULL,  -- qqe_long, price_above, ema_cross, etc.
    condition_text TEXT,  -- Human-readable condition
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    triggered_at TIMESTAMP,  -- When alert was triggered
    is_active BOOLEAN DEFAULT TRUE
);

-- User Preferences (Key-Value Store)
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    value TEXT,  -- JSON or plain text
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, key)
);

-- Performance Indexes
CREATE INDEX idx_watchlist_user ON watchlist(user_id);
CREATE INDEX idx_alerts_user ON alerts(user_id);
CREATE INDEX idx_alerts_symbol ON alerts(symbol);
CREATE INDEX idx_alerts_active ON alerts(is_active);
CREATE INDEX idx_preferences_user ON user_preferences(user_id);
```

**Relationships:**
- One user → Many watchlist entries (CASCADE DELETE)
- One user → Many alerts (CASCADE DELETE)
- One user → Many preferences (CASCADE DELETE)

---

## FUNCTIONAL REQUIREMENTS

### 1. USER AUTHENTICATION & MANAGEMENT

**Features:**
- User registration with validation
  - Username: 3+ characters, unique
  - Email: Valid format, unique
  - Password: 6+ characters, bcrypt hashing
  - Full name (optional)
- Login with username/password
- Session persistence across page refreshes
- Role-based access control:
  - **User:** Access to all analysis features
  - **Admin:** Can manage other users (except superadmins)
  - **Superadmin:** Full system control
- User profile management
- Last login tracking
- Account activation/deactivation

**Admin Panel (Admin/Superadmin only):**
- View all users table
- Change user roles
- Activate/deactivate accounts
- View system statistics (total users, active users, etc.)

### 2. SINGLE STOCK ANALYSIS MODE

**Input:**
- Stock symbol (text input, auto-uppercase)
- Timeframe:
  - Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max
  - Interval: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo
- QQE parameters (customizable):
  - RSI period (default: 14)
  - Smoothing factor (default: 5)
  - QQE factor (default: 4.236)
- Data source selection (Yahoo Finance or Alpha Vantage)

**Output (4 Tabs):**

**Tab 1: Overview**
- **Candlestick Chart:**
  - Price action with candlesticks
  - 5 EMA overlays (9, 20, 50, 100, 200)
  - MA Cloud (filled area between short and long EMAs)
  - Signal annotations (green "Long", red "Short")
  - Interactive legend (toggle EMAs on/off)
- **QQE Panel (below price chart):**
  - QQE indicator line
  - Long/short signal zones
  - Signal markers
- **Volume Panel:**
  - Volume bars (color-coded: green up, red down)
  - Volume surge detection
- **Key Metrics Cards:**
  - Current price
  - Price change (% and absolute)
  - Volume
  - QQE value
  - Trend (bullish/bearish/neutral)
  - Signal count (1h, 4h, 24h)

**Tab 2: Patterns**
- **Candlestick Patterns Detected (15+):**
  - Pattern name, timeframe, bullish/bearish indication
  - Historical reliability score (if available)
  - Table with most recent patterns
- **Chart Patterns Detected (20+):**
  - Pattern type (e.g., Head & Shoulders, Double Top)
  - Support/resistance levels
  - Price target (measure rule)
  - Pattern strength score
  - Visual markers on chart (optional)
- **Pattern Descriptions:**
  - Explanation of each pattern detected
  - Trading implications

**Tab 3: Support & Resistance**
- **Support Levels Table:**
  - Price level
  - Strength score (1-5)
  - Number of touches
  - Distance from current price
- **Resistance Levels Table:**
  - Same structure as support
- **Key Levels Chart:**
  - Horizontal lines on price chart
  - Color-coded by strength

**Tab 4: Detailed Metrics**
- **Trend Analysis:**
  - Short-term trend (MA Cloud)
  - Medium-term trend (50 EMA)
  - Long-term trend (200 EMA)
  - Overall trend consensus
- **Volume Analysis:**
  - Average volume (20-day)
  - Current volume vs average
  - Volume surge indicator
  - Bulkowski volume methodology result
- **Volatility Metrics:**
  - ATR (Average True Range)
  - Bollinger Band width
  - Historical volatility
- **Performance Metrics:**
  - Returns (1d, 1w, 1m, 3m, 6m, 1y)
  - Maximum drawdown (period)
  - Sharpe ratio (if sufficient data)

### 3. PORTFOLIO DASHBOARD MODE

**Features:**
- **Watchlist Integration:**
  - Display all stocks from user's watchlist
  - Add/remove stocks directly from dashboard
- **Batch Analysis:**
  - Analyze all watchlist stocks at once
  - Two modes:
    - **Full Analysis:** Complete technical analysis (slower)
    - **Quick Mode:** Essential indicators only (faster)
- **Portfolio Summary:**
  - Total stocks monitored
  - Bullish signals count
  - Bearish signals count
  - Neutral count
  - Active alerts triggered
- **Stock Table:**
  - Columns: Symbol, Name, Price, Change %, Trend, QQE Signal, Alerts
  - Sortable by any column
  - Click to jump to single stock analysis
- **Alert Status:**
  - Visual indicators for triggered alerts
  - Quick access to alert details
- **Refresh Control:**
  - Manual refresh button
  - Auto-refresh option (every N minutes)

### 4. MULTI-STOCK COMPARISON MODE

**Features:**
- **Stock Selection:**
  - Choose multiple stocks from watchlist
  - Or manually enter symbols (comma-separated)
  - Support 2-10 stocks per comparison
- **Timeframe Selection:**
  - Period: 1mo, 3mo, 6mo, 1y, 2y, 5y
- **Normalized Performance Chart:**
  - All stocks start at 100 (baseline)
  - Shows relative performance over time
  - Interactive Plotly chart with legend
- **Correlation Matrix:**
  - Heatmap showing correlation coefficients
  - Color scale: -1 (red) to +1 (green)
  - Identify strongly correlated pairs
- **Performance Metrics Table:**
  - Stock, Total Return %, Volatility, Sharpe Ratio
  - Best/worst performers highlighted
- **Relative Strength:**
  - Compare each stock vs benchmark (e.g., SPY)
  - Rank stocks by relative strength
- **Sector Analysis:**
  - Group stocks by sector (if data available)
  - Sector strength ranking

### 5. BACKTESTING MODE

**Features:**
- **Strategy Selection:**
  - Pre-built strategies:
    1. **QQE Strategy:** Long on QQE bullish, short on bearish
    2. **EMA Crossover:** 9 EMA crosses 20 EMA
    3. **MA Cloud Trend:** Trade based on MA cloud color
  - Custom strategies (from Strategy Builder)
- **Input Parameters:**
  - Stock symbol
  - Backtest period (start date, end date or period)
  - Initial capital (default: $10,000)
  - Position sizing (% of capital per trade, default: 100%)
  - Risk management:
    - Stop loss (% or ATR multiplier)
    - Take profit (% or risk/reward ratio)
- **Backtest Execution:**
  - Simulate trades based on strategy
  - Track entry/exit prices, P&L
  - Apply stop loss and take profit
  - Calculate performance metrics
- **Results Display:**
  - **Equity Curve Chart:**
    - Portfolio value over time
    - Drawdown shading
    - Buy/sell markers
  - **Performance Metrics:**
    - Total return (%)
    - CAGR (annualized return)
    - Win rate (%)
    - Profit factor (gross profit / gross loss)
    - Sharpe ratio
    - Maximum drawdown (%)
    - Average win / average loss
    - Largest win / largest loss
    - Total trades
    - Longest winning/losing streak
    - Average trade duration
  - **Trade Log Table:**
    - Entry date, entry price
    - Exit date, exit price
    - Direction (long/short)
    - P&L ($, %)
    - Duration (days)
    - Exit reason (signal, stop loss, take profit)
  - **CSV Export:**
    - Download complete trade log
- **Comparison Mode:**
  - Run multiple strategies on same stock
  - Compare results side-by-side

### 6. STRATEGY BUILDER MODE

**Features:**
- **Custom Strategy Creation:**
  - Name your strategy
  - Define entry conditions (long and/or short)
  - Define exit conditions
- **Condition Builder:**
  - **Indicator Selection:**
    - Price (close, open, high, low)
    - Moving averages (SMA, EMA)
    - RSI, MACD, Stochastic
    - Bollinger Bands
    - ATR, ADX
    - QQE
    - Volume
    - And 15+ more indicators
  - **Comparison Operators:**
    - Greater than, less than
    - Crosses above, crosses below
    - Equal to, not equal to
  - **Logic Operators:**
    - AND (all conditions must be true)
    - OR (any condition must be true)
  - **Value Types:**
    - Fixed numbers (e.g., RSI > 70)
    - Other indicators (e.g., EMA9 > EMA20)
    - Percentage of price (e.g., Stop loss at 2% below entry)
- **Entry Rules:**
  - **Long Entry:** Define conditions for buy signal
  - **Short Entry:** Define conditions for short signal (optional)
- **Exit Rules:**
  - **Long Exit:** When to close long positions
  - **Short Exit:** When to close short positions
  - **Universal Exit:** Applies to both (e.g., time-based)
- **Pre-built Templates:**
  - **Trend Following:** EMA crossover with trend filter
  - **Mean Reversion:** Bollinger Band bounce
  - **Momentum:** RSI + MACD combination
  - **Breakout:** Price breaks resistance with volume confirmation
- **Strategy Testing:**
  - Save strategy
  - Immediately test with backtester
  - Iterate and refine
- **Strategy Library:**
  - View all saved strategies
  - Edit, delete, duplicate strategies
  - Share with other users (optional advanced feature)

### 7. ALERT MANAGER MODE

**Features:**
- **Alert Creation:**
  - **Alert Types:**
    1. **Price Alerts:**
       - Price goes above X
       - Price goes below X
       - Price crosses above X
       - Price crosses below X
    2. **Indicator Alerts:**
       - QQE long signal
       - QQE short signal
       - RSI > 70 (overbought)
       - RSI < 30 (oversold)
       - And more...
    3. **Trend Alerts:**
       - MA Cloud turns bullish
       - MA Cloud turns bearish
       - Stock enters uptrend (price > 200 EMA)
    4. **Crossover Alerts:**
       - EMA 9 crosses above EMA 20
       - EMA 9 crosses below EMA 20
       - Price crosses VWAP
  - **Configuration:**
    - Stock symbol
    - Alert type
    - Condition details (price level, indicator threshold, etc.)
    - Human-readable condition text
- **Active Alerts List:**
  - Table showing all user's alerts
  - Columns: Symbol, Type, Condition, Created, Status
  - Status: Active, Triggered, Inactive
  - Actions: Delete, Edit (optional), Deactivate
- **Alert Triggering:**
  - Auto-check alerts when viewing Portfolio Dashboard
  - Mark as triggered with timestamp
  - Visual notification (colored badge, icon)
  - Optional: Email/SMS notification (advanced feature)
- **Alert History:**
  - View triggered alerts log
  - Filter by symbol, date range
  - Reset triggered alerts to active

### 8. ADMIN PANEL MODE (Admin/Superadmin Only)

**Features:**
- **User Management Table:**
  - Columns: ID, Username, Email, Full Name, Role, Created, Last Login, Active
  - Sortable and searchable
- **User Actions:**
  - **Change Role:**
    - Dropdown to select new role (user/admin/superadmin)
    - Admins cannot modify superadmins
    - Superadmins can modify all
  - **Activate/Deactivate Account:**
    - Toggle active status
    - Deactivated users cannot log in
  - **View User Activity:**
    - Last login, created date
    - Number of watchlist stocks
    - Number of alerts
- **System Statistics:**
  - Total users
  - Active users
  - New users (last 7 days, 30 days)
  - Total watchlist entries
  - Total alerts
  - Database size (optional)
- **Audit Log (Optional Advanced Feature):**
  - Track admin actions
  - User login history
  - System changes log

---

## NON-FUNCTIONAL REQUIREMENTS

### 1. PERFORMANCE

- **Page Load Time:** < 2 seconds for dashboard
- **Chart Rendering:** < 1 second for single stock
- **Backtesting:** < 5 seconds for 1 year of daily data
- **Batch Analysis:** < 30 seconds for 10 stocks (quick mode)
- **Data Caching:** 5-minute TTL to reduce API calls
- **Database Queries:** < 100ms for typical operations
- **Concurrent Users:** Support 100+ simultaneous users (with proper scaling)

### 2. SCALABILITY

- **Horizontal Scaling:** Support multiple Streamlit instances with shared session store (Redis)
- **Database:** PostgreSQL with read replicas for high traffic
- **Caching:** Distributed cache (Redis) for multi-instance deployments
- **Background Tasks:** Celery for alert monitoring and data updates
- **Load Balancing:** Nginx or cloud load balancer

### 3. SECURITY

- **Password Security:**
  - bcrypt hashing (12 rounds minimum)
  - Minimum 6 characters
  - No plain text storage
- **Session Management:**
  - Secure session tokens
  - Auto-logout after inactivity (30 minutes)
  - XSRF protection enabled
- **Input Validation:**
  - Server-side validation for all inputs
  - SQL injection prevention (parameterized queries)
  - XSS prevention (escape user inputs)
- **HTTPS:**
  - Enforce HTTPS in production
  - Redirect HTTP to HTTPS
- **API Keys:**
  - Store in environment variables
  - Never expose in client-side code
- **Rate Limiting (Optional):**
  - Limit login attempts (5 per minute)
  - Limit API calls per user
- **Audit Logging:**
  - Track admin actions
  - Log authentication events

### 4. RELIABILITY

- **Error Handling:**
  - Graceful degradation for API failures
  - User-friendly error messages
  - Fallback to cached data when available
- **Data Integrity:**
  - Database constraints (UNIQUE, FOREIGN KEY)
  - Transaction management for critical operations
  - Automated backups (daily recommended)
- **Monitoring:**
  - Application health checks
  - Database connection monitoring
  - Error tracking (Sentry or similar)
- **Uptime:** 99.5%+ availability target

### 5. USABILITY

- **Intuitive UI:**
  - Clear navigation with sidebar
  - Consistent design patterns
  - Helpful tooltips and hints
- **Responsive Design:**
  - Optimized for desktop (primary)
  - Tablet support
  - Mobile view (basic support, Streamlit limitation)
- **Accessibility:**
  - Keyboard navigation where possible
  - Color contrast compliance
  - Alt text for icons
- **Loading Indicators:**
  - Spinners for data fetching
  - Progress bars for long operations
- **Feedback:**
  - Success/error messages
  - Confirmation dialogs for destructive actions

### 6. MAINTAINABILITY

- **Code Quality:**
  - Modular design with clear separation of concerns
  - Type hints in Python code
  - Docstrings for all functions
  - Consistent naming conventions
- **Documentation:**
  - README with quick start guide
  - Deployment guide
  - API documentation (if REST API added)
  - User manual
- **Testing:**
  - Unit tests (pytest)
  - Integration tests
  - End-to-end tests (optional)
  - Target: 70%+ code coverage
- **Version Control:**
  - Git with semantic versioning
  - Branching strategy (main, develop, feature branches)
  - Pull request reviews

---

## UI/UX DESIGN SPECIFICATIONS

### 1. LAYOUT

**Overall Structure:**
```
┌────────────────────────────────────────────────────────────┐
│                         HEADER                             │
│  Logo: 📈 [Platform Name] Trading Signals                 │
│  Subtitle: Comprehensive Stock Technical Analysis         │
└────────────────────────────────────────────────────────────┘

┌──────────────┬─────────────────────────────────────────────┐
│   SIDEBAR    │          MAIN CONTENT AREA                  │
│   (300px)    │           (Remaining width)                 │
│              │                                             │
│ ┌──────────┐ │  ┌────────────────────────────────────┐    │
│ │ Logo     │ │  │                                    │    │
│ │ 👤 User  │ │  │      MODE-SPECIFIC CONTENT         │    │
│ │ 🚪 Logout│ │  │                                    │    │
│ └──────────┘ │  │  • Inputs (forms, selects)         │    │
│              │  │  • Charts (interactive Plotly)     │    │
│ Data Source  │  │  • Tables (styled DataFrames)      │    │
│ ● Yahoo      │  │  • Metrics (card layout)           │    │
│ ○ AlphaVant  │  │  • Actions (buttons)               │    │
│              │  │                                    │    │
│ ─────────    │  └────────────────────────────────────┘    │
│              │                                             │
│ Mode Select  │  ┌────────────────────────────────────┐    │
│ ● Single     │  │         TABBED VIEWS               │    │
│ ○ Portfolio  │  │  ┌────┬────┬────┬────┐            │    │
│ ○ Compare    │  │  │Tab1│Tab2│Tab3│Tab4│            │    │
│ ○ Backtest   │  │  └────┴────┴────┴────┘            │    │
│ ○ Strategy   │  │                                    │    │
│ ○ Alerts     │  │  Detailed analysis results         │    │
│ ○ Admin      │  │                                    │    │
│              │  └────────────────────────────────────┘    │
│ ─────────    │                                             │
│              │                                             │
│ 📊 Watchlist │                                             │
│ ┌──────────┐ │                                             │
│ │ AAPL  🗑️ │ │                                             │
│ │ TSLA  🗑️ │ │                                             │
│ │ NVDA  🗑️ │ │                                             │
│ │ [+ Add]  │ │                                             │
│ └──────────┘ │                                             │
└──────────────┴─────────────────────────────────────────────┘
```

### 2. COLOR SCHEME

**Primary Colors:**
- **Green:** `#00c853` - Bullish signals, long positions, success messages
- **Red:** `#ff1744` - Bearish signals, short positions, warnings
- **Blue:** `#2196f3` - Neutral, informational, links

**Background:**
- **Main:** `#ffffff` (white)
- **Secondary:** `#f0f2f6` (light gray)
- **Card:** `#fafafa` (off-white)

**Text:**
- **Primary:** `#262730` (dark gray)
- **Secondary:** `#6c757d` (medium gray)
- **Muted:** `#adb5bd` (light gray)

**Chart Colors:**
- **Candlestick Up:** Green (`#00c853`)
- **Candlestick Down:** Red (`#ff1744`)
- **EMA 9:** Blue (`#2196f3`)
- **EMA 20:** Orange (`#ff9800`)
- **EMA 50:** Purple (`#9c27b0`)
- **EMA 100:** Brown (`#795548`)
- **EMA 200:** Gray (`#607d8b`)
- **Volume:** Light blue with transparency (`rgba(33, 150, 243, 0.3)`)

**Alert/Status Colors:**
- **Success:** Green
- **Warning:** Orange (`#ff9800`)
- **Error:** Red
- **Info:** Blue

### 3. TYPOGRAPHY

**Font Family:**
- **Primary:** -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
- **Monospace (metrics):** Courier New, monospace

**Headers:**
- **H1:** 3rem (48px), bold, centered
- **H2:** 2rem (32px), bold
- **H3:** 1.5rem (24px), semi-bold
- **H4:** 1.25rem (20px), semi-bold

**Body:**
- **Regular:** 1rem (16px), normal weight
- **Small:** 0.875rem (14px)
- **Tiny:** 0.75rem (12px)

**Metrics/Numbers:**
- **Large:** 2rem, bold, monospace
- **Medium:** 1.5rem, semi-bold, monospace
- **Small:** 1rem, normal, monospace

### 4. COMPONENT DESIGN

**Metric Cards:**
```css
.metric-card {
    background: #fafafa;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 8px 0;
}

.metric-card .label {
    font-size: 0.875rem;
    color: #6c757d;
    margin-bottom: 4px;
}

.metric-card .value {
    font-size: 2rem;
    font-weight: bold;
    color: #262730;
}

.metric-card .change {
    font-size: 1rem;
    margin-top: 4px;
}

.metric-card .change.positive {
    color: #00c853;
}

.metric-card .change.negative {
    color: #ff1744;
}
```

**Signal Badges:**
```css
.signal-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.875rem;
    font-weight: bold;
}

.signal-badge.long {
    background: #00c853;
    color: white;
}

.signal-badge.short {
    background: #ff1744;
    color: white;
}

.signal-badge.neutral {
    background: #9e9e9e;
    color: white;
}
```

**Buttons:**
```css
.btn-primary {
    background: #00c853;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 10px 20px;
    font-size: 1rem;
    cursor: pointer;
}

.btn-primary:hover {
    background: #00a844;
}

.btn-secondary {
    background: #e0e0e0;
    color: #262730;
    border: none;
    border-radius: 4px;
    padding: 10px 20px;
    font-size: 1rem;
    cursor: pointer;
}

.btn-danger {
    background: #ff1744;
    color: white;
}
```

**Tables:**
```css
.data-table {
    width: 100%;
    border-collapse: collapse;
}

.data-table th {
    background: #f0f2f6;
    padding: 12px;
    text-align: left;
    font-weight: bold;
    border-bottom: 2px solid #e0e0e0;
}

.data-table td {
    padding: 12px;
    border-bottom: 1px solid #e0e0e0;
}

.data-table tr:hover {
    background: #f9f9f9;
}

.data-table tr:nth-child(even) {
    background: #fafafa;
}
```

**Charts:**
- **Height:** 600px (main price chart), 300px (volume/indicator panels)
- **Margin:** Auto-adjusted for labels
- **Grid:** Light gray, subtle
- **Hover Tooltip:** Dark background, white text, rounded corners
- **Annotations:** Signal markers with text labels
- **Legend:** Top-right, interactive (click to hide/show series)

### 5. INTERACTION DESIGN

**Loading States:**
- **Data Fetching:** Spinner with "Loading data..." message
- **Analysis Running:** Progress bar (if deterministic) or spinner
- **Chart Rendering:** Placeholder skeleton

**Empty States:**
- **No Watchlist:** "Your watchlist is empty. Add stocks to get started."
- **No Alerts:** "No alerts configured. Create your first alert!"
- **No Data:** "No data available for this symbol. Try a different stock or timeframe."

**Error States:**
- **API Failure:** "Failed to fetch data. Please try again later."
- **Invalid Symbol:** "Symbol not found. Please check and try again."
- **Network Error:** "Network error. Check your connection."

**Confirmation Dialogs:**
- **Delete Alert:** "Are you sure you want to delete this alert?"
- **Remove from Watchlist:** "Remove [SYMBOL] from watchlist?"

**Notifications:**
- **Success:** Green banner at top, auto-dismiss after 3 seconds
- **Error:** Red banner, manual dismiss
- **Info:** Blue banner, auto-dismiss after 5 seconds

### 6. RESPONSIVE DESIGN

**Desktop (>1200px):**
- Sidebar: 300px fixed width
- Main content: Remaining space
- Charts: Full width
- Tables: Full width
- Metrics: 3-4 columns grid

**Tablet (768px-1200px):**
- Sidebar: Collapsible, overlay on main content
- Charts: Full width, scale down
- Tables: Horizontal scroll if needed
- Metrics: 2 columns grid

**Mobile (<768px):**
- Sidebar: Hamburger menu
- Charts: Full width, reduced height
- Tables: Vertical cards instead of table
- Metrics: 1 column
- **Note:** Streamlit has limited mobile optimization, focus on desktop

---

## IMPLEMENTATION STRATEGY

### PHASE 1: FOUNDATION (Weeks 1-2)

**Goal:** Set up basic infrastructure and authentication

**Tasks:**
1. **Project Setup:**
   - Initialize Git repository
   - Set up Python environment (Python 3.11+)
   - Create project structure (modular files)
   - Install dependencies (Streamlit, pandas, yfinance, etc.)
   - Create `.env.example` for configuration

2. **Database Setup:**
   - Design PostgreSQL schema
   - Create migration scripts
   - Set up database connection module with context managers
   - Create indexes for performance

3. **Authentication System:**
   - Implement UserDB class (auth.py)
   - Build registration UI with validation
   - Build login UI
   - Implement bcrypt password hashing
   - Create session management with Streamlit
   - Build basic user profile page

4. **Basic UI Framework:**
   - Create app.py with Streamlit basics
   - Design sidebar navigation
   - Implement mode switching logic
   - Add custom CSS for branding

**Deliverable:** Working authentication system with user registration, login, and basic dashboard shell

### PHASE 2: CORE ANALYSIS (Weeks 3-5)

**Goal:** Implement single stock technical analysis

**Tasks:**
1. **Data Fetching:**
   - Implement Yahoo Finance integration (yfinance)
   - Create data caching with Streamlit `@st.cache_data`
   - Add timeframe selection UI
   - Implement error handling for API failures

2. **Technical Analyzer Module:**
   - Calculate EMAs (9, 20, 50, 100, 200)
   - Implement MA Cloud logic
   - Calculate QQE indicator
   - Calculate VWAP with bands
   - Detect 15+ candlestick patterns
   - Detect 20+ chart patterns
   - Find support/resistance levels
   - Analyze volume (Bulkowski methodology)
   - Generate buy/sell signals

3. **Visualization:**
   - Build interactive candlestick chart with Plotly
   - Add EMA overlays
   - Add MA Cloud visualization
   - Create QQE panel below price chart
   - Create volume panel
   - Add signal annotations
   - Implement tabbed interface (Overview, Patterns, S/R, Metrics)

4. **Single Stock UI:**
   - Stock symbol input
   - Timeframe selection (period, interval)
   - QQE parameter configuration
   - Analyze button
   - Display results in 4 tabs

**Deliverable:** Fully functional single stock analysis mode with charts and pattern detection

### PHASE 3: PORTFOLIO & COMPARISON (Weeks 6-7)

**Goal:** Multi-stock monitoring and comparison

**Tasks:**
1. **Watchlist System:**
   - Implement WatchlistDB (database.py)
   - Add watchlist UI in sidebar
   - Add/remove stock functionality
   - Notes field for each stock

2. **Portfolio Dashboard:**
   - Batch analysis engine (loop through watchlist)
   - Quick mode (reduced indicators)
   - Portfolio summary metrics
   - Stock table with sortable columns
   - Click to navigate to single stock analysis

3. **Multi-Stock Comparison:**
   - Stock selection UI (multi-select)
   - Normalized performance calculation
   - Correlation matrix (pandas, scipy)
   - Relative strength analysis
   - Comparison charts and tables

**Deliverable:** Portfolio monitoring and multi-stock comparison features

### PHASE 4: BACKTESTING (Weeks 8-9)

**Goal:** Strategy backtesting engine

**Tasks:**
1. **Backtester Module:**
   - Implement Trade class (entry, exit, P&L)
   - Build strategy execution simulator
   - Add risk management (stop loss, take profit)
   - Calculate performance metrics (Sharpe, drawdown, etc.)

2. **Pre-built Strategies:**
   - QQE strategy
   - EMA crossover strategy
   - MA Cloud trend strategy

3. **Backtest UI:**
   - Strategy selection
   - Parameter configuration
   - Risk management inputs
   - Run backtest button
   - Results display:
     - Equity curve chart
     - Metrics cards
     - Trade log table
     - CSV export

**Deliverable:** Working backtesting engine with 3 pre-built strategies

### PHASE 5: CUSTOM STRATEGIES & ALERTS (Weeks 10-11)

**Goal:** User-defined strategies and alerts

**Tasks:**
1. **Strategy Builder:**
   - Condition builder UI (dynamic rows)
   - Indicator selection dropdown
   - Comparison operator selection
   - Logic operators (AND/OR)
   - Entry/exit rule configuration
   - Pre-built templates
   - Save/load strategies
   - Integration with backtester

2. **Alert System:**
   - Implement AlertsDB (database.py)
   - Alert creation UI (4 types: price, indicator, trend, crossover)
   - Alert monitoring engine
   - Trigger detection logic
   - Alert status display in Portfolio Dashboard
   - Alert management (view, delete, deactivate)

**Deliverable:** Custom strategy builder and alert system

### PHASE 6: ADMIN & POLISH (Weeks 12-13)

**Goal:** Admin features and production readiness

**Tasks:**
1. **Admin Panel:**
   - User management table
   - Role change functionality
   - Account activation/deactivation
   - System statistics dashboard

2. **Alpha Vantage Integration:**
   - Implement AlphaVantageProvider (alpha_vantage_data.py)
   - Add data source switcher in sidebar
   - News sentiment integration
   - Rate limit handling (25 calls/day)

3. **Polish & Optimization:**
   - Improve loading times
   - Optimize database queries
   - Add loading indicators throughout
   - Improve error messages
   - Add helpful tooltips and hints
   - Comprehensive testing

4. **Documentation:**
   - README with quick start
   - Deployment guide
   - User manual
   - API documentation (if REST API added)

5. **Deployment Preparation:**
   - Create Docker configuration
   - Set up Nginx reverse proxy config
   - Prepare Replit deployment
   - Database migration scripts
   - Automated setup script (finalize_setup.py)

**Deliverable:** Production-ready application with admin features and deployment guides

### PHASE 7: TESTING & LAUNCH (Week 14)

**Goal:** Testing and production launch

**Tasks:**
1. **Testing:**
   - Unit tests (pytest) for core modules
   - Integration tests (database, API)
   - Manual UI testing
   - Performance testing
   - Security testing

2. **Deployment:**
   - Set up production database (PostgreSQL)
   - Deploy to production server
   - Configure HTTPS (SSL certificate)
   - Set up monitoring (error tracking, uptime)
   - Create first superadmin account

3. **Launch:**
   - Invite beta users
   - Gather feedback
   - Fix critical bugs
   - Iterate based on feedback

**Deliverable:** Live production application

---

## FUTURE ENHANCEMENTS (Post-MVP)

### 1. ADVANCED FEATURES

- **Paper Trading:** Simulate live trading without real money
- **Live Trading Integration:** Connect to brokers (Alpaca, Interactive Brokers, TD Ameritrade)
- **Options Analysis:** Options chain, Greeks, strategies
- **Fundamental Analysis:** P/E, EPS, revenue, earnings reports
- **Economic Calendar:** Track key economic events
- **Stock Screener:** Filter stocks by criteria
- **Heatmaps:** Sector performance, market movers
- **Social Sentiment:** Twitter, Reddit, StockTwits sentiment analysis
- **Machine Learning Predictions:** Price forecasting with ML models

### 2. COLLABORATION FEATURES

- **Shared Watchlists:** Team watchlists
- **Shared Strategies:** Publish and share strategies with community
- **Comments & Annotations:** Collaborate on charts
- **Notifications:** Email, SMS, push notifications for alerts

### 3. MOBILE APP

- **Native iOS/Android App:** React Native or Flutter
- **Mobile-optimized UI:** Simplified for small screens
- **Push Notifications:** Real-time alerts on mobile

### 4. PREMIUM FEATURES

- **Advanced Data Sources:** Real-time Level 2 data, order flow
- **Unlimited Alerts:** Remove alert limits for premium users
- **Historical Backtesting:** 10+ years of data
- **Custom Indicators:** Build custom technical indicators
- **API Access:** REST API for algorithmic trading
- **Priority Support:** Dedicated support for premium users

### 5. INTEGRATIONS

- **TradingView:** Embed TradingView charts
- **Discord/Slack:** Alert notifications to chat
- **Zapier:** Automate workflows
- **Google Sheets:** Export data to spreadsheets
- **Webhooks:** Custom integrations

---

## SUCCESS METRICS (KPIs)

### 1. USER METRICS

- **User Growth:**
  - New registrations per week
  - Monthly active users (MAU)
  - User retention rate (30-day, 90-day)

- **Engagement:**
  - Average session duration
  - Analyses run per user per week
  - Watchlist size (average stocks per user)
  - Alerts created per user
  - Strategies built per user

### 2. SYSTEM METRICS

- **Performance:**
  - Page load time (< 2 seconds target)
  - API response time (< 500ms target)
  - Uptime (99.5%+ target)
  - Error rate (< 1% target)

- **Usage:**
  - API calls per day (monitor limits)
  - Database query performance
  - Cache hit rate (70%+ target)

### 3. BUSINESS METRICS (if monetizing)

- **Conversion:**
  - Free to paid conversion rate
  - Monthly recurring revenue (MRR)
  - Customer lifetime value (CLV)
  - Churn rate

---

## RISK MITIGATION

### 1. TECHNICAL RISKS

| Risk | Impact | Mitigation |
|------|--------|------------|
| API rate limits exceeded | High | Implement caching, use multiple data sources, upgrade to paid tiers |
| Database downtime | High | Regular backups, read replicas, monitoring and alerts |
| Slow performance with many users | Medium | Horizontal scaling, Redis cache, optimize queries |
| Data accuracy issues | Medium | Validate data from multiple sources, show data source and timestamp |
| Security breach | High | bcrypt hashing, XSRF protection, regular security audits, HTTPS |

### 2. BUSINESS RISKS

| Risk | Impact | Mitigation |
|------|--------|------------|
| Low user adoption | High | Focus on UX, gather feedback early, iterate quickly |
| Competitor with similar features | Medium | Differentiate with unique features, superior UX, better pricing |
| Data provider changes API | Medium | Abstract data layer, support multiple providers |
| Regulatory compliance (financial data) | Medium | Add disclaimers, don't provide financial advice, consult legal |

---

## CONCLUSION

This comprehensive design prompt provides all necessary specifications to build a production-ready stock trading technical analysis platform. The architecture is modular, scalable, and secure, with a clear implementation roadmap spanning 14 weeks.

**Key Strengths:**
- **Comprehensive Feature Set:** 35+ indicators, backtesting, custom strategies
- **User-Centric Design:** Intuitive UI, clear visualizations
- **Multi-user Support:** Role-based access, data isolation
- **Production-Ready:** Security, performance, scalability considerations
- **Extensible:** Easy to add new indicators, data sources, features

**Recommended Tech Stack:**
- Python 3.11+ (backend logic)
- Streamlit 1.50.0 (rapid UI development)
- PostgreSQL (robust database)
- Plotly (interactive charts)
- yfinance + Alpha Vantage (data sources)
- Docker (containerization)
- Nginx (production deployment)

**Next Steps:**
1. Review and approve this design specification
2. Set up development environment
3. Begin Phase 1 implementation
4. Iterate based on user feedback
5. Launch MVP and gather real-world usage data
6. Implement advanced features post-launch

This platform has the potential to become a comprehensive trading analysis tool for retail and professional traders alike, combining powerful technical analysis with an accessible, user-friendly interface.
