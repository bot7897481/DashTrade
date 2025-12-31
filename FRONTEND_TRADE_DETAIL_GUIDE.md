# Frontend Implementation Guide: Trade Detail Page

## Overview

This guide provides complete specifications for implementing a Trade Detail page that displays comprehensive market context captured at the time of each trade execution.

---

## 1. API Endpoint

### GET /api/trades/{trade_id}

**Authentication:** Required (Bearer token)

**Request:**
```javascript
const response = await fetch(`${API_BASE_URL}/api/trades/${tradeId}`, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
const data = await response.json();
```

**Response Status Codes:**
- `200` - Success
- `401` - Unauthorized (invalid/missing token)
- `404` - Trade not found

---

## 2. Response Data Structure

```typescript
interface TradeDetailResponse {
  trade: {
    id: number;
    symbol: string;           // e.g., "AAPL"
    timeframe: string;        // e.g., "5min"
    action: string;           // "LONG" | "CLOSE"
    status: string;           // "filled" | "pending" | "rejected"
    created_at: string;       // ISO timestamp
    filled_at: string | null; // ISO timestamp
  };

  execution: {
    notional: number;         // Dollar amount traded
    filled_qty: number;       // Shares filled
    filled_avg_price: number; // Average fill price
    expected_price: number;   // Price at signal time
    slippage: number;         // Price difference (dollars)
    slippage_percent: number; // Price difference (%)
    bid_price: number;        // Bid at execution
    ask_price: number;        // Ask at execution
    spread: number;           // Bid-ask spread (dollars)
    spread_percent: number;   // Bid-ask spread (%)
    order_id: string;         // Alpaca order ID
    order_type: string;       // "market" | "limit"
    time_in_force: string;    // "day" | "gtc"
  };

  timing: {
    signal_received_at: string;   // When webhook received
    order_submitted_at: string;   // When order sent to Alpaca
    execution_latency_ms: number; // Signal to order time
    time_to_fill_ms: number;      // Order to fill time
    market_open: boolean;         // Was market open?
    extended_hours: boolean;      // Extended hours trade?
    signal_source: string;        // "webhook" | "manual"
  };

  stock: {
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    prev_close: number;
    change_percent: number;   // Day's change %
    avg_volume: number;       // 20-day average
    volume_ratio: number;     // Today vs average
  };

  fundamentals: {
    market_cap: number;
    pe_ratio: number;
    forward_pe: number;
    eps: number;
    beta: number;
    dividend_yield: number;
    shares_outstanding: number;
    short_ratio: number;
    fifty_two_week_high: number;
    fifty_two_week_low: number;
    fifty_day_ma: number;
    two_hundred_day_ma: number;
  };

  market_indices: {
    sp500: { price: number; change_percent: number };
    nasdaq: { price: number; change_percent: number };
    dji: { price: number; change_percent: number };
    russell: { price: number; change_percent: number };
    vix: { price: number; change_percent: number };
  };

  treasury: {
    yield_10y: number;
    yield_2y: number;
    yield_curve_spread: number;
  };

  sector: {
    etf_symbol: string;       // Stock's sector ETF (e.g., "XLK")
    etf_price: number;
    etf_change_percent: number;
    sector_etfs: {
      XLK: number;  // Technology
      XLF: number;  // Financials
      XLE: number;  // Energy
      XLV: number;  // Healthcare
      XLY: number;  // Consumer Discretionary
      XLP: number;  // Consumer Staples
      XLI: number;  // Industrials
      XLB: number;  // Materials
      XLU: number;  // Utilities
      XLRE: number; // Real Estate
    };
  };

  position: {
    before: string;           // "flat" | "long" | "short"
    after: string;            // Position after trade
    qty_before: number;
    value_before: number;
    avg_entry: number;
    unrealized_pl: number;
  };

  account: {
    equity: number;
    cash: number;
    buying_power: number;
    portfolio_value: number;
    total_positions_count: number;
    total_positions_value: number;
  };

  technical: {
    rsi_14: number;                   // RSI(14) value 0-100
    price_vs_50ma_percent: number;    // % above/below 50MA
    price_vs_200ma_percent: number;   // % above/below 200MA
    price_vs_52w_high_percent: number;// % from 52-week high
    price_vs_52w_low_percent: number; // % from 52-week low
  };

  metadata: {
    context_captured_at: string;
    data_source: string;      // "yfinance"
    fetch_latency_ms: number;
    errors: string | null;
  };
}
```

