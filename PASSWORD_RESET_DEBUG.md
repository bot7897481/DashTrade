# Password Reset Debugging Guide

## Quick Checklist

### 1. Verify API Server is Running

**Check Railway:**
- Go to Railway Dashboard → Your Project → API Service
- Verify service status is "Running" ✅
- Check deployment logs for errors

**Test Health Endpoint:**
```bash
curl https://your-railway-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "DashTrade API Server",
  "database": "connected"
}
```

### 2. Verify Frontend API Configuration

**In Lovable Frontend:**
- Check if `API_URL` or `API_BASE_URL` is configured
- Should point to: `https://your-railway-app.railway.app`
- NOT `http://localhost:8081` (that's only for local development)

**Example Configuration:**
```javascript
// In your frontend config file
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://your-railway-app.railway.app';
```

### 3. Test API Endpoints Directly

**Test Forgot Password:**
```bash
curl -X POST https://your-railway-app.railway.app/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com"}'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "If the email exists, a password reset link has been sent"
}
```

**If you get errors:**
- `Connection refused` → API server not running
- `404 Not Found` → Wrong URL or endpoint path
- `500 Internal Server Error` → Check Railway logs

### 4. Check Railway Logs

**View Logs:**
1. Railway Dashboard → Your Project → API Service
2. Click "View Logs" or "Deployments" → Latest → Logs
3. Look for:
   - `Password reset email sent to [email]` ✅ (success)
   - `Failed to send password reset email` ❌ (email issue)
   - `Error sending password reset email` ❌ (error details)

### 5. Verify Email Configuration

**Check Environment Variables in Railway:**
- `SMTP_SERVER` - Should be set (e.g., `smtp.gmail.com`)
- `SMTP_PORT` - Should be set (e.g., `587`)
- `SMTP_EMAIL` - Your sender email
- `SMTP_PASSWORD` - Your email password/app password

**Test Email Sending:**
The logs will show if email sending failed. Common issues:
- SMTP credentials not configured
- Email provider blocking the connection
- Invalid email address

### 6. Check Database

**Verify Token Was Created:**
Run this on Railway (in Shell/Console):
```bash
python3 check_password_reset.py
```

This will show:
- Recent password reset tokens
- Token status (active/used/expired)
- Associated user emails

### 7. Frontend Implementation Issues

**Common Frontend Problems:**

1. **Wrong API URL**
   ```javascript
   // ❌ WRONG (local development only)
   const API_URL = 'http://localhost:8081';
   
   // ✅ CORRECT (Railway production)
   const API_URL = 'https://your-railway-app.railway.app';
   ```

2. **Missing Content-Type Header**
   ```javascript
   // ❌ WRONG
   fetch(`${API_URL}/api/auth/forgot-password`, {
     method: 'POST',
     body: JSON.stringify({ email })
   })
   
   // ✅ CORRECT
   fetch(`${API_URL}/api/auth/forgot-password`, {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json'
     },
     body: JSON.stringify({ email })
   })
   ```

3. **Not Handling Errors**
   ```javascript
   // ✅ CORRECT
   try {
     const response = await fetch(`${API_URL}/api/auth/forgot-password`, {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ email })
     });
     
     const data = await response.json();
     
     if (!response.ok) {
       throw new Error(data.error || 'Request failed');
     }
     
     // Show success message
     alert(data.message);
   } catch (error) {
     // Show error message
     alert(`Error: ${error.message}`);
   }
   ```

## Step-by-Step Debugging

### Step 1: Test API Server Health

```bash
# Replace with your Railway URL
curl https://your-railway-app.railway.app/health
```

**If this fails:**
- API server is not running
- Wrong URL
- Railway service is down

### Step 2: Test Forgot Password Endpoint

```bash
curl -X POST https://your-railway-app.railway.app/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}' \
  -v
```

**Check the response:**
- Status 200 = Success ✅
- Status 400 = Bad request (check email format)
- Status 500 = Server error (check Railway logs)

### Step 3: Check Railway Logs

After making the request, immediately check Railway logs:
- Look for `Password reset email sent to...` ✅
- Look for `Failed to send password reset email` ❌
- Look for any error messages

### Step 4: Verify Email Was Sent

- Check your email inbox
- Check spam/junk folder
- Verify email address exists in database

### Step 5: Test Reset Password Endpoint

```bash
# Get token from email or database
curl -X POST https://your-railway-app.railway.app/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your-token-here",
    "new_password": "newPassword123"
  }'
```

## Common Error Messages

### "Network Error" or "Failed to Fetch"
- **Cause:** Frontend can't reach backend
- **Fix:** Check API URL, verify Railway service is running

### "CORS Error"
- **Cause:** Browser blocking cross-origin request
- **Fix:** Backend already allows all origins, check API URL

### "404 Not Found"
- **Cause:** Wrong endpoint path
- **Fix:** Use `/api/auth/forgot-password` (not `/forgot-password`)

### "500 Internal Server Error"
- **Cause:** Server-side error
- **Fix:** Check Railway logs for details

### "Failed to send reset email"
- **Cause:** SMTP configuration issue
- **Fix:** Verify SMTP credentials in Railway environment variables

### "Invalid or expired reset token"
- **Cause:** Token expired (1 hour) or already used
- **Fix:** Request a new password reset

## Getting Help

If you're still stuck:

1. **Check Railway Logs** - Most errors are logged there
2. **Test with curl** - Verify endpoints work outside frontend
3. **Check Browser Console** - Look for frontend errors
4. **Verify Environment Variables** - All required vars should be set
5. **Test Database Connection** - Run `check_password_reset.py`

## Quick Test Script

Use the provided test script:

```bash
# Set your Railway API URL
export API_URL=https://your-railway-app.railway.app

# Run tests
python3 test_password_reset_api.py
```

This will test:
- Health endpoint
- Forgot password endpoint
- Reset password endpoint

