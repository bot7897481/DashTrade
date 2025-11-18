# NovAlgo Trading Bot - Complete System Documentation

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [File Structure](#file-structure)
5. [Data Flow](#data-flow)
6. [API Endpoints](#api-endpoints)
7. [Google Sheets Structure](#google-sheets-structure)
8. [Configuration](#configuration)
9. [Deployment](#deployment)
10. [Monitoring](#monitoring)
11. [Development Guide](#development-guide)
12. [Troubleshooting](#troubleshooting)

---

## 🎯 System Overview

**Project:** NovAlgo Automated Trading System  
**Purpose:** Fully automated multi-stock, multi-timeframe trading bot  
**Status:** PRODUCTION - Live & Profitable  
**Current P&L:** +$426 (as of deployment)

### Key Features
- ✅ Automated trading execution via Alpaca API
- ✅ Signal reception from TradingView Pine Script
- ✅ Multi-stock support (18 stocks active)
- ✅ Multi-timeframe trading (5min, 15min, 30min, 45min)
- ✅ Google Sheets configuration management
- ✅ Real-time status tracking with PST timestamps
- ✅ Performance analytics dashboard
- ✅ Email/SMS/Slack notifications
- ✅ Advanced analytics (Sharpe ratio, drawdown, SPY comparison)
- ✅ CSV export and chart generation
- ✅ Security hardened with IP whitelisting

### Technology Stack
- **Language:** Python 3.10+
- **Framework:** Flask (webhook server)
- **APIs:** Alpaca Trading API, Google Sheets API, TradingView Webhooks
- **Infrastructure:** Azure VM (Ubuntu 22.04), systemd services
- **Libraries:** alpaca-trade-api, gspread, flask, pandas, matplotlib, twilio
- **Deployment:** Production on port 80, systemd service management

---

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TRADINGVIEW                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Pine Script │  │  Pine Script │  │  Pine Script │             │
│  │   Chart 1    │  │   Chart 2    │  │   Chart N    │             │
│  │  (HOOD 15M)  │  │  (AAPL 15M)  │  │  (TSLA 30M)  │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                  │                  │                     │
│         │ Webhook (BUY)   │ Webhook (SELL)  │ Webhook (BUY)      │
│         └──────────────────┴──────────────────┴────────────────┐   │
└─────────────────────────────────────────────────────────────────┼───┘
                                                                  │
                                  HTTP POST                       │
                                  (JSON payload)                  │
                                                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AZURE VM (20.245.132.209)                        │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                   FIREWALL (UFW)                              │ │
│  │  Port 80:  Only TradingView IPs + User IPs                   │ │
│  │  Port 22:  SSH (open)                                        │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │              TRADING BOT (Port 80)                            │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │  Flask Webhook Server                                   │ │ │
│  │  │  - Receives TradingView signals                         │ │ │
│  │  │  - Validates webhook secret                             │ │ │
│  │  │  - Parses JSON (action, symbol, timeframe)             │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  │                          │                                     │ │
│  │                          ▼                                     │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │  Configuration Manager                                  │ │ │
│  │  │  - Reads Google Sheets on each webhook                 │ │ │
│  │  │  - Matches (symbol, timeframe) to position_size        │ │ │
│  │  │  - Checks active status                                │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  │                          │                                     │ │
│  │                          ▼                                     │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │  Trading Engine                                         │ │ │
│  │  │  - execute_long_signal()                                │ │ │
│  │  │  - execute_short_signal()                               │ │ │
│  │  │  - execute_close_signal()                               │ │ │
│  │  │  - Manages opposite position closing                   │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  │                          │                                     │ │
│  │                          ▼                                     │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │  Status Tracker                                         │ │ │
│  │  │  - Updates Google Sheets "Order Status" column         │ │ │
│  │  │  - READY → ORDER SUBMITTED → FILLED/FAILED             │ │ │
│  │  │  - PST timestamps                                       │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  │                          │                                     │ │
│  │                          ▼                                     │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │  Performance Tracker (Background Thread)                │ │ │
│  │  │  - Runs every 5 minutes                                 │ │ │
│  │  │  - Calculates P&L, win rate, stats                     │ │ │
│  │  │  - Updates "Performance" tab in Google Sheets          │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │         ANALYTICS SUITE (Separate Script)                     │ │
│  │  - Email reports (HTML)                                       │ │
│  │  - SMS alerts (Twilio)                                        │ │
│  │  - Slack notifications                                        │ │
│  │  - CSV exports                                                │ │
│  │  - Chart generation (matplotlib)                              │ │
│  │  - Advanced metrics (Sharpe, drawdown, SPY comparison)       │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                          │                    │
                          ▼                    ▼
        ┌─────────────────────────┐  ┌──────────────────────┐
        │   ALPACA API            │  │  GOOGLE SHEETS API   │
        │  (Paper Trading)        │  │  (Configuration &    │
        │  - Place orders         │  │   Performance Data)  │
        │  - Get positions        │  │                      │
        │  - Get account data     │  │                      │
        │  - Get trade history    │  │                      │
        └─────────────────────────┘  └──────────────────────┘
```

### Component Interaction Flow

```
1. TradingView Signal Generated
   ↓
2. Webhook sent to Azure VM (Port 80)
   ↓
3. Flask receives POST request
   ↓
4. Validate webhook secret
   ↓
5. Read Google Sheets Config tab
   ↓
6. Match (symbol, timeframe) to find position_size
   ↓
7. Update status: "ORDER SUBMITTED"
   ↓
8. Send order to Alpaca API
   ↓
9. Wait 2 seconds, check order status
   ↓
10. Update status: "FILLED" or "FAILED"
    ↓
11. Return JSON response to TradingView
    ↓
12. Background thread updates Performance tab (every 5 min)
```

---

## 🔧 Components

### 1. Trading Bot (trading_bot.py)
**Purpose:** Main trading engine  
**Port:** 80  
**Process:** systemd service (trading-bot.service)  
**Logs:** /home/azureuser/trading_bot.log + journalctl

**Key Functions:**
```python
get_stock_config()           # Read Google Sheets Config tab
update_order_status()        # Update Order Status column
execute_long_signal()        # Execute BUY orders
execute_short_signal()       # Execute SELL orders
execute_close_signal()       # Close positions
update_performance_dashboard() # Update Performance tab
performance_updater()        # Background thread (5 min loop)
```

**Endpoints:**
- `POST /webhook` - Receive TradingView signals
- `GET /health` - Health check
- `GET /config` - Show active configuration
- `GET /positions` - Show current Alpaca positions
- `GET /performance` - Manually trigger performance update

### 2. Analytics Suite (complete_analytics.py)
**Purpose:** Comprehensive reporting and alerts  
**Execution:** Manual or cron job  
**Output:** Exports to `/home/azureuser/analytics_exports/`

**Features:**
- Email reports (HTML with attachments)
- SMS alerts (Twilio)
- Slack notifications
- CSV exports (positions, trades, account summary)
- Performance charts (matplotlib PNG)
- Advanced metrics (Sharpe ratio, max drawdown, SPY comparison)
- Alert threshold checking

**Key Functions:**
```python
get_account_data()           # Fetch account metrics
get_positions_data()         # Fetch all positions
get_trading_history()        # Fetch trade history
calculate_sharpe_ratio()     # Risk-adjusted returns
calculate_max_drawdown()     # Maximum loss from peak
get_spy_comparison()         # Compare to S&P 500
export_to_csv()              # Export data to CSV
generate_performance_chart() # Create visual charts
send_email_report()          # Email HTML report
send_sms_alert()             # SMS via Twilio
send_slack_notification()    # Slack webhook
check_alerts()               # Check alert thresholds
```

### 3. Profit Analyzer (profit_analyzer.py)
**Purpose:** Quick profit summary  
**Execution:** On-demand  
**Output:** Terminal display

**Shows:**
- Account summary
- Position table with P&L
- Best/worst performers
- Long vs short breakdown
- Win rate

### 4. Google Sheets Integration
**Sheet ID:** `1OltaqcoHrm0mvAiT9L1IS4XsVJZGErqnB1ZzKi5Wvk8`  
**Authentication:** Service account (credentials.json)

**Tabs:**
1. **Config** - Stock configuration (read on every webhook)
2. **Performance** - Performance metrics (updated every 5 min)

---

## 📁 File Structure

```
/home/azureuser/
│
├── trading_bot.py                    # Main trading bot (PRODUCTION)
├── complete_analytics.py             # Analytics suite
├── profit_analyzer.py                # Quick profit checker
├── advanced_analytics.py             # Advanced metrics script
│
├── credentials.json                  # Google Sheets service account
│
├── trading_bot.log                   # Trading bot logs
├── ibkr_bot.log                      # Future: IBKR bot logs
│
├── backup/                           # Code backups
│   ├── trading_bot_20251010_0530.py
│   ├── trading_bot_working.py
│   └── ...
│
├── analytics_exports/                # Analytics output
│   ├── positions_20251010_183045.csv
│   ├── trades_20251010_183045.csv
│   ├── account_20251010_183045.csv
│   ├── performance_chart_20251010_183045.png
│   └── ...
│
├── tradingbot_env/                   # Python virtual environment (optional)
│   └── ...
│
└── IBJts/                            # Future: IB Gateway installation
    └── ...

/etc/systemd/system/
├── trading-bot.service               # Trading bot systemd service
└── ibkr-bot.service                  # Future: IBKR bot service

/var/log/
└── journal/                          # System logs (journalctl)
```

---

## 🔄 Data Flow

### 1. Webhook Signal Flow

```
TradingView Alert Triggers
  ↓
JSON Payload Created:
{
  "action": "BUY",
  "symbol": "AAPL",
  "timeframe": "15 Min",
  "secret": "my_secret_key_123"
}
  ↓
HTTP POST → http://20.245.132.209/webhook
  ↓
Flask receives request
  ↓
Validate secret == "my_secret_key_123"
  ↓
Parse: action="BUY", symbol="AAPL", timeframe="15 Min"
  ↓
Call get_stock_config()
  ↓
Google Sheets API: Read "Config" tab
  ↓
Find row where: symbol="AAPL" AND Time Frame="15 Min" AND active=TRUE
  ↓
Extract: position_size=5000
  ↓
Call execute_long_signal("AAPL", "15 Min", 5000)
  ↓
Check Alpaca: get_current_position("AAPL")
  ↓
If SHORT: Close position first
If LONG: Skip (already long)
If FLAT: Continue
  ↓
Update Google Sheets: Order Status="ORDER SUBMITTED"
  ↓
Alpaca API: Submit market order (BUY $5000 of AAPL)
  ↓
Wait 2 seconds
  ↓
Alpaca API: Check order status
  ↓
If filled: Update Order Status="FILLED"
If pending: Status stays "ORDER SUBMITTED"
If failed: Update Order Status="FAILED"
  ↓
Return JSON response to TradingView
```

### 2. Performance Update Flow

```
Background Thread Loop (every 5 minutes)
  ↓
Call update_performance_dashboard()
  ↓
Alpaca API: Get activities (last 30 days, type=FILL)
  ↓
Group by symbol: {AAPL: {buys: [...], sells: [...]}}
  ↓
Match buys with sells (FIFO):
  For each sell:
    Find matching buy by time
    Calculate P&L = (sell_price - buy_price) * qty
    Increment total_trades
    If P&L > 0: winning_trades++
    If P&L < 0: losing_trades++
  ↓
Calculate metrics per symbol:
  - total_trades
  - winning_trades, losing_trades
  - win_rate = winning_trades / total_trades * 100
  - total_pnl
  - avg_pnl_per_trade
  - best_trade, worst_trade
  ↓
Google Sheets API: Write to "Performance" tab
  ↓
Update timestamp (PST)
  ↓
Sleep 300 seconds (5 minutes)
  ↓
Loop back
```

---

## 🌐 API Endpoints

### Trading Bot Endpoints

#### POST /webhook
**Purpose:** Receive TradingView signals  
**Method:** POST  
**Auth:** Webhook secret in JSON payload

**Request Body:**
```json
{
  "action": "BUY" | "SELL" | "CLOSE",
  "symbol": "AAPL",
  "timeframe": "15 Min",
  "secret": "my_secret_key_123"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "action": "BUY",
  "symbol": "AAPL",
  "timeframe": "15 Min",
  "amount": 5000,
  "order_id": "abc123..."
}
```

**Response (Error):**
```json
{
  "error": "Missing timeframe"
}
```

**Status Codes:**
- 200: Success or skipped (not active)
- 400: Bad request (missing data)
- 401: Unauthorized (invalid secret)
- 500: Server error

---

#### GET /health
**Purpose:** Check if bot is running  
**Method:** GET  
**Auth:** None

**Response:**
```json
{
  "status": "healthy - PRODUCTION",
  "port": 80,
  "timestamp": "2025-10-10T22:30:00-07:00",
  "active_configs": 18
}
```

---

#### GET /config
**Purpose:** Show active configuration  
**Method:** GET  
**Auth:** None

**Response:**
```json
{
  "config": {
    "AAPL 15 Min": 5000,
    "HOOD 45 Min": 40000,
    "TSLA 30 Min": 30000
  },
  "total": 18
}
```

---

#### GET /positions
**Purpose:** Show current Alpaca positions  
**Method:** GET  
**Auth:** None

**Response:**
```json
{
  "positions": [
    {
      "symbol": "AAPL",
      "qty": "-19",
      "side": "SHORT",
      "market_value": "-4668.3",
      "unrealized_pl": "130.15"
    }
  ],
  "total": 7
}
```

---

#### GET /performance
**Purpose:** Manually trigger performance update  
**Method:** GET  
**Auth:** None

**Response:**
```json
{
  "status": "Performance updated"
}
```

---

## 📊 Google Sheets Structure

### Sheet URL
```
https://docs.google.com/spreadsheets/d/1OltaqcoHrm0mvAiT9L1IS4XsVJZGErqnB1ZzKi5Wvk8
```

### Tab 1: Config

| Column | Type | Example | Description | Required |
|--------|------|---------|-------------|----------|
| symbol | TEXT | AAPL | Stock ticker symbol | ✅ Yes |
| position_size | NUMBER | 5000 | Dollar amount per trade | ✅ Yes |
| active | BOOLEAN | TRUE | Enable/disable trading | ✅ Yes |
| Time Frame | TEXT | 15 Min | Must match TradingView | ✅ Yes |
| Order Status | TEXT | FILLED | Auto-updated by bot | ⚠️ Auto |
| Last Updated | TEXT | 2025-10-10... | PST timestamp | ⚠️ Auto |

**Valid Timeframe Values:**
- `5 Min`
- `15 Min`
- `30 Min`
- `45 Min`

**Order Status Values:**
- `READY` - Active and waiting for signal
- `ORDER SUBMITTED` - Order sent to Alpaca
- `FILLED` - Order executed successfully
- `FAILED` - Order rejected
- `WAITING` - Position closed, awaiting next signal
- `INACTIVE` - Stock is disabled (active=FALSE)
- `ALREADY LONG` - Skipped duplicate BUY
- `ALREADY SHORT` - Skipped duplicate SELL

### Tab 2: Performance

| Column | Type | Description |
|--------|------|-------------|
| symbol | TEXT | Stock ticker |
| total_trades | NUMBER | Total closed trades |
| winning_trades | NUMBER | Profitable trades |
| losing_trades | NUMBER | Loss trades |
| win_rate | TEXT | Percentage (e.g., "55.5%") |
| total_pnl | TEXT | Total profit/loss (e.g., "$250.50") |
| avg_pnl_per_trade | TEXT | Average per trade |
| best_trade | TEXT | Largest win |
| worst_trade | TEXT | Largest loss |
| last_updated | TEXT | Timestamp (PST) |

**Update Frequency:** Every 5 minutes (automatic)  
**Data Source:** Alpaca trade history (last 30 days)  
**Calculation Method:** FIFO matching of buys and sells

---

## ⚙️ Configuration

### Environment Variables (Not Used Currently)
All configuration is hardcoded in Python files for simplicity.

### Alpaca API Credentials
**File:** `trading_bot.py` (lines 20-23)
```python
ALPACA_API_KEY = "PKL3QOG3TPAQ7NUYB86D"
ALPACA_SECRET_KEY = "zZxfTNPa7gBmU0RvSY0akIZujQWPXAeYhPD0O8Cz"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
```

**Type:** Paper Trading  
**Account Balance:** ~$160,000 (virtual money)

### Google Sheets API
**File:** `credentials.json`  
**Type:** Service account authentication  
**Permissions:** Editor access to Google Sheet

### Webhook Secret
**File:** `trading_bot.py` (line 24)
```python
WEBHOOK_SECRET = "my_secret_key_123"
```

**Usage:** Validates TradingView webhook requests  
**Security:** Change this to a stronger secret for production

### Timezone
**Setting:** PST (America/Los_Angeles)  
**Usage:** All timestamps in logs and Google Sheets

---

## 🚀 Deployment

### Initial Deployment

```bash
# 1. SSH to Azure VM
ssh azureuser@20.245.132.209

# 2. Install dependencies
sudo pip3 install flask alpaca-trade-api gspread oauth2client pytz

# 3. Upload credentials
# Upload credentials.json to /home/azureuser/

# 4. Create trading bot file
nano trading_bot.py
# Paste code, save

# 5. Test manually first
python3 trading_bot.py
# Should see: ✅ BOT IS LIVE!
# Ctrl+C to stop

# 6. Create systemd service
sudo nano /etc/systemd/system/trading-bot.service
```

**Service File:**
```ini
[Unit]
Description=NovAlgo Trading Bot
After=network.target

[Service]
Type=simple
User=azureuser
WorkingDirectory=/home/azureuser
ExecStart=/usr/bin/python3 /home/azureuser/trading_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 7. Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot

# 8. Verify running
sudo systemctl status trading-bot
```

### Updating Code

```bash
# 1. Backup current version
cp trading_bot.py trading_bot_backup_$(date +%Y%m%d_%H%M).py

# 2. Edit file
nano trading_bot.py
# Make changes

# 3. Restart service
sudo systemctl restart trading-bot

# 4. Check status
sudo systemctl status trading-bot

# 5. Watch logs
sudo journalctl -u trading-bot -f

# If broken, restore:
# cp trading_bot_backup_YYYYMMDD_HHMM.py trading_bot.py
# sudo systemctl restart trading-bot
```

---

## 📊 Monitoring

### Real-time Logs

```bash
# Watch live logs
sudo journalctl -u trading-bot -f

# Last 100 lines
sudo journalctl -u trading-bot -n 100

# Since 1 hour ago
sudo journalctl -u trading-bot --since "1 hour ago"

# Search for errors
sudo journalctl -u trading-bot | grep "ERROR"

# Search for specific stock
sudo journalctl -u trading-bot | grep "AAPL"
```

### Quick Status Check

```bash
# One-command status
curl http://20.245.132.209/health && \
curl http://20.245.132.209/config && \
curl http://20.245.132.209/positions
```

### Performance Monitoring

```bash
# Run profit analyzer
python3 profit_analyzer.py

# Run complete analytics
python3 complete_analytics.py

# Check exports
ls -lh /home/azureuser/analytics_exports/
```

---

## 💻 Development Guide

### Local Development

**NOT RECOMMENDED** - The bot needs to be accessible from TradingView webhooks.

If you need to test locally:
```bash
# Use ngrok for local testing
ngrok http 80

# Update TradingView webhook URL to ngrok URL
# https://abc123.ngrok.io/webhook
```

### Adding New Features

**Example: Add new endpoint**

```python
# In trading_bot.py

@app.route('/your-endpoint', methods=['GET'])
def your_function():
    """Your endpoint description"""
    # Your code here
    return jsonify({"result": "data"}), 200
```

**Then:**
```bash
# Restart bot
sudo systemctl restart trading-bot

# Test endpoint
curl http://20.245.132.209/your-endpoint
```

### Debugging

**Enable debug mode:**
```python
# In trading_bot.py, change last line:
app.run(host='0.0.0.0', port=80, debug=True)  # Add debug=True
```

**⚠️ WARNING:** Never run debug mode in production!

### Testing Webhooks

```bash
# Send test webhook
curl -X POST http://20.245.132.209/webhook \
  -H "Content-Type: application/json" \
  -d '{"action": "BUY", "symbol": "AAPL", "timeframe": "15 Min", "secret": "my_secret_key_123"}'
```

---

## 🆘 Troubleshooting

### Common Issues

#### 1. Bot Not Receiving Webhooks

**Symptoms:** TradingView sends alert, nothing in logs

**Check:**
```bash
# Firewall status
sudo ufw status

# Bot running?
sudo systemctl status trading-bot

# Port 80 open?
sudo lsof -i :80

# Test manually
curl http://20.245.132.209/health
```

**Fix:**
```bash
# Restart bot
sudo systemctl restart trading-bot

# Check firewall allows TradingView IPs
sudo ufw allow from 52.89.214.238 to any port 80
```

---

#### 2. Google Sheets Not Updating

**Symptoms:** Order Status or Performance not updating

**Check:**
```bash
# Check logs for Google Sheets errors
sudo journalctl -u trading-bot | grep "Google Sheets"

# Test Google Sheets connection
python3 -c "import gspread; from oauth2client.service_account import ServiceAccountCredentials; scope = ['https://spreadsheets.google.com/feeds']; creds = ServiceAccountCredentials.from_json_keyfile_name('/home/azureuser/credentials.json', scope); client = gspread.authorize(creds); print('Connected')"
```

**Fix:**
- Verify credentials.json exists and has correct permissions
- Check service account has Editor access to sheet
- Verify sheet ID is correct

---

#### 3. Orders Not Executing

**Symptoms:** Webhook received but no order in Alpaca

**Check:**
```bash
# Check Alpaca connection
curl http://20.245.132.209/positions

# Look for order errors in logs
sudo journalctl -u trading-bot | grep "ORDER FAILED"
```

**Common Causes:**
- Market is closed
- Insufficient buying power
- Stock not tradeable
- Invalid symbol

---

#### 4. Performance Dashboard Empty

**Symptoms:** Performance tab shows no data

**Possible Reasons:**
- No trades executed yet (need at least 1 closed trade)
- Bot hasn't run 5-minute update yet
- Calculation error in P&L matching

**Fix:**
```bash
# Manually trigger update
curl http://20.245.132.209/performance

# Check logs
sudo journalctl -u trading-bot -n 50 | grep "Performance"
```

---

## 🔐 Security Best Practices

### Current Security Measures

✅ Firewall (UFW) blocking all ports except 22, 80  
✅ Port 80 restricted to TradingView IPs + user IPs  
✅ Webhook secret validation  
✅ HTTPS not implemented (HTTP only)  
✅ No authentication on GET endpoints

### Recommended Enhancements

1. **Add HTTPS (SSL/TLS)**
   - Get free SSL cert from Let's Encrypt
   - Use nginx as reverse proxy

2. **API Key Authentication**
   - Add API key header to GET endpoints
   - Rotate keys periodically

3. **Rate Limiting**
   - Limit webhook requests per minute
   - Prevent DOS attacks

4. **Secret Rotation**
   - Change webhook secret monthly
   - Use environment variables

---

## 📚 Additional Resources

### Documentation Links
- Alpaca API: https://alpaca.markets/docs/
- Google Sheets API: https://developers.google.com/sheets/api
- Flask: https://flask.palletsprojects.com/
- TradingView Webhooks: https://www.tradingview.com/support/solutions/43000529348-webhook-alerts/

### Useful Commands Cheatsheet

See `cheatsheet.md` artifact for complete command reference.

---

## 📞 Support

### Getting Help

**For Bot Issues:**
1. Check logs: `sudo journalctl -u trading-bot -f`
2. Check this README troubleshooting section
3. Restore from backup if needed

**For Alpaca Issues:**
- Alpaca Support: https://alpaca.markets/support
- Paper Trading Dashboard: https://app.alpaca.markets/paper/dashboard/overview

**For Google Sheets Issues:**
- Verify service account permissions
- Check credentials.json
- Test connection manually

---

## 📝 Change Log

### Version 2.0 (2025-10-10)
- ✅ Added multi-timeframe support
- ✅ Added order status tracking
- ✅ Added PST timezone conversion
- ✅ Enhanced logging and error handling
- ✅ Security hardening (firewall rules)
- ✅ Performance dashboard improvements

### Version 1.0 (2025-10-08)
- ✅ Initial deployment
- ✅ Multi-stock trading
- ✅ Google Sheets integration
- ✅ Basic performance tracking

---

## ⚖️ License

Private project - All rights reserved.

---

## 👤 Maintainer

**Project Owner:** Abed  
**Server:** Azure VM (20.245.132.209)  
**Status:** Production - Live Trading

---

*Last Updated: 2025-10-10*