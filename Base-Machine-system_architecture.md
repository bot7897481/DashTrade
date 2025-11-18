# NovAlgo Trading Bot - System Architecture

## 📐 Purpose

This document provides technical architecture details for AI assistants (Claude, ChatGPT, etc.) and developers to understand and modify the system.

---

## 🏛️ System Architecture Overview

### Layered Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐│
│  │  TradingView     │  │  Google Sheets   │  │  Email/SMS/   ││
│  │  Webhook UI      │  │  Interface       │  │  Slack        ││
│  └──────────────────┘  └──────────────────┘  └───────────────┘│
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Flask Webhook Server (Port 80)              │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐│  │
│  │  │ Validation │→ │ Config Mgr │→ │ Trading Engine     ││  │
│  │  │ Middleware │  │            │  │ - Long/Short/Close ││  │
│  │  └────────────┘  └────────────┘  └────────────────────┘│  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Background Services                           │  │
│  │  ┌──────────────────────┐  ┌──────────────────────────┐│  │
│  │  │ Performance Updater  │  │ Analytics Suite          ││  │
│  │  │ (5 min intervals)    │  │ (On-demand)              ││  │
│  │  └──────────────────────┘  └──────────────────────────┘│  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      INTEGRATION LAYER                          │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ Alpaca API      │  │ Google Sheets    │  │ Notification  │ │
│  │ Connector       │  │ API Connector    │  │ Gateways      │ │
│  └─────────────────┘  └──────────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                          │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ Alpaca Markets  │  │ Google Cloud     │  │ Twilio/Slack  │ │
│  │ (Trading API)   │  │ (Sheets API)     │  │ (Alerts)      │ │
│  └─────────────────┘  └──────────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Request Flow Diagrams

### Webhook Request Flow (Detailed)

