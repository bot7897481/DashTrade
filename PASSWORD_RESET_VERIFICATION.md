# Password Reset Verification Guide

## ✅ Confirmed Working

- **Backend API URL**: `https://overflowing-spontaneity-production.up.railway.app`
- **Connection Status**: ✅ Working (401 response confirms server is alive)
- **Frontend-Backend Communication**: ✅ Configured correctly

## Password Reset Endpoints

### 1. Forgot Password Endpoint

**URL:** `POST https://overflowing-spontaneity-production.up.railway.app/api/auth/forgot-password`

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Expected Response (Success):**
```json
{
  "success": true,
  "message": "If the email exists, a password reset link has been sent"
}
```

**Expected Response (Email Send Failed):**
```json
{
  "success": false,
  "error": "Failed to send reset email. Please try again later."
}
```

### 2. Reset Password Endpoint

**URL:** `POST https://overflowing-spontaneity-production.up.railway.app/api/auth/reset-password`

**Request:**
```json
{
  "token": "reset-token-from-email",
  "new_password": "newSecurePassword123"
}
```

**Expected Response (Success):**
```json
{
  "success": true,
  "message": "Password has been reset successfully"
}
```

**Expected Response (Error):**
```json
{
  "success": false,
  "error": "Invalid or expired reset token"
}
```

## Testing from Frontend (Lovable)

### Test Forgot Password

In your Lovable frontend, test with this code:

```javascript
const API_URL = 'https://overflowing-spontaneity-production.up.railway.app';

async function testForgotPassword() {
  try {
    const response = await fetch(`${API_URL}/api/auth/forgot-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: 'your-email@example.com'
      })
    });
    
    const data = await response.json();
    console.log('Response:', data);
    
    if (data.success) {
      alert('Password reset email sent! Check your inbox.');
    } else {
      alert(`Error: ${data.error || 'Unknown error'}`);
    }
  } catch (error) {
    console.error('Error:', error);
    alert(`Network error: ${error.message}`);
  }
}
```

### Test Reset Password

```javascript
async function testResetPassword(token, newPassword) {
  try {
    const response = await fetch(`${API_URL}/api/auth/reset-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        token: token,
        new_password: newPassword
      })
    });
    
    const data = await response.json();
    console.log('Response:', data);
    
    if (data.success) {
      alert('Password reset successful!');
      // Redirect to login page
    } else {
      alert(`Error: ${data.error || 'Unknown error'}`);
    }
  } catch (error) {
    console.error('Error:', error);
    alert(`Network error: ${error.message}`);
  }
}
```

## Common Issues & Solutions

### Issue 1: "Failed to send reset email"

**Check Railway Logs:**
1. Go to Railway Dashboard → Your Project → API Service
2. Click "View Logs" or "Deployments" → Latest → Logs
3. Look for:
   - `Password reset email sent to [email]` ✅
   - `Failed to send password reset email` ❌
   - `Error sending password reset email: [details]` ❌

**Check SMTP Configuration:**
Verify these environment variables are set in Railway:
- `SMTP_SERVER` (e.g., `smtp.gmail.com`)
- `SMTP_PORT` (e.g., `587`)
- `SMTP_EMAIL` (your sender email)
- `SMTP_PASSWORD` (your email password or app password)

**Solution:**
If SMTP is not configured, the endpoint will return:
```json
{
  "success": false,
  "error": "Failed to send reset email. Please try again later."
}
```

### Issue 2: Email Not Received

**Check:**
1. ✅ Inbox (wait 1-2 minutes)
2. ✅ Spam/Junk folder
3. ✅ Email address is correct
4. ✅ Email exists in database

**Verify Token Was Created:**
Run this on Railway (Shell/Console):
```bash
python3 check_password_reset.py
```

This shows if a token was created for your email.

### Issue 3: "Invalid or expired reset token"

**Causes:**
- Token expired (tokens expire after 1 hour)
- Token already used (tokens can only be used once)
- Invalid token format
- Token doesn't exist in database

**Solution:**
Request a new password reset to get a fresh token.

### Issue 4: Frontend Not Calling Endpoint

**Check:**
1. Browser console for errors
2. Network tab in DevTools to see if request is sent
3. Request URL is correct: `/api/auth/forgot-password` (not `/forgot-password`)
4. Content-Type header is set: `application/json`

## Verification Checklist

- [ ] API server is running (health check returns 200)
- [ ] Frontend can reach backend (login endpoint returns 401 for invalid creds)
- [ ] Forgot password endpoint exists and is accessible
- [ ] SMTP credentials are configured in Railway
- [ ] Email is being sent (check Railway logs)
- [ ] Token is created in database (run `check_password_reset.py`)
- [ ] Reset password endpoint validates tokens correctly
- [ ] Frontend extracts token from URL correctly
- [ ] Frontend calls reset endpoint with correct payload

## Debugging Steps

### Step 1: Test Endpoint Directly

Use browser console or Postman:

```javascript
// In browser console on your frontend
fetch('https://overflowing-spontaneity-production.up.railway.app/api/auth/forgot-password', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'your-email@example.com' })
})
.then(r => r.json())
.then(console.log)
.catch(console.error);
```

### Step 2: Check Railway Logs

After making the request, immediately check Railway logs for:
- Request received
- Token generated
- Email sent status

### Step 3: Verify Database

Check if token was created:
```bash
# On Railway Shell/Console
python3 check_password_reset.py
```

### Step 4: Test Email Configuration

If email isn't sending, test SMTP separately or check Railway logs for SMTP errors.

## Expected Flow

1. **User clicks "Forgot Password"** → Frontend calls `/api/auth/forgot-password`
2. **Backend generates token** → Stores in `password_reset_tokens` table
3. **Backend sends email** → With link: `https://alert-to-action-bot.lovable.app/reset-password?token=TOKEN`
4. **User clicks link** → Frontend extracts token from URL
5. **User enters new password** → Frontend calls `/api/auth/reset-password` with token and password
6. **Backend validates token** → Checks expiration and usage
7. **Backend updates password** → Marks token as used
8. **User redirected to login** → Can login with new password

## Next Steps

1. **Test the forgot password endpoint** from your frontend
2. **Check Railway logs** immediately after the request
3. **Verify SMTP configuration** if email isn't sending
4. **Check your email** (including spam folder)
5. **Test the reset password endpoint** with a valid token

If you're still having issues, share:
- What error message you're seeing
- Railway logs output
- Browser console errors
- Network request details from DevTools

