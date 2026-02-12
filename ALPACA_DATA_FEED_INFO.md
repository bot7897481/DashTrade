# Alpaca Data Feed Information

## ✅ **No 15-Minute Delay on Alpaca**

**Alpaca does NOT have a 15-minute delay** when purchasing securities. The pricing data you receive depends on your Alpaca subscription level.

---

## 📊 Alpaca Data Feed Options

### **Free Plan (Default)**
- **Data Feed:** IEX (Investors Exchange)
- **Latency:** Real-time for IEX trades
- **Coverage:** ~2-3% of total market volume
- **Limitation:** Only reflects prices from IEX exchange, not all U.S. exchanges

### **Algo Trader Plus Plan ($99/month)**
- **Data Feed:** SIP (Securities Information Processor)
- **Latency:** Real-time across all exchanges
- **Coverage:** All U.S. stock exchanges (NYSE, NASDAQ, etc.)
- **Best for:** Professional trading requiring full market coverage

---

## 🔍 How Your Code Fetches Prices

### Current Implementation

**File:** `bot_engine.py`

```python
def get_price_quote(self, symbol: str) -> Dict:
    """Get latest quote for a stock or crypto"""
    # For stocks:
    request_params = StockLatestQuoteRequest(symbol_or_symbols=symbol_upper)
    quote = self.stock_data_client.get_stock_latest_quote(request_params)
    
    # For crypto:
    request_params = CryptoLatestQuoteRequest(symbol_or_symbols=crypto_symbol)
    quote = self.crypto_data_client.get_crypto_latest_quote(request_params)
```

**What this means:**
- ✅ Uses Alpaca's `get_stock_latest_quote()` - **real-time data**
- ✅ Uses Alpaca's `get_crypto_latest_quote()` - **real-time data**
- ⚠️ **Free plan:** Real-time from IEX only (limited coverage)
- ✅ **Paid plan:** Real-time from all exchanges (full coverage)

---

## ⚠️ Important Distinction

### **Yahoo Finance vs Alpaca**

**Yahoo Finance (mentioned in `replit.md`):**
- ❌ **15-minute delay** on free tier
- Used for historical data and analysis
- NOT used for actual trade execution

**Alpaca (used for trading):**
- ✅ **Real-time** pricing (no delay)
- Used for actual trade execution
- Coverage depends on subscription level

---

## 🎯 What This Means for Your Trades

### When You Place an Order:

1. **Price Quote:** Fetched in real-time from Alpaca
   - Free plan: IEX real-time prices
   - Paid plan: All exchanges real-time prices

2. **Order Execution:** Market orders execute at current market price
   - No delay in execution
   - Price may differ slightly from quote due to:
     - Market movement between quote and execution
     - Slippage (especially for larger orders)
     - Spread (bid/ask difference)

3. **Fill Price:** The actual price you get is the **execution price**, not the quote price
   - This is normal and expected
   - Slippage is tracked in your trade logs

---

## 📈 Crypto Trading

**Crypto prices are always real-time:**
- ✅ No delay for crypto quotes
- ✅ 24/7 market access
- ✅ Real-time pricing from Alpaca's crypto data feed

---

## 🔧 How to Check Your Data Feed

### Check Your Alpaca Account:
1. Log into Alpaca dashboard
2. Go to **Account Settings** → **Market Data**
3. Check which data feed you're subscribed to:
   - **IEX** = Free plan (limited coverage)
   - **SIP** = Paid plan (full coverage)

### In Your Code:
The code doesn't explicitly select a data feed - it uses whatever your Alpaca account has access to.

---

## 💡 Recommendations

### For Paper Trading:
- ✅ Free IEX feed is sufficient for testing
- ✅ Real-time data from IEX exchange
- ✅ Good for learning and strategy development

### For Live Trading:
- ⚠️ Consider upgrading to SIP feed ($99/month)
- ✅ Full market coverage
- ✅ Better price discovery across all exchanges
- ✅ More accurate for larger orders

---

## 📝 Summary

| Aspect | Free Plan (IEX) | Paid Plan (SIP) |
|--------|------------------|-----------------|
| **Delay** | ❌ None (real-time) | ❌ None (real-time) |
| **Coverage** | IEX only (2-3% volume) | All U.S. exchanges |
| **Best For** | Paper trading, testing | Live trading, professional |
| **Cost** | Free | $99/month |

**Bottom Line:** Alpaca provides **real-time pricing** with no 15-minute delay. The difference is in **market coverage**, not latency.

---

## 🚨 If You're Seeing Price Delays

If you notice significant price differences:

1. **Check your Alpaca subscription level**
   - Free plan = IEX only (limited coverage)
   - Prices may differ from other exchanges

2. **Check execution vs quote**
   - Quote is a snapshot in time
   - Execution happens milliseconds later
   - Market can move between quote and fill

3. **Check slippage in trade logs**
   - Your code tracks slippage
   - Look at `slippage` and `slippage_percent` fields

4. **Verify you're using Alpaca, not Yahoo Finance**
   - Yahoo Finance has 15-minute delay
   - Alpaca is real-time

---

**Your code is correctly using Alpaca's real-time data feeds!** 🎯