```
┌─────────────┐
│ TradingView │
│   Alert     │
└──────┬──────┘
       │ 1. HTTP POST /webhook
       │    Content-Type: application/json
       │    Body: {"action": "BUY", "symbol": "AAPL", "timeframe": "15 Min", "secret": "..."}
       ▼
┌──────────────────────────────────────┐
│     Flask Server (Port 80)           │
│  ┌────────────────────────────────┐  │
│  │  @app.route('/webhook')        │  │
│  │  def webhook():                │  │
│  └────────────────────────────────┘  │
└──────────────┬───────────────────────┘
               │ 2. Parse JSON request
               ▼
       ┌───────────────┐
       │ Validation    │
       │ Check secret  │
       └───────┬───────┘
               │ 3. If valid, continue
               │    If invalid, return 401
               ▼
       ┌───────────────────────────┐
       │ Extract Data:             │
       │ - action = "BUY"          │
       │ - symbol = "AAPL"         │
       │ - timeframe = "15 Min"    │
       └───────┬───────────────────┘
               │ 4. Call get_stock_config()
               ▼
┌──────────────────────────────────────┐
│     Google Sheets API Call           │
│  ┌────────────────────────────────┐  │
│  │ 1. Authenticate (credentials)  │  │
│  │ 2. Open sheet by ID            │  │
│  │ 3. Read "Config" tab           │  │
│  │ 4. Get all records             │  │
│  └────────────────────────────────┘  │
└──────────────┬───────────────────────┘
               │ 5. Returns: {("AAPL", "15 Min"): 5000, ...}
               ▼
       ┌───────────────────────────┐
       │ Match Key:                │
       │ ("AAPL", "15 Min")        │
       │ Found: position_size=5000 │
       └───────┬───────────────────┘
               │ 6. Call execute_long_signal("AAPL", "15 Min", 5000)
               ▼
┌────────────────────────────────────────────┐
│       Trading Engine: execute_long_signal  │
│  ┌──────────────────────────────────────┐  │
│  │ 1. Check current position (Alpaca)  │  │
│  │    → GET /v2/positions/AAPL          │  │
│  │                                      │  │
│  │ 2. If SHORT: Close first             │  │
│  │    → DELETE /v2/positions/AAPL       │  │
│  │                                      │  │
│  │ 3. If already LONG: Skip             │  │
│  │    → Return {"status": "skipped"}    │  │
│  │                                      │  │
│  │ 4. If FLAT: Continue                 │  │
│  └──────────────────────────────────────┘  │
└────────────────┬───────────────────────────┘
                 │ 7. Place order
                 ▼
┌────────────────────────────────────────────┐
│       Update Status: "ORDER SUBMITTED"     │
│  ┌──────────────────────────────────────┐  │
│  │ Google Sheets API                    │  │
│  │ Update cell E[row] = "ORDER SUBMITTED"│ │
│  │ Update cell F[row] = "2025-10-10..." │  │
│  └──────────────────────────────────────┘  │
└────────────────┬───────────────────────────┘
                 │ 8. Submit to Alpaca
                 ▼
┌────────────────────────────────────────────┐
│         Alpaca API: Place Order            │
│  ┌──────────────────────────────────────┐  │
│  │ POST /v2/orders                      │  │
│  │ {                                    │  │
│  │   "symbol": "AAPL",                  │  │
│  │   "notional": 5000,                  │  │
│  │   "side": "buy",                     │  │
│  │   "type": "market",                  │  │
│  │   "time_in_force": "day"             │  │
│  │ }                                    │  │
│  │                                      │  │
│  │ Response: {"id": "abc123...", ...}  │  │
│  └──────────────────────────────────────┘  │
└────────────────┬───────────────────────────┘
                 │ 9. Wait 2 seconds
                 ▼
┌────────────────────────────────────────────┐
│         Check Order Status                 │
│  ┌──────────────────────────────────────┐  │
│  │ GET /v2/orders/abc123                │  │
│  │                                      │  │
│  │ If status == "filled":               │  │
│  │   → Update Status: "FILLED"          │  │
│  │ If status == "pending":              │  │
│  │   → Keep "ORDER SUBMITTED"           │  │
│  │ If status == "rejected":             │  │
│  │   → Update Status: "FAILED"          │  │
│  └──────────────────────────────────────┘  │
└────────────────┬───────────────────────────┘
                 │ 10. Return response
                 ▼
┌────────────────────────────────────────────┐
│         Return JSON to TradingView         │
│  {                                         │
│    "status": "success",                    │
│    "action": "BUY",                        │
│    "symbol": "AAPL",                       │
│    "timeframe": "15 Min",                  │
│    "amount": 5000,                         │
│    "order_id": "abc123..."                 │
│  }                                         │
└────────────────────────────────────────────┘
```

---

## 📦 Component Details

### 1. Flask Webhook Server

**File:** `trading_bot.py`  
**Class:** N/A (functional design)  
**Port:** 80  
**Framework:** Flask 2.x

**Responsibilities:**
- Accept HTTP POST requests from TradingView
- Validate webhook secret
- Route requests to appropriate handlers
- Serve utility endpoints (health, config, positions)
- Return JSON responses

**Key Routes:**
```python
POST   /webhook        # Main trading endpoint
GET    /health         # Health check
GET    /config         # Show configuration
GET    /positions      # Show current positions
GET    /performance    # Trigger performance update
```

**Dependencies:**
- Flask
- alpaca-trade-api
- gspread
- oauth2client
- pytz

---

### 2. Configuration Manager

**Responsibilities:**
- Read Google Sheets "Config" tab
- Parse and validate configuration
- Map (symbol, timeframe) to position_size
- Track row numbers for status updates
- Handle active/inactive states

