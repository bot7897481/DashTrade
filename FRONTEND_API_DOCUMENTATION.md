# DashTrade Frontend API Documentation
## For Lovable AI / React Frontend Integration

**API Base URL:** `https://overflowing-spontaneity-production.up.railway.app`
**Webhook URL:** `https://webhook.novalgo.org`

---

## New Features to Implement

### 1. Per-Bot Webhook URLs (Simplified TradingView Integration)

Each bot now has its own unique webhook URL. Users no longer need to specify symbol and timeframe in TradingView alerts - just the action!

**TradingView Setup (Simplified):**
```
Webhook URL: https://webhook.novalgo.org/webhook?token=bot_xxxYourBotToken
Message: {"action": "{{strategy.order.action}}"}
```

---

## API Endpoints

### Authentication

#### POST /api/auth/register
Create a new user account.

**Request:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string (optional)",
  "admin_code": "string (optional)"
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Registration successful",
  "user_id": 123,
  "token": "jwt_token_here"
}
```

#### POST /api/auth/login
Authenticate and get JWT token. **Supports login with username OR email address.**

**Request:**
```json
{
  "username": "string",  // Can be username OR email address
  "password": "string"
}
```

**Examples:**
```json
// Login with username
{ "username": "johndoe", "password": "secret123" }

// Login with email
{ "username": "john@example.com", "password": "secret123" }
```

**Response (200):**
```json
{
  "success": true,
  "token": "jwt_token_here",
  "user": {
    "id": 123,
    "username": "string",
    "email": "string",
    "full_name": "string",
    "role": "user"
  }
}
```

**Frontend Implementation Notes:**
- The `username` field accepts EITHER a username or email address
- Backend detects email by checking for `@` character
- Update form label to "Username or Email"
- Update placeholder to show both options: "johndoe or john@example.com"
- Validation should accept: email format OR 3+ characters for username

#### GET /api/auth/me
Get current authenticated user info.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": 123,
  "username": "string",
  "email": "string",
  "full_name": "string",
  "role": "user",
  "created_at": "2024-01-01T00:00:00"
}
```

---

### Bot Management

#### GET /api/bots
Get all bots for the authenticated user.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "bots": [
    {
      "id": 1,
      "user_id": 123,
      "symbol": "SPY",
      "timeframe": "15 Min",
      "position_size": 1000.00,
      "is_active": true,
      "strategy_name": "My Strategy",
      "risk_limit_percent": 10.00,
      "daily_loss_limit": 500.00,
      "max_position_size": 2000.00,
      "order_status": "READY",
      "last_signal": "BUY",
      "last_signal_time": "2024-01-01T12:00:00",
      "current_position_side": "LONG",
      "total_pnl": 150.50,
      "total_trades": 25,
      "signal_source": "webhook",
      "webhook_token": "bot_abc123...",
      "webhook_url": "https://webhook.novalgo.org/webhook?token=bot_abc123...",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T12:00:00"
    }
  ],
  "total": 1,
  "active": 1
}
```

**NEW FIELDS:**
- `webhook_token` - Unique token for this bot's webhook
- `webhook_url` - Full URL to use in TradingView alerts

#### POST /api/bots
Create a new bot configuration.

**Headers:** `Authorization: Bearer <token>`

**Request:**
```json
{
  "symbol": "SPY",
  "timeframe": "15 Min",
  "position_size": 1000.00,
  "strategy_name": "My Strategy (optional)",
  "risk_limit_percent": 10.0,
  "daily_loss_limit": 500.00,
  "max_position_size": 2000.00,
  "signal_source": "webhook"
}
```

**Response (201):**
```json
{
  "success": true,
  "bot_id": 1,
  "message": "Bot created for SPY 15 Min",
  "webhook_url": "https://webhook.novalgo.org/webhook?token=bot_abc123...",
  "webhook_payload": "{\"action\": \"{{strategy.order.action}}\"}"
}
```

**NEW FIELDS:**
- `webhook_url` - Ready-to-use URL for TradingView
- `webhook_payload` - Example payload to copy into TradingView alert

#### PUT /api/bots/:id
Update a bot configuration.

**Headers:** `Authorization: Bearer <token>`

**Request:**
```json
{
  "position_size": 1500.00,
  "strategy_name": "Updated Strategy",
  "risk_limit_percent": 15.0,
  "daily_loss_limit": 750.00,
  "max_position_size": 3000.00
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Bot updated"
}
```

#### DELETE /api/bots/:id
Delete a bot configuration.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "success": true,
  "message": "Bot deleted"
}
```

