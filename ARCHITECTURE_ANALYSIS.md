# DashTrade - Complete Architecture Analysis & Base44.ai Design Prompt

## Executive Summary

**DashTrade** is a production-ready, multi-user stock trading technical analysis platform built with Python and Streamlit. The application features 35+ technical indicators, backtesting capabilities, portfolio management, custom strategy building, and role-based authentication.

**Key Metrics:**
- **Total Code:** 8,315 lines of Python
- **Core Files:** 16 Python modules
- **Database:** PostgreSQL with 4 main tables
- **Users:** Multi-user with role-based access (user/admin/superadmin)
- **Features:** 7 operational modes, 15+ candlestick patterns, 20+ chart patterns

---

## 1. COMPLETE SYSTEM LAYOUT

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER LAYER                               │
│  Web Browser → Streamlit UI (Reactive Interface)               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER (app.py)                   │
│  ┌──────────────┬──────────────┬─────────────┬────────────┐    │
│  │ Login/Auth   │ Dashboard    │  Portfolio  │   Admin    │    │
│  │  Module      │   7 Modes    │  Watchlist  │   Panel    │    │
│  └──────────────┴──────────────┴─────────────┴────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                         │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │ TechnicalAnalyzer   │  │    Backtester       │              │
│  │ • 15+ Candlesticks  │  │ • Strategy Engine   │              │
│  │ • 20+ Chart Patterns│  │ • Performance Calc  │              │
│  │ • EMAs, QQE, VWAP   │  │ • Risk Management   │              │
│  │ • Signal Generation │  │ • Trade Tracking    │              │
│  └─────────────────────┘  └─────────────────────┘              │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │ ComparisonAnalyzer  │  │  StrategyBuilder    │              │
│  │ • Correlation       │  │ • Custom Rules      │              │
│  │ • Relative Strength │  │ • Templates         │              │
│  │ • Performance Comp  │  │ • Signal Testing    │              │
│  └─────────────────────┘  └─────────────────────┘              │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │   AlertMonitor      │  │ AlphaVantageData    │              │
│  │ • Condition Checking│  │ • News Sentiment    │              │
│  │ • Trigger System    │  │ • Real-time Data    │              │
│  └─────────────────────┘  └─────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     DATA ACCESS LAYER                           │
│  ┌──────────────┬──────────────┬──────────────┬─────────────┐  │
│  │   UserDB     │ WatchlistDB  │   AlertsDB   │PreferencesDB│  │
│  │ (auth.py)    │(database.py) │(database.py) │(database.py)│  │
│  └──────────────┴──────────────┴──────────────┴─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PERSISTENCE LAYER                            │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              PostgreSQL Database                       │    │
│  │  • users (authentication, roles)                       │    │
│  │  • watchlist (user stock lists)                        │    │
│  │  • alerts (price & technical alerts)                   │    │
│  │  • user_preferences (settings)                         │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL DATA SOURCES                        │
│  ┌───────────────────────────┬──────────────────────────────┐  │
│  │   Yahoo Finance (yfinance)│  Alpha Vantage API           │  │
│  │   • Historical data       │  • Real-time data            │  │
│  │   • 15-min delay          │  • News sentiment            │  │
│  │   • Unlimited usage       │  • 25 calls/day limit        │  │
│  └───────────────────────────┴──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Module Breakdown

#### Core Application Files

| File | Lines | Purpose | Key Components |
|------|-------|---------|----------------|
| `app.py` | 2021 | Main Streamlit application | UI, routing, session management, 7 operational modes |
| `technical_analyzer.py` | 1135+ | Technical analysis engine | Pattern detection, indicators, signals |
| `database.py` | ~400 | Database operations | Watchlist, alerts, preferences management |
| `auth.py` | ~300 | Authentication system | User registration, login, role management |
| `backtester.py` | ~500 | Strategy backtesting | Trade execution, performance metrics |
| `strategy_builder.py` | ~600 | Custom strategy creator | Rule builder, templates, testing |
| `comparison_analyzer.py` | ~400 | Multi-stock analysis | Correlation, relative strength |
| `alert_system.py` | ~350 | Alert monitoring | Condition checking, triggering |
| `alpha_vantage_data.py` | ~250 | Alpha Vantage integration | API client, data fetching |