**Data Structure:**
```python
# Input: Google Sheets rows
[
  {"symbol": "AAPL", "position_size": 5000, "active": True, "Time Frame": "15 Min"},
  {"symbol": "HOOD", "position_size": 40000, "active": True, "Time Frame": "45 Min"}
]

# Output: config_dict
{
  ("AAPL", "15 Min"): 5000,
  ("HOOD", "45 Min"): 40000
}

# Also maintains: config_row_map
{
  ("AAPL", "15 Min"): 2,  # Row number in sheet
  ("HOOD", "45 Min"): 3
}
```

**Key Functions:**
```python
def get_stock_config() -> dict
    """
    Returns: Dict mapping (symbol, timeframe) to position_size
    Side effects: Updates config_row_map global variable
    """
```

---

### 3. Trading Engine

**Responsibilities:**
- Execute BUY/SELL/CLOSE signals
- Check existing positions
- Manage opposite position closing
- Place orders via Alpaca API
- Update order status in Google Sheets

**State Machine:**

```
[WEBHOOK RECEIVED]
       │
       ▼
┌─────────────────┐
│  Parse Signal   │
│  (BUY/SELL/     │
│   CLOSE)        │
└────────┬────────┘
         │
         ▼
  ┌─────────────┐     NO      ┌──────────────┐
  │ Check Active│──────────────▶│ Return       │
  │ in Config?  │             │ "skipped"    │
  └──────┬──────┘             └──────────────┘
         │ YES
         ▼
  ┌─────────────────┐
  │ Get Position    │
  │ from Alpaca     │
  └────────┬────────┘
           │
           ▼
   ┌──────────────────────┐
   │ Position State?      │
   └──┬────────┬──────────┘
      │        │
  LONG│    SHORT│    FLAT│
      │        │         │
      ▼        ▼         ▼
┌──────────┐ ┌──────┐ ┌─────────┐
│If BUY:   │ │Close │ │Continue │
│ Skip     │ │First │ │to Order │
│If SELL:  │ │      │ │         │
│ Close    │ └──────┘ └─────────┘
└──────────┘
      │
      ▼
┌──────────────────┐
│ Update Status:   │
│ "ORDER SUBMITTED"│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Submit Order to  │
│ Alpaca API       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Wait 2 seconds   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Check Status     │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
 FILLED   PENDING/
    │      FAILED
    ▼         ▼
┌─────────┐ ┌──────────┐
│ Update  │ │ Update   │
│ "FILLED"│ │ "FAILED" │
└─────────┘ └──────────┘
```

**Key Functions:**
```python
def execute_long_signal(symbol, timeframe, position_size) -> dict
    """
    Executes BUY order
    Returns: {"status": "success|error|skipped", ...}
    """

def execute_short_signal(symbol, timeframe, position_size) -> dict
    """
    Executes SELL order
    Returns: {"status": "success|error|skipped", ...}
    """

def execute_close_signal(symbol, timeframe) -> dict
    """
    Closes position
    Returns: {"status": "success|info", ...}
    """
```

---

### 4. Status Tracker

**Responsibilities:**
- Update "Order Status" column in Google Sheets
- Update "Last Updated" timestamp (PST)
- Track order lifecycle

**Status Flow:**
```
READY
  ↓ (webhook received)
ORDER SUBMITTED
  ↓ (2 seconds later)
FILLED / FAILED / PARTIAL FILL
  ↓ (position closed)
WAITING
```

**Special States:**
- `ALREADY LONG` - Skipped duplicate BUY
- `ALREADY SHORT` - Skipped duplicate SELL
- `INACTIVE` - Stock disabled (active=FALSE)

**Key Functions:**
```python
def update_order_status(symbol, timeframe, status, message="")
    """
    Updates Google Sheets columns E (status) and F (timestamp)
    Uses config_row_map to find correct row
    """
```

---

### 5. Performance Tracker

**Responsibilities:**
- Calculate realized P&L from trade history
- Update "Performance" tab every 5 minutes
- Match buys with sells using FIFO
- Calculate win rate, average P&L, best/worst trades

**Algorithm: FIFO P&L Calculation**

