# Investigation: Why 3 CLOSE Alerts Only Execute 1 Order

## Question
**User Observation:** Three BUY alerts from TradingView result in three orders executed in Alpaca. Three CLOSE alerts from TradingView only result in ONE order executed. Why?

---

## 🔍 Root Cause Analysis

### The Fundamental Difference

**BUY Orders:**
- BUY orders are **additive** - each BUY order adds to the existing position
- Multiple BUY orders on the same symbol = one cumulative position
- Example: BUY $100 → BUY $100 → BUY $100 = Position of $300 total

**CLOSE Orders:**
- CLOSE orders are **destructive** - they close the ENTIRE position
- Once closed, position becomes FLAT
- Subsequent CLOSE orders find no position to close

---

## 📋 Code Analysis

### CLOSE Order Logic (Lines 437-440 in bot_engine.py)

```python
# Handle CLOSE signal
if action == 'CLOSE':
    if current_side == 'FLAT':  # ← KEY CHECK
        logger.info(f"ℹ️  {symbol} already flat")
        return {'status': 'info', 'message': 'Already flat'}  # ← SKIPS
```

**What Happens:**
1. **First CLOSE signal arrives:**
   - Checks position: `current_side = 'LONG'` (position exists)
   - Condition `if current_side == 'FLAT'` = **FALSE**
   - Continues → Executes close → Position becomes FLAT

2. **Second CLOSE signal arrives (few milliseconds later):**
   - Checks position: `current_side = 'FLAT'` (already closed by first signal)
   - Condition `if current_side == 'FLAT'` = **TRUE**
   - Returns early → **SKIPPED** ✅

3. **Third CLOSE signal arrives:**
   - Checks position: `current_side = 'FLAT'` (still flat)
   - Condition `if current_side == 'FLAT'` = **TRUE**
   - Returns early → **SKIPPED** ✅

**Result:** Only the **first CLOSE** executes, the other two are skipped.

---

### BUY Order Logic (How It Works)

**Important Note:** If BUY orders are executing 3 times, they must be:
1. From **different timeframes** (3 different bots), OR
2. Coming in **before position is recognized** (race condition), OR
3. The logic allows multiple BUYs (which seems unlikely based on code)

**Typical BUY Flow:**
1. **First BUY signal:**
   - Position: FLAT → Executes BUY → Position: LONG

2. **Second BUY signal (if same symbol/timeframe):**
   - Should check: `if current_side == 'LONG'` → Skip (but user says it doesn't)
   - OR: Different timeframe = different bot → Executes separately

3. **Third BUY signal:**
   - Same logic as above

**Why BUY might execute 3 times:**
- If you have **3 different bots** (e.g., BTC/USD on 1min, 5min, 15min), each executes independently
- Each bot creates its own position (in the bot's tracking)
- But in Alpaca, they all add to the same physical position

---

## 🎯 Why This Behavior Exists

### Design Logic

**CLOSE is Protective:**
- CLOSE closes the **entire position** (not partial)
- Once closed, there's **nothing left to close**
- Multiple CLOSE signals would be **redundant** and potentially **dangerous**
- The code protects against duplicate closes

**BUY is Additive:**
- BUY orders can accumulate (multiple buys = larger position)
- Each BUY executes independently
- Alpaca combines them into one position

---

## 📊 Timeline Example

### Scenario: 3 CLOSE Alerts Arrive

```
Time: 12:00:00.000
├─ CLOSE Alert #1 arrives
│  ├─ Check position: LONG (qty: 0.001)
│  ├─ Execute close_order()
│  ├─ Alpaca: Close position
│  └─ Position becomes: FLAT
│
Time: 12:00:00.050 (50ms later)
├─ CLOSE Alert #2 arrives
│  ├─ Check position: FLAT ← Already closed!
│  ├─ Early return: "Already flat"
│  └─ SKIPPED ✅
│
Time: 12:00:00.100 (100ms later)
├─ CLOSE Alert #3 arrives
│  ├─ Check position: FLAT ← Still flat!
│  ├─ Early return: "Already flat"
│  └─ SKIPPED ✅
```

**Result:** 1 CLOSE executed, 2 skipped

---

### Scenario: 3 BUY Alerts Arrive

**If same symbol/timeframe:**
```
Time: 12:00:00.000
├─ BUY Alert #1 arrives
│  ├─ Check position: FLAT
│  ├─ Execute buy_order($100)
│  └─ Position: LONG (0.001 BTC)
│
Time: 12:00:00.050
├─ BUY Alert #2 arrives
│  ├─ Check position: LONG (0.001 BTC)
│  ├─ Should skip (already LONG)
│  └─ BUT: If code doesn't check, executes anyway
│
Time: 12:00:00.100
├─ BUY Alert #3 arrives
│  ├─ Same as #2
│  └─ Executes (if not checked)
```

**If different timeframes (3 different bots):**
```
Bot 1 (BTC/USD 1min): BUY → Executes
Bot 2 (BTC/USD 5min): BUY → Executes (separate bot)
Bot 3 (BTC/USD 15min): BUY → Executes (separate bot)
```
All three add to the same Alpaca position, but are tracked separately in database.

---

## 🔑 Key Insights

### Why Only 1 CLOSE Executes

1. **Position State Changes:**
   - First CLOSE: LONG → FLAT (destructive change)
   - Second CLOSE: FLAT → FLAT (no change, skipped)
   - Third CLOSE: FLAT → FLAT (no change, skipped)

2. **Protective Logic:**
   - Code checks `if current_side == 'FLAT'` before closing
   - Prevents duplicate close orders
   - Prevents closing a non-existent position

3. **Alpaca Behavior:**
   - `close_position()` requires an open position
   - If position already closed, Alpaca would reject it
   - Code protects against this by checking first

---

### Why 3 BUYs Might Execute

**Possible Reasons:**

1. **Different Bots/Timeframes:**
   - 3 separate bot configurations (different timeframes)
   - Each bot executes independently
   - All add to the same Alpaca position

2. **Race Condition:**
   - Alerts arrive before first order is filled
   - Position check happens before Alpaca updates
   - All three see FLAT position → all execute

3. **Logic Gap:**
   - BUY might not check for existing LONG position
   - Or check happens too late
   - Multiple BUYs allowed

---

## 🎓 Conclusion

### Expected Behavior

**CLOSE Orders:**
- ✅ Only the **first CLOSE** should execute
- ✅ Subsequent CLOSE orders should be **skipped** (position already FLAT)
- ✅ This is **correct and protective** behavior

**BUY Orders:**
- ⚠️ If 3 BUYs execute, they're likely from **different bots/timeframes**
- ⚠️ Or there's a **race condition** where all see FLAT simultaneously
- ⚠️ Or the logic doesn't properly check for existing LONG position

---

## 📝 Summary

**Why 3 CLOSE alerts only execute 1 order:**

1. **CLOSE is destructive** - Closes entire position
2. **Position state changes** - LONG → FLAT after first close
3. **Protective check** - Code skips if position is already FLAT
4. **Prevents errors** - Avoids trying to close non-existent position

**This is EXPECTED and CORRECT behavior!**

The first CLOSE executes successfully. The second and third CLOSE signals are correctly rejected because there's no position left to close.

---

## 🔧 If You Want All 3 CLOSE Orders to Execute

**This is NOT recommended**, but if you want it:

1. **Remove the FLAT check** (not recommended - would cause errors)
2. **Allow partial closes** (different logic - close 1/3 of position per signal)
3. **Use different symbols** (each CLOSE for different symbol)

**However, the current behavior is correct and safe!**

