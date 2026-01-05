# Frontend Update Guide - Positions & Trades API

## Overview
The backend has been updated to fix the $NaN issue in Recent Trades by pulling data directly from Alpaca API. This guide explains what the frontend team needs to know.

---

## 🔄 Key Changes

### 1. New Endpoint: `/api/trades/recent`
**Use this for Recent Trades display** - Pulls directly from Alpaca API (fixes $NaN issue)

### 2. Updated Endpoint: `/api/dashboard`
Now includes `recent_trades_source` field to indicate data source

### 3. Existing Endpoints Still Work
- `/api/positions` - Already pulls from Alpaca ✅
- `/api/trades` - Still pulls from database (use `/api/trades/recent` instead)

---

## 📡 API Endpoints

### 1. Get Recent Trades (NEW - Recommended)
**Endpoint:** `GET /api/trades/recent`

**Headers:**
```
Authorization: Bearer {token}
```

**Query Parameters:**
- `days` (optional, default: 7) - Number of days to look back
- `limit` (optional, default: 20) - Maximum number of trades

**Example Request:**
```javascript
const response = await fetch('/api/trades/recent?days=7&limit=10', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

**Response:**
```json
{
  "trades": [
    {
      "symbol": "BTC/USD",
      "side": "BUY",
      "action": "BUY",
      "qty": 0.00106628,
      "price": 91943.15,
      "transaction_time": "2025-01-26T12:18:00+00:00",
      "order_id": "abc123...",
      "value": 98.05
    },
    {
      "symbol": "BTC/USD",
      "side": "SELL",
      "action": "SELL",
      "qty": 0.00106628,
      "price": 92100.50,
      "transaction_time": "2025-01-26T12:24:00+00:00",
      "order_id": "def456...",
      "value": 98.19
    }
  ],
  "total": 10,
  "source": "alpaca_api"
}
```

**Field Descriptions:**
- `symbol` - Trading symbol (e.g., "BTC/USD", "AAPL")
- `side` - "BUY", "SELL" (from Alpaca)
- `action` - Same as `side` (for compatibility)
- `qty` - Quantity filled (actual number, not null/NaN)
- `price` - Fill price (actual number, not null/NaN)
- `transaction_time` - ISO 8601 timestamp
- `order_id` - Alpaca order ID
- `value` - Calculated value (qty * price)

**Error Responses:**
```json
// If API keys not configured
{
  "error": "Alpaca API keys not configured",
  "details": "..."
}
// Status: 400
```

---

### 2. Get Dashboard Data (UPDATED)
**Endpoint:** `GET /api/dashboard`

**Response Now Includes:**
```json
{
  "account": {
    "equity": 99985.82,
    "cash": 89807.14,
    "buying_power": 198278.14,
    "portfolio_value": 99985.82
  },
  "positions": [
    {
      "symbol": "AAPL",
      "qty": 0.367542731,
      "side": "LONG",
      "market_value": 99.61,
      "unrealized_pl": -0.38,
      "unrealized_plpc": -0.38,
      "entry_price": 271.23,
      "current_price": 271.00
    }
  ],
  "bots": {
    "total": 66,
    "active": 66
  },
  "recent_trades": [
    // Same format as /api/trades/recent
  ],
  "recent_trades_source": "alpaca",  // NEW FIELD: "alpaca" or "database"
  "api_keys_configured": true
}
```

**New Field:**
- `recent_trades_source` - Indicates data source:
  - `"alpaca"` - Data from Alpaca API (has real prices)
  - `"database"` - Data from database (fallback if API keys not configured)

---

### 3. Get Positions (No Changes - Already Working)
**Endpoint:** `GET /api/positions`

**Response:**
```json
{
  "positions": [
    {
      "symbol": "BTC/USD",
      "qty": 0.00106628,
      "side": "LONG",
      "market_value": 98.05,
      "unrealized_pl": -1.95,
      "unrealized_plpc": -1.95,
      "entry_price": 91943.15,
      "current_price": 90185.00
    }
  ],
  "total": 1
}
```

**Note:** This endpoint already pulls from Alpaca API correctly ✅

---

## 🎨 Frontend Implementation Recommendations

### For Recent Trades Section

**Option 1: Use New Endpoint (Recommended)**
```javascript
// Fetch recent trades from Alpaca API
const fetchRecentTrades = async () => {
  try {
    const response = await fetch('/api/trades/recent?days=7&limit=10', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (!response.ok) {
      // Handle error (e.g., API keys not configured)
      const error = await response.json();
      console.error(error.error);
      return [];
    }
    
    const data = await response.json();
    return data.trades; // Array of trades with real prices
  } catch (error) {
    console.error('Failed to fetch recent trades:', error);
    return [];
  }
};
```

**Option 2: Use Dashboard Endpoint (Fallback)**
```javascript
// Get from dashboard (includes recent_trades)
const fetchDashboard = async () => {
  const response = await fetch('/api/dashboard', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  const data = await response.json();
  
  // Check data source
  if (data.recent_trades_source === 'alpaca') {
    // Use recent_trades from dashboard
    return data.recent_trades;
  } else {
    // Fallback: use /api/trades/recent directly
    return await fetchRecentTrades();
  }
};
```

---

### Display Format

**Example React Component:**
```jsx
function RecentTrades({ trades }) {
  return (
    <div>
      <h2>Recent Trades</h2>
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Symbol</th>
            <th>Action</th>
            <th>Quantity</th>
            <th>Price</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((trade, index) => (
            <tr key={index}>
              <td>{new Date(trade.transaction_time).toLocaleString()}</td>
              <td>{trade.symbol}</td>
              <td>
                <span className={trade.side === 'BUY' ? 'green' : 'red'}>
                  {trade.action}
                </span>
              </td>
              <td>{trade.qty.toFixed(8)}</td>
              <td>${trade.price.toFixed(2)}</td>
              <td>${trade.value.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

### Handling CLOSE Orders

**Important:** CLOSE orders now have proper quantity and price!

**Before (showing $NaN):**
```json
{
  "action": "CLOSE",
  "qty": null,
  "price": null,
  "filled_qty": null,
  "filled_avg_price": null
}
```

**After (with real data):**
```json
{
  "action": "CLOSE",
  "side": "SELL",  // CLOSE appears as SELL in Alpaca
  "qty": 0.00106628,
  "price": 92100.50,
  "transaction_time": "2025-01-26T12:24:00+00:00"
}
```

**Display Logic:**
```javascript
// When displaying trades
const getActionLabel = (trade) => {
  if (trade.action === 'CLOSE' || (trade.side === 'SELL' && trade.qty > 0)) {
    return 'CLOSE';
  }
  return trade.action;
};

const getActionColor = (trade) => {
  const action = getActionLabel(trade);
  if (action === 'BUY') return 'green';
  if (action === 'SELL' || action === 'CLOSE') return 'red';
  return 'gray';
};
```

---

## 🔍 Data Quality Improvements

### What Changed

1. **Recent Trades Now Have Real Prices**
   - Before: Prices showed as `$NaN` or `null`
   - After: Prices are actual numbers from Alpaca API

2. **CLOSE Orders Now Show Quantity & Price**
   - Before: `qty: null`, `price: null`
   - After: `qty: 0.00106628`, `price: 91943.15`

3. **Consistent Data Source**
   - Positions: Alpaca API ✅
   - Recent Trades: Alpaca API ✅ (via `/api/trades/recent`)

### Data Validation

```javascript
// Validate trade data
const isValidTrade = (trade) => {
  return (
    trade.qty !== null &&
    trade.qty !== undefined &&
    trade.price !== null &&
    trade.price !== undefined &&
    !isNaN(trade.qty) &&
    !isNaN(trade.price) &&
    trade.price > 0
  );
};

// Filter invalid trades (shouldn't happen anymore, but good practice)
const validTrades = trades.filter(isValidTrade);
```

---

## 📋 Migration Checklist

- [ ] Update Recent Trades component to use `/api/trades/recent`
- [ ] Remove any $NaN/null handling code (no longer needed)
- [ ] Update CLOSE order display to show quantity and price
- [ ] Test with real Alpaca account (API keys configured)
- [ ] Handle error case when API keys not configured (status 400)
- [ ] Display proper error message if Alpaca API unavailable

---

## 🐛 Error Handling

### API Keys Not Configured
```javascript
if (response.status === 400) {
  const error = await response.json();
  if (error.error === 'Alpaca API keys not configured') {
    // Show message: "Please configure Alpaca API keys to view recent trades"
    return [];
  }
}
```

### Network Errors
```javascript
catch (error) {
  // Fallback to dashboard endpoint or show cached data
  console.error('Failed to fetch recent trades:', error);
  // Optionally show error message to user
}
```

---

## 📞 Questions?

If you need clarification on:
- API endpoint usage
- Data format
- Error handling
- Migration strategy

Please refer to this document or contact the backend team.

---

## ✨ Summary

**Key Takeaway:** Use `/api/trades/recent` endpoint for Recent Trades to get real prices from Alpaca API. This fixes the $NaN issue and ensures CLOSE orders show proper quantities and prices.