```python
# Pseudocode
for each symbol:
    buys = get_buys(symbol)  # Sorted by time
    sells = get_sells(symbol)
    
    buy_queue = buys.copy()
    total_pnl = 0
    
    for sell in sells:
        remaining_qty = sell.qty
        
        while remaining_qty > 0 and buy_queue:
            buy = buy_queue[0]
            
            matched_qty = min(remaining_qty, buy.qty)
            pnl = (sell.price - buy.price) * matched_qty
            
            total_pnl += pnl
            remaining_qty -= matched_qty
            buy.qty -= matched_qty
            
            if buy.qty == 0:
                buy_queue.pop(0)
    
    return total_pnl
```

**Background Thread:**
```python
def performance_updater():
    while True:
        time.sleep(60)  # Initial delay
        update_performance_dashboard()
        time.sleep(300)  # 5 minutes
```

---

## 🗄️ Data Models

### Configuration Data Model

```python
class StockConfig:
    """
    Represents one row in Google Sheets Config tab
    """
    symbol: str            # e.g., "AAPL"
    position_size: int     # e.g., 5000
    active: bool           # True/False
    timeframe: str         # e.g., "15 Min"
    order_status: str      # e.g., "FILLED"
    last_updated: str      # e.g., "2025-10-10 14:30:00 PST"
    
    # Derived
    config_key: tuple      # (symbol, timeframe)
    row_number: int        # Row in Google Sheets (for updates)
```

### Position Data Model

```python
class Position:
    """
    Represents current position from Alpaca
    """
    symbol: str
    qty: float             # Positive = LONG, Negative = SHORT
    side: str              # "LONG" or "SHORT"
    market_value: float
    unrealized_pl: float
    unrealized_plpc: float  # Percentage
    entry_price: float      # Average entry price
    current_price: float
```

### Trade Data Model

```python
class Trade:
    """
    Represents one fill activity from Alpaca
    """
    symbol: str
    side: str              # "buy" or "sell"
    qty: float
    price: float
    transaction_time: datetime
    order_id: str
```

### Performance Data Model

```python
class PerformanceMetrics:
    """
    Represents performance data for one symbol
    """
    symbol: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float        # Percentage
    total_pnl: float
    avg_pnl_per_trade: float
    best_trade: float
    worst_trade: float
    last_updated: str
```

---

## 🔌 API Contracts

### Alpaca API

**Base URL:** `https://paper-api.alpaca.markets`

**Authentication:**
```
Headers:
  APCA-API-KEY-ID: {API_KEY}
  APCA-API-SECRET-KEY: {SECRET_KEY}
```

**Key Endpoints Used:**

```python
# Get account info
GET /v2/account
Response: {
  "equity": "160000.00",
  "cash": "150000.00",
  "buying_power": "160000.00",
  ...
}

# Get positions
GET /v2/positions
Response: [
  {
    "symbol": "AAPL",
    "qty": "-19",
    "market_value": "-4668.30",
    "unrealized_pl": "130.15",
    ...
  }
]

# Place order
POST /v2/orders
Body: {
  "symbol": "AAPL",
  "notional": 5000,
  "side": "buy",
  "type": "market",
  "time_in_force": "day"
}
Response: {
  "id": "abc123...",
  "status": "accepted",
  ...
}

# Get order status
GET /v2/orders/{order_id}
Response: {
  "id": "abc123...",
  "status": "filled",
  ...
}

# Close position
DELETE /v2/positions/{symbol}
Response: {status: "ok"}

# Get activities
GET /v2/account/activities?activity_types=FILL&date={start_date}
Response: [
  {
    "activity_type": "FILL",
    "symbol": "AAPL",
    "side": "buy",
    "qty": "15",
    "price": "145.50",
    "transaction_time": "2025-10-10T10:30:00Z",
    ...
  }
]
```

---

### Google Sheets API

**Authentication:** OAuth2 Service Account

**Key Operations:**

