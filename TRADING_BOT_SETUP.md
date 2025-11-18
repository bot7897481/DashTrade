# 🤖 DashTrade Trading Bot - Setup Guide

## Overview

The Trading Bot system allows each user to create unlimited automated trading strategies that execute via TradingView webhooks and Alpaca Markets. Each user has their own:

- ✅ Alpaca API credentials (encrypted)
- ✅ Unlimited bot configurations (symbol + timeframe combinations)
- ✅ Independent trade execution
- ✅ Risk management (% loss limits)
- ✅ Performance tracking
- ✅ Trade history

---

## Architecture

```
TradingView Alert → Webhook (Port 8080) → User's Bot Config → Alpaca API → Trade Executed → Database Logged
```

**Two Servers Running:**
- **Streamlit** (Port 5000): User dashboard & bot management
- **Flask** (Port 8080): Webhook receiver for TradingView

---

## Initial Setup (One-Time)

### Step 1: Install Dependencies

```bash
uv sync
```

This will install:
- `flask` - Webhook server
- `alpaca-trade-api` - Trading execution
- `cryptography` - API key encryption
- Plus all existing dependencies

### Step 2: Generate Encryption Key

```bash
.venv/bin/python encryption.py
```

Copy the output key (starts with `ENCRYPTION_KEY=...`)

### Step 3: Add to Replit Secrets

1. Click "Tools" → "Secrets" in Replit
2. Add new secret:
   - **Key**: `ENCRYPTION_KEY`
   - **Value**: Paste the key from Step 2

⚠️ **Important**: Never commit this key to git!

### Step 4: Run Database Migration

```bash
.venv/bin/python migrate_bot_tables.py
```

Type `yes` when prompted. This creates 6 new tables:
- `user_api_keys`
- `user_bot_configs`
- `bot_trades`
- `bot_performance`
- `user_webhook_tokens`
- `bot_risk_events`

### Step 5: Start Both Servers

Click the **Run** button in Replit

This starts:
1. Streamlit on port 5000 (main dashboard)
2. Flask webhook server on port 8080

---

## User Setup (Per User)

### 1. Connect Alpaca Account