---

## 3. Adding Link to Trade List

In the existing trades list component, add a clickable link/icon next to each trade:

```tsx
// Example: In your TradeRow component
<TableRow>
  <TableCell>{trade.symbol}</TableCell>
  <TableCell>{trade.action}</TableCell>
  <TableCell>${trade.filled_avg_price}</TableCell>
  <TableCell>{trade.status}</TableCell>
  <TableCell>
    {/* ADD THIS: Link to trade detail */}
    <Button
      variant="ghost"
      size="sm"
      onClick={() => navigate(`/trades/${trade.id}`)}
    >
      <InfoIcon className="h-4 w-4" />
      Details
    </Button>
  </TableCell>
</TableRow>
```

---

## 4. Suggested Page Layout

### Header Section
```
+------------------------------------------------------------------+
|  [Back Button]                                                    |
|                                                                   |
|  AAPL - Long Trade                                               |
|  Executed: Dec 30, 2024 at 2:34:15 PM EST                        |
|  Status: [Filled Badge]                                          |
+------------------------------------------------------------------+
```

### Trade Summary Card (Hero Section)
```
+------------------------------------------------------------------+
|  TRADE EXECUTION SUMMARY                                          |
|  +------------------+  +------------------+  +------------------+ |
|  |   Filled Price   |  |    Quantity      |  |     Notional     | |
|  |    $245.32       |  |    4.08 shares   |  |    $1,000.00     | |
|  +------------------+  +------------------+  +------------------+ |
|                                                                   |
|  +------------------+  +------------------+  +------------------+ |
|  |    Slippage      |  |  Bid-Ask Spread  |  |   Fill Time      | |
|  |  +$0.12 (+0.05%) |  |  $0.08 (0.03%)   |  |     45ms         | |
|  +------------------+  +------------------+  +------------------+ |
+------------------------------------------------------------------+
```

### Tab-Based Content Sections

```
+------------------------------------------------------------------+
| [Market] [Stock] [Fundamentals] [Technical] [Account] [Timing]   |
+------------------------------------------------------------------+
|                                                                   |
|  (Content based on selected tab)                                 |
|                                                                   |
+------------------------------------------------------------------+
```

---

## 5. Section Details

### 5.1 Market Tab

**Market Indices Card:**
```
+--------------------------------+
|  MARKET INDICES AT TRADE TIME  |
|--------------------------------|
|  S&P 500    4,789.23   +0.45%  |
|  NASDAQ    15,234.56   +0.62%  |
|  DOW       37,456.78   +0.31%  |
|  Russell   2,034.56    +0.28%  |
|  VIX           14.23   -2.15%  |
+--------------------------------+
```

**Treasury Yields Card:**
```
+--------------------------------+
|  TREASURY YIELDS               |
|--------------------------------|
|  10-Year Yield      4.25%      |
|  2-Year Yield       4.65%      |
|  Yield Curve       -0.40%      |
|  (Inverted: recession signal)  |
+--------------------------------+
```

**Sector ETFs Card:**
```
+--------------------------------+
|  SECTOR PERFORMANCE            |
|--------------------------------|
|  Stock's Sector: XLK (Tech)    |
|  Sector Price: $198.45 +1.2%   |
|--------------------------------|
|  XLK (Tech)       $198.45      |
|  XLF (Finance)    $42.34       |
|  XLE (Energy)     $87.23       |
|  XLV (Health)     $145.67      |
|  ... (expandable)              |
+--------------------------------+
```

### 5.2 Stock Tab

