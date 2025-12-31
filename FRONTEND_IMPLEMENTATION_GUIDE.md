# Frontend Implementation Guide for DashTrade

This guide covers all the features the frontend needs to implement to fully utilize the backend capabilities.

---

## Table of Contents

1. [TradingView Setup Display](#1-tradingview-setup-display)
2. [Trade Detail Page](#2-trade-detail-page)
3. [Strategy Performance Dashboard](#3-strategy-performance-dashboard)
4. [Trade History with P&L](#4-trade-history-with-pl)
5. [AI Strategy Insights](#5-ai-strategy-insights)
6. [Strategy Marketplace](#6-strategy-marketplace)

---

## 1. TradingView Setup Display

When a user creates or views a bot, show the TradingView webhook setup information.

### API Endpoint

```
GET /api/bots
Authorization: Bearer <token>
```

### Response Structure

Each bot includes `tradingview_setup`:

```json
{
  "bots": [
    {
      "id": 1,
      "symbol": "SPY",
      "timeframe": "5min",
      "webhook_url": "https://webhook.novalgo.org/webhook?token=abc123...",
      "tradingview_setup": {
        "basic_message": "{\"action\": \"{{strategy.order.action}}\", \"symbol\": \"{{ticker}}\", \"timeframe\": \"{{interval}}\"}",
        "exit_message": "{\"action\": \"CLOSE\", \"symbol\": \"{{ticker}}\", \"timeframe\": \"{{interval}}\"}",
        "ai_learning_message": "{\"action\": \"{{strategy.order.action}}\", \"symbol\": \"{{ticker}}\", \"timeframe\": \"{{interval}}\", \"strategy_type\": \"momentum\", \"entry_indicator\": \"RSI\", \"rsi_value\": {{rsi}}, \"rsi_period\": 14, \"ma_fast\": 9, \"ma_slow\": 21}",
        "instructions": [...],
        "ai_learning_params": {...}
      }
    }
  ]
}
```

### UI Component

```
┌─────────────────────────────────────────────────────────────────┐
│  TradingView Webhook Setup                                      │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Webhook URL                                            [Copy]  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ https://webhook.novalgo.org/webhook?token=abc123...     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ [Basic] [AI Learning] [Exit]                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Alert Message (paste into TradingView)                 [Copy]  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ {"action": "{{strategy.order.action}}",                 │   │
│  │  "symbol": "{{ticker}}",                                │   │
│  │  "timeframe": "{{interval}}"}                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  📋 Instructions:                                               │
│  1. In TradingView, create an alert on your strategy           │
│  2. Set 'Webhook URL' to the URL above                         │
│  3. Paste the alert message into the message field             │
│  4. Enable the Webhook checkbox                                │
│                                                                 │
│  💡 Tip: Use "AI Learning" format to help improve strategies   │
└─────────────────────────────────────────────────────────────────┘
```

### React Component Example

```tsx
function TradingViewSetup({ bot }) {
  const [messageType, setMessageType] = useState('basic');

  const messages = {
    basic: bot.tradingview_setup?.basic_message,
    ai: bot.tradingview_setup?.ai_learning_message,
    exit: bot.tradingview_setup?.exit_message,
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>TradingView Webhook Setup</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Webhook URL */}
        <div>
          <Label>Webhook URL</Label>
          <div className="flex gap-2">
            <Input value={bot.webhook_url} readOnly />
            <Button onClick={() => copyToClipboard(bot.webhook_url)}>
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Message Type Tabs */}
        <Tabs value={messageType} onValueChange={setMessageType}>
          <TabsList>
            <TabsTrigger value="basic">Basic</TabsTrigger>
            <TabsTrigger value="ai">AI Learning</TabsTrigger>
            <TabsTrigger value="exit">Exit</TabsTrigger>
          </TabsList>
        </Tabs>

        {/* Alert Message */}
        <div>
          <Label>Alert Message</Label>
          <div className="flex gap-2">
            <Textarea
              value={messages[messageType]}
              readOnly
              className="font-mono text-sm"
            />
            <Button onClick={() => copyToClipboard(messages[messageType])}>
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Instructions */}
        <Alert>
          <AlertDescription>
            <ol className="list-decimal list-inside space-y-1">
              {bot.tradingview_setup?.instructions?.map((instruction, i) => (
                <li key={i}>{instruction}</li>
              ))}
            </ol>
          </AlertDescription>
        </Alert>
      </CardContent>
    </Card>
  );
}
```

---

## 2. Trade Detail Page

Display comprehensive trade information including market context captured at execution time.

### API Endpoint

```
GET /api/trades/{trade_id}
Authorization: Bearer <token>
```

### Response Structure

```json
{
  "trade": {
    "id": 123,
    "symbol": "SPY",
    "action": "LONG",
    "status": "filled",
    "created_at": "2024-12-31T10:30:00Z"
  },
  "execution": {
    "filled_qty": 4.08,
    "filled_avg_price": 245.32,
    "slippage_percent": 0.05,
    "spread_percent": 0.03
  },
  "timing": {
    "execution_latency_ms": 12,
    "time_to_fill_ms": 45,
    "market_open": true
  },
  "stock": {
    "open": 244.50,
    "high": 246.80,
    "low": 243.20,
    "close": 245.60,
    "volume": 45200000,
    "change_percent": 0.90
  },
  "fundamentals": {
    "market_cap": 3800000000000,
    "pe_ratio": 29.45,
    "beta": 1.28
  },
  "market_indices": {
    "sp500": { "price": 4789.23, "change_percent": 0.45 },
    "nasdaq": { "price": 15234.56, "change_percent": 0.62 },
    "vix": { "price": 14.23, "change_percent": -2.15 }
  },
  "treasury": {
    "yield_10y": 4.25,
    "yield_2y": 4.65,
    "yield_curve_spread": -0.40
  },
  "technical": {
    "rsi_14": 62.5,
    "price_vs_50ma_percent": 3.0,
    "price_vs_200ma_percent": 15.7
  },
  "account": {
    "equity": 25432.56,
    "buying_power": 10468.24
  }
}
```

### UI Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back                                                         │
│                                                                 │
│  SPY Long Trade                                    [Filled ✓]   │
│  December 31, 2024 at 10:30:15 AM                              │
├─────────────────────────────────────────────────────────────────┤
│                    EXECUTION SUMMARY                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  $245.32 │  │   4.08   │  │ $1,000   │  │  +0.05%  │       │
│  │   Price  │  │  Shares  │  │ Notional │  │ Slippage │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
├─────────────────────────────────────────────────────────────────┤
│  [Market] [Stock] [Fundamentals] [Technical] [Account]          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  MARKET INDICES                    TREASURY YIELDS              │
│  ┌────────────────────────┐       ┌────────────────────────┐   │
│  │ S&P 500   4,789  +0.45%│       │ 10-Year    4.25%       │   │
│  │ NASDAQ   15,234  +0.62%│       │ 2-Year     4.65%       │   │
│  │ VIX         14   -2.15%│       │ Spread    -0.40%       │   │
│  └────────────────────────┘       └────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Add Link to Trade List

In the trades list, add a "Details" link for each trade:

```tsx
// In your TradesTable component
<TableRow>
  <TableCell>{trade.symbol}</TableCell>
  <TableCell>{trade.action}</TableCell>
  <TableCell>${trade.filled_avg_price}</TableCell>
  <TableCell>
    <Badge variant={trade.status === 'filled' ? 'success' : 'secondary'}>
      {trade.status}
    </Badge>
  </TableCell>
  <TableCell>
    <Button
      variant="ghost"
      size="sm"
      onClick={() => navigate(`/trades/${trade.id}`)}
    >
      <Eye className="h-4 w-4 mr-1" />
      Details
    </Button>
  </TableCell>
</TableRow>
```

---

## 3. Strategy Performance Dashboard

Display performance metrics calculated from trade outcomes.

### API Endpoint (NEW - needs to be added)

```
GET /api/performance?strategy_type=momentum&symbol=SPY
Authorization: Bearer <token>
```

### Suggested Response

```json
{
  "summary": {
    "total_trades": 145,
    "winning_trades": 90,
    "losing_trades": 55,
    "win_rate": 62.07,
    "total_pnl_dollars": 2340.50,
    "avg_pnl_percent": 1.12,
    "profit_factor": 1.8,
    "avg_hold_duration_minutes": 45
  },
  "by_indicator": [
    { "entry_indicator": "RSI", "total_trades": 89, "win_rate": 65.2, "avg_return": 1.4 },
    { "entry_indicator": "MACD", "total_trades": 56, "win_rate": 57.1, "avg_return": 0.8 }
  ],
  "by_market_condition": [
    { "vix_regime": "Normal VIX (15-20)", "total_trades": 78, "win_rate": 68.5, "avg_return": 1.8 },
    { "vix_regime": "High VIX (>25)", "total_trades": 23, "win_rate": 43.5, "avg_return": -0.5 }
  ]
}
```

### UI Component

```
┌─────────────────────────────────────────────────────────────────┐
│  Strategy Performance                                           │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │   145   │  │  62.1%  │  │ +$2,340 │  │   1.8   │           │
│  │ Trades  │  │Win Rate │  │Total P&L│  │ Profit  │           │
│  │         │  │         │  │         │  │ Factor  │           │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │
│                                                                 │
│  Performance by Entry Indicator                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Indicator │ Trades │ Win Rate │ Avg Return │            │   │
│  │───────────│────────│──────────│────────────│            │   │
│  │ RSI       │   89   │  65.2%   │   +1.4%    │ ████████   │   │
│  │ MACD      │   56   │  57.1%   │   +0.8%    │ ██████     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Performance by Market Condition                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ VIX Level      │ Trades │ Win Rate │ Avg Return │       │   │
│  │────────────────│────────│──────────│────────────│       │   │
│  │ Normal (15-20) │   78   │  68.5%   │   +1.8%    │ ✓Best │   │
│  │ Low (<15)      │   44   │  61.4%   │   +1.2%    │       │   │
│  │ High (>25)     │   23   │  43.5%   │   -0.5%    │ ⚠Avoid│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Trade History with P&L

Enhanced trade history showing profit/loss for each closed trade.

### API Endpoint (NEW - needs to be added)

```
GET /api/trades/outcomes?status=closed&limit=50
Authorization: Bearer <token>
```

### Suggested Response

```json
{
  "outcomes": [
    {
      "trade_id": 123,
      "symbol": "SPY",
      "position_type": "long",
      "entry_price": 245.32,
      "exit_price": 248.50,
      "entry_time": "2024-12-31T10:30:00Z",
      "exit_time": "2024-12-31T14:45:00Z",
      "exit_reason": "take_profit",
      "pnl_dollars": 127.20,
      "pnl_percent": 1.30,
      "hold_duration_minutes": 255,
      "is_winner": true
    }
  ],
  "summary": {
    "total_pnl": 2340.50,
    "today_pnl": 127.20,
    "this_week_pnl": 450.30
  }
}
```

### UI Component

```
┌─────────────────────────────────────────────────────────────────┐
│  Trade History                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Summary: Today +$127.20 │ This Week +$450.30 │ Total +$2,340  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Symbol │ Type │ Entry    │ Exit     │ P&L      │ Dur.   │   │
│  │────────│──────│──────────│──────────│──────────│────────│   │
│  │ SPY    │ Long │ $245.32  │ $248.50  │ +$127.20 │ 4h 15m │   │
│  │        │      │ 10:30 AM │ 2:45 PM  │ (+1.30%) │        │   │
│  │────────│──────│──────────│──────────│──────────│────────│   │
│  │ AAPL   │ Long │ $192.45  │ $191.20  │ -$64.50  │ 2h 30m │   │
│  │        │      │ 9:45 AM  │ 12:15 PM │ (-0.65%) │        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Color coding:
- Green text/background for winning trades (pnl_dollars > 0)
- Red text/background for losing trades (pnl_dollars < 0)

---

## 5. AI Strategy Insights

Display AI-discovered patterns and recommendations.

### API Endpoint (NEW - needs to be added)

```
GET /api/insights?min_confidence=60
Authorization: Bearer <token>
```

### Suggested Response

```json
{
  "insights": [
    {
      "id": 1,
      "insight_type": "optimal_params",
      "confidence_score": 87.5,
      "title": "RSI entries optimal when VIX is 15-20",
      "description": "Based on 234 trades, RSI-based entries perform significantly better during normal market volatility periods.",
      "observed_win_rate": 68.2,
      "observed_avg_return": 1.9,
      "observed_trades": 234,
      "recommendation": "Consider pausing RSI strategies when VIX exceeds 25",
      "recommended_params": {
        "rsi_threshold": 32,
        "vix_max": 25
      }
    }
  ]
}
```

### UI Component

```
┌─────────────────────────────────────────────────────────────────┐
│  🤖 AI Strategy Insights                                        │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  💡 RSI entries optimal when VIX is 15-20               │   │
│  │  ─────────────────────────────────────────────────────  │   │
│  │  Confidence: ████████████░░░░ 87.5%                     │   │
│  │  Based on 234 trades                                    │   │
│  │                                                         │   │
│  │  Observed Results:                                      │   │
│  │  • Win Rate: 68.2% (vs 55% overall)                    │   │
│  │  • Avg Return: +1.9% (vs +0.8% overall)                │   │
│  │                                                         │   │
│  │  Recommendation:                                        │   │
│  │  Consider pausing RSI strategies when VIX > 25         │   │
│  │                                                         │   │
│  │  [Apply to Strategy]  [Dismiss]                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  💡 15-minute timeframe outperforms 5-minute            │   │
│  │  ─────────────────────────────────────────────────────  │   │
│  │  Confidence: ██████████░░░░░░ 72.3%                     │   │
│  │  Based on 156 trades                                    │   │
│  │  ...                                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Strategy Marketplace

Display system strategies users can subscribe to.

### API Endpoints

```
GET /api/strategies              # List all strategies
GET /api/strategies/{id}         # Strategy details
POST /api/strategies/{id}/subscribe    # Subscribe
DELETE /api/strategies/{id}/subscribe  # Unsubscribe
```

### Strategy Card Component

```
┌─────────────────────────────────────────────────────────────────┐
│  SPY Momentum Strategy                              [LIVE] 🟢   │
│  "Momentum-based entries on SPY using RSI and MA crossovers"   │
├─────────────────────────────────────────────────────────────────┤
│  📈 +23.5%      📊 156 Trades    ✅ 62% Win Rate               │
│  📉 -8.2% DD    ⏱️ 6 months      👥 24 subscribers             │
├─────────────────────────────────────────────────────────────────┤
│  ⚠️ Risk Level: Medium                                          │
│  Past performance does not guarantee future results            │
├─────────────────────────────────────────────────────────────────┤
│  [View Details]                        [Subscribe - Free]       │
└─────────────────────────────────────────────────────────────────┘
```

### Subscription Flow

1. User clicks "Subscribe"
2. Show risk disclaimer modal
3. User selects which bot to link
4. Confirm subscription

```
┌─────────────────────────────────────────────────────────────────┐
│  Subscribe to SPY Momentum Strategy                      [X]    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ⚠️ Risk Disclaimer                                             │
│  ─────────────────────────────────────────────────────────────  │
│  Trading involves substantial risk of loss. Past performance   │
│  is not indicative of future results. You are solely           │
│  responsible for your trading decisions.                        │
│                                                                 │
│  [✓] I understand and accept the risks                         │
│                                                                 │
│  Select Bot to Receive Signals:                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ○ SPY Bot (5min) - $1,000/trade                         │   │
│  │ ○ SPY Bot (15min) - $500/trade                          │   │
│  │ ○ Create New Bot...                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  [Cancel]                              [Subscribe]              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Helper Functions

### Format Currency

```typescript
export const formatCurrency = (value: number | null): string => {
  if (value === null || value === undefined || isNaN(value)) return 'N/A';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(value);
};
```

### Format Percent

```typescript
export const formatPercent = (value: number | null): string => {
  if (value === null || value === undefined || isNaN(value)) return 'N/A';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
};
```

### Format Large Numbers

```typescript
export const formatLargeNumber = (value: number | null): string => {
  if (value === null || value === undefined) return 'N/A';
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return formatCurrency(value);
};
```

### P&L Color

```typescript
export const getPnlColor = (value: number | null): string => {
  if (value === null || value === undefined) return 'text-gray-500';
  if (value > 0) return 'text-green-600';
  if (value < 0) return 'text-red-600';
  return 'text-gray-500';
};
```

---

## Routes to Add

```tsx
// Add these routes to your router
<Route path="/trades/:tradeId" element={<TradeDetailPage />} />
<Route path="/performance" element={<PerformanceDashboard />} />
<Route path="/insights" element={<AIInsightsPage />} />
<Route path="/strategies" element={<StrategyMarketplace />} />
<Route path="/strategies/:strategyId" element={<StrategyDetailPage />} />
```

---

## Implementation Priority

| Priority | Feature | Complexity |
|----------|---------|------------|
| 1 | TradingView Setup with copy buttons | Low |
| 2 | Trade Detail Page link | Low |
| 3 | Trade Detail Page full UI | Medium |
| 4 | Trade History with P&L | Medium |
| 5 | Strategy Performance Dashboard | Medium |
| 6 | AI Insights Display | Medium |
| 7 | Strategy Marketplace | High |

---

## Summary Checklist

### TradingView Setup
- [ ] Display webhook URL with copy button
- [ ] Tabs for Basic/AI Learning/Exit messages
- [ ] Display instructions
- [ ] Show AI Learning parameter descriptions

### Trade Detail Page
- [ ] Add "Details" button to trade list
- [ ] Create route `/trades/:tradeId`
- [ ] Fetch trade detail from API
- [ ] Display execution summary
- [ ] Display market indices
- [ ] Display stock data
- [ ] Display fundamentals
- [ ] Display technical indicators
- [ ] Display account context

### Performance Dashboard
- [ ] Create performance summary cards
- [ ] Performance by indicator chart/table
- [ ] Performance by market condition chart/table
- [ ] Filter by date range, symbol, strategy

### Trade History with P&L
- [ ] Enhanced trade list with P&L column
- [ ] Color coding for wins/losses
- [ ] Summary totals (today, week, total)
- [ ] Filter by status (open/closed)

### AI Insights
- [ ] Display insight cards
- [ ] Confidence score visualization
- [ ] Recommendation actions
- [ ] Dismiss/apply functionality

### Strategy Marketplace
- [ ] Strategy listing cards
- [ ] Strategy detail page
- [ ] Subscription flow with disclaimer
- [ ] Bot selection for subscription