1. Go to [Alpaca Markets](https://alpaca.markets) and create a free account
2. Navigate to Paper Trading dashboard
3. Generate API keys (API Key + Secret Key)
4. In DashTrade, go to **🤖 Trading Bot** page
5. Click **Setup** tab
6. Enter your Alpaca API credentials
7. Select **Paper** mode (recommended for testing)
8. Click "Save API Keys"

✅ Keys are encrypted and stored securely in the database

### 2. Get Your Webhook URL

After adding API keys:
1. Click "Generate Webhook URL"
2. Copy the URL (looks like: `https://your-replit.repl.co/webhook?token=usr_abc123...`)

This is your unique URL for TradingView webhooks.

### 3. Create Your First Bot

1. Go to **My Bots** tab
2. Click "➕ Add New Bot"
3. Fill in:
   - **Symbol**: AAPL (or any stock)
   - **Timeframe**: 15 Min
   - **Position Size**: $5000 (how much $ per trade)
   - **Risk Limit**: 10% (close position if loss exceeds this)
4. Click "Create Bot"

✅ Bot is now active and ready to receive signals!

### 4. Configure TradingView Alert

1. Open TradingView chart for your symbol
2. Create an alert (bell icon)
3. Set conditions (your strategy)
4. In **Webhook URL**, paste your webhook URL from Step 2
5. In **Message** field, use this template:

```json
{
  "action": "{{strategy.order.action}}",
  "symbol": "{{ticker}}",
  "timeframe": "15 Min"
}
```

⚠️ **Important**: The `timeframe` must match exactly what you configured in your bot!

6. Save the alert

---

## How It Works

### Signal Flow

```
1. TradingView detects condition → Sends webhook
   ↓
2. Flask server receives POST request
   ↓
3. Validates token → Gets user_id
   ↓
4. Looks up bot config (symbol + timeframe)
   ↓
5. Checks if bot is active
   ↓
6. Checks risk limits
   ↓
7. Executes trade via Alpaca API
   ↓
8. Logs trade to database
   ↓
9. Updates bot status
```

### Trade Logic

**BUY Signal:**
- If already LONG → Skip
- If SHORT → Close short, then buy
- If FLAT → Buy

**SELL Signal:**
- If already SHORT → Skip
- If LONG → Close long, then sell
- If FLAT → Sell (short)

**CLOSE Signal:**
- Close position (regardless of direction)

### Risk Management

Each bot has:
- **Risk Limit %**: If unrealized loss exceeds this, position is auto-closed and bot disabled
- **Daily Loss Limit** (optional): Max $ loss per day
- **Max Position Size** (optional): Override position size limit

When risk limit is hit:
1. Position is closed immediately
2. Bot is disabled (prevents further trading)
3. Event is logged to `bot_risk_events` table
4. User can see this in "Risk Events" tab

---

## Using the Dashboard

### My Bots Tab

View all your bots:
- See status (READY, ORDER SUBMITTED, FILLED, etc.)
- Enable/disable individual bots
- Delete bots
- View total P&L per bot

### Live Positions Tab

Real-time view from Alpaca:
- Current positions
- Unrealized P&L
- Entry price vs current price
- Position side (LONG/SHORT)

### Trade History Tab

All executed trades:
- Timestamp
- Symbol + timeframe
- Action (BUY/SELL/CLOSE)
- Status
- Order ID
- Filled quantity and price

**Export**: Click "Export to CSV" to download

### Performance Tab

- Total P&L across all bots
- Total trades executed
- Per-symbol breakdown
- Best/worst performers

### Risk Events Tab

Shows all risk limit triggers:
- When it happened
- Which bot
- Threshold vs actual loss
- Action taken (position closed, bot disabled)

---

## Advanced Usage

### Multiple Timeframes

You can trade the same symbol on different timeframes:

```
AAPL - 5 Min  → $5,000 per trade
AAPL - 15 Min → $10,000 per trade
AAPL - 30 Min → $8,000 per trade
```

Each is tracked independently!

**TradingView Setup:**
- Create separate alerts for each timeframe
- Each alert uses the SAME webhook URL
- But different `timeframe` values in the message

### Testing Webhooks

Use the test endpoint to verify your payload:

```bash
curl -X POST https://your-replit.repl.co/test-webhook \
  -H "Content-Type: application/json" \
  -d '{"action": "BUY", "symbol": "AAPL", "timeframe": "15 Min"}'
```

### View User Positions (API)

```bash
curl "https://your-replit.repl.co/user/YOUR_USER_ID/positions?token=YOUR_TOKEN"
```

Returns your current Alpaca positions.

---

## Troubleshooting

### "No Alpaca API keys found"

**Solution**: Go to Setup tab and add your API keys

### "Invalid or inactive token"

**Solution**: Regenerate your webhook URL in the Setup tab

### "No bot configuration found"

**Solution**: Create a bot for that symbol+timeframe combination

### Orders not executing

**Possible causes:**
1. Market is closed (Alpaca only trades during market hours)
2. Bot is disabled
3. Insufficient buying power
4. Symbol not tradeable

**Check:**
- Live Positions tab (see account buying power)
- My Bots tab (ensure bot is active)
- Trade History tab (check for error messages)

### Risk limit hit unexpectedly

**Solution**: Check Risk Events tab to see what triggered it. You can adjust the risk limit % when creating/editing a bot.

---

## Security Best Practices

✅ **DO:**
- Use Paper Trading first to test
- Start with small position sizes
- Set conservative risk limits
- Monitor your bots regularly
- Keep your webhook token private

❌ **DON'T:**
- Share your webhook URL
- Commit API keys to git
- Skip risk limits
- Start with live trading
- Use your entire account balance per trade

---

## File Structure

```
/DashTrade/
├── encryption.py                    # API key encryption utilities
├── bot_database.py                  # Database operations for bots
├── bot_engine.py                    # Trading execution engine
├── webhook_server.py                # Flask webhook server (port 8080)
├── migrate_bot_tables.py            # Database migration script
├── pages/
│   └── 7_🤖_Trading_Bot.py          # Streamlit bot management page
└── migrations/
    └── 001_create_bot_tables.sql    # SQL migration
```

---

## Database Schema

### user_api_keys
Stores encrypted Alpaca credentials per user

### user_bot_configs
One row per symbol+timeframe combination:
- symbol, timeframe, position_size
- risk_limit_percent, daily_loss_limit
- is_active, order_status
- total_pnl, total_trades

### bot_trades
Every trade execution logged:
- user_id, bot_config_id
- action (BUY/SELL/CLOSE)
- order_id, status
- filled_qty, filled_price
- realized_pnl

### user_webhook_tokens
One secure token per user for TradingView

### bot_risk_events
Logs when risk limits are triggered

---

## API Endpoints

### POST /webhook?token=YOUR_TOKEN
Main webhook endpoint (called by TradingView)

### GET /health
Health check

### POST /test-webhook
Test webhook payload (no auth)

### GET /user/<id>/positions?token=YOUR_TOKEN
Get current positions

### GET /user/<id>/bots?token=YOUR_TOKEN
Get all bot configs

---

## Support

**Issues?**
- Check Replit console logs
- Check "Risk Events" tab for auto-closures
- Verify database migration ran successfully
- Ensure ENCRYPTION_KEY is set in Secrets

**Feature Requests?**
Open an issue or modify the code!

---

## Next Steps

1. ✅ Complete initial setup (above)
2. ✅ Test with paper trading
3. ✅ Monitor performance for 1-2 weeks
4. ✅ Adjust risk limits as needed
5. ✅ Scale to more symbols/timeframes
6. ⚠️  Consider live trading (when confident)

---

**Happy Trading! 🚀**

*Remember: Past performance does not guarantee future results. Trade responsibly.*