#### Supporting Files

- `main.py` - Simple entry point wrapper
- `create_admin.py` - Admin creation utility
- `finalize_setup.py` - Automated setup script
- `migrate_database.py` - Database schema migration
- `setup_database.py` - Database connection checker
- `test_auth.py` - Authentication tests

### 1.3 Database Schema (PostgreSQL)

```sql
-- Core Schema Design

TABLE users {
    id: SERIAL PRIMARY KEY
    username: VARCHAR(255) UNIQUE NOT NULL
    email: VARCHAR(255) UNIQUE NOT NULL
    password_hash: VARCHAR(255) NOT NULL
    full_name: VARCHAR(255)
    role: VARCHAR(50) DEFAULT 'user'  -- user|admin|superadmin
    created_at: TIMESTAMP DEFAULT NOW()
    last_login: TIMESTAMP
    is_active: BOOLEAN DEFAULT TRUE
}

TABLE watchlist {
    id: SERIAL PRIMARY KEY
    user_id: INTEGER REFERENCES users(id) ON DELETE CASCADE
    symbol: VARCHAR(20) NOT NULL
    name: VARCHAR(255)
    added_at: TIMESTAMP DEFAULT NOW()
    notes: TEXT
    UNIQUE(user_id, symbol)
}

TABLE alerts {
    id: SERIAL PRIMARY KEY
    user_id: INTEGER REFERENCES users(id) ON DELETE CASCADE
    symbol: VARCHAR(20) NOT NULL
    alert_type: VARCHAR(100) NOT NULL
    condition_text: TEXT
    created_at: TIMESTAMP DEFAULT NOW()
    triggered_at: TIMESTAMP
    is_active: BOOLEAN DEFAULT TRUE
}

TABLE user_preferences {
    id: SERIAL PRIMARY KEY
    user_id: INTEGER REFERENCES users(id) ON DELETE CASCADE
    key: VARCHAR(255) NOT NULL
    value: TEXT
    updated_at: TIMESTAMP DEFAULT NOW()
    UNIQUE(user_id, key)
}

-- Indexes for Performance
INDEX idx_watchlist_user ON watchlist(user_id)
INDEX idx_alerts_user ON alerts(user_id)
INDEX idx_alerts_symbol ON alerts(symbol)
INDEX idx_preferences_user ON user_preferences(user_id)
```

**Relationships:**
- One user → Many watchlist entries (CASCADE DELETE)
- One user → Many alerts (CASCADE DELETE)
- One user → Many preferences (CASCADE DELETE)

### 1.4 Technology Stack

**Backend:**
- Python 3.11+
- Streamlit 1.50.0 (Web framework)
- PostgreSQL (Database)
- psycopg2 2.9.11 (DB adapter)

**Data Processing:**
- Pandas 2.3.3 (Data manipulation)
- NumPy 2.3.4 (Numerical computation)
- TA 0.11.0 (Technical indicators)
- SciPy 1.16.2 (Statistical analysis)

**Data Sources:**
- yfinance 0.2.66 (Yahoo Finance)
- requests 2.32.5 (Alpha Vantage API)

**Visualization:**
- Plotly 6.3.1 (Interactive charts)
- Matplotlib 3.10.7 (Static plots)

**Security:**
- bcrypt 4.0.1 (Password hashing)
- streamlit-authenticator 0.3.3 (Session management)

### 1.5 Application Modes & User Flows

#### Mode 1: Single Stock Analysis
**User Flow:**
1. Select "Single Stock Analysis" from sidebar
2. Enter stock symbol (e.g., AAPL)
3. Configure timeframe (period, interval)
4. Adjust QQE parameters (optional)
5. Click "Analyze"
6. View results in 4 tabs:
   - **Overview:** Price chart with signals, EMA cloud, volume
   - **Patterns:** Candlestick and chart patterns detected
   - **Support/Resistance:** Key price levels
   - **Metrics:** Performance statistics, trend analysis

