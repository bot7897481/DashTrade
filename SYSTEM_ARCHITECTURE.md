# DashTrade System Architecture Documentation

**Version:** 1.0
**Last Updated:** 2025-11-30
**Project:** DashTrade (NovAlgo Trading Platform)
**Total Codebase:** ~10,236 lines of Python across 16+ core modules

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Technology Stack](#technology-stack)
4. [Architecture Layers](#architecture-layers)
5. [Core Components](#core-components)
6. [Data Flow Diagrams](#data-flow-diagrams)
7. [Database Schema](#database-schema)
8. [External Integrations](#external-integrations)
9. [Security Architecture](#security-architecture)
10. [Deployment Architecture](#deployment-architecture)
11. [File Structure](#file-structure)
12. [API Reference](#api-reference)

---

## 1. Executive Summary

**DashTrade** is a production-ready, multi-user stock trading platform that combines technical analysis, automated trading, and portfolio management into a single application.

### Key Capabilities

- **Real-time Technical Analysis**: 35+ indicators, pattern detection, support/resistance
- **Automated Trading Bot**: TradingView webhook integration with Alpaca Markets
- **Multi-User System**: Role-based access control with encrypted credentials
- **Strategy Development**: Backtesting engine and custom strategy builder
- **Portfolio Management**: Watchlists, alerts, performance tracking

### Technology Summary

| Component | Technology |
|-----------|-----------|
| **Frontend** | Streamlit (Python-based reactive UI) |
| **Backend** | Python 3.11+ with Flask webhook server |
| **Database** | PostgreSQL 16 |
| **Data Sources** | Yahoo Finance, Alpha Vantage |
| **Broker Integration** | Alpaca Markets API |
| **Deployment** | Replit with Docker support |

---

## 2. System Overview

### 2.1 What DashTrade Does

DashTrade is a comprehensive trading platform with three main use cases:

1. **Educational Analysis Dashboard**
   - Interactive charts with candlestick patterns
   - Technical indicators (EMAs, RSI, MACD, etc.)
   - Pattern recognition (15+ candlestick, 20+ chart patterns)
   - Support/resistance level detection

2. **Automated Trading System**
   - Receives TradingView webhook alerts
   - Executes trades via Alpaca Markets API
   - Manages positions and risk limits
   - Logs all trades and performance metrics

3. **Portfolio Management**
   - Multi-stock watchlists
   - Price and technical alerts
   - Performance tracking and analytics
   - Strategy backtesting

### 2.2 Target Users

- **Retail Traders**: Automated trading based on TradingView strategies
- **Developers**: Building custom trading algorithms
- **Financial Analysts**: Technical analysis and research
- **Portfolio Managers**: Multi-symbol monitoring

---

## 3. Technology Stack

### 3.1 Core Technologies

```
┌─────────────────────────────────────────┐
│         User Interface Layer            │
│   Streamlit 1.50.0 (Python Web UI)     │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│        Application Layer                │
│  Python 3.11+ with Flask 3.0.0         │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│         Data Layer                      │
│  PostgreSQL 16 + psycopg2 2.9.11       │
└─────────────────────────────────────────┘
```

### 3.2 Complete Dependency Matrix

| Category | Library | Version | Purpose |
|----------|---------|---------|---------|
| **Web Framework** | streamlit | 1.50.0 | Reactive dashboard UI |
| | flask | 3.0.0 | Webhook server |
| **Data Processing** | pandas | 2.3.3 | Time series analysis |
| | numpy | 2.3.4 | Numerical computations |
| | scipy | 1.16.2 | Statistical analysis |
| | ta | 0.11.0 | Technical indicators |
| **Visualization** | plotly | 6.3.1 | Interactive charts |
| | matplotlib | 3.10.7 | Static plots |
| **External APIs** | yfinance | 0.2.66 | Yahoo Finance data |
| | alpaca-py | 0.43.0 | Trade execution |
| | requests | 2.32.5 | HTTP client |
| **Database** | psycopg2-binary | 2.9.11 | PostgreSQL adapter |
| | sqlalchemy | 2.0.44 | ORM (optional) |
| **Security** | bcrypt | 4.0.1 | Password hashing |
| | cryptography | 41.0.0 | API key encryption |
| | streamlit-authenticator | 0.3.3 | Session management |

### 3.3 Development Tools

- **Package Manager**: Poetry / UV
- **Version Control**: Git + GitHub
- **Hosting**: Replit (dev/test), Docker (production)
- **Database Migrations**: SQL scripts in `/migrations`

---

## 4. Architecture Layers

### 4.1 Multi-Layered Architecture

```
┌───────────────────────────────────────────────────────────┐
│                 PRESENTATION LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   app.py     │  │ Trading Bot  │  │ Webhook API  │   │
│  │  (Streamlit) │  │     Page     │  │   (Flask)    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└───────────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────────┐
│                 BUSINESS LOGIC LAYER                      │
│  ┌───────────────┐  ┌────────────────┐  ┌─────────────┐ │
│  │  Technical    │  │  Trading       │  │  Backtest   │ │
│  │  Analyzer     │  │  Engine        │  │  Engine     │ │
│  └───────────────┘  └────────────────┘  └─────────────┘ │
│                                                           │
│  ┌───────────────┐  ┌────────────────┐  ┌─────────────┐ │
│  │  Strategy     │  │  Alert         │  │  Comparison │ │
│  │  Builder      │  │  Monitor       │  │  Analyzer   │ │
│  └───────────────┘  └────────────────┘  └─────────────┘ │
└───────────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────────┐
│                 DATA ACCESS LAYER                         │
│  ┌───────────────┐  ┌────────────────┐  ┌─────────────┐ │
│  │   UserDB      │  │  WatchlistDB   │  │  AlertsDB   │ │
│  └───────────────┘  └────────────────┘  └─────────────┘ │
│                                                           │
│  ┌───────────────┐  ┌────────────────┐  ┌─────────────┐ │
│  │ BotAPIKeysDB  │  │  BotConfigDB   │  │ BotTradesDB │ │
│  └───────────────┘  └────────────────┘  └─────────────┘ │
└───────────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────────┐
│                 PERSISTENCE LAYER                         │
│                  PostgreSQL Database                      │
└───────────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────────┐
│                 EXTERNAL SERVICES                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Yahoo Finance│  │ Alpaca API   │  │ Alpha Vantage│   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└───────────────────────────────────────────────────────────┘
```

### 4.2 Separation of Concerns

| Layer | Responsibilities | Key Files |
|-------|-----------------|-----------|
| **Presentation** | User interface, sessions, input validation | `app.py`, `pages/*.py`, `webhook_server.py` |
| **Business Logic** | Analysis, trading, calculations, strategies | `technical_analyzer.py`, `bot_engine.py`, `backtester.py` |
| **Data Access** | Database queries, CRUD operations | `auth.py`, `database.py`, `bot_database.py` |
| **Persistence** | Data storage, transactions | PostgreSQL |
| **External Services** | API integrations, data fetching | `alpha_vantage_data.py`, libraries |

---

## 5. Core Components

### 5.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                       USER INTERFACE                        │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐        │
│  │  Analysis  │  │  Portfolio  │  │  Backtesting │        │
│  │    Mode    │  │    Mode     │  │     Mode     │        │
│  └────────────┘  └─────────────┘  └──────────────┘        │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐        │
│  │ Comparison │  │   Alerts    │  │  Custom      │        │
│  │    Mode    │  │    Mode     │  │  Strategies  │        │
│  └────────────┘  └─────────────┘  └──────────────┘        │
│  ┌────────────┐                                            │
│  │ Trading    │                                            │
│  │  Bot Page  │                                            │
│  └────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Main Application (app.py)

**File:** `/home/user/DashTrade/app.py`
**Lines:** 2,020
**Entry Point:** Streamlit dashboard

#### Key Functions

```python
# Data fetching with caching
@st.cache_data(ttl=300)  # 5-minute cache
def fetch_yahoo_data(symbol, period, interval):
    """Fetch stock data from Yahoo Finance"""

# Analysis modes
def analyze_single_stock()      # Single symbol analysis
def portfolio_dashboard()       # Multi-stock overview
def comparison_mode()           # Side-by-side comparison
def backtesting_mode()          # Strategy testing
def custom_strategy_mode()      # User-defined rules
def alert_monitoring_mode()     # Alert management
def portfolio_monitoring_mode() # Portfolio tracking
```

#### User Journey

```
User Login
    ↓
Mode Selection (7 options)
    ↓
┌─────────────────────────────────────────┐
│ Single Stock Analysis                   │
│  • Select symbol (ticker input)         │
│  • Choose timeframe (1d to 5y)          │
│  • Set interval (1m to 1wk)             │
│  • Toggle 35+ indicators                │
│  • View patterns and signals            │
│  • Add to watchlist                     │
└─────────────────────────────────────────┘
```

### 5.3 Technical Analysis Engine (technical_analyzer.py)

**File:** `/home/user/DashTrade/technical_analyzer.py`
**Lines:** 1,195
**Purpose:** Core analysis algorithms

#### Class: TechnicalAnalyzer

```python
class TechnicalAnalyzer:
    """
    Comprehensive technical analysis with pattern recognition
    """

    # Trend Indicators
    def calculate_emas(df, periods=[9, 20, 50, 100, 200])
    def calculate_ma_cloud(df)
    def calculate_vwap(df)
    def calculate_qqe(df, period=14, smoothing=5)

    # Pattern Detection
    def detect_candlestick_patterns(df) -> List[str]
        # Returns: Doji, Hammer, Shooting Star, Engulfing, etc.

    def detect_chart_patterns(df) -> List[str]
        # Returns: Double Top, Head & Shoulders, Triangles, etc.

    # Support & Resistance
    def find_support_resistance(df, lookback=50) -> dict
        # Returns: {support: [prices], resistance: [prices]}

    # Volume Analysis
    def analyze_volume(df) -> dict
        # Bulkowski methodology

    # Risk Management
    def calculate_risk_metrics(df, entry_price) -> dict
        # Returns: stop_loss, take_profit, position_size

    # Signal Generation
    def generate_signals(df) -> str
        # Returns: "BUY", "SELL", or "HOLD"
```

#### Supported Patterns

**Candlestick Patterns (15+)**
- Doji (Indecision)
- Hammer / Inverted Hammer (Reversal)
- Shooting Star (Bearish reversal)
- Engulfing (Bullish/Bearish)
- Morning Star / Evening Star (Reversal confirmation)
- Harami (Inside day)
- Piercing / Dark Cloud (Reversal)

**Chart Patterns (20+)**
- Double Top / Double Bottom
- Head and Shoulders / Inverse H&S
- Ascending / Descending Triangles
- Symmetrical Triangles
- Wedges (Rising/Falling)
- Flags and Pennants
- Cup and Handle

### 5.4 Trading Bot System

#### Architecture

```
TradingView Alert → Webhook → Bot Engine → Alpaca API → Market
                      ↓
                 Database Log
```

#### Component 1: Webhook Server (webhook_server.py)

**File:** `/home/user/DashTrade/webhook_server.py`
**Lines:** 274
**Port:** 8080
**Framework:** Flask

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Receives TradingView alerts

    Expected URL: http://your-domain.com/webhook?token=USER_TOKEN

    Expected JSON Payload:
    {
        "action": "BUY" | "SELL" | "CLOSE",
        "symbol": "AAPL",
        "timeframe": "15 Min",
        "price": 145.50 (optional)
    }
    """

    # 1. Validate token
    token = request.args.get('token')
    user = WebhookTokenDB.get_user_by_token(token)

    # 2. Parse action
    data = request.json
    action = data['action']
    symbol = data['symbol']
    timeframe = data['timeframe']

    # 3. Get bot configuration
    config = BotConfigDB.get_config(user_id, symbol, timeframe)

    # 4. Execute trade
    engine = TradingEngine(user_id)
    result = engine.place_market_order(action, symbol, config.position_size)

    # 5. Log trade
    BotTradesDB.log_trade(user_id, config.id, result)

    return jsonify({"status": "success", "order_id": result.order_id})
```

#### Component 2: Trading Engine (bot_engine.py)

**File:** `/home/user/DashTrade/bot_engine.py`
**Lines:** 403
**Purpose:** Execute trades via Alpaca API

```python
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

class TradingEngine:
    """
    Per-user trading execution engine
    """

    def __init__(self, user_id: int):
        # Get encrypted API keys
        keys = BotAPIKeysDB.get_user_keys(user_id)

        # Decrypt credentials
        api_key = decrypt_key(keys.alpaca_api_key_encrypted)
        secret_key = decrypt_key(keys.alpaca_secret_key_encrypted)

        # Initialize Alpaca client
        self.client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=(keys.alpaca_mode == 'paper')
        )
        self.user_id = user_id

    def get_current_position(self, symbol: str):
        """Check current position for symbol"""
        try:
            position = self.client.get_open_position(symbol)
            return {
                'qty': float(position.qty),
                'side': position.side,
                'avg_entry_price': float(position.avg_entry_price),
                'market_value': float(position.market_value),
                'unrealized_pl': float(position.unrealized_pl)
            }
        except:
            return None

    def place_market_order(self, action: str, symbol: str, quantity: float):
        """
        Execute market order

        Args:
            action: "BUY", "SELL", or "CLOSE"
            symbol: Stock ticker
            quantity: Number of shares

        Returns:
            Order object with order_id, filled_qty, filled_avg_price
        """

        # Check risk limits
        if not self.check_risk_limits(symbol, quantity):
            raise Exception("Risk limit exceeded")

        # Handle CLOSE action
        if action == "CLOSE":
            self.client.close_position(symbol)
            return

        # Prepare order request
        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=OrderSide.BUY if action == "BUY" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )

        # Submit order
        order = self.client.submit_order(order_data)

        return order

    def check_risk_limits(self, symbol: str, quantity: float) -> bool:
        """
        Validate trade against risk parameters

        Checks:
        - Daily loss limit
        - Maximum position size
        - Account equity
        """
        config = BotConfigDB.get_config(self.user_id, symbol)

        # Check daily loss limit
        if config.daily_loss_limit:
            today_pnl = BotTradesDB.get_daily_pnl(self.user_id)
            if today_pnl < -config.daily_loss_limit:
                BotConfigDB.disable_bot(config.id)
                RiskEventDB.log_event(
                    self.user_id,
                    config.id,
                    'DAILY_LOSS_LIMIT',
                    config.daily_loss_limit,
                    today_pnl
                )
                return False

        # Check max position size
        if config.max_position_size:
            current_pos = self.get_current_position(symbol)
            if current_pos and current_pos['qty'] >= config.max_position_size:
                return False

        return True
```

#### Component 3: Bot Database (bot_database.py)

**File:** `/home/user/DashTrade/bot_database.py`
**Lines:** 438
**Purpose:** Database operations for bot system

```python
class BotAPIKeysDB:
    """Encrypted Alpaca API credentials"""

    @staticmethod
    def store_keys(user_id, api_key, secret_key, mode='paper'):
        encrypted_api = encrypt_key(api_key)
        encrypted_secret = encrypt_key(secret_key)
        # Store in user_api_keys table

    @staticmethod
    def get_user_keys(user_id):
        # Retrieve encrypted keys
        # Return as object with encrypted fields

class BotConfigDB:
    """Bot configuration per symbol/timeframe"""

    @staticmethod
    def create_config(user_id, symbol, timeframe, position_size,
                      risk_limit_percent=10, daily_loss_limit=None):
        # Insert into user_bot_configs table

    @staticmethod
    def get_config(user_id, symbol, timeframe):
        # Retrieve configuration

    @staticmethod
    def update_pnl(config_id, realized_pnl):
        # Update total_pnl and total_trades

class BotTradesDB:
    """Trade execution log"""

    @staticmethod
    def log_trade(user_id, bot_config_id, action, symbol,
                  quantity, price, order_id):
        # Insert into bot_trades table

    @staticmethod
    def get_trade_history(user_id, symbol=None, limit=100):
        # Retrieve trade history

    @staticmethod
    def get_daily_pnl(user_id):
        # Calculate today's realized P&L

class WebhookTokenDB:
    """Webhook authentication"""

    @staticmethod
    def generate_token(user_id):
        token = secrets.token_urlsafe(32)
        # Store in user_webhook_tokens table
        return token

    @staticmethod
    def get_user_by_token(token):
        # Lookup user_id by token
        # Increment request_count
        # Update last_used_at
```

### 5.5 Backtesting System (backtester.py)

**File:** `/home/user/DashTrade/backtester.py`
**Lines:** 375
**Purpose:** Strategy performance testing

```python
from dataclasses import dataclass
from typing import List

@dataclass
class Trade:
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    quantity: float
    side: str  # "LONG" or "SHORT"
    pnl: float
    pnl_percent: float

@dataclass
class BacktestResults:
    trades: List[Trade]
    total_pnl: float
    total_return_percent: float
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    num_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    consecutive_wins: int
    consecutive_losses: int

class Backtester:
    """
    Strategy backtesting engine
    """

    def backtest_strategy(self, df, entry_conditions, exit_conditions,
                          initial_capital=10000, position_size_pct=100):
        """
        Run backtest on historical data

        Args:
            df: Historical OHLCV data
            entry_conditions: List of StrategyCondition for entries
            exit_conditions: List of StrategyCondition for exits
            initial_capital: Starting capital
            position_size_pct: % of capital per trade

        Returns:
            BacktestResults object
        """

        trades = []
        equity = initial_capital
        in_position = False
        entry_price = 0

        for i in range(len(df)):
            # Check entry conditions
            if not in_position and self._check_conditions(df, i, entry_conditions):
                entry_price = df.iloc[i]['close']
                in_position = True

            # Check exit conditions
            elif in_position and self._check_conditions(df, i, exit_conditions):
                exit_price = df.iloc[i]['close']
                pnl = (exit_price - entry_price) * (equity * position_size_pct / 100) / entry_price

                trades.append(Trade(
                    entry_date=df.iloc[i-1].name,
                    exit_date=df.iloc[i].name,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    quantity=(equity * position_size_pct / 100) / entry_price,
                    side="LONG",
                    pnl=pnl,
                    pnl_percent=(exit_price - entry_price) / entry_price * 100
                ))

                equity += pnl
                in_position = False

        return self._calculate_metrics(trades, initial_capital)

    def _calculate_metrics(self, trades, initial_capital):
        """Calculate performance metrics"""

        winning = [t for t in trades if t.pnl > 0]
        losing = [t for t in trades if t.pnl < 0]

        total_pnl = sum(t.pnl for t in trades)

        return BacktestResults(
            trades=trades,
            total_pnl=total_pnl,
            total_return_percent=(total_pnl / initial_capital) * 100,
            win_rate=len(winning) / len(trades) * 100 if trades else 0,
            max_drawdown=self._calculate_max_drawdown(trades, initial_capital),
            sharpe_ratio=self._calculate_sharpe(trades),
            num_trades=len(trades),
            winning_trades=len(winning),
            losing_trades=len(losing),
            avg_win=sum(t.pnl for t in winning) / len(winning) if winning else 0,
            avg_loss=sum(t.pnl for t in losing) / len(losing) if losing else 0,
            largest_win=max((t.pnl for t in winning), default=0),
            largest_loss=min((t.pnl for t in losing), default=0),
            consecutive_wins=self._max_consecutive(winning),
            consecutive_losses=self._max_consecutive(losing)
        )
```

### 5.6 Strategy Builder (strategy_builder.py)

**File:** `/home/user/DashTrade/strategy_builder.py`
**Lines:** 299
**Purpose:** Custom strategy creation

```python
from dataclasses import dataclass
from typing import List

@dataclass
class StrategyCondition:
    indicator1: str      # "ema_9", "rsi", "price", "volume"
    operator: str        # ">", "<", "crosses_above", "crosses_below"
    indicator2: str      # "ema_20", "70", "support", "1000000"

@dataclass
class CustomStrategy:
    name: str
    entry_conditions: List[StrategyCondition]
    exit_conditions: List[StrategyCondition]
    stop_loss_pct: float
    take_profit_pct: float

class StrategyBuilder:
    """
    Interactive strategy creation tool
    """

    def add_condition(self, condition_type: str, indicator1: str,
                      operator: str, indicator2: str):
        """
        Add entry or exit condition

        Example:
            builder.add_condition('entry', 'ema_9', 'crosses_above', 'ema_20')
            builder.add_condition('entry', 'rsi', '>', '30')
            builder.add_condition('exit', 'price', '<', 'support')
        """

        condition = StrategyCondition(indicator1, operator, indicator2)

        if condition_type == 'entry':
            self.entry_conditions.append(condition)
        else:
            self.exit_conditions.append(condition)

    def test_on_data(self, symbol: str, period: str, interval: str):
        """
        Backtest custom strategy

        Returns:
            BacktestResults object
        """

        df = fetch_yahoo_data(symbol, period, interval)
        backtester = Backtester()

        results = backtester.backtest_strategy(
            df,
            self.entry_conditions,
            self.exit_conditions
        )

        return results

    def save_strategy(self, user_id: int):
        """Persist strategy to database"""
        # Store in user_preferences as JSON
```

### 5.7 Other Key Components

#### Comparison Analyzer (comparison_analyzer.py)

```python
class ComparisonAnalyzer:
    """Multi-stock analysis"""

    def fetch_all_data(symbols: List[str], period: str)
    def calculate_correlation(df1, df2) -> float
    def relative_strength(symbols: List[str]) -> dict
    def plot_normalized(dataframes: dict)
```

#### Alert System (alert_system.py)

```python
@dataclass
class AlertCondition:
    symbol: str
    condition_type: str  # "price_above", "ema_cross", "pattern_detected"
    threshold: float

class AlertMonitor:
    def check_conditions(user_id: int) -> List[str]
    def trigger_alert(alert_id: int)
```

#### Authentication (auth.py)

```python
class UserDB:
    @staticmethod
    def register_user(username, password, email, role='user')

    @staticmethod
    def authenticate_user(username, password) -> dict

    @staticmethod
    def hash_password(password) -> str

    @staticmethod
    def get_user_role(user_id) -> str
```

---

## 6. Data Flow Diagrams

### 6.1 User Analysis Flow

```
┌────────────┐
│    User    │
│   Input    │
│ (Symbol,   │
│ Timeframe) │
└─────┬──────┘
      ↓
┌─────────────────────────┐
│  fetch_yahoo_data()     │
│  (5-minute cache)       │
└─────┬───────────────────┘
      ↓
┌─────────────────────────┐
│  TechnicalAnalyzer      │
│  ├─ calculate_emas()    │
│  ├─ detect_patterns()   │
│  ├─ find_support_res()  │
│  └─ generate_signals()  │
└─────┬───────────────────┘
      ↓
┌─────────────────────────┐
│  Database Queries       │
│  ├─ WatchlistDB         │
│  ├─ PreferencesDB       │
│  └─ AlertsDB            │
└─────┬───────────────────┘
      ↓
┌─────────────────────────┐
│  Plotly Visualization   │
│  ├─ Candlestick chart   │
│  ├─ EMAs overlay        │
│  ├─ Pattern markers     │
│  └─ Volume bars         │
└─────┬───────────────────┘
      ↓
┌─────────────────────────┐
│  Streamlit Dashboard    │
│  (Display to User)      │
└─────────────────────────┘
```

### 6.2 Automated Trading Flow

```
┌──────────────────┐
│  TradingView     │
│     Alert        │
│ (Webhook POST)   │
└────────┬─────────┘
         ↓
┌────────────────────────────┐
│  webhook_server.py         │
│  /webhook?token=USER_TOKEN │
│  ├─ Parse JSON payload     │
│  ├─ Validate token         │
│  └─ Extract action/symbol  │
└────────┬───────────────────┘
         ↓
┌────────────────────────────┐
│  WebhookTokenDB            │
│  get_user_by_token()       │
└────────┬───────────────────┘
         ↓
┌────────────────────────────┐
│  BotConfigDB               │
│  get_config(user, symbol)  │
│  ├─ position_size          │
│  ├─ risk_limits            │
│  └─ current_position       │
└────────┬───────────────────┘
         ↓
┌────────────────────────────┐
│  TradingEngine             │
│  ├─ Get encrypted API keys │
│  ├─ Initialize Alpaca      │
│  ├─ Check risk limits      │
│  └─ Execute order          │
└────────┬───────────────────┘
         ↓
┌────────────────────────────┐
│  Alpaca Markets API        │
│  MarketOrderRequest        │
│  └─ Submit to market       │
└────────┬───────────────────┘
         ↓
┌────────────────────────────┐
│  BotTradesDB               │
│  log_trade()               │
└────────┬───────────────────┘
         ↓
┌────────────────────────────┐
│  RiskEventDB               │
│  check_limits()            │
│  ├─ Daily loss exceeded?   │
│  └─ Disable if threshold   │
└────────┬───────────────────┘
         ↓
┌────────────────────────────┐
│  Response to Webhook       │
│  {"status": "success"}     │
└────────────────────────────┘
```

### 6.3 Backtesting Flow

```
┌──────────────────┐
│  User Defines    │
│   Strategy       │
│ (Entry/Exit)     │
└────────┬─────────┘
         ↓
┌────────────────────────────┐
│  StrategyBuilder           │
│  ├─ Parse conditions       │
│  └─ Build strategy object  │
└────────┬───────────────────┘
         ↓
┌────────────────────────────┐
│  Backtester                │
│  ├─ Fetch historical data  │
│  ├─ Simulate trades        │
│  ├─ Calculate P&L          │
│  └─ Track equity curve     │
└────────┬───────────────────┘
         ↓
┌────────────────────────────┐
│  Calculate Metrics         │
│  ├─ Win rate               │
│  ├─ Sharpe ratio           │
│  ├─ Max drawdown           │
│  └─ Total return           │
└────────┬───────────────────┘
         ↓
┌────────────────────────────┐
│  Plotly Visualization      │
│  ├─ Equity curve           │
│  ├─ Drawdown chart         │
│  └─ Trade history table    │
└────────┬───────────────────┘
         ↓
┌────────────────────────────┐
│  Display Results           │
└────────────────────────────┘
```

---

## 7. Database Schema

### 7.1 Entity Relationship Diagram

```
┌─────────────────┐
│     users       │ 1
├─────────────────┤   ↓ Many
│ PK id           │───┬────────────────────────┐
│    username     │   │                        │
│    email        │   │                        │
│    password_hash│   │                        │
│    role         │   │                        │
└─────────────────┘   ↓                        ↓
                 ┌──────────────┐       ┌──────────────┐
                 │  watchlist   │       │  alerts      │
                 ├──────────────┤       ├──────────────┤
                 │ PK id        │       │ PK id        │
                 │ FK user_id   │       │ FK user_id   │
                 │    symbol    │       │    symbol    │
                 │    added_at  │       │    condition │
                 └──────────────┘       └──────────────┘
                        ↓                        ↓
                 ┌──────────────────────────────────┐
                 │     user_api_keys (encrypted)    │
                 ├──────────────────────────────────┤
                 │ PK id                            │
                 │ FK user_id (UNIQUE)              │
                 │    alpaca_api_key_encrypted      │
                 │    alpaca_secret_key_encrypted   │
                 │    alpaca_mode (paper|live)      │
                 └──────────┬───────────────────────┘
                            ↓
                 ┌──────────────────────────────────┐
                 │     user_bot_configs             │
                 ├──────────────────────────────────┤
                 │ PK id                            │
                 │ FK user_id                       │
                 │    symbol                        │
                 │    timeframe                     │
                 │    position_size                 │
                 │    risk_limit_percent            │
                 │    daily_loss_limit              │
                 │    total_pnl                     │
                 │    is_active                     │
                 └──────────┬───────────────────────┘
                            ↓
                 ┌──────────────────────────────────┐
                 │     bot_trades                   │
                 ├──────────────────────────────────┤
                 │ PK id                            │
                 │ FK user_id                       │
                 │ FK bot_config_id                 │
                 │    symbol                        │
                 │    action (BUY|SELL|CLOSE)       │
                 │    quantity                      │
                 │    price                         │
                 │    order_id                      │
                 │    realized_pnl                  │
                 │    created_at                    │
                 └──────────────────────────────────┘
```

### 7.2 Table Definitions

#### users

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',  -- user | admin | superadmin
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### watchlist

```sql
CREATE TABLE watchlist (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    added_at TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    UNIQUE(user_id, symbol)
);

CREATE INDEX idx_watchlist_user ON watchlist(user_id);
```

#### alerts

```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    alert_type VARCHAR(100) NOT NULL,  -- price_above, ema_cross, pattern
    condition_text TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    triggered_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### user_api_keys

```sql
CREATE TABLE user_api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    alpaca_api_key_encrypted TEXT NOT NULL,
    alpaca_secret_key_encrypted TEXT NOT NULL,
    alpaca_mode VARCHAR(10) DEFAULT 'paper',  -- paper | live
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### user_bot_configs

```sql
CREATE TABLE user_bot_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    timeframe VARCHAR(20) NOT NULL,  -- "1 Min", "5 Min", "15 Min", etc.
    position_size DECIMAL(12, 2) NOT NULL,
    risk_limit_percent DECIMAL(5, 2) DEFAULT 10.00,
    daily_loss_limit DECIMAL(12, 2),
    max_position_size DECIMAL(12, 2),
    is_active BOOLEAN DEFAULT TRUE,
    current_position_side VARCHAR(10),  -- LONG | SHORT | NULL
    total_pnl DECIMAL(12, 2) DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, symbol, timeframe)
);

CREATE INDEX idx_bot_configs_user_active ON user_bot_configs(user_id, is_active);
```

#### bot_trades

```sql
CREATE TABLE bot_trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    bot_config_id INTEGER REFERENCES user_bot_configs(id),
    symbol VARCHAR(10) NOT NULL,
    timeframe VARCHAR(20),
    action VARCHAR(10) NOT NULL,  -- BUY | SELL | CLOSE
    quantity DECIMAL(16, 8),
    price DECIMAL(16, 4),
    notional DECIMAL(12, 2),
    order_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'SUBMITTED',
    filled_qty DECIMAL(16, 8),
    filled_avg_price DECIMAL(16, 4),
    filled_at TIMESTAMP,
    realized_pnl DECIMAL(12, 2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_bot_trades_user_symbol ON bot_trades(user_id, symbol, created_at DESC);
```

#### user_webhook_tokens

```sql
CREATE TABLE user_webhook_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    request_count INTEGER DEFAULT 0
);

CREATE INDEX idx_webhook_tokens_token ON user_webhook_tokens(token);
```

#### bot_risk_events

```sql
CREATE TABLE bot_risk_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    bot_config_id INTEGER REFERENCES user_bot_configs(id),
    event_type VARCHAR(50) NOT NULL,
    symbol VARCHAR(10),
    threshold_value DECIMAL(12, 2),
    current_value DECIMAL(12, 2),
    action_taken VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_risk_events_user ON bot_risk_events(user_id, created_at DESC);
```

---

## 8. External Integrations

### 8.1 Alpaca Markets API

**Purpose:** Real-time trade execution

```python
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Initialize client
client = TradingClient(api_key, secret_key, paper=True)

# Get account info
account = client.get_account()
print(f"Buying power: ${account.buying_power}")

# Place market order
order_request = MarketOrderRequest(
    symbol="AAPL",
    qty=10,
    side=OrderSide.BUY,
    time_in_force=TimeInForce.DAY
)
order = client.submit_order(order_request)

# Get positions
positions = client.get_all_positions()
for position in positions:
    print(f"{position.symbol}: {position.qty} @ ${position.avg_entry_price}")

# Close position
client.close_position("AAPL")
```

**Key Features:**
- Paper trading (simulated)
- Live trading (production)
- Market/limit/stop orders
- Position tracking
- Account equity monitoring

**Security:**
- API keys encrypted using Fernet
- Keys stored in PostgreSQL encrypted column
- Per-user isolated credentials

### 8.2 Yahoo Finance (yfinance)

**Purpose:** Primary data source

```python
import yfinance as yf

# Get stock data
ticker = yf.Ticker("AAPL")
df = ticker.history(period="1y", interval="1d")

# Available columns: Open, High, Low, Close, Volume
# Intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
# Periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
```

**Advantages:**
- No API key required
- Unlimited requests
- 15-minute delayed data
- 5-year historical data

### 8.3 Alpha Vantage API

**Purpose:** Alternative data source, news sentiment

```python
class AlphaVantageProvider:
    BASE_URL = "https://www.alphavantage.co/query"

    def get_intraday_data(symbol, interval='5min'):
        """Get minute-level data"""
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': interval,
            'apikey': API_KEY
        }

    def get_news_sentiment(symbol):
        """Get news with sentiment scores"""
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': symbol,
            'apikey': API_KEY
        }
```

**Limitations:**
- 25 API calls/day (free tier)
- Rate limiting implemented
- Used as fallback

### 8.4 PostgreSQL Database

**Connection:**

```python
import psycopg2
import os

# From environment variable
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cursor = conn.cursor()

# Execute query
cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
user = cursor.fetchone()

# Commit and close
conn.commit()
cursor.close()
conn.close()
```

**Connection String Format:**
```
postgresql://username:password@host:port/database
```

---

## 9. Security Architecture

### 9.1 Authentication Flow

```
User Login
    ↓
┌──────────────────────────┐
│  auth.py                 │
│  authenticate_user()     │
│  ├─ Lookup username      │
│  ├─ Retrieve password    │
│  │   hash from DB        │
│  ├─ bcrypt.checkpw()     │
│  └─ Return user object   │
└──────────┬───────────────┘
           ↓
┌──────────────────────────┐
│  Streamlit Session       │
│  st.session_state        │
│  ├─ user_id              │
│  ├─ username             │
│  ├─ role                 │
│  └─ authenticated=True   │
└──────────────────────────┘
```

### 9.2 Password Security

```python
import bcrypt

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt with salt

    Bcrypt automatically:
    - Generates random salt
    - Applies multiple rounds of hashing
    - Stores salt with hash
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against stored hash"""
    return bcrypt.checkpw(
        password.encode('utf-8'),
        password_hash.encode('utf-8')
    )
```

### 9.3 API Key Encryption

```python
from cryptography.fernet import Fernet
import os

# Load encryption key from environment
ENCRYPTION_KEY = os.environ['ENCRYPTION_KEY']
cipher = Fernet(ENCRYPTION_KEY)

def encrypt_key(api_key: str) -> str:
    """Encrypt API key using Fernet (AES-128)"""
    encrypted = cipher.encrypt(api_key.encode())
    return encrypted.decode()

def decrypt_key(encrypted_key: str) -> str:
    """Decrypt API key"""
    decrypted = cipher.decrypt(encrypted_key.encode())
    return decrypted.decode()

# Usage
encrypted_api_key = encrypt_key("PK123ABC...")
# Store in database: alpaca_api_key_encrypted = encrypted_api_key

# Later, when needed
api_key = decrypt_key(encrypted_api_key)
client = TradingClient(api_key=api_key, ...)
```

### 9.4 Role-Based Access Control

```python
# User roles
ROLES = {
    'user': ['view_own_data', 'manage_own_bots'],
    'admin': ['view_own_data', 'manage_own_bots', 'manage_users'],
    'superadmin': ['view_own_data', 'manage_own_bots', 'manage_users',
                   'system_settings']
}

def require_role(required_role: str):
    """Decorator to enforce role-based access"""
    user_role = st.session_state.get('role')

    if user_role != required_role and user_role != 'superadmin':
        st.error("Insufficient permissions")
        st.stop()
```

### 9.5 Webhook Token Security

```python
import secrets

def generate_webhook_token(user_id: int) -> str:
    """
    Generate cryptographically secure token

    Returns: 43-character URL-safe token
    Example: "x7k9mNpQ2wR5tY8uI3oP1aS4dF6gH0jK2lZ5xC7vB9nM4qW"
    """
    token = secrets.token_urlsafe(32)

    # Store in database
    WebhookTokenDB.create_token(user_id, token)

    return token

# TradingView webhook URL
# http://your-domain.com/webhook?token=x7k9mNpQ2wR5tY8uI3oP1aS4dF6gH0jK2lZ5xC7vB9nM4qW
```

---

## 10. Deployment Architecture

### 10.1 Replit Deployment

```
┌─────────────────────────────────────────┐
│         Replit Instance                 │
│         (Ubuntu Linux)                  │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Streamlit App (Port 5000)        │ │
│  │  └─ External: Port 80 (HTTP)      │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Flask Webhook (Port 8080)        │ │
│  │  └─ External: Port 8080           │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  PostgreSQL 16                    │ │
│  │  └─ Internal only                 │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Python 3.11 Runtime              │ │
│  │  Poetry Package Manager           │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**Replit Configuration (.replit):**

```toml
[deployment]
deploymentTarget = "autoscale"
run = ["streamlit", "run", "app.py", "--server.port", "5000"]

[workflows]
runButton = "Project"

[[workflows.workflow]]
name = "Project"

[[workflows.workflow.tasks]]
task = "workflow.run"
args = "Streamlit"

[[workflows.workflow.tasks]]
task = "workflow.run"
args = "Webhook Server"

[[workflows.workflow]]
name = "Streamlit"

[[workflows.workflow.tasks]]
task = "shell.exec"
args = "streamlit run app.py --server.port 5000 --server.address 0.0.0.0"
waitForPort = 5000

[[workflows.workflow]]
name = "Webhook Server"

[[workflows.workflow.tasks]]
task = "shell.exec"
args = "python webhook_server.py"
waitForPort = 8080

[[ports]]
localPort = 5000
externalPort = 80

[[ports]]
localPort = 8080
externalPort = 8080
```

### 10.2 Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

# Copy application
COPY . .

# Expose ports
EXPOSE 5000 8080

# Run both services
CMD ["sh", "-c", "streamlit run app.py --server.port 5000 & python webhook_server.py"]
```

**Docker Compose:**

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/dashtrade
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
    depends_on:
      - db

  db:
    image: postgres:16
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=dashtrade
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### 10.3 Production Checklist

**Environment Setup:**
- [ ] DATABASE_URL configured
- [ ] ENCRYPTION_KEY generated and stored
- [ ] ALPHA_VANTAGE_API_KEY (optional)
- [ ] SESSION_SECRET set

**Database:**
- [ ] PostgreSQL 16 installed
- [ ] Database created
- [ ] Migrations run (`python migrate_bot_tables.py`)
- [ ] Admin user created (`python create_admin.py`)

**Security:**
- [ ] HTTPS enabled (SSL certificate)
- [ ] Firewall rules configured
- [ ] CSRF protection enabled
- [ ] Database backups scheduled

**Monitoring:**
- [ ] Application logs configured
- [ ] Error tracking (Sentry, etc.)
- [ ] Uptime monitoring
- [ ] Database performance monitoring

---

## 11. File Structure

```
/home/user/DashTrade/
│
├── Application Entry Points
│   ├── app.py                          # Main Streamlit app (2020 lines)
│   ├── webhook_server.py               # Flask webhook server (274 lines)
│   └── main.py                         # Simple wrapper
│
├── Pages (Streamlit Multi-Page)
│   └── pages/
│       └── 7_🤖_Trading_Bot.py         # Trading bot management
│
├── Core Business Logic
│   ├── technical_analyzer.py           # Technical analysis engine (1195 lines)
│   ├── bot_engine.py                   # Trading execution (403 lines)
│   ├── backtester.py                   # Strategy backtesting (375 lines)
│   ├── strategy_builder.py             # Custom strategy creation (299 lines)
│   ├── comparison_analyzer.py          # Multi-stock analysis (269 lines)
│   ├── alert_system.py                 # Alert monitoring (320 lines)
│   ├── advanced_analytics.py           # Trading analytics (424 lines)
│   ├── complete_analytics.py           # Comprehensive analytics (684 lines)
│   └── alpha_vantage_data.py           # Alpha Vantage API client (369 lines)
│
├── Data Access Layer
│   ├── auth.py                         # User authentication (317 lines)
│   ├── database.py                     # Watchlist & alerts (192 lines)
│   ├── bot_database.py                 # Bot system DB (438 lines)
│   └── encryption.py                   # API key encryption
│
├── Database Setup & Migrations
│   ├── setup_database.py               # Initial database setup
│   ├── migrate_database.py             # Database migrations
│   ├── migrate_bot_tables.py           # Bot table migrations
│   ├── create_admin.py                 # Admin user creation
│   └── migrations/
│       └── 001_create_bot_tables.sql   # Bot system schema
│
├── Configuration
│   ├── .env.example                    # Environment variables template
│   ├── .replit                         # Replit deployment config
│   ├── .streamlit/
│   │   └── config.toml                 # Streamlit configuration
│   ├── pyproject.toml                  # Project dependencies (Poetry)
│   ├── poetry.lock                     # Locked dependencies
│   └── .gitignore                      # Git ignore rules
│
├── Documentation
│   ├── README.md                       # Main readme
│   ├── QUICKSTART.md                   # Quick start guide
│   ├── ARCHITECTURE_ANALYSIS.md        # Detailed architecture
│   ├── EXECUTIVE_SUMMARY.md            # Executive overview
│   ├── TRADING_BOT_SETUP.md            # Bot setup instructions
│   ├── AUTHENTICATION_SETUP.md         # Auth setup
│   ├── ADMIN_SETUP.md                  # Admin configuration
│   ├── DEPLOYMENT_GUIDE.md             # Deployment instructions
│   ├── REPLIT_WORKFLOW_GUIDE.md        # Replit deployment
│   ├── SYNC_GUIDE.md                   # Git sync guide
│   ├── Base-Machine-system_architecture.md
│   └── Base-Machine-system_readme.md
│
└── Supporting Files
    └── attached_assets/                # Historical assets and logs
```

---

## 12. API Reference

### 12.1 TradingView Webhook Format

**Endpoint:** `POST http://your-domain.com/webhook?token=USER_TOKEN`

**Headers:**
```
Content-Type: application/json
```

**Payload:**
```json
{
    "action": "BUY",
    "symbol": "AAPL",
    "timeframe": "15 Min",
    "price": 145.50
}
```

**Actions:**
- `BUY` - Open long position
- `SELL` - Open short position (or close long)
- `CLOSE` - Close current position

**Timeframes:**
- `1 Min`, `5 Min`, `15 Min`, `30 Min`, `1 Hour`, `4 Hour`, `1 Day`

**Response:**
```json
{
    "status": "success",
    "order_id": "abc123",
    "symbol": "AAPL",
    "action": "BUY",
    "filled_qty": 10,
    "filled_avg_price": 145.48,
    "notional": 1454.80
}
```

**Error Response:**
```json
{
    "status": "error",
    "message": "Invalid token",
    "code": "AUTH_ERROR"
}
```

### 12.2 TradingView Alert Setup

**Example Alert Message:**

```json
{
    "action": "{{strategy.order.action}}",
    "symbol": "{{ticker}}",
    "timeframe": "{{interval}}",
    "price": {{close}}
}
```

**Webhook URL:**
```
http://your-replit-domain.com/webhook?token=YOUR_WEBHOOK_TOKEN
```

---

## Conclusion

DashTrade is a full-featured, production-ready trading platform combining:

- **Educational Dashboard**: Real-time technical analysis with 35+ indicators
- **Automated Trading**: TradingView webhook integration with Alpaca Markets
- **Multi-User System**: Secure, role-based access with encrypted credentials
- **Strategy Development**: Backtesting and custom strategy builder
- **Portfolio Management**: Watchlists, alerts, performance tracking

**Total Codebase:** ~10,236 lines of Python across 16+ core modules

**Key Technologies:** Streamlit, Flask, PostgreSQL, Alpaca API, Yahoo Finance

**Deployment:** Replit (dev/test), Docker (production)

---

**For Questions or Support:**
- GitHub: https://github.com/bot7897481/DashTrade
- Documentation: See `/home/user/DashTrade/README.md`