**Price Action Card:**
```
+--------------------------------+
|  STOCK PRICE DATA              |
|--------------------------------|
|  Open         $244.50          |
|  High         $246.80          |
|  Low          $243.20          |
|  Close        $245.60          |
|  Prev Close   $243.40          |
|  Day Change   +0.90%           |
+--------------------------------+
```

**Volume Card:**
```
+--------------------------------+
|  VOLUME ANALYSIS               |
|--------------------------------|
|  Today's Volume    45.2M       |
|  Avg Volume (20d)  38.5M       |
|  Volume Ratio      1.17x       |
|  (Above average trading)       |
+--------------------------------+
```

### 5.3 Fundamentals Tab

**Valuation Card:**
```
+--------------------------------+
|  VALUATION METRICS             |
|--------------------------------|
|  Market Cap      $3.8T         |
|  P/E Ratio       29.45         |
|  Forward P/E     26.12         |
|  EPS             $6.42         |
+--------------------------------+
```

**Company Stats Card:**
```
+--------------------------------+
|  COMPANY STATISTICS            |
|--------------------------------|
|  Beta             1.28         |
|  Dividend Yield   0.52%        |
|  Shares Out       15.4B        |
|  Short Ratio      1.2          |
+--------------------------------+
```

**52-Week Range Card:**
```
+--------------------------------+
|  52-WEEK RANGE                 |
|--------------------------------|
|  52W High        $256.89       |
|  52W Low         $164.23       |
|  Current: 85% of range         |
|  [==========|====]             |
|  $164.23      $245.60  $256.89 |
+--------------------------------+
```

### 5.4 Technical Tab

**Moving Averages Card:**
```
+--------------------------------+
|  MOVING AVERAGES               |
|--------------------------------|
|  50-Day MA       $238.45       |
|  Price vs 50MA   +3.0%         |
|  200-Day MA      $212.34       |
|  Price vs 200MA  +15.7%        |
|  (Above both MAs: Bullish)     |
+--------------------------------+
```

**RSI Card:**
```
+--------------------------------+
|  MOMENTUM INDICATOR            |
|--------------------------------|
|  RSI (14)        62.5          |
|  [====|========|=====]         |
|  0   30        70    100       |
|  Status: Neutral               |
|  (Overbought > 70)             |
+--------------------------------+
```

**Price Position Card:**
```
+--------------------------------+
|  PRICE POSITION                |
|--------------------------------|
|  From 52W High   -4.4%         |
|  From 52W Low    +49.6%        |
+--------------------------------+
```

### 5.5 Account Tab

**Account Snapshot Card:**
```
+--------------------------------+
|  ACCOUNT AT TRADE TIME         |
|--------------------------------|
|  Total Equity    $25,432.56    |
|  Cash Available  $5,234.12     |
|  Buying Power    $10,468.24    |
|  Portfolio Value $20,198.44    |
+--------------------------------+
```

**Position Context Card:**
```
+--------------------------------+
|  POSITION CONTEXT              |
|--------------------------------|
|  Position Before    Flat       |
|  Position After     Long       |
|  Qty Before         0          |
|  Value Before       $0         |
|--------------------------------|
|  Total Positions    5          |
|  Positions Value    $15,234    |
+--------------------------------+
```

### 5.6 Timing Tab

**Execution Timeline Card:**
```
+--------------------------------+
|  EXECUTION TIMELINE            |
|--------------------------------|
|  Signal Received               |
|  > 2:34:15.123 PM              |
|           | 12ms               |
|  Order Submitted               |
|  > 2:34:15.135 PM              |
|           | 45ms               |
|  Order Filled                  |
|  > 2:34:15.180 PM              |
|--------------------------------|
|  Total Latency: 57ms           |
+--------------------------------+
```

**Market Status Card:**
```
+--------------------------------+
|  MARKET STATUS                 |
|--------------------------------|
|  Market Open       Yes         |
|  Extended Hours    No          |
|  Signal Source     Webhook     |
|  Order Type        Market      |
|  Time in Force     Day         |
+--------------------------------+
```