#### Mode 2: Portfolio Dashboard
**User Flow:**
1. Add stocks to watchlist from sidebar
2. Select "Portfolio Dashboard"
3. Choose analysis mode (Full/Quick)
4. Click "Analyze All Stocks"
5. View portfolio-wide metrics:
   - Bullish/bearish breakdown
   - Active alerts triggered
   - Quick access to individual stock analysis

#### Mode 3: Multi-Stock Comparison
**User Flow:**
1. Select "Multi-Stock Comparison"
2. Choose stocks from watchlist (or enter new ones)
3. Set comparison period
4. View results:
   - Normalized price performance chart
   - Correlation heatmap
   - Performance metrics table
   - Relative strength rankings

#### Mode 4: Backtesting
**User Flow:**
1. Select "Backtesting"
2. Enter stock symbol
3. Choose strategy (QQE, EMA Crossover, MA Cloud)
4. Configure parameters and risk management
5. Run backtest
6. Analyze results:
   - Equity curve
   - Performance metrics (Sharpe, max drawdown)
   - Trade log with CSV export
   - Win rate and profit factor

#### Mode 5: Strategy Builder
**User Flow:**
1. Select "Strategy Builder"
2. Choose creation method:
   - Build from scratch
   - Use template
3. Add entry conditions (indicator comparisons)
4. Add exit conditions
5. Configure logic (AND/OR)
6. Test strategy with backtest
7. Save for future use

#### Mode 6: Alert Manager
**User Flow:**
1. Select "Alert Manager"
2. Create new alert:
   - Choose alert type (price, indicator, crossover, trend)
   - Set conditions
   - Configure symbol
3. View active alerts list
4. Delete or modify alerts
5. Alerts auto-trigger in Portfolio Dashboard

#### Mode 7: Admin Panel (Admin/Superadmin only)
**User Flow:**
1. Select "Admin Panel"
2. View all users table
3. Manage users:
   - Change roles
   - Activate/deactivate accounts
4. View system statistics

---

## 2. FEATURE INVENTORY

### 2.1 Technical Analysis Features

**Moving Averages:**
- 5 EMAs: 9, 20, 50, 100, 200-period
- MA Cloud visualization (short vs long EMA)
- EMA crossover detection

**Momentum Indicators:**
- QQE (Quantified Qualitative Estimation)
  - Long/short signal generation
  - Customizable parameters (RSI period, smoothing factor)
  - Signal tracking (1h, 4h, 24h counts)

**Volume Analysis:**
- VWAP (Volume Weighted Average Price)
- VWAP bands (standard deviation based)
- Volume surge detection
- Bulkowski volume methodology

**Candlestick Patterns (15+):**
- Doji (Regular, Dragonfly, Gravestone)
- Hammer & Inverted Hammer
- Bullish/Bearish Engulfing
- Morning Star / Evening Star
- Shooting Star
- Hanging Man
- Piercing Pattern / Dark Cloud Cover
- Three White Soldiers / Three Black Crows

**Chart Patterns (20+):**
- Double Top / Double Bottom
- Head & Shoulders (Regular & Inverse)
- Cup & Handle / Inverted Cup & Handle
- Ascending/Descending/Symmetrical Triangles
- Rising/Falling Wedges
- Bull/Bear Flags
- Rectangles (continuation/reversal)
- Pennants

**Support & Resistance:**
- Automatic level detection
- Strength scoring
- Touch count tracking

### 2.2 Backtesting Capabilities

**Pre-built Strategies:**
1. **QQE Strategy:** Long on QQE bullish, short on bearish
2. **EMA Crossover:** 9/20 EMA cross signals
3. **MA Cloud Trend:** Cloud-based trend following

**Risk Management:**
- Stop loss (fixed % or ATR-based)
- Take profit targets
- Position sizing (% of capital)
- Trade duration limits

