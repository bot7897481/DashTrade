# Fix Admin Login Issue on Railway

## Quick Fix

If you can't login with `admin` / `Admin123`, run this script on Railway:

### Option 1: Railway Shell (Recommended)

1. Go to your Railway dashboard
2. Click on your project
3. Click on the **"View Logs"** or **"Shell"** button
4. Run:
   ```bash
   python fix_admin_login.py
   ```

### Option 2: Railway Console

1. Go to Railway dashboard → Your Project → **Deployments**
2. Click on the latest deployment
3. Open the **Console** tab
4. Run:
   ```bash
   python fix_admin_login.py
   ```

### Option 3: Add to Release Command (Temporary)

If the above doesn't work, you can temporarily modify your `Procfile`:

```
release: python finalize_setup.py && python fix_admin_login.py
```

Then push to GitHub and Railway will redeploy.

## What the Script Does

The `fix_admin_login.py` script will:

1. ✅ Check if database tables exist
2. ✅ Find or create admin user
3. ✅ Reset password to `Admin123`
4. ✅ Ensure account is active
5. ✅ Test authentication
6. ✅ Provide detailed diagnostics

## Expected Output

You should see:
```
✅ ADMIN LOGIN FIXED SUCCESSFULLY!
📝 Login Credentials:
   Username: admin
   Password: Admin123
```

## After Running the Script

1. Go to your Railway app URL
2. Login with:
   - **Username:** `admin`
   - **Password:** `Admin123`

## If It Still Doesn't Work

1. Check Railway logs for errors
2. Verify `DATABASE_URL` is set in Railway variables
3. Check if PostgreSQL service is running
4. Run `debug_admin_login.py` for more diagnostics:
   ```bash
   python debug_admin_login.py
   ```

## Alternative: Manual Database Update

If you have direct database access, you can manually update:

```sql
UPDATE users 
SET password_hash = '$2b$12$...' -- bcrypt hash of 'Admin123'
WHERE username = 'admin';
```

But the script is easier and safer!