#### POST /api/bots/:id/toggle
Toggle bot active/inactive status.

**Headers:** `Authorization: Bearer <token>`

**Request (optional):**
```json
{
  "is_active": true
}
```

**Response (200):**
```json
{
  "success": true,
  "is_active": true,
  "message": "Bot activated"
}
```

#### POST /api/bots/:id/regenerate-token (NEW)
Regenerate webhook token for a bot.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "success": true,
  "webhook_token": "bot_newtoken123...",
  "webhook_url": "https://webhook.novalgo.org/webhook?token=bot_newtoken123...",
  "webhook_payload": "{\"action\": \"{{strategy.order.action}}\"}",
  "message": "Webhook token regenerated. Update your TradingView alert with the new URL."
}
```

---

### Trading & Account

#### GET /api/account
Get Alpaca account information.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "equity": 25000.00,
  "cash": 10000.00,
  "buying_power": 50000.00,
  "portfolio_value": 25000.00
}
```

#### GET /api/positions
Get all open positions.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "positions": [
    {
      "symbol": "SPY",
      "qty": 10,
      "side": "LONG",
      "market_value": 4500.00,
      "unrealized_pl": 50.00,
      "unrealized_plpc": 1.12,
      "entry_price": 445.00,
      "current_price": 450.00
    }
  ],
  "total": 1
}
```

#### GET /api/trades
Get trade history with enhanced details.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (int, default 50): Max number of trades to return
- `symbol` (string, optional): Filter by symbol

**Response (200):**
```json
{
  "trades": [
    {
      "id": 1,
      "user_id": 123,
      "bot_config_id": 1,
      "symbol": "SPY",
      "timeframe": "15 Min",
      "action": "BUY",
      "notional": 1000.00,
      "order_id": "alpaca-order-id",
      "status": "FILLED",
      "filled_qty": 2.22,
      "filled_avg_price": 450.50,
      "filled_at": "2024-01-01T12:00:05",
      "created_at": "2024-01-01T12:00:00",

      // NEW Enhanced Trade Details
      "bid_price": 450.45,
      "ask_price": 450.55,
      "spread": 0.10,
      "spread_percent": 0.022,
      "market_open": true,
      "extended_hours": false,
      "signal_source": "bot_webhook",
      "signal_received_at": "2024-01-01T12:00:00",
      "order_submitted_at": "2024-01-01T12:00:01",
      "execution_latency_ms": 1000,
      "time_to_fill_ms": 4000,
      "order_type": "market",
      "time_in_force": "day",
      "expected_price": 450.55,
      "slippage": -0.05,
      "slippage_percent": -0.011,
      "position_before": "FLAT",
      "position_after": "LONG",
      "position_qty_before": 0,
      "position_value_before": 0,
      "account_equity": 25000.00,
      "account_buying_power": 50000.00
    }
  ],
  "total": 1
}
```

**NEW FIELDS EXPLAINED:**

| Field | Description |
|-------|-------------|
| `bid_price` | Best bid price at time of order |
| `ask_price` | Best ask price at time of order |
| `spread` | Difference between ask and bid (in $) |
| `spread_percent` | Spread as percentage of price |
| `market_open` | Whether market was open (true/false) |
| `extended_hours` | Whether trade was in extended hours |
| `signal_source` | Source: "bot_webhook", "user_webhook", "system" |
| `signal_received_at` | When the webhook signal was received |
| `order_submitted_at` | When order was submitted to Alpaca |
| `execution_latency_ms` | Time from signal to order submission (ms) |
| `time_to_fill_ms` | Time from submission to fill (ms) |
| `expected_price` | Price we expected to get (ask for buy, bid for sell) |
| `slippage` | Difference between expected and actual price ($) |
| `slippage_percent` | Slippage as percentage |
| `position_before` | Position state before trade: "LONG", "SHORT", "FLAT" |
| `position_after` | Position state after trade |
| `position_qty_before` | Number of shares before trade |
| `position_value_before` | Dollar value of position before trade |
| `account_equity` | Account equity at time of trade |
| `account_buying_power` | Buying power at time of trade |

---

### Settings

#### POST /api/settings/api-keys
Save Alpaca API keys.

**Headers:** `Authorization: Bearer <token>`

**Request:**
```json
{
  "api_key": "PK...",
  "secret_key": "secret...",
  "mode": "paper"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "API keys saved (paper mode)"
}
```

#### GET /api/settings/api-keys/status
Check if API keys are configured.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "configured": true,
  "mode": "paper",
  "is_active": true
}
```