**Performance Metrics:**
- Total return & CAGR
- Win rate & profit factor
- Sharpe ratio
- Maximum drawdown
- Average win/loss
- Longest win/loss streaks
- Trade count & duration

**Outputs:**
- Equity curve chart
- Drawdown chart
- Trade log table
- CSV export

### 2.3 Portfolio Management

**Watchlist:**
- Add/remove stocks
- Notes per stock
- Quick access to analysis
- Multi-user isolation

**Batch Analysis:**
- Analyze all watchlist stocks
- Quick mode (reduced indicators)
- Bullish/bearish summary
- Alert status checking

**Alert System:**
- **Price Alerts:** Above/below, crosses
- **Indicator Alerts:** QQE signals
- **Trend Alerts:** MA cloud changes
- **Crossover Alerts:** EMA crosses
- Auto-triggering with visual feedback

### 2.4 Authentication & Security

**User Management:**
- Registration with validation
- bcrypt password hashing (12 rounds)
- Email validation
- Session persistence

**Role-Based Access:**
- **User:** Basic access to all analysis features
- **Admin:** User management capabilities
- **Superadmin:** Full system control

**Security Features:**
- XSRF protection enabled
- CORS disabled
- Secure password requirements (6+ chars)
- Last login tracking
- Account activation/deactivation

### 2.5 Data Integration

**Yahoo Finance (Primary):**
- Unlimited API calls
- 15-minute delayed data
- Historical data up to max available
- Intervals: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo
- Periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max

**Alpha Vantage (Optional):**
- Real-time data
- News sentiment analysis
- 25 API calls per day
- Intraday (1min, 5min, 15min, 30min, 60min)
- Daily, weekly, monthly data

**Caching:**
- 5-minute TTL on data fetches
- Streamlit `@st.cache_data` decorator
- Reduces API calls
- Improves performance

---

## 3. UI/UX DESIGN SPECIFICATIONS

### 3.1 Layout Structure

```
┌────────────────────────────────────────────────────────────┐
│                         HEADER                             │
│  📈 NovAlgo Trading Signals                                │
│  Subtitle: Comprehensive Stock Technical Analysis         │
└────────────────────────────────────────────────────────────┘

┌──────────────┬─────────────────────────────────────────────┐
│   SIDEBAR    │          MAIN CONTENT AREA                  │
│   (300px)    │           (Remaining width)                 │
│              │                                             │
│ ┌──────────┐ │  ┌────────────────────────────────────┐    │
│ │ 📈 Logo  │ │  │                                    │    │
│ │ Username │ │  │      MODE-SPECIFIC CONTENT         │    │
│ │ Logout   │ │  │                                    │    │
│ └──────────┘ │  │  • Charts (Plotly interactive)     │    │
│              │  │  • Tables (styled DataFrames)      │    │
│ Data Source  │  │  • Forms (input widgets)           │    │
│ ● Yahoo      │  │  • Metrics (card layout)           │    │
│ ○ AlphaVant  │  │                                    │    │
│              │  └────────────────────────────────────┘    │
│ ─────────    │                                             │
│              │  ┌────────────────────────────────────┐    │
│ Mode Select  │  │         TABBED VIEWS               │    │
│ ● Single     │  │  Tab1 │ Tab2 │ Tab3 │ Tab4        │    │
│ ○ Portfolio  │  │                                    │    │
│ ○ Compare    │  │  Detailed analysis results         │    │
│ ○ Backtest   │  │                                    │    │
│ ○ Strategy   │  └────────────────────────────────────┘    │
│ ○ Alerts     │                                             │
│ ○ Admin      │                                             │
│              │                                             │
│ ─────────    │                                             │
│              │                                             │
│ 📊 Watchlist │                                             │
│ ┌──────────┐ │                                             │
│ │ AAPL     │ │                                             │
│ │ TSLA  🗑️ │ │                                             │
│ │ NVDA  🗑️ │ │                                             │
│ └──────────┘ │                                             │
│              │                                             │
│ [+ Add]      │                                             │
└──────────────┴─────────────────────────────────────────────┘
```

### 3.2 Color Scheme

