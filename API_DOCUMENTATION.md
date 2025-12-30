# DashTrade REST API Documentation

## Base URL
```
https://YOUR-RAILWAY-APP.up.railway.app
```

## Authentication

All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

Tokens expire after 7 days. Obtain a token via `/api/auth/login` or `/api/auth/register`.

---

## Authentication Endpoints

### Register New User
```
POST /api/auth/register
```

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "User registered successfully",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "user"
  }
}
```

**Error (400):**
```json
{
  "error": "Username already exists"
}
```

---

### Login
```
POST /api/auth/login
```

**Request Body:**
```json
{
  "username": "johndoe",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "user"
  }
}
```

**Error (401):**
```json
{
  "error": "Invalid credentials"
}
```

---

### Get Current User
```
GET /api/auth/me
```
*Requires Authentication*

**Response (200):**
```json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "user",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

---

## Bot Management Endpoints

### Get All Bots
```
GET /api/bots
```
*Requires Authentication*

**Response (200):**
```json
{
  "bots": [
    {
      "id": 1,
      "user_id": 1,
      "name": "SPY Momentum Bot",
      "symbol": "SPY",
      "strategy": "momentum",
      "is_active": true,
      "position_size": 100.0,
      "max_position_value": 10000.0,
      "stop_loss_percent": 2.0,
      "take_profit_percent": 5.0,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "active": 1
}
```

---

### Create Bot
```
POST /api/bots
```
*Requires Authentication*

**Request Body:**
```json
{
  "name": "SPY Momentum Bot",
  "symbol": "SPY",
  "strategy": "momentum",
  "position_size": 100.0,
  "max_position_value": 10000.0,
  "stop_loss_percent": 2.0,
  "take_profit_percent": 5.0
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Bot created successfully",
  "bot": {
    "id": 1,
    "name": "SPY Momentum Bot",
    "symbol": "SPY",
    "strategy": "momentum",
    "is_active": false,
    "position_size": 100.0,
    "max_position_value": 10000.0,
    "stop_loss_percent": 2.0,
    "take_profit_percent": 5.0
  }
}
```

---

### Update Bot
```
PUT /api/bots/<bot_id>
```
*Requires Authentication*

**Request Body (all fields optional):**
```json
{
  "name": "Updated Bot Name",
  "symbol": "AAPL",
  "strategy": "trend_following",
  "position_size": 150.0,
  "max_position_value": 15000.0,
  "stop_loss_percent": 3.0,
  "take_profit_percent": 8.0
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Bot updated successfully"
}
```

**Error (404):**
```json
{
  "error": "Bot not found or access denied"
}
```

---

### Delete Bot
```
DELETE /api/bots/<bot_id>
```
*Requires Authentication*

**Response (200):**
```json
{
  "success": true,
  "message": "Bot deleted successfully"
}
```

---

### Toggle Bot Active/Inactive
```
POST /api/bots/<bot_id>/toggle
```
*Requires Authentication*

**Response (200):**
```json
{
  "success": true,
  "message": "Bot activated successfully",
  "is_active": true
}
```

**Error (400) - When API keys not configured:**
```json
{
  "error": "API keys not configured. Please add your Alpaca API keys first."
}
```

---

## Trading & Account Endpoints

### Get Account Info
```
GET /api/account
```
*Requires Authentication*

**Response (200):**
```json
{
  "account": {
    "id": "abc123",
    "account_number": "PA123456",
    "status": "ACTIVE",
    "currency": "USD",
    "buying_power": 50000.0,
    "cash": 25000.0,
    "portfolio_value": 75000.0,
    "equity": 75000.0,
    "last_equity": 74500.0,
    "long_market_value": 50000.0,
    "short_market_value": 0.0,
    "initial_margin": 25000.0,
    "maintenance_margin": 15000.0,
    "daytrade_count": 2,
    "pattern_day_trader": false
  }
}
```

**Error (400):**
```json
{
  "error": "API keys not configured"
}
```

---

### Get Positions
```
GET /api/positions
```
*Requires Authentication*

**Response (200):**
```json
{
  "positions": [
    {
      "symbol": "SPY",
      "qty": 10.0,
      "avg_entry_price": 450.50,
      "market_value": 4600.0,
      "cost_basis": 4505.0,
      "unrealized_pl": 95.0,
      "unrealized_plpc": 0.021,
      "current_price": 460.0,
      "change_today": 0.015,
      "side": "long"
    }
  ],
  "total": 1
}
```

---

### Get Trade History
```
GET /api/trades
```
*Requires Authentication*

**Query Parameters:**
- `limit` (optional): Number of trades to return (default: 50)

**Response (200):**
```json
{
  "trades": [
    {
      "id": 1,
      "bot_id": 1,
      "bot_name": "SPY Momentum Bot",
      "symbol": "SPY",
      "side": "buy",
      "qty": 10.0,
      "price": 450.50,
      "order_type": "market",
      "status": "filled",
      "alpaca_order_id": "abc123-def456",
      "executed_at": "2024-01-15T14:30:00Z",
      "created_at": "2024-01-15T14:29:55Z"
    }
  ],
  "total": 1
}
```