---

### User Webhook Token (Legacy - Still Supported)

#### GET /api/webhook-token
Get user's webhook token (requires symbol/timeframe in payload).

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "token": "usr_abc123...",
  "webhook_url": "https://webhook.novalgo.org/webhook?token=usr_abc123..."
}
```

#### POST /api/webhook-token/regenerate
Regenerate user's webhook token.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "success": true,
  "token": "usr_newtoken123...",
  "webhook_url": "https://webhook.novalgo.org/webhook?token=usr_newtoken123..."
}
```

---

### Dashboard

#### GET /api/dashboard
Get dashboard summary.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "account": {
    "equity": 25000.00,
    "cash": 10000.00,
    "buying_power": 50000.00,
    "portfolio_value": 25000.00
  },
  "positions": [...],
  "bots": {
    "total": 5,
    "active": 3
  },
  "recent_trades": [...],
  "api_keys_configured": true
}
```

---

## Frontend UI Recommendations

### Bot Card Component
Display each bot with:
- Symbol and Timeframe
- Position Size
- Status (Active/Inactive toggle)
- Current Position (LONG/SHORT/FLAT)
- Total P&L
- **NEW: Webhook URL with copy button**
- **NEW: "Regenerate Token" button**

Example UI:
```
┌─────────────────────────────────────────────────┐
│ SPY - 15 Min                        [Active ✓] │
├─────────────────────────────────────────────────┤
│ Position Size: $1,000                           │
│ Current: LONG (+$50.00)                        │
│ Total P&L: +$150.50 (25 trades)                │
├─────────────────────────────────────────────────┤
│ Webhook URL:                                    │
│ [https://webhook.novalgo.org/we...] [Copy]     │
│                                                 │
│ TradingView Payload:                           │
│ {"action": "{{strategy.order.action}}"}  [Copy]│
│                                                 │
│ [Regenerate Token]                              │
└─────────────────────────────────────────────────┘
```

### Trade History Component
Display enhanced trade details:
- Show execution quality metrics (slippage, latency)
- Color-code slippage (green for positive, red for negative)
- Show market conditions at time of trade
- Filter by symbol, date range, action type

Example Row:
```
┌──────────────────────────────────────────────────────────────────────┐
│ BUY SPY @ $450.50 (2.22 shares)                    Jan 1, 12:00 PM  │
│ Expected: $450.55 | Slippage: -$0.05 (-0.01%)     Filled in 4.0s   │
│ Market: Open | Spread: $0.10 (0.02%)              Signal: bot_webhook│
│ Position: FLAT → LONG | Account: $25,000                            │
└──────────────────────────────────────────────────────────────────────┘
```

### Trade Analytics Dashboard (NEW)
Create a new page/section showing:
- Average slippage over time
- Average execution latency
- Best/worst execution times
- Spread analysis
- Extended hours vs regular hours performance

---

## Webhook Integration Guide (For Users)

### Option 1: Bot-Specific Webhook (Recommended - Simplest)
1. Create a bot for your symbol/timeframe
2. Copy the bot's webhook URL
3. In TradingView, create alert with:
   - Webhook URL: `https://webhook.novalgo.org/webhook?token=bot_xxxYourToken`
   - Message: `{"action": "{{strategy.order.action}}"}`

### Option 2: User Webhook (Legacy)
1. Get your user webhook token from Settings
2. In TradingView, create alert with:
   - Webhook URL: `https://webhook.novalgo.org/webhook?token=usr_xxxYourToken`
   - Message: `{"action": "{{strategy.order.action}}", "symbol": "SPY", "timeframe": "15 Min"}`

---

## Error Responses

All endpoints return errors in this format:
```json
{
  "error": "Error message description"
}
```

Common HTTP status codes:
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (missing or invalid token)
- `404` - Not Found
- `500` - Internal Server Error

---

## TypeScript Interfaces

```typescript
interface Bot {
  id: number;
  user_id: number;
  symbol: string;
  timeframe: string;
  position_size: number;
  is_active: boolean;
  strategy_name?: string;
  risk_limit_percent: number;
  daily_loss_limit?: number;
  max_position_size?: number;
  order_status: string;
  last_signal?: string;
  last_signal_time?: string;
  current_position_side?: string;
  total_pnl: number;
  total_trades: number;
  signal_source: string;
  webhook_token: string;
  webhook_url: string;
  created_at: string;
  updated_at: string;
}

interface Trade {
  id: number;
  user_id: number;
  bot_config_id: number;
  symbol: string;
  timeframe: string;
  action: 'BUY' | 'SELL' | 'CLOSE';
  notional: number;
  order_id?: string;
  status: string;
  filled_qty?: number;
  filled_avg_price?: number;
  filled_at?: string;
  created_at: string;

  // Enhanced details
  bid_price?: number;
  ask_price?: number;
  spread?: number;
  spread_percent?: number;
  market_open?: boolean;
  extended_hours?: boolean;
  signal_source?: string;
  signal_received_at?: string;
  order_submitted_at?: string;
  execution_latency_ms?: number;
  time_to_fill_ms?: number;
  order_type?: string;
  time_in_force?: string;
  expected_price?: number;
  slippage?: number;
  slippage_percent?: number;
  position_before?: string;
  position_after?: string;
  position_qty_before?: number;
  position_value_before?: number;
  account_equity?: number;
  account_buying_power?: number;
}

interface Position {
  symbol: string;
  qty: number;
  side: 'LONG' | 'SHORT';
  market_value: number;
  unrealized_pl: number;
  unrealized_plpc: number;
  entry_price: number;
  current_price: number;
}

interface Account {
  equity: number;
  cash: number;
  buying_power: number;
  portfolio_value: number;
}
```

---

## Summary of Changes

### New Features:
1. **Per-Bot Webhook URLs** - Each bot gets unique webhook token
2. **Enhanced Trade Details** - 20+ new fields tracking execution quality
3. **Token Regeneration** - Can regenerate webhook tokens per bot
4. **Signal Source Tracking** - Know if trade came from bot webhook, user webhook, or system

### New API Endpoints:
- `POST /api/bots/:id/regenerate-token` - Regenerate bot webhook token

### Updated API Responses:
- `GET /api/bots` - Now includes `webhook_token` and `webhook_url`
- `POST /api/bots` - Now returns `webhook_url` and `webhook_payload`
- `GET /api/trades` - Now includes 20+ enhanced execution detail fields