```python
# Open spreadsheet
spreadsheet = client.open_by_key(SHEET_ID)

# Get worksheet
sheet = spreadsheet.worksheet('Config')

# Read all records (returns list of dicts)
records = sheet.get_all_records()
# Returns: [{"symbol": "AAPL", "position_size": 5000, ...}, ...]

# Update single cell
sheet.update('E2', [['FILLED']])

# Update range
sheet.update('A2:J5', [[row1], [row2], [row3], [row4]])

# Batch clear
sheet.batch_clear(['A2:J100'])
```

---

## 🔄 State Management

### Global State Variables

```python
# In trading_bot.py

position_tracker = {}
# Stores: {(symbol, timeframe): {"side": "buy", "order_id": "...", "timestamp": ...}}
# Purpose: Track recent orders
# Lifetime: Process lifetime (cleared on restart)

config_row_map = {}
# Stores: {(symbol, timeframe): row_number}
# Purpose: Map config keys to Google Sheets rows for updates
# Lifetime: Regenerated on each get_stock_config() call

# No other global state - stateless design
```

### Session Management

**No user sessions** - Each webhook is independent

**Idempotency:** 
- Duplicate webhooks for same symbol/timeframe are handled
- "ALREADY LONG" / "ALREADY SHORT" prevents duplicate entries
- No database, so no transaction management needed

---

## 🔐 Security Architecture

### Defense in Depth

```
Layer 1: Network (Azure NSG)
  → Only ports 22, 80 open

Layer 2: Firewall (UFW)
  → Port 80: Only TradingView IPs + User IPs
  → Port 22: All IPs (SSH)

Layer 3: Application (Flask)
  → Webhook secret validation
  → JSON parsing with error handling

Layer 4: API (Alpaca/Google)
  → API keys/credentials stored in code
  → Paper trading (limited risk)
```

### Authentication Flow

```
TradingView → Webhook Request
  ↓
Contains secret in JSON body
  ↓
Flask validates: data.get('secret') == WEBHOOK_SECRET
  ↓
If match: Continue
If no match: Return 401 Unauthorized
```

**Weakness:** Secret in plaintext in code  
**Mitigation:** Use environment variables (future)

---

## 📊 Monitoring & Observability

### Logging Strategy

**Log Levels:**
- `INFO`: Normal operations (webhook received, order placed, config loaded)
- `WARNING`: Non-critical issues (stock not in config, duplicate signal)
- `ERROR`: Failures (API errors, order failures, Google Sheets errors)

**Log Destinations:**
1. **stdout/stderr** → captured by systemd
2. **File:** `/home/azureuser/trading_bot.log`
3. **journald:** System journal (persistent)

**Log Format:**
```
2025-10-10 14:30:00,123 - INFO - 📨 WEBHOOK: {"action": "BUY", "symbol": "AAPL", ...}
2025-10-10 14:30:00,456 - INFO - ✅ ORDER SUBMITTED: BUY $5,000 AAPL 15 Min - Order ID: abc123
```

### Metrics Tracked

**Application Metrics:**
- Webhooks received per hour
- Orders placed per hour
- Order success rate
- Average response time

**Business Metrics:**
- Total P&L
- Win rate
- Position count
- Exposure levels

**System Metrics:**
- Memory usage (via systemd)
- CPU usage
- Uptime

---

## 🚀 Deployment Architecture

### Infrastructure

```
Azure Cloud
└── Virtual Machine (B1s)
    ├── OS: Ubuntu 22.04 LTS
    ├── RAM: 1 GB
    ├── CPU: 1 vCPU
    ├── Disk: 30 GB SSD
    ├── IP: 20.245.132.209 (static)
    └── Network Security Group
        ├── Allow: 22 (SSH)
        ├── Allow: 80 (HTTP)
        └── Deny: All others
```

### Service Management

