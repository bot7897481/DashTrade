# Admin Code Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: "Invalid admin activation code"

**Symptoms:**
- You enter a code but get "Invalid admin activation code" error
- Code looks correct but doesn't work

**Solutions:**

1. **Check Railway Variables:**
   - Go to Railway Dashboard → Your Project → Variables
   - Look for `ADMIN_CODE` variable
   - Copy the exact value (it might have dashes or not)

2. **Code Format:**
   - Codes work **with or without dashes**
   - `1234-5678-9012-3939` = `1234567890123939` ✅
   - Make sure it's exactly 16 digits

3. **Default Code:**
   - If `ADMIN_CODE` is **NOT set** in Railway, use: `1234-5678-9012-3456`
   - If `ADMIN_CODE` **IS set**, use that exact code

4. **Test Your Code:**
   ```bash
   # Run this locally to test
   python test_admin_code.py
   ```

### Issue 2: Database Connection Error

**Symptoms:**
- Error: "connection to server at localhost (::1), port 5432 failed"
- "Connection refused"

**Cause:**
You're running the app **locally** but `DATABASE_URL` is not set or pointing to localhost.

**Solutions:**

1. **Use Railway-Deployed App:**
   - Don't run `streamlit run app.py` locally
   - Access your Railway app URL instead
   - Railway automatically sets `DATABASE_URL`

2. **If Testing Locally:**
   - Set `DATABASE_URL` in your `.env` file
   - Or export it: `export DATABASE_URL='your-railway-db-url'`
   - But it's better to test on Railway!

### Issue 3: Code Works Locally But Not on Railway

**Cause:**
- `ADMIN_CODE` variable not set in Railway
- Variable name is wrong (should be exactly `ADMIN_CODE`)
- Railway hasn't redeployed after adding variable

**Solutions:**

1. **Verify Variable in Railway:**
   - Railway Dashboard → Project → Variables
   - Should see: `ADMIN_CODE` = `1234567890123939` (or with dashes)

2. **Redeploy:**
   - After adding/changing `ADMIN_CODE`, Railway should auto-redeploy
   - Or trigger manual redeploy

3. **Check Variable Format:**
   - Railway stores it as-is
   - If you set `1234-5678-9012-3939`, it stores with dashes
   - If you set `1234567890123939`, it stores without dashes
   - Both work! ✅

## Step-by-Step Setup

### 1. Set Admin Code in Railway

1. Go to **Railway Dashboard**
2. Click your **Project**
3. Click **Variables** tab
4. Click **+ New Variable**
5. Add:
   - **Name:** `ADMIN_CODE`
   - **Value:** `1234567890123939` (your 16-digit code, with or without dashes)
6. Click **Add**

### 2. Wait for Redeploy

- Railway will automatically redeploy
- Check deployment logs to confirm

### 3. Test Registration

1. Go to your Railway app URL
2. Click "Create New Account"
3. Fill in registration form
4. Enter admin code: `1234-5678-9012-3939` (or `1234567890123939`)
5. Submit

### 4. Verify Admin Status

1. Login with your new account
2. Check if you have admin privileges
3. Look for admin panel or admin features

## Testing Admin Code

Run this script to test your admin code setup:

```bash
python test_admin_code.py
```

This will show:
- What `ADMIN_CODE` is set to
- Which codes are valid
- Which codes are invalid

## Quick Reference

| Scenario | Code to Use |
|----------|-------------|
| `ADMIN_CODE` not set in Railway | `1234-5678-9012-3456` (default) |
| `ADMIN_CODE` = `1234567890123939` | `1234-5678-9012-3939` or `1234567890123939` |
| `ADMIN_CODE` = `1234-5678-9012-3939` | `1234-5678-9012-3939` or `1234567890123939` |
| Want regular user account | Leave field blank |

## Still Having Issues?

1. **Check Railway Logs:**
   - Railway → Deployments → View Logs
   - Look for errors or warnings

2. **Verify Environment Variables:**
   - Railway → Variables
   - Make sure `ADMIN_CODE` exists
   - Check `DATABASE_URL` is set (should be automatic)

3. **Test Code Validation:**
   ```bash
   python test_admin_code.py
   ```

4. **Check Code Format:**
   - Must be exactly 16 digits
   - Numbers only (0-9)
   - Dashes/spaces are optional

## Example: Your Setup

Based on your message:
- You set: `1234-5678-9012-3939` in Railway
- Use this code: `1234-5678-9012-3939` or `1234567890123939`
- Make sure you're testing on **Railway URL**, not locally!

