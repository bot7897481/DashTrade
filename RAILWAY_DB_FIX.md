# Fix Railway Database Connection Error

## The Error You're Seeing

```
connection to server at "localhost" (::1), port 5432 failed: Connection refused
```

## What This Means

This error means the app is trying to connect to **localhost** (your local computer) instead of Railway's database. This happens when:

1. ❌ You're running the app **locally** with `streamlit run app.py`
2. ❌ Railway doesn't have `DATABASE_URL` set
3. ❌ PostgreSQL service isn't connected in Railway

## ✅ Solution: Use Railway URL (Not Local)

### Step 1: Get Your Railway URL

1. Go to **Railway Dashboard**
2. Click your **Project**
3. Click your **Service** (the web service)
4. Find your **Public URL** (looks like `https://your-app.railway.app`)
5. **Copy this URL**

### Step 2: Access Through Railway URL

- ✅ **DO THIS:** Open `https://your-app.railway.app` in your browser
- ❌ **DON'T DO THIS:** Run `streamlit run app.py` locally

### Step 3: Verify Railway Setup

1. **Check PostgreSQL Service:**
   - Railway Dashboard → Your Project
   - Make sure you have a **PostgreSQL** service added
   - It should show as "Running" ✅

2. **Check DATABASE_URL Variable:**
   - Railway Dashboard → Your Project → **Variables** tab
   - Look for `DATABASE_URL`
   - Railway **automatically** sets this when you add PostgreSQL
   - It should look like: `postgresql://user:pass@host:port/db`

3. **If DATABASE_URL is Missing:**
   - Make sure PostgreSQL service is added
   - Railway should auto-set it
   - If not, check service connection

## Quick Diagnostic

Run this on Railway to check your setup:

```bash
# In Railway Shell/Console
python check_railway_db.py
```

This will show:
- ✅ If you're on Railway
- ✅ If DATABASE_URL is set
- ✅ If connection works

## Common Mistakes

### Mistake 1: Running Locally
```bash
# ❌ DON'T DO THIS
streamlit run app.py
```

**Why:** This tries to connect to localhost database, which doesn't exist.

**Fix:** Use Railway URL instead.

### Mistake 2: Testing on Localhost
```
❌ http://localhost:8501
```

**Why:** This is your local computer, not Railway.

**Fix:** Use Railway URL: `https://your-app.railway.app`

### Mistake 3: Missing PostgreSQL Service
- Railway project has no PostgreSQL service
- DATABASE_URL is not set

**Fix:** Add PostgreSQL service in Railway.

## Step-by-Step Railway Setup

### 1. Add PostgreSQL Service

1. Railway Dashboard → Your Project
2. Click **"+ New"** → **"Database"** → **"PostgreSQL"**
3. Wait for it to provision (takes ~30 seconds)
4. Railway automatically sets `DATABASE_URL`

### 2. Verify Variables

1. Railway Dashboard → Your Project → **Variables**
2. You should see:
   - `DATABASE_URL` ✅ (auto-set by Railway)
   - `ADMIN_CODE` ✅ (if you added it)

### 3. Deploy Your App

1. Push to GitHub (if connected)
2. Or Railway will auto-deploy
3. Check deployment logs

### 4. Access Your App

1. Railway Dashboard → Your Service
2. Click **"Settings"** → **"Generate Domain"** (if needed)
3. Copy the **Public URL**
4. Open in browser: `https://your-app.railway.app`

## Testing

### Test Database Connection

1. Go to Railway Shell/Console
2. Run: `python check_railway_db.py`
3. Should show: ✅ Connection successful

### Test Registration

1. Go to your Railway URL (not localhost!)
2. Click "Create New Account"
3. Fill in form
4. Enter admin code: `1234-5678-9012-3939`
5. Should work! ✅

## Still Having Issues?

### Check Railway Logs

1. Railway Dashboard → Deployments
2. Click latest deployment
3. Check **Logs** tab
4. Look for errors

### Verify PostgreSQL is Running

1. Railway Dashboard → PostgreSQL Service
2. Should show "Running" status
3. Check connection details

### Redeploy

1. Railway Dashboard → Your Service
2. Click **"Deploy"** → **"Redeploy"**
3. Wait for deployment to finish

## Summary

**The Key Point:**
- ❌ Don't run `streamlit run app.py` locally
- ✅ Use your Railway URL: `https://your-app.railway.app`
- ✅ Railway automatically sets DATABASE_URL
- ✅ PostgreSQL service must be added in Railway

**Your Railway URL is your app - use that, not localhost!**