```
systemd
└── trading-bot.service
    ├── Type: simple
    ├── User: azureuser
    ├── ExecStart: /usr/bin/python3 /home/azureuser/trading_bot.py
    ├── Restart: always
    ├── RestartSec: 10s
    └── Logs: journalctl -u trading-bot
```

### Deployment Pipeline

```
1. Code Development (Local/AI-generated)
   ↓
2. Manual testing (optional)
   ↓
3. SSH to Azure VM
   ↓
4. Backup current version
   ↓
5. Upload/edit new code
   ↓
6. Restart systemd service
   ↓
7. Verify logs
   ↓
8. Test with manual webhook
   ↓
9. Monitor for 1 hour
```

**No CI/CD** - Manual deployment

---

## 🔮 Future Architecture Plans

### Planned: IBKR Bot (Options & Futures)

```
Same Azure VM
├── trading_bot.py (Port 80) ← Existing
└── ibkr_bot.py (Port 8080) ← New
    ├── IB Gateway (localhost:7497)
    ├── Google Sheets (new tabs)
    └── TradingView webhooks
```

### Potential Enhancements

1. **Database Layer**
   - Replace Google Sheets with PostgreSQL
   - Store trade history locally
   - Faster queries, more complex analytics

2. **Message Queue**
   - Add Redis/RabbitMQ
   - Queue webhooks for processing
   - Better handling of bursts

3. **API Gateway**
   - nginx reverse proxy
   - HTTPS/SSL
   - Rate limiting
   - Load balancing (if scaling)

4. **Containerization**
   - Docker containers
   - docker-compose for multi-bot setup
   - Easier deployment

---

## 📝 Code Organization Principles

### Functional Programming Style

- Pure functions where possible
- Minimal global state
- Explicit dependencies (no hidden state)

### Error Handling Pattern

```python
try:
    result = risky_operation()
    logger.info("✅ Success")
    return {"status": "success", "data": result}
except SpecificException as e:
    logger.error(f"❌ Error: {e}")
    return {"status": "error", "reason": str(e)}
except Exception as e:
    logger.error(f"❌ Unexpected error: {e}")
    logger.error(traceback.format_exc())
    return {"status": "error", "reason": "Internal error"}
```

### Naming Conventions

- Functions: `snake_case` (e.g., `get_stock_config`)
- Constants: `UPPER_CASE` (e.g., `WEBHOOK_SECRET`)
- Variables: `snake_case` (e.g., `position_size`)
- Files: `snake_case.py` (e.g., `trading_bot.py`)

---

## 🧪 Testing Strategy

### Current State: Manual Testing

**No automated tests** - All testing is manual

**Test Procedure:**
1. Update code
2. Restart bot
3. Send manual webhook via curl
4. Check logs
5. Verify Google Sheets updated
6. Check Alpaca positions

### Future: Automated Testing

**Unit Tests:**
```python
def test_get_stock_config():
    # Mock Google Sheets response
    # Assert correct parsing
    pass

def test_execute_long_signal():
    # Mock Alpaca API
    # Assert order placed correctly
    pass
```

**Integration Tests:**
```python
def test_full_webhook_flow():
    # Send test webhook
    # Verify end-to-end flow
    pass
```

---

## 📚 Dependencies

### Python Requirements

```
flask==2.3.0
alpaca-trade-api==3.0.0
gspread==5.10.0
oauth2client==4.1.3
pytz==2023.3

# Optional (for analytics)
matplotlib==3.7.0
pandas==2.0.0
numpy==1.24.0
twilio==8.5.0
requests==2.31.0
```

### External Services

- **Alpaca Markets** - Trading API (free paper trading)
- **Google Cloud** - Sheets API (free tier)
- **TradingView** - Webhook source (free/premium)
- **Twilio** - SMS alerts (pay-per-use)
- **Slack** - Team notifications (free)

---

*This document is intended for AI assistants and developers to understand the system architecture for maintenance and enhancement purposes.*

*Last Updated: 2025-10-10*