---

## 6. Helper Functions

### Format Currency
```typescript
const formatCurrency = (value: number | null): string => {
  if (value === null || value === undefined || isNaN(value)) return 'N/A';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
};
```

### Format Large Numbers
```typescript
const formatLargeNumber = (value: number | null): string => {
  if (value === null || value === undefined) return 'N/A';
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return formatCurrency(value);
};
```

### Format Percent
```typescript
const formatPercent = (value: number | null): string => {
  if (value === null || value === undefined || isNaN(value)) return 'N/A';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
};
```

### Format Volume
```typescript
const formatVolume = (value: number | null): string => {
  if (value === null || value === undefined) return 'N/A';
  if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
  if (value >= 1e3) return `${(value / 1e3).toFixed(2)}K`;
  return value.toString();
};
```

### Get Color Class
```typescript
const getChangeColor = (value: number | null): string => {
  if (value === null || value === undefined) return 'text-gray-500';
  return value >= 0 ? 'text-green-600' : 'text-red-600';
};
```

### RSI Status
```typescript
const getRsiStatus = (rsi: number | null): { label: string; color: string } => {
  if (rsi === null) return { label: 'N/A', color: 'gray' };
  if (rsi >= 70) return { label: 'Overbought', color: 'red' };
  if (rsi <= 30) return { label: 'Oversold', color: 'green' };
  return { label: 'Neutral', color: 'gray' };
};
```

---

## 7. React Component Example

```tsx
// pages/TradeDetail.tsx
import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowLeft, TrendingUp, TrendingDown } from 'lucide-react';

interface TradeDetail { /* ... TypeScript interface from above */ }

export default function TradeDetailPage() {
  const { tradeId } = useParams();
  const navigate = useNavigate();
  const [trade, setTrade] = useState<TradeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTradeDetail = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/api/trades/${tradeId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
          throw new Error(response.status === 404 ? 'Trade not found' : 'Failed to load');
        }

        const data = await response.json();
        setTrade(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTradeDetail();
  }, [tradeId]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;
  if (!trade) return <NotFound />;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
      </div>

      <div className="space-y-2">
        <h1 className="text-3xl font-bold">
          {trade.trade.symbol} - {trade.trade.action} Trade
        </h1>
        <p className="text-muted-foreground">
          Executed: {new Date(trade.trade.filled_at).toLocaleString()}
        </p>
        <Badge variant={trade.trade.status === 'filled' ? 'success' : 'secondary'}>
          {trade.trade.status}
        </Badge>
      </div>

      {/* Trade Summary Card */}
      <Card>
        <CardHeader>
          <CardTitle>Trade Execution Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <StatCard label="Filled Price" value={formatCurrency(trade.execution.filled_avg_price)} />
            <StatCard label="Quantity" value={`${trade.execution.filled_qty} shares`} />
            <StatCard label="Notional" value={formatCurrency(trade.execution.notional)} />
            <StatCard
              label="Slippage"
              value={formatPercent(trade.execution.slippage_percent)}
              color={getChangeColor(-trade.execution.slippage_percent)}
            />
            <StatCard label="Spread" value={formatPercent(trade.execution.spread_percent)} />
            <StatCard label="Fill Time" value={`${trade.timing.time_to_fill_ms}ms`} />
          </div>
        </CardContent>
      </Card>

      {/* Tabbed Content */}
      <Tabs defaultValue="market">
        <TabsList className="grid grid-cols-6 w-full">
          <TabsTrigger value="market">Market</TabsTrigger>
          <TabsTrigger value="stock">Stock</TabsTrigger>
          <TabsTrigger value="fundamentals">Fundamentals</TabsTrigger>
          <TabsTrigger value="technical">Technical</TabsTrigger>
          <TabsTrigger value="account">Account</TabsTrigger>
          <TabsTrigger value="timing">Timing</TabsTrigger>
        </TabsList>

        <TabsContent value="market">
          <MarketTab data={trade} />
        </TabsContent>

        <TabsContent value="stock">
          <StockTab data={trade} />
        </TabsContent>

        {/* ... other tabs */}
      </Tabs>

      {/* Metadata Footer */}
      <div className="text-sm text-muted-foreground">
        Data captured at {trade.metadata.context_captured_at}
        from {trade.metadata.data_source}
        (latency: {trade.metadata.fetch_latency_ms}ms)
        {trade.metadata.errors && (
          <span className="text-yellow-600"> - Some data unavailable: {trade.metadata.errors}</span>
        )}
      </div>
    </div>
  );
}

// Reusable stat card component
function StatCard({ label, value, color = '' }: { label: string; value: string; color?: string }) {
  return (
    <div className="text-center p-4 bg-muted rounded-lg">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className={`text-xl font-bold ${color}`}>{value}</p>
    </div>
  );
}
```