---

### Get Dashboard Summary
```
GET /api/dashboard
```
*Requires Authentication*

**Response (200):**
```json
{
  "account": {
    "portfolio_value": 75000.0,
    "buying_power": 50000.0,
    "cash": 25000.0,
    "equity": 75000.0
  },
  "bots": {
    "total": 3,
    "active": 2
  },
  "positions": {
    "total": 2,
    "market_value": 15000.0
  },
  "recent_trades": [
    {
      "id": 1,
      "symbol": "SPY",
      "side": "buy",
      "qty": 10.0,
      "price": 450.50,
      "executed_at": "2024-01-15T14:30:00Z"
    }
  ]
}
```

---

## Settings Endpoints

### Save API Keys
```
POST /api/settings/api-keys
```
*Requires Authentication*

**Request Body:**
```json
{
  "api_key": "PKXXXXXXXXXXXXXXXXXX",
  "api_secret": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "is_paper": true
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "API keys saved successfully"
}
```

---

### Get API Keys Status
```
GET /api/settings/api-keys/status
```
*Requires Authentication*

**Response (200):**
```json
{
  "configured": true,
  "is_paper": true,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

---

### Get Webhook Token
```
GET /api/webhook-token
```
*Requires Authentication*

**Response (200):**
```json
{
  "token": "abc123def456",
  "webhook_url": "https://your-app.up.railway.app/webhook/abc123def456",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### Regenerate Webhook Token
```
POST /api/webhook-token/regenerate
```
*Requires Authentication*

**Response (200):**
```json
{
  "success": true,
  "token": "new789token012",
  "webhook_url": "https://your-app.up.railway.app/webhook/new789token012",
  "message": "Webhook token regenerated successfully"
}
```

---

## Error Responses

### Authentication Errors

**401 - Token Missing:**
```json
{
  "error": "Token is missing"
}
```

**401 - Token Invalid/Expired:**
```json
{
  "error": "Token is invalid or expired"
}
```

### Validation Errors

**400 - Missing Required Fields:**
```json
{
  "error": "Missing required fields: username, email, password"
}
```

### Server Errors

**500 - Internal Server Error:**
```json
{
  "error": "An internal error occurred"
}
```

---

## React Integration Example

```typescript
// api.ts - API client configuration
const API_BASE_URL = 'https://your-app.up.railway.app';

// Store token in localStorage after login
export const setToken = (token: string) => {
  localStorage.setItem('auth_token', token);
};

export const getToken = () => localStorage.getItem('auth_token');

// Axios instance with auth interceptor
import axios from 'axios';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth header to all requests
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// Usage example:
// const response = await api.get('/api/bots');
// const bots = response.data.bots;
```

---

## Data Models

### User
```typescript
interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role: 'user' | 'admin';
  created_at: string;
}
```

### Bot
```typescript
interface Bot {
  id: number;
  user_id: number;
  name: string;
  symbol: string;
  strategy: string;
  is_active: boolean;
  position_size: number;
  max_position_value: number;
  stop_loss_percent?: number;
  take_profit_percent?: number;
  created_at: string;
  updated_at?: string;
}
```

### Trade
```typescript
interface Trade {
  id: number;
  bot_id: number;
  bot_name: string;
  symbol: string;
  side: 'buy' | 'sell';
  qty: number;
  price: number;
  order_type: string;
  status: string;
  alpaca_order_id?: string;
  executed_at?: string;
  created_at: string;
}
```

### Position
```typescript
interface Position {
  symbol: string;
  qty: number;
  avg_entry_price: number;
  market_value: number;
  cost_basis: number;
  unrealized_pl: number;
  unrealized_plpc: number;
  current_price: number;
  change_today: number;
  side: 'long' | 'short';
}
```

### Account
```typescript
interface Account {
  id: string;
  account_number: string;
  status: string;
  currency: string;
  buying_power: number;
  cash: number;
  portfolio_value: number;
  equity: number;
  last_equity: number;
  long_market_value: number;
  short_market_value: number;
  initial_margin: number;
  maintenance_margin: number;
  daytrade_count: number;
  pattern_day_trader: boolean;
}
```

---

## Notes for Frontend Development

1. **Authentication Flow:**
   - User registers or logs in
   - Store JWT token in localStorage
   - Include token in all subsequent API requests
   - Handle 401 responses by redirecting to login

2. **API Keys Setup:**
   - Users must configure Alpaca API keys before activating bots
   - Use `/api/settings/api-keys/status` to check if keys are configured
   - Show setup prompt if keys not configured

3. **Webhook URL:**
   - Each user gets a unique webhook URL
   - This URL is used in TradingView alerts
   - Token can be regenerated if compromised

4. **Bot Activation:**
   - Bots cannot be activated without API keys
   - Check API key status before allowing bot toggle

5. **Real-time Updates:**
   - Consider polling `/api/dashboard` for updates
   - Poll `/api/positions` during market hours
   - Recommended polling interval: 30 seconds
