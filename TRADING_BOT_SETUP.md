# Trading Bot Setup Guide for Replit

## Current Issue

You're seeing this error:
```
psycopg2.errors.UndefinedTable: relation "user_api_keys" does not exist
```

**Why?** The Trading Bot needs 6 database tables that haven't been created yet.

---

## Quick Fix (5 minutes)

Follow these exact steps in **Replit**:

### **Step 1: Pull Latest Code**

Open the **Replit Shell** and run:
```bash
git pull origin claude/learn-replit-01VJWXqcpk6TTxoc63oYcQHd
```

You should see:
```
✅ setup_bot_database.py created
```

---

### **Step 2: Run the Database Setup Script**

In the **Replit Shell**, run:
```bash
python3 setup_bot_database.py
```

You should see:
```
🤖 TRADING BOT DATABASE SETUP
📡 Connecting to database...
⚙️  Creating bot tables...
✅ Verifying tables...
✅ All 6 bot tables created successfully:
   ✓ bot_performance
   ✓ bot_risk_events
   ✓ bot_trades
   ✓ user_api_keys
   ✓ user_bot_configs
   ✓ user_webhook_tokens

✅ BOT DATABASE SETUP COMPLETED!
```

---

### **Step 3: Restart Your App**

1. Click the **Stop** button in Replit
2. Click **Run** to start the app again

---

### **Step 4: Test the Trading Bot**

1. Go to your Streamlit app in the browser
2. Click on **🤖 Trading Bot** in the sidebar
3. Click on the **⚙️ Setup** tab

**You should now see:**
```
⚙️ Bot Setup

Connect Alpaca Account
```

Instead of the error! ✅

---

## Summary

**What You Need to Do NOW:**

1. ✅ Run: `git pull origin claude/learn-replit-01VJWXqcpk6TTxoc63oYcQHd`
2. ✅ Run: `python3 setup_bot_database.py`
3. ✅ Restart your app (Stop → Run)
4. ✅ Test the Trading Bot page

**That's it!** The error will be gone. 🚀