---

## 8. Routing Setup

Add route to your router configuration:

```tsx
// App.tsx or routes.tsx
import TradeDetailPage from './pages/TradeDetail';

<Routes>
  {/* Existing routes */}
  <Route path="/trades" element={<TradesListPage />} />

  {/* ADD THIS: Trade detail route */}
  <Route path="/trades/:tradeId" element={<TradeDetailPage />} />
</Routes>
```

---

## 9. Loading & Error States

### Loading Skeleton
```tsx
function LoadingSkeleton() {
  return (
    <div className="container mx-auto p-6 space-y-6 animate-pulse">
      <div className="h-8 w-64 bg-gray-200 rounded" />
      <div className="h-4 w-48 bg-gray-200 rounded" />
      <Card>
        <CardContent className="p-6">
          <div className="grid grid-cols-6 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

### Error State
```tsx
function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-64">
      <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
      <h2 className="text-xl font-semibold mb-2">Error Loading Trade</h2>
      <p className="text-muted-foreground mb-4">{message}</p>
      <Button onClick={onRetry}>Try Again</Button>
    </div>
  );
}
```

---

## 10. Null/Missing Data Handling

The API may return `null` for some fields if data wasn't available at capture time. Always handle nulls:

```tsx
// Always check for null before rendering
{trade.fundamentals.pe_ratio !== null ? (
  <span>{trade.fundamentals.pe_ratio.toFixed(2)}</span>
) : (
  <span className="text-muted-foreground">N/A</span>
)}

// Or use the helper function
<span>{formatCurrency(trade.execution.filled_avg_price)}</span>
```

---

## 11. Mobile Responsiveness

- Use responsive grid: `grid-cols-2 md:grid-cols-3 lg:grid-cols-6`
- Stack tabs vertically on mobile or use horizontal scroll
- Reduce stat card padding on mobile
- Consider collapsible sections for mobile

---

## 12. Sector ETF Reference

| Symbol | Sector |
|--------|--------|
| XLK | Technology |
| XLF | Financials |
| XLE | Energy |
| XLV | Healthcare |
| XLY | Consumer Discretionary |
| XLP | Consumer Staples |
| XLI | Industrials |
| XLB | Materials |
| XLU | Utilities |
| XLRE | Real Estate |

---

## 13. Index Reference

| Key | Description |
|-----|-------------|
| sp500 | S&P 500 Index |
| nasdaq | NASDAQ Composite |
| dji | Dow Jones Industrial Average |
| russell | Russell 2000 (Small Cap) |
| vix | CBOE Volatility Index (Fear Index) |

---

## Summary Checklist

- [ ] Add route `/trades/:tradeId` to router
- [ ] Create TradeDetailPage component
- [ ] Add "Details" link/button to trade list rows
- [ ] Implement API call with auth header
- [ ] Create loading skeleton
- [ ] Create error state
- [ ] Implement Trade Summary hero card
- [ ] Implement tabbed interface with 6 tabs
- [ ] Add helper functions for formatting
- [ ] Handle null/missing data gracefully
- [ ] Test mobile responsiveness
- [ ] Add metadata footer showing data source