**Primary Colors:**
- Green: `#00c853` (Bullish, Long signals, Success)
- Red: `#ff1744` (Bearish, Short signals, Warnings)
- Blue: `#2196f3` (Neutral, Info, Links)

**Background:**
- Main: `#ffffff`
- Secondary: `#f0f2f6`
- Card: `#fafafa`

**Text:**
- Primary: `#262730`
- Secondary: `#6c757d`
- Muted: `#adb5bd`

**Chart Colors:**
- Candlestick Up: Green
- Candlestick Down: Red
- EMA 9: Blue
- EMA 20: Orange
- EMA 50: Purple
- EMA 100: Brown
- EMA 200: Gray
- Volume: Light blue with transparency

### 3.3 Typography

**Headers:**
- H1: 3rem, bold, centered
- H2: 2rem, bold
- H3: 1.5rem, semi-bold
- H4: 1.25rem, semi-bold

**Body:**
- Regular: 1rem, normal
- Small: 0.875rem
- Tiny: 0.75rem

**Monospace:**
- Code/Metrics: Courier New, 0.9rem

### 3.4 Component Specifications

**Metric Cards:**
```css
.metric-card {
    background: #fafafa;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 8px 0;
}
```

**Signal Badges:**
- Long: Green background, white text, rounded
- Short: Red background, white text, rounded
- Neutral: Gray background, dark text, rounded

**Charts:**
- Height: 600px (main), 300px (volume panel)
- Interactive: Zoom, pan, hover tooltips
- Annotations: Signal markers with text labels
- Legend: Top-right, toggle visibility

**Tables:**
- Striped rows for readability
- Sortable columns
- Responsive width
- Hover highlighting

**Forms:**
- Input fields: Border, rounded corners
- Buttons: Primary (green), Secondary (gray)
- Sliders: Custom track color
- Select dropdowns: Full-width

### 3.5 Responsive Design

**Desktop (>1200px):**
- Sidebar: 300px fixed width
- Main content: Remaining space
- Charts: Full width
- Tables: Horizontal scroll if needed

**Tablet (768px-1200px):**
- Sidebar: Collapsible
- Charts: Scale down
- Tables: Smaller font

**Mobile (<768px):**
- Not optimized (Streamlit limitation)
- Best viewed on desktop

---

## 4. DEPLOYMENT & CONFIGURATION

### 4.1 Environment Setup

**Required Environment Variables:**
```env
# Database (Required)
DATABASE_URL=postgresql://user:password@host:port/database

# Alpha Vantage (Optional)
ALPHA_VANTAGE_API_KEY=your_api_key_here

# Server Configuration (Optional)
APP_PORT=5000
APP_HOST=0.0.0.0
```

### 4.2 Deployment Options

**Option 1: Replit (Recommended for Quick Deploy)**
```bash
1. Fork repository to Replit
2. Add DATABASE_URL to Secrets
3. Run: python finalize_setup.py
4. Click "Run" button
5. Access via Replit-provided URL
```

**Option 2: Local Development**
```bash
1. Clone repository
2. Install dependencies: pip install -e .
3. Set environment variables
4. Run: python finalize_setup.py
5. Start: streamlit run app.py --server.port 5000
```

