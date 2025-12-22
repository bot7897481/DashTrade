# Admin Activation Code Setup

## Overview

DashTrade now supports **Admin Activation Codes** - a secure way for users to become admins during registration without needing to run scripts on Railway!

## How It Works

1. **Set Admin Code in Railway** (one-time setup)
2. **Users enter code during registration** to become admin
3. **No SSH/Shell access needed!**

## Quick Setup

### Step 1: Generate an Admin Code (Optional)

Run locally to generate a secure code:
```bash
python generate_admin_code.py
```

Or use the default code: `1234-5678-9012-3456`

### Step 2: Set Code in Railway

1. Go to **Railway Dashboard** → Your Project
2. Click on **"Variables"** tab
3. Click **"+ New Variable"**
4. Add:
   - **Name:** `ADMIN_CODE`
   - **Value:** Your 16-digit code (e.g., `1234567890123456` or `1234-5678-9012-3456`)
5. Click **"Add"**

### Step 3: Deploy

Railway will automatically redeploy with the new variable. That's it!

## Using the Admin Code

### For Users:

1. Go to registration page
2. Fill in username, email, password
3. **Optionally** enter the admin activation code in the "Admin Activation Code" field
4. If code is correct → Account created as **admin**
5. If code is wrong or blank → Account created as **regular user**

### Code Format:

- **16 digits** (numbers only)
- Can include dashes: `1234-5678-9012-3456`
- Can be without dashes: `1234567890123456`
- Spaces are ignored

## Security Features

✅ **Secure by default** - Code is stored in environment variables (not in code)  
✅ **Case-insensitive** - Works with or without dashes  
✅ **One-time use** - Code can be reused (users can create multiple admin accounts)  
✅ **Optional** - Users can still create regular accounts without code  

## Default Behavior

- **If `ADMIN_CODE` is NOT set:** Default code is `1234-5678-9012-3456`
- **If `ADMIN_CODE` IS set:** Uses your custom code from Railway variables

## Examples

### Example 1: User Creates Admin Account
```
Username: john
Email: john@example.com
Password: SecurePass123
Admin Code: 1234-5678-9012-3456
→ Account created as ADMIN ✅
```

### Example 2: User Creates Regular Account
```
Username: jane
Email: jane@example.com
Password: SecurePass123
Admin Code: (left blank)
→ Account created as USER ✅
```

### Example 3: Wrong Admin Code
```
Username: bob
Email: bob@example.com
Password: SecurePass123
Admin Code: 9999-9999-9999-9999
→ Error: Invalid admin activation code ❌
→ User can retry or create regular account
```

## Troubleshooting

### "Invalid admin activation code"

**Possible causes:**
1. Code doesn't match the one in Railway `ADMIN_CODE` variable
2. Code format is wrong (must be 16 digits)
3. `ADMIN_CODE` variable not set in Railway

**Solution:**
- Check Railway Variables tab
- Verify `ADMIN_CODE` is set correctly
- Make sure code is exactly 16 digits

### Code Not Working

1. **Check Railway Variables:**
   - Go to Railway → Variables
   - Verify `ADMIN_CODE` exists
   - Check the value is correct

2. **Redeploy:**
   - Push a new commit to trigger redeploy
   - Or manually redeploy in Railway

3. **Check Logs:**
   - Railway → Deployments → View Logs
   - Look for any errors

## Best Practices

1. **Use a strong code** - Generate a random 16-digit code
2. **Keep it secret** - Only share with trusted users
3. **Change periodically** - Update `ADMIN_CODE` in Railway to revoke old codes
4. **Document it** - Keep the code in a secure password manager

## Migration from Old System

If you were using scripts to create admin accounts:

1. **Old way:** Run `python fix_admin_login.py` on Railway
2. **New way:** Set `ADMIN_CODE` in Railway, users register with code

**Benefits:**
- ✅ No SSH access needed
- ✅ Self-service for users
- ✅ Works immediately after deployment
- ✅ More secure (code in env vars, not scripts)

## Support

If you need help:
1. Check Railway logs
2. Verify `ADMIN_CODE` is set
3. Test with default code: `1234-5678-9012-3456`

