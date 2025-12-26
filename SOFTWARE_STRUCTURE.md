# DashTrade (NovAlgo) - Complete Software Structure

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [User Guide](#3-user-guide)
4. [Admin Guide](#4-admin-guide)
5. [Technical Documentation](#5-technical-documentation)
6. [Database Schema](#6-database-schema)
7. [API & Integrations](#7-api--integrations)
8. [File Structure Reference](#8-file-structure-reference)
9. [Deployment Guide](#9-deployment-guide)
10. [Security Overview](#10-security-overview)
11. [Troubleshooting](#11-troubleshooting)

---

# 1. Executive Summary

## 1.1 What is DashTrade?

**DashTrade** (branded as **NovAlgo**) is an AI-powered stock trading signal dashboard and automated trading platform. It combines technical analysis, pattern recognition, risk management, and automated trade execution through integration with Alpaca Markets API.

## 1.2 Business Value

| Capability | Business Benefit |
|------------|------------------|
| **Automated Trading** | Execute trades 24/7 without manual intervention |
| **AI Assistant** | Claude AI helps users analyze markets and execute trades |
| **Technical Analysis** | 20+ indicators, 35+ patterns detected automatically |
| **Risk Management** | Built-in stop-loss, position sizing, and risk limits |
| **Multi-User Platform** | Support for multiple users with role-based access |
| **Webhook Integration** | Connect with TradingView and external signal providers |

## 1.3 Key Metrics

| Metric | Value |
|--------|-------|
| Total Python Files | ~50 |
| Lines of Code | 20,000+ |
| Database Tables | 15+ |
| Technical Indicators | 20+ |
| Candlestick Patterns | 15+ |
| Chart Patterns | 20+ |
| Application Modes | 8 |

## 1.4 Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND                                │
│                    Streamlit (Python)                        │
│              Interactive Charts (Plotly)                     │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND                                 │
│                    Python 3.11                               │
│    Flask (Webhooks) │ Tornado (Async) │ Pandas (Data)       │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      DATABASE                                │
│              PostgreSQL (Primary)                            │
│              SQLite (Fallback/Development)                   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   EXTERNAL SERVICES                          │
│  Alpaca API │ Yahoo Finance │ Alpha Vantage │ Anthropic AI  │
└─────────────────────────────────────────────────────────────┘
```

## 1.5 User Roles

| Role | Permissions |
|------|-------------|
| **User** | Stock analysis, trading bot, backtesting, AI assistant |
| **Admin** | All user permissions + user management, system strategies |
| **SuperAdmin** | All admin permissions + full system access |

---

# 2. System Architecture

## 2.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                              │
│                                                                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│  │   Login     │ │  Dashboard  │ │  Analysis   │ │  Bot Setup  │    │
│  │  Register   │ │  Portfolio  │ │  Backtest   │ │  AI Chat    │    │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                             │
│                                                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │
│  │  Authentication │  │  Technical      │  │  Trading        │       │
│  │  (auth.py)      │  │  Analyzer       │  │  Engine         │       │
│  │                 │  │  (1216 lines)   │  │  (bot_engine)   │       │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘       │
│                                                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │
│  │  Strategy       │  │  Backtester     │  │  AI Assistant   │       │
│  │  Builder        │  │  Framework      │  │  (Claude)       │       │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘       │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                                   │
│                                                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │
│  │  PostgreSQL     │  │  Bot Database   │  │  User Database  │       │
│  │  (Primary)      │  │  (bot_database) │  │  (database.py)  │       │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘       │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       EXTERNAL INTEGRATIONS                           │
│                                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Alpaca   │  │ Yahoo    │  │ Alpha    │  │ Claude   │  │ SMTP   │ │
│  │ Trading  │  │ Finance  │  │ Vantage  │  │ AI       │  │ Email  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

## 2.2 Data Flow Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ TradingView │────▶│  Webhook    │────▶│  Validate   │
│   Alert     │     │  Server     │     │  Token      │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Log Trade  │◀────│  Execute    │◀────│  Get User   │
│  to DB      │     │  via Alpaca │     │  Config     │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │  Forward to │
                                        │  Outgoing   │
                                        │  Webhooks   │
                                        └─────────────┘
```

## 2.3 Component Interactions

```
User Login (auth.py)
    │
    ▼
Session State Management (app.py)
    │
    ▼
Mode Selection
    │
    ├──▶ Single Stock Analysis
    │       ├── fetch_stock_data() [Yahoo/Alpha Vantage]
    │       ├── TechnicalAnalyzer.run_complete_analysis()
    │       ├── create_candlestick_chart_with_signals()
    │       └── display_results()
    │
    ├──▶ Trading Bot Setup
    │       ├── BotAPIKeysDB.save_api_keys() [encrypted]
    │       ├── WebhookTokenDB.generate_token()
    │       └── webhook_server.py listens
    │               └── TradingEngine.execute_trade()
    │                       ├── Alpaca API
    │                       ├── BotTradesDB.log_trade()
    │                       └── forward_to_outgoing_webhooks()
    │
    ├──▶ Backtesting
    │       ├── fetch_stock_data()
    │       ├── TechnicalAnalyzer.add_all_indicators()
    │       ├── Backtester.backtest()
    │       └── display_results()
    │
    └──▶ AI Assistant
            ├── LLMKeysDB.get_key() [decrypted]
            ├── AIAssistant.chat_stream()
            ├── Tool: TradingEngine.get_account_summary()
            └── Tool: TradingEngine.place_manual_order()
```

---

# 3. User Guide

## 3.1 Getting Started

### 3.1.1 Registration

1. Navigate to the DashTrade landing page
2. Click **"Get Started"** or **"Register"**
3. Fill in your details:
   - Username (unique)
   - Email address
   - Password (minimum 6 characters)
4. Click **Register**
5. You'll be automatically logged in

### 3.1.2 Login

1. Enter your username and password
2. Click **Login**
3. You'll be directed to the main dashboard

## 3.2 Application Modes

### 3.2.1 Single Stock Analysis

**Purpose**: Analyze individual stocks with comprehensive technical analysis

**How to Use**:
1. Select **"Single Stock Analysis"** from the sidebar
2. Enter a stock symbol (e.g., AAPL, TSLA, MSFT)
3. Choose your timeframe:
   - 1 Day, 5 Days, 1 Month, 3 Months, 6 Months, 1 Year, 2 Years, 5 Years
4. Select data interval:
   - 1m, 5m, 15m, 30m, 1h, 1d, 1wk
5. Click **Analyze**

**What You'll See**:
- Interactive candlestick chart
- Moving averages (EMA 9, 20, 50, 100, 200)
- MA Cloud visualization
- QQE momentum indicator
- Volume analysis
- Support and resistance levels
- Pattern detection results
- Trading signals (BUY/SELL recommendations)

### 3.2.2 Portfolio Dashboard

**Purpose**: Monitor multiple stocks simultaneously

**How to Use**:
1. Select **"Portfolio Dashboard"** from sidebar
2. Add stocks to your watchlist
3. View real-time prices and changes
4. Set alerts for price movements

**Features**:
- Multi-stock monitoring
- Performance tracking
- Quick analysis mode
- Alert notifications

### 3.2.3 Multi-Stock Comparison

**Purpose**: Compare multiple stocks for correlation and relative strength

**How to Use**:
1. Select **"Multi-Stock Comparison"**
2. Enter 2-5 stock symbols
3. Choose comparison period
4. View results

**What You'll See**:
- Correlation matrix
- Relative strength comparison
- Normalized price charts
- Performance metrics table

### 3.2.4 Backtesting

**Purpose**: Test trading strategies on historical data

**How to Use**:
1. Select **"Backtesting"** from sidebar
2. Enter stock symbol
3. Choose date range
4. Select or create a strategy
5. Configure parameters:
   - Initial capital
   - Position size (%)
   - Stop loss (%)
   - Take profit (%)
6. Click **Run Backtest**

**Results Include**:
- Total return (%)
- Win rate
- Profit factor
- Maximum drawdown
- Sharpe ratio
- Trade list with details
- Equity curve chart

### 3.2.5 Strategy Builder

**Purpose**: Create custom trading strategies

**How to Use**:
1. Select **"Strategy Builder"**
2. Define entry conditions:
   - Choose indicator (EMA, RSI, QQE, etc.)
   - Select operator (crosses above, greater than, etc.)
   - Set value or comparison indicator
3. Add exit conditions
4. Combine with AND/OR logic
5. Save strategy
6. Test with backtester

**Available Indicators**:
- EMA (9, 20, 50, 100, 200)
- RSI
- QQE
- VWAP
- Volume
- Price action

### 3.2.6 Alert Manager

**Purpose**: Set up automated alerts for price and indicator movements

**Types of Alerts**:
1. **Price Alerts**:
   - Price above/below target
   - Price crosses level

2. **Indicator Alerts**:
   - EMA crossovers
   - RSI overbought/oversold
   - QQE signal changes

3. **Pattern Alerts**:
   - Candlestick patterns detected
   - Chart patterns formed

**How to Set Up**:
1. Go to **Alert Manager**
2. Click **New Alert**
3. Select symbol
4. Choose alert type
5. Set conditions
6. Enable notifications
7. Save alert

### 3.2.7 Trading Bot

**Purpose**: Automate trade execution based on signals

**Setup Steps**:

#### Step 1: Configure Alpaca API
1. Go to **Trading Bot** page
2. Navigate to **API Setup** tab
3. Enter your Alpaca credentials:
   - API Key
   - Secret Key
   - Select Paper/Live trading mode
4. Click **Save & Verify**

#### Step 2: Create a Bot
1. Go to **Bot Configuration** tab
2. Click **Create New Bot**
3. Configure:
   - Symbol (e.g., AAPL)
   - Timeframe (e.g., 15 Min)
   - Position size (% of account)
   - Max daily trades
   - Risk per trade (%)
4. Save configuration

#### Step 3: Get Webhook URL
1. Go to **Webhook Setup** tab
2. Click **Generate Token**
3. Copy your unique webhook URL:
   ```
   https://your-domain.com/webhook?token=YOUR_TOKEN
   ```

#### Step 4: Configure TradingView
1. In TradingView, create an alert
2. Set webhook URL to your copied URL
3. Configure alert message format:
   ```json
   {
     "action": "BUY",
     "symbol": "AAPL",
     "timeframe": "15 Min"
   }
   ```

#### Step 5: Activate Bot
1. Toggle bot to **Active**
2. Monitor trades in **Trade History** tab

### 3.2.8 AI Assistant

**Purpose**: Chat with Claude AI for market analysis and trading help

**Setup**:
1. Go to **AI Assistant**
2. Enter your Anthropic API key (saved encrypted)
3. Start chatting

**Capabilities**:
- Market analysis questions
- Trading recommendations
- Execute trades via Alpaca
- View account summary
- Check positions
- Get real-time quotes

**Example Commands**:
- "What's my account balance?"
- "Show my current positions"
- "Buy 10 shares of AAPL"
- "What's the current price of TSLA?"
- "Analyze the trend for MSFT"

## 3.3 Understanding Technical Indicators

### 3.3.1 Moving Averages (EMA)

| EMA Period | Use Case |
|------------|----------|
| EMA 9 | Short-term momentum |
| EMA 20 | Short-term trend |
| EMA 50 | Medium-term trend |
| EMA 100 | Long-term trend |
| EMA 200 | Major trend direction |

**Signals**:
- Price above EMAs = Bullish
- Price below EMAs = Bearish
- EMA crossovers = Trend changes

### 3.3.2 MA Cloud

The MA Cloud shows the area between two moving averages:
- **Green Cloud**: Bullish trend (fast MA above slow MA)
- **Red Cloud**: Bearish trend (fast MA below slow MA)

### 3.3.3 QQE (Quantitative Qualitative Estimation)

A momentum indicator that combines RSI with smoothing:
- **QQE Line above Signal**: Bullish momentum
- **QQE Line below Signal**: Bearish momentum
- **Crossovers**: Potential entry/exit signals

### 3.3.4 RSI (Relative Strength Index)

| Level | Interpretation |
|-------|----------------|
| Above 70 | Overbought (potential sell) |
| Below 30 | Oversold (potential buy) |
| 50 line | Neutral/trend confirmation |

### 3.3.5 Volume Analysis

- **High volume on breakout**: Confirms move
- **Low volume on breakout**: Weak move, potential reversal
- **Volume divergence**: Warning sign

## 3.4 Understanding Patterns

### 3.4.1 Candlestick Patterns

| Pattern | Type | Signal |
|---------|------|--------|
| Doji | Neutral | Indecision, potential reversal |
| Hammer | Bullish | Potential bottom |
| Shooting Star | Bearish | Potential top |
| Engulfing (Bull) | Bullish | Strong reversal up |
| Engulfing (Bear) | Bearish | Strong reversal down |
| Morning Star | Bullish | Three-candle reversal |
| Evening Star | Bearish | Three-candle reversal |

### 3.4.2 Chart Patterns

| Pattern | Type | Target Calculation |
|---------|------|-------------------|
| Double Top | Bearish | Height of pattern subtracted from neckline |
| Double Bottom | Bullish | Height of pattern added to neckline |
| Head & Shoulders | Bearish | Head height from neckline |
| Inverse H&S | Bullish | Head height from neckline |
| Ascending Triangle | Bullish | Height of triangle at breakout |
| Descending Triangle | Bearish | Height of triangle at breakout |

---

# 4. Admin Guide

## 4.1 Accessing Admin Panel

1. Login with admin credentials
2. Select **"Admin Panel"** from sidebar (only visible to admins)

## 4.2 User Management

### 4.2.1 View All Users
- See list of all registered users
- View registration dates
- Check user roles

### 4.2.2 Change User Roles
1. Find user in the list
2. Click **Change Role**
3. Select new role:
   - User
   - Admin
   - SuperAdmin
4. Confirm change

### 4.2.3 Delete Users
1. Find user in the list
2. Click **Delete**
3. Confirm deletion
4. All user data will be removed

## 4.3 System Strategies

### 4.3.1 What are System Strategies?
Admin-created trading strategies that users can subscribe to. When a signal is received via the system webhook, all subscribed users receive the trade.

### 4.3.2 Create System Strategy
1. Go to **System Strategies** tab
2. Click **Create Strategy**
3. Fill in details:
   - Strategy Name
   - Description
   - Symbol(s)
   - Timeframe
   - Webhook token (auto-generated)
4. Save strategy

### 4.3.3 Manage Subscriptions
- View which users are subscribed
- Remove subscriptions if needed
- Monitor strategy performance

### 4.3.4 System Webhook
Use this URL for system strategy signals:
```
https://your-domain.com/system-webhook?token=STRATEGY_TOKEN
```

## 4.4 Site Statistics

View platform-wide metrics:
- Total registered users
- Active bots
- Total trades executed
- Trading volume
- Most popular symbols
- User growth trends

## 4.5 Admin Code Management

The admin registration code is set via environment variable:
```
ADMIN_CODE=1234-5678-9012-3456
```

Default code (for development): `1234-5678-9012-3456`

**Important**: Change this in production!

---

# 5. Technical Documentation

## 5.1 Core Modules

### 5.1.1 app.py (Main Application)
**Lines**: 4,019
**Purpose**: Main Streamlit application entry point

**Key Functions**:
```python
main()                          # Application entry point
show_landing_page()             # Landing page display
show_login_page()               # Login form
show_register_page()            # Registration form
show_single_stock_analysis()    # Stock analysis mode
show_portfolio_dashboard()      # Portfolio mode
show_backtesting()              # Backtesting mode
show_strategy_builder()         # Strategy creation
show_alert_manager()            # Alert management
show_admin_panel()              # Admin functions
create_candlestick_chart()      # Chart generation
fetch_stock_data()              # Data retrieval
```

### 5.1.2 auth.py (Authentication)
**Lines**: 605
**Purpose**: User authentication and management

**Classes**:
```python
class UserDB:
    create_users_table()        # Initialize schema
    register_user()             # New user registration
    login()                     # User authentication
    hash_password()             # Bcrypt hashing
    verify_password()           # Password verification
    validate_admin_code()       # Admin code check
    get_user_by_id()           # User lookup
    get_all_users()            # Admin: list users
    update_user_role()         # Change user role
    delete_user()              # Remove user
```

### 5.1.3 technical_analyzer.py
**Lines**: 1,216
**Purpose**: Complete technical analysis engine

**Class: TechnicalAnalyzer**

```python
# Indicators
calculate_emas()               # EMA 9, 20, 50, 100, 200
calculate_ma_cloud()           # Moving average cloud
calculate_rsi()                # Relative Strength Index
calculate_qqe()                # QQE momentum
calculate_vwap()               # Volume Weighted Avg Price
calculate_atr()                # Average True Range

# Candlestick Patterns
detect_doji()                  # Doji candles
detect_hammer()                # Hammer pattern
detect_shooting_star()         # Shooting star
detect_engulfing()             # Engulfing patterns
detect_morning_star()          # Morning star
detect_evening_star()          # Evening star
detect_three_white_soldiers()  # Three white soldiers
detect_three_black_crows()     # Three black crows

# Chart Patterns
detect_double_top()            # Double top
detect_double_bottom()         # Double bottom
detect_head_and_shoulders()    # H&S pattern
detect_inverse_head_and_shoulders()
detect_ascending_triangle()    # Ascending triangle
detect_descending_triangle()   # Descending triangle
detect_symmetrical_triangle()  # Symmetrical triangle
detect_wedge()                 # Wedge patterns
detect_flag()                  # Flag patterns

# Support/Resistance
find_pivot_points()            # Pivot calculations
identify_support_resistance()  # S/R levels

# Analysis
run_complete_analysis()        # Full analysis
generate_trading_signals()     # Buy/Sell signals
add_all_indicators()          # Calculate all indicators
```

### 5.1.4 bot_engine.py
**Lines**: 501
**Purpose**: Trading execution engine

**Class: TradingEngine**
```python
__init__(api_key, secret_key, paper=True)
place_manual_order()           # Execute order
get_price_quote()              # Get current price
get_current_position()         # Check positions
get_account_summary()          # Account details
get_market_clock()             # Market hours
check_risk_limits()            # Validate risk
execute_trade()                # Full trade lifecycle
calculate_position_size()      # Dynamic sizing
```

### 5.1.5 bot_database.py
**Lines**: 829
**Purpose**: Bot-related database operations

**Classes**:
```python
class BotAPIKeysDB:
    save_api_keys()            # Store encrypted keys
    get_api_keys()             # Retrieve & decrypt
    delete_api_keys()          # Remove keys

class BotConfigDB:
    create_bot()               # New bot config
    get_user_bots()            # List user's bots
    get_bot_by_id()            # Single bot
    update_bot()               # Modify config
    toggle_bot()               # Enable/disable
    delete_bot()               # Remove bot

class BotTradesDB:
    log_trade()                # Record trade
    get_user_trades()          # Trade history
    update_trade_status()      # Update status
    get_trade_statistics()     # Performance stats

class WebhookTokenDB:
    generate_token()           # Create token
    validate_token()           # Verify token
    get_user_by_token()        # Lookup user
    revoke_token()             # Invalidate

class SystemStrategyDB:
    create_strategy()          # New strategy
    get_all_strategies()       # List strategies
    get_strategy_by_token()    # Lookup by token
    update_strategy()          # Modify strategy
    delete_strategy()          # Remove strategy

class UserStrategySubscriptionDB:
    subscribe()                # Add subscription
    unsubscribe()              # Remove subscription
    get_user_subscriptions()   # User's subscriptions
    get_strategy_subscribers() # Strategy's users

class UserOutgoingWebhookDB:
    create_webhook()           # New outgoing webhook
    get_user_webhooks()        # List webhooks
    update_webhook()           # Modify webhook
    delete_webhook()           # Remove webhook

class RiskEventDB:
    log_event()                # Record risk event
    get_user_events()          # Event history
```

### 5.1.6 webhook_server.py
**Lines**: 497
**Purpose**: Flask webhook receiver

**Endpoints**:
```python
POST /webhook?token=<token>
    # User webhook receiver
    # Validates token, executes trade

POST /system-webhook?token=<token>
    # System strategy webhook
    # Executes for all subscribers

GET /health
    # Health check endpoint
```

### 5.1.7 ai_assistant.py
**Lines**: 10,964
**Purpose**: Claude AI integration

**Class: AIAssistant**
```python
__init__(api_key, alpaca_engine)
chat_stream()                  # Streaming chat
process_tool_call()            # Handle tool use

# Available Tools:
get_account_summary()          # Account info
get_active_positions()         # Open positions
get_stock_price()              # Quote lookup
get_market_clock()             # Market status
place_trading_order()          # Execute order
```

### 5.1.8 strategy_builder.py
**Lines**: 299
**Purpose**: Custom strategy creation

**Classes**:
```python
class StrategyCondition:
    indicator                  # Which indicator
    operator                   # Comparison type
    value                      # Target value
    evaluate()                 # Check condition

class CustomStrategy:
    name                       # Strategy name
    long_conditions            # Entry conditions
    short_conditions           # Short conditions
    exit_conditions            # Exit conditions
    should_enter_long()        # Check long entry
    should_enter_short()       # Check short entry
    should_exit()              # Check exit

class StrategyTemplates:
    ema_crossover()            # EMA cross strategy
    cloud_breakout()           # Cloud strategy
    qqe_momentum()             # QQE strategy
```

### 5.1.9 backtester.py
**Lines**: 458
**Purpose**: Strategy backtesting

**Classes**:
```python
@dataclass
class Trade:
    entry_date, exit_date
    entry_price, exit_price
    direction, size
    pnl, pnl_percent

@dataclass
class BacktestResults:
    total_return
    win_rate
    profit_factor
    max_drawdown
    sharpe_ratio
    trades_list
    equity_curve

class Backtester:
    __init__(data, strategy)
    backtest()                 # Run simulation
    calculate_metrics()        # Performance stats
    generate_report()          # Full report
```

## 5.2 Data Providers

### 5.2.1 yahoo_finance_data.py
```python
fetch_yahoo_data(symbol, period, interval)
# Returns: pandas DataFrame with OHLCV data
# Rate limit: Unlimited
# Delay: 15 minutes
```

### 5.2.2 alpha_vantage_data.py
**Lines**: 369
```python
class AlphaVantageData:
    get_intraday_data()        # Intraday bars
    get_daily_data()           # Daily bars
    get_quote()                # Real-time quote
    get_company_overview()     # Company info
# Rate limit: 25 calls/day (free)
```

## 5.3 Utility Modules

### 5.3.1 encryption.py
```python
generate_encryption_key()      # Create Fernet key
encrypt_alpaca_keys()          # Encrypt API keys
decrypt_alpaca_keys()          # Decrypt API keys
```

### 5.3.2 notification_service.py
```python
class NotificationService:
    send_email()               # Send email alert
    send_trade_alert()         # Trade notification
    generate_html_template()   # Email formatting
```

### 5.3.3 advanced_analytics.py
**Lines**: 424
```python
class AdvancedAnalytics:
    calculate_sharpe_ratio()
    calculate_sortino_ratio()
    calculate_max_drawdown()
    calculate_calmar_ratio()
    calculate_win_rate()
    calculate_profit_factor()
    generate_performance_report()
```

---

# 6. Database Schema

## 6.1 Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│     users       │       │   user_api_keys │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │──┐    │ id (PK)         │
│ username        │  │    │ user_id (FK)    │──┐
│ email           │  │    │ api_key_enc     │  │
│ password_hash   │  │    │ secret_key_enc  │  │
│ role            │  │    │ paper_trading   │  │
│ created_at      │  │    │ created_at      │  │
└─────────────────┘  │    └─────────────────┘  │
                     │                          │
         ┌───────────┴──────────────────────────┘
         │
         ▼
┌─────────────────┐       ┌─────────────────┐
│ user_bot_configs│       │   bot_trades    │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │──┐    │ id (PK)         │
│ user_id (FK)    │  │    │ bot_id (FK)     │──┘
│ symbol          │  │    │ user_id (FK)    │
│ timeframe       │  │    │ symbol          │
│ position_size   │  │    │ action          │
│ max_daily_trades│  │    │ quantity        │
│ risk_per_trade  │  │    │ entry_price     │
│ is_active       │  │    │ exit_price      │
│ total_pnl       │  │    │ pnl             │
│ created_at      │  │    │ status          │
└─────────────────┘  │    │ created_at      │
                     │    └─────────────────┘
         ┌───────────┘
         │
         ▼
┌─────────────────┐       ┌─────────────────┐
│ webhook_tokens  │       │ system_strategies│
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ user_id (FK)    │       │ name            │
│ token           │       │ description     │
│ created_at      │       │ symbol          │
│ is_active       │       │ timeframe       │
└─────────────────┘       │ webhook_token   │
                          │ is_active       │
                          │ created_by (FK) │
                          │ created_at      │
                          └─────────────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │user_strategy_   │
                          │subscriptions    │
                          ├─────────────────┤
                          │ id (PK)         │
                          │ user_id (FK)    │
                          │ strategy_id (FK)│
                          │ created_at      │
                          └─────────────────┘
```

## 6.2 Table Definitions

### 6.2.1 users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6.2.2 user_api_keys
```sql
CREATE TABLE user_api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    api_key_encrypted TEXT NOT NULL,
    secret_key_encrypted TEXT NOT NULL,
    paper_trading BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6.2.3 user_bot_configs
```sql
CREATE TABLE user_bot_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(20) NOT NULL,
    position_size_percent DECIMAL(5,2) DEFAULT 10.0,
    max_daily_trades INTEGER DEFAULT 5,
    risk_per_trade_percent DECIMAL(5,2) DEFAULT 2.0,
    stop_loss_percent DECIMAL(5,2),
    take_profit_percent DECIMAL(5,2),
    is_active BOOLEAN DEFAULT FALSE,
    total_pnl DECIMAL(15,2) DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6.2.4 bot_trades
```sql
CREATE TABLE bot_trades (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER REFERENCES user_bot_configs(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    action VARCHAR(10) NOT NULL,
    quantity DECIMAL(15,6) NOT NULL,
    entry_price DECIMAL(15,6),
    exit_price DECIMAL(15,6),
    pnl DECIMAL(15,2),
    pnl_percent DECIMAL(8,4),
    status VARCHAR(20) DEFAULT 'pending',
    alpaca_order_id VARCHAR(100),
    timeframe VARCHAR(20),
    signal_source VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6.2.5 user_webhook_tokens
```sql
CREATE TABLE user_webhook_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(64) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6.2.6 system_strategies
```sql
CREATE TABLE system_strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(20) NOT NULL,
    webhook_token VARCHAR(64) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id),
    total_signals INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6.2.7 user_strategy_subscriptions
```sql
CREATE TABLE user_strategy_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES system_strategies(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, strategy_id)
);
```

### 6.2.8 user_outgoing_webhooks
```sql
CREATE TABLE user_outgoing_webhooks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    url TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    send_on_signal BOOLEAN DEFAULT TRUE,
    send_on_trade BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6.2.9 bot_risk_events
```sql
CREATE TABLE bot_risk_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    bot_id INTEGER REFERENCES user_bot_configs(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    description TEXT,
    action_taken VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6.2.10 watchlist
```sql
CREATE TABLE watchlist (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, symbol)
);
```

### 6.2.11 alerts
```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    condition VARCHAR(50) NOT NULL,
    value DECIMAL(15,6),
    is_active BOOLEAN DEFAULT TRUE,
    triggered BOOLEAN DEFAULT FALSE,
    triggered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6.2.12 user_preferences
```sql
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    preference_key VARCHAR(100) NOT NULL,
    preference_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, preference_key)
);
```

### 6.2.13 user_llm_keys
```sql
CREATE TABLE user_llm_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) DEFAULT 'anthropic',
    api_key_encrypted TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, provider)
);
```

---

# 7. API & Integrations

## 7.1 Alpaca Markets API

### 7.1.1 Configuration
```python
from alpaca.trading.client import TradingClient

# Paper Trading
client = TradingClient(
    api_key="YOUR_API_KEY",
    secret_key="YOUR_SECRET_KEY",
    paper=True  # Set to False for live trading
)
```

### 7.1.2 Available Operations

| Operation | Method | Description |
|-----------|--------|-------------|
| Get Account | `get_account()` | Account balance, equity, buying power |
| Get Positions | `get_all_positions()` | All open positions |
| Get Position | `get_position(symbol)` | Single position |
| Place Order | `submit_order()` | Market/limit orders |
| Cancel Order | `cancel_order(order_id)` | Cancel pending order |
| Get Orders | `get_orders()` | Order history |
| Get Clock | `get_clock()` | Market hours status |

### 7.1.3 Order Types Supported
- **Market Order**: Execute at current market price
- **Limit Order**: Execute at specified price or better

## 7.2 Yahoo Finance

### 7.2.1 Usage
```python
import yfinance as yf

ticker = yf.Ticker("AAPL")
data = ticker.history(period="1mo", interval="1d")
```

### 7.2.2 Available Periods
`1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `ytd`, `max`

### 7.2.3 Available Intervals
`1m`, `2m`, `5m`, `15m`, `30m`, `60m`, `90m`, `1h`, `1d`, `5d`, `1wk`, `1mo`, `3mo`

## 7.3 Alpha Vantage

### 7.3.1 Configuration
```python
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"
```

### 7.3.2 Endpoints Used

| Function | Endpoint | Description |
|----------|----------|-------------|
| TIME_SERIES_INTRADAY | Intraday data | 1min to 60min bars |
| TIME_SERIES_DAILY | Daily data | Daily OHLCV |
| GLOBAL_QUOTE | Real-time quote | Current price |
| OVERVIEW | Company info | Fundamental data |

### 7.3.3 Rate Limits
- **Free tier**: 25 API calls per day
- **Premium**: Higher limits available

## 7.4 Anthropic Claude AI

### 7.4.1 Configuration
```python
from anthropic import Anthropic

client = Anthropic(api_key="YOUR_API_KEY")
```

### 7.4.2 Model Used
- **claude-3-5-sonnet-20241022** (Claude 3.5 Sonnet)

### 7.4.3 Tool Definitions
```python
tools = [
    {
        "name": "get_account_summary",
        "description": "Get trading account summary",
        "input_schema": {...}
    },
    {
        "name": "get_active_positions",
        "description": "Get all open positions",
        "input_schema": {...}
    },
    {
        "name": "get_stock_price",
        "description": "Get current stock price",
        "input_schema": {"symbol": "string"}
    },
    {
        "name": "place_trading_order",
        "description": "Place a trading order",
        "input_schema": {
            "symbol": "string",
            "quantity": "integer",
            "side": "buy|sell",
            "order_type": "market|limit"
        }
    }
]
```

## 7.5 Webhook Integration

### 7.5.1 User Webhook Endpoint
```
POST /webhook?token=<USER_TOKEN>

Headers:
  Content-Type: application/json

Body:
{
  "action": "BUY" | "SELL" | "CLOSE",
  "symbol": "AAPL",
  "timeframe": "15 Min"
}

Response:
{
  "success": true,
  "message": "Trade executed",
  "order_id": "xxx-xxx-xxx"
}
```

### 7.5.2 System Strategy Webhook
```
POST /system-webhook?token=<STRATEGY_TOKEN>

Headers:
  Content-Type: application/json

Body:
{
  "action": "BUY" | "SELL" | "CLOSE",
  "symbol": "AAPL",
  "timeframe": "15 Min"
}

Response:
{
  "success": true,
  "message": "Signal processed for N subscribers",
  "executions": [...]
}
```

### 7.5.3 TradingView Alert Setup

1. Create alert in TradingView
2. Select "Webhook URL" notification
3. Enter your webhook URL
4. Configure message:
```
{
  "action": "{{strategy.order.action}}",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}"
}
```

## 7.6 Email Notifications (SMTP)

### 7.6.1 Configuration
```python
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
```

### 7.6.2 Gmail Setup
1. Enable 2-factor authentication
2. Create App Password
3. Use App Password as SMTP_PASSWORD

---

# 8. File Structure Reference

```
DashTrade/
│
├── 📄 app.py                           # Main Streamlit application (4019 lines)
│
├── 📁 pages/
│   └── 📄 7_🤖_Trading_Bot.py          # Trading bot management UI
│
├── 📁 migrations/
│   ├── 📄 001_create_bot_tables.sql    # Bot database schema
│   └── 📄 002_system_strategies.sql    # Strategies schema
│
├── 🔐 Authentication & Database
│   ├── 📄 auth.py                      # User authentication (605 lines)
│   ├── 📄 database.py                  # Watchlist, alerts, preferences
│   ├── 📄 bot_database.py              # Bot configuration (829 lines)
│   └── 📄 encryption.py                # Fernet encryption
│
├── 📈 Trading & Analysis
│   ├── 📄 bot_engine.py                # Alpaca trading engine (501 lines)
│   ├── 📄 technical_analyzer.py        # Technical analysis (1216 lines)
│   ├── 📄 strategy_builder.py          # Strategy creation (299 lines)
│   ├── 📄 backtester.py                # Backtesting framework (458 lines)
│   ├── 📄 alert_system.py              # Alert monitoring (320 lines)
│   └── 📄 trading_bot.py               # Bot logic (605 lines)
│
├── 📊 Data Providers
│   ├── 📄 yahoo_finance_data.py        # Yahoo Finance integration
│   ├── 📄 alpha_vantage_data.py        # Alpha Vantage API (369 lines)
│   └── 📄 comparison_analyzer.py       # Multi-stock analysis
│
├── 🌐 External Integration
│   ├── 📄 webhook_server.py            # Flask webhook server (497 lines)
│   ├── 📄 webhook_routes.py            # Tornado webhook handlers (292 lines)
│   ├── 📄 ai_assistant.py              # Claude AI integration (10964 lines)
│   └── 📄 notification_service.py      # Email notifications
│
├── 📉 Advanced Analytics
│   ├── 📄 advanced_analytics.py        # Trading statistics (424 lines)
│   └── 📄 complete_analytics.py        # Comprehensive analytics (684 lines)
│
├── 🚀 Startup & Utilities
│   ├── 📄 start.py                     # Unified startup script
│   ├── 📄 main.py                      # Entry point
│   ├── 📄 run_server.py                # Streamlit runner
│   ├── 📄 run_bot_engine.py            # Bot execution loop
│   ├── 📄 run_alerts.py                # Alert monitoring
│   ├── 📄 create_admin.py              # Admin creation
│   └── 📄 migrate_*.py                 # Database migrations
│
├── ⚙️ Configuration
│   ├── 📄 .env.example                 # Environment template
│   ├── 📄 .streamlit/config.toml       # Streamlit config
│   ├── 📄 .replit                      # Replit config
│   ├── 📄 Dockerfile                   # Docker setup
│   ├── 📄 Procfile                     # Heroku/Railway
│   └── 📄 requirements.txt             # Dependencies
│
└── 📚 Documentation
    ├── 📄 README.md                    # Project overview
    ├── 📄 SOFTWARE_STRUCTURE.md        # This document
    ├── 📄 ARCHITECTURE_ANALYSIS.md     # System design
    ├── 📄 ADMIN_SETUP.md               # Admin guide
    ├── 📄 TRADING_BOT_SETUP.md         # Bot setup
    ├── 📄 DEPLOYMENT_GUIDE.md          # Deployment
    └── 📄 RAILWAY_DEPLOYMENT.md        # Railway setup
```

---

# 9. Deployment Guide

## 9.1 Environment Variables

### Required Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Encryption (CRITICAL - keep secret!)
ENCRYPTION_KEY=your-fernet-key-here

# Admin Registration
ADMIN_CODE=1234-5678-9012-3456

# Optional: Data Provider
ALPHA_VANTAGE_API_KEY=your-key

# Optional: Email Notifications
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Webhook URL (for production)
WEBHOOK_BASE_URL=https://your-domain.com
```

### Generate Encryption Key
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

## 9.2 Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL (or SQLite for development)
- pip

### Setup Steps
```bash
# Clone repository
git clone https://github.com/your-repo/DashTrade.git
cd DashTrade

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your values

# Run application
python start.py
```

### Access Points
- **Main App**: http://localhost:5000
- **Webhook Server**: http://localhost:8080

## 9.3 Railway Deployment

### Step 1: Create Project
1. Go to [railway.app](https://railway.app)
2. Create new project
3. Deploy from GitHub repo

### Step 2: Add PostgreSQL
1. Click **+ New**
2. Select **Database → PostgreSQL**
3. Railway auto-connects DATABASE_URL

### Step 3: Configure Variables
Add in Railway dashboard:
```
ENCRYPTION_KEY=your-key
ADMIN_CODE=your-code
WEBHOOK_BASE_URL=https://your-app.railway.app
```

### Step 4: Deploy
Railway automatically builds from Dockerfile

### Railway-Specific Config
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE $PORT
CMD python start.py
```

## 9.4 Replit Deployment

### Configuration (.replit)
```toml
run = "python start.py"
language = "python3"
entrypoint = "start.py"

[nix]
channel = "stable-23_11"

[env]
PYTHONPATH = "/home/runner/${REPL_SLUG}"

[[ports]]
localPort = 5000
externalPort = 80

[[ports]]
localPort = 8080
externalPort = 8080
```

### Secrets
Add in Replit Secrets tab:
- `DATABASE_URL`
- `ENCRYPTION_KEY`
- `ADMIN_CODE`

## 9.5 Docker Deployment

### Build & Run
```bash
# Build image
docker build -t dashtrade .

# Run container
docker run -d \
  -p 5000:5000 \
  -p 8080:8080 \
  -e DATABASE_URL="postgresql://..." \
  -e ENCRYPTION_KEY="..." \
  -e ADMIN_CODE="..." \
  dashtrade
```

### Docker Compose
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/dashtrade
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - ADMIN_CODE=${ADMIN_CODE}
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=dashtrade
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 9.6 Production Checklist

- [ ] Change default ADMIN_CODE
- [ ] Generate secure ENCRYPTION_KEY
- [ ] Configure HTTPS/SSL
- [ ] Set up database backups
- [ ] Configure email notifications
- [ ] Set WEBHOOK_BASE_URL to public domain
- [ ] Test paper trading before live
- [ ] Monitor error logs
- [ ] Set up uptime monitoring

---

# 10. Security Overview

## 10.1 Authentication Security

### Password Handling
```python
import bcrypt

# Hashing (on registration)
password_hash = bcrypt.hashpw(
    password.encode('utf-8'),
    bcrypt.gensalt()
)

# Verification (on login)
bcrypt.checkpw(
    password.encode('utf-8'),
    stored_hash
)
```

### Session Management
- Streamlit session state
- No persistent sessions (stateless)
- Logout clears all session data

## 10.2 API Key Encryption

### Fernet Symmetric Encryption
```python
from cryptography.fernet import Fernet

# Encryption
cipher = Fernet(ENCRYPTION_KEY)
encrypted = cipher.encrypt(api_key.encode())

# Decryption
decrypted = cipher.decrypt(encrypted).decode()
```

### Storage
- Keys stored encrypted in database
- ENCRYPTION_KEY in environment variable
- Never logged or displayed

## 10.3 Webhook Security

### Token Validation
- Unique 64-character tokens per user
- Token required in URL parameter
- Invalid tokens rejected immediately

### Rate Limiting (Recommended)
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/webhook')
@limiter.limit("10 per minute")
def webhook():
    pass
```

## 10.4 Database Security

### SQL Injection Prevention
All queries use parameterized statements:
```python
cursor.execute(
    "SELECT * FROM users WHERE id = %s",
    (user_id,)
)
```

### Access Control
- Role-based permissions
- User can only access own data
- Admin functions require admin role

## 10.5 Security Best Practices

| Practice | Implementation |
|----------|----------------|
| HTTPS | Enforce in production |
| Password Policy | Minimum 6 characters |
| API Key Rotation | Manual via UI |
| Session Timeout | Browser close |
| Error Messages | Generic (no details) |
| Logging | No sensitive data |

## 10.6 Known Considerations

1. **Rate Limiting**: Not implemented by default
2. **2FA**: Not implemented
3. **Password Complexity**: Basic validation only
4. **Session Tokens**: Uses Streamlit default

---

# 11. Troubleshooting

## 11.1 Common Issues

### Database Connection Failed
```
Error: could not connect to server
```
**Solutions**:
1. Check DATABASE_URL format
2. Verify database is running
3. Check network/firewall rules
4. Verify credentials

### Encryption Key Error
```
Error: Fernet key must be 32 url-safe base64-encoded bytes
```
**Solution**:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```
Use the generated key in ENCRYPTION_KEY

### Webhook Not Receiving
**Checklist**:
1. Verify webhook URL is publicly accessible
2. Check token is valid
3. Confirm TradingView alert is active
4. Check webhook server is running (port 8080)
5. Review server logs

### Alpaca API Errors
```
Error: forbidden
```
**Solutions**:
1. Verify API keys are correct
2. Check paper vs live mode setting
3. Ensure market is open (for some operations)
4. Verify account is active

### Bot Not Executing Trades
**Checklist**:
1. Bot is set to Active
2. API keys are saved and valid
3. Webhook token is generated
4. Position size is > 0
5. Risk limits not exceeded
6. Market is open

## 11.2 Log Locations

### Streamlit Logs
```bash
# Terminal output when running
streamlit run app.py 2>&1 | tee app.log
```

### Webhook Server Logs
```bash
# Flask output
python webhook_server.py 2>&1 | tee webhook.log
```

## 11.3 Debug Mode

### Enable Streamlit Debug
```python
# In app.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Webhook Locally
```bash
curl -X POST "http://localhost:8080/webhook?token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action":"BUY","symbol":"AAPL","timeframe":"15 Min"}'
```

## 11.4 Performance Issues

### Slow Data Loading
- Use caching: `@st.cache_data(ttl=300)`
- Reduce data range
- Use Yahoo Finance instead of Alpha Vantage

### Memory Issues
- Limit trade history queries
- Clear session state periodically
- Restart application

## 11.5 Support Resources

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check README.md and guides
- **Logs**: Review application and webhook logs
- **Database**: Check data integrity

---

# Appendix A: Quick Reference

## A.1 Key URLs

| Service | URL |
|---------|-----|
| Main App | http://localhost:5000 |
| Webhook Server | http://localhost:8080 |
| User Webhook | /webhook?token=TOKEN |
| System Webhook | /system-webhook?token=TOKEN |
| Health Check | /health |

## A.2 Default Values

| Setting | Default |
|---------|---------|
| Admin Code | 1234-5678-9012-3456 |
| Position Size | 10% |
| Max Daily Trades | 5 |
| Risk Per Trade | 2% |
| Data Cache TTL | 300 seconds |

## A.3 Role Permissions

| Action | User | Admin | SuperAdmin |
|--------|------|-------|------------|
| Stock Analysis | ✅ | ✅ | ✅ |
| Trading Bot | ✅ | ✅ | ✅ |
| Backtesting | ✅ | ✅ | ✅ |
| AI Assistant | ✅ | ✅ | ✅ |
| View Users | ❌ | ✅ | ✅ |
| Change Roles | ❌ | ✅ | ✅ |
| Delete Users | ❌ | ✅ | ✅ |
| System Strategies | ❌ | ✅ | ✅ |

## A.4 Webhook Message Format

```json
{
  "action": "BUY|SELL|CLOSE",
  "symbol": "AAPL",
  "timeframe": "15 Min",
  "price": 150.00,        // Optional
  "quantity": 10          // Optional
}
```

## A.5 Technical Indicators Available

| Category | Indicators |
|----------|------------|
| Moving Averages | EMA 9, 20, 50, 100, 200, SMA, MA Cloud |
| Momentum | RSI, QQE, MACD |
| Volatility | ATR, Bollinger Bands |
| Volume | VWAP, Volume Analysis |
| Support/Resistance | Pivot Points, Auto S/R |

---

# Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Alpaca** | Commission-free stock trading API |
| **ATR** | Average True Range - volatility indicator |
| **Backtest** | Testing strategy on historical data |
| **EMA** | Exponential Moving Average |
| **Fernet** | Symmetric encryption algorithm |
| **OHLCV** | Open, High, Low, Close, Volume |
| **Paper Trading** | Simulated trading with fake money |
| **QQE** | Quantitative Qualitative Estimation |
| **RSI** | Relative Strength Index |
| **S/R** | Support and Resistance levels |
| **Streamlit** | Python web application framework |
| **VWAP** | Volume Weighted Average Price |
| **Webhook** | HTTP callback for event notifications |

---

*Document Version: 1.0*
*Last Updated: December 2024*
*DashTrade (NovAlgo) - AI-Powered Trading Platform*