**Option 3: Docker**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
EXPOSE 5000
CMD ["streamlit", "run", "app.py", "--server.port", "5000"]
```

**Option 4: Production (Nginx + Systemd)**
```nginx
server {
    listen 443 ssl;
    server_name trading.example.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 4.3 Database Providers

**Recommended Options:**
1. **Neon.tech** - Free tier, 10GB storage, 100h compute/month
2. **Supabase** - Free tier, 500MB storage, PostgreSQL 15
3. **ElephantSQL** - Free tier, 20MB storage
4. **Replit PostgreSQL** - Built-in, automatic setup
5. **Local PostgreSQL** - Full control, no limits

### 4.4 Setup Process

```bash
# Step 1: Clone and install
git clone <repository>
cd DashTrade
pip install -e .

# Step 2: Configure environment
cp .env.example .env
# Edit .env with DATABASE_URL

# Step 3: Run finalization script
python finalize_setup.py
# This will:
# - Test database connection
# - Create all tables
# - Add indexes
# - Create superadmin account

# Step 4: Start application
streamlit run app.py --server.port 5000
```

---

## 5. BEST PRACTICES & STRATEGY RECOMMENDATIONS

### 5.1 Architecture Patterns

**Current Strengths:**
1. ✅ **Modular Design:** Clear separation of concerns
2. ✅ **Context Managers:** Safe database operations
3. ✅ **Caching Strategy:** Reduced API calls, improved performance
4. ✅ **Error Handling:** Try-except blocks with user feedback
5. ✅ **Documentation:** Comprehensive guides

**Suggested Improvements:**
1. **API Layer:** Add REST API for mobile/external access
2. **Async Operations:** Use asyncio for parallel data fetching
3. **Redis Caching:** Distribute cache across instances
4. **Celery Tasks:** Background alert monitoring
5. **WebSocket:** Real-time data updates
6. **Testing:** Unit tests, integration tests, E2E tests
7. **Logging:** Structured logging (JSON format)
8. **Monitoring:** Application performance monitoring (APM)

### 5.2 Scalability Strategy

**Current Limitations:**
- Streamlit is single-threaded
- No horizontal scaling without session persistence
- Database connections not pooled

**Recommended Architecture for Scale:**

```
┌───────────────────────────────────────────────────┐
│              Load Balancer (Nginx)                │
└───────────────────────────────────────────────────┘
                      ↓
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Streamlit   │ │  Streamlit   │ │  Streamlit   │
│  Instance 1  │ │  Instance 2  │ │  Instance 3  │
└──────────────┘ └──────────────┘ └──────────────┘
        ↓             ↓             ↓
┌───────────────────────────────────────────────────┐
│            Redis (Session Store)                  │
└───────────────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────────────┐
│       PostgreSQL (Read Replicas)                  │
│  Primary (Write) ──→ Replica 1, Replica 2        │
└───────────────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────────────┐
│       Celery + Redis (Background Tasks)           │
│  • Alert monitoring                               │
│  • Data updates                                   │
│  • Batch processing                               │
└───────────────────────────────────────────────────┘
```

### 5.3 Performance Optimization

**Current Optimizations:**
- Data caching (5-min TTL)
- Efficient pandas operations
- Minimal database queries

**Additional Recommendations:**
1. **Database Indexing:** Already implemented
2. **Query Optimization:** Use EXPLAIN ANALYZE
3. **Batch Operations:** Bulk inserts/updates
4. **CDN:** Static assets (charts, images)
5. **Lazy Loading:** Load charts on-demand
6. **Data Pagination:** Limit historical data
7. **Compression:** Gzip responses

### 5.4 Security Hardening

**Current Security:**
- bcrypt password hashing
- XSRF protection
- SQL injection prevention (parameterized queries)
- Role-based access control

**Additional Recommendations:**
1. **Rate Limiting:** Prevent brute force
2. **2FA:** Two-factor authentication
3. **API Keys:** User-specific API access
4. **Audit Logging:** Track user actions
5. **Input Validation:** Server-side validation
6. **HTTPS Enforcement:** Redirect HTTP to HTTPS
7. **Security Headers:** CSP, HSTS, X-Frame-Options
8. **Dependency Scanning:** Regular vulnerability checks

### 5.5 Monitoring & Observability

**Recommended Stack:**
- **Application Monitoring:** Sentry, New Relic
- **Database Monitoring:** pg_stat_statements
- **Logging:** ELK Stack (Elasticsearch, Logstash, Kibana)
- **Metrics:** Prometheus + Grafana
- **Uptime Monitoring:** UptimeRobot, Pingdom

**Key Metrics to Track:**
- Request latency (p50, p95, p99)
- Error rate
- Database query performance
- API call success rate
- User session duration
- Feature usage statistics
- Alert trigger frequency

---

## 6. BASE44.AI OPTIMAL DESIGN PROMPT

