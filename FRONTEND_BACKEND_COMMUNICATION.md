# Frontend-Backend Communication Guide

## Architecture Overview

Your application has a **split architecture**:

- **Frontend**: React app hosted on Lovable (`https://alert-to-action-bot.lovable.app`)
- **Backend API**: Flask server running on Railway (port 8081, or Railway's PORT env var)

## How Frontend Talks to Backend

### 1. API Base URL Configuration

The frontend needs to know where your backend API is hosted. You need to configure the API base URL in your Lovable frontend.

**Backend API URL Format:**
```
https://your-railway-app.railway.app
```

Or if Railway provides a custom domain:
```
https://api.yourdomain.com
```

### 2. Frontend API Calls

Your frontend should make HTTP requests to the backend like this:

#### Example: Password Reset Request

```javascript
// In your Lovable frontend
const API_BASE_URL = 'https://your-railway-app.railway.app'; // Set this in your frontend config

// Forgot Password
async function forgotPassword(email) {
  const response = await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email: email })
  });
  
  const data = await response.json();
  return data;
}

// Reset Password
async function resetPassword(token, newPassword) {
  const response = await fetch(`${API_BASE_URL}/api/auth/reset-password`, {
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
  return data;
}
```

### 3. CORS Configuration

The backend is already configured to accept requests from any origin:

```python
# In api_server.py
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
```

This means your Lovable frontend can make requests to the Railway backend without CORS issues.

## Password Reset Flow

### Step 1: User Requests Password Reset

**Frontend → Backend:**
```
POST https://your-railway-app.railway.app/api/auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Backend Response:**
```json
{
  "success": true,
  "message": "If the email exists, a password reset link has been sent"
}
```

**What Backend Does:**
1. Generates a secure reset token
2. Stores token in `password_reset_tokens` table (expires in 1 hour)
3. Sends email with reset link: `https://alert-to-action-bot.lovable.app/reset-password?token=TOKEN`

### Step 2: User Clicks Reset Link

The user receives an email and clicks the link, which takes them to:
```
https://alert-to-action-bot.lovable.app/reset-password?token=abc123...
```

### Step 3: Frontend Extracts Token and Shows Reset Form

```javascript
// In your reset password page component
const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get('token');

// Show form with token
```

### Step 4: User Submits New Password

**Frontend → Backend:**
```
POST https://your-railway-app.railway.app/api/auth/reset-password
Content-Type: application/json

{
  "token": "abc123...",
  "new_password": "newSecurePassword123"
}
```

**Backend Response (Success):**
```json
{
  "success": true,
  "message": "Password has been reset successfully"
}
```

**Backend Response (Error):**
```json
{
  "success": false,
  "error": "Invalid or expired reset token"
}
```

## Finding Your Railway API URL

1. **Go to Railway Dashboard**
   - Open your Railway project
   - Click on your API service (the one running `api_server.py`)

2. **Check Settings → Networking**
   - Look for "Public Domain" or "Custom Domain"
   - Copy the URL (e.g., `https://your-app.railway.app`)

3. **Or Check Environment Variables**
   - Railway automatically sets `RAILWAY_PUBLIC_DOMAIN`
   - You can also check the deployment logs

## Common Issues & Solutions

### Issue 1: "Network Error" or "Failed to Fetch"

**Problem:** Frontend can't reach the backend API

**Solutions:**
- ✅ Verify Railway API service is running (check Railway dashboard)
- ✅ Check the API base URL in your frontend config
- ✅ Test the API directly: `curl https://your-railway-app.railway.app/health`
- ✅ Check Railway logs for errors

### Issue 2: "CORS Error"

**Problem:** Browser blocks the request due to CORS

**Solutions:**
- ✅ Backend already allows all origins (`origins: "*"`)
- ✅ Make sure you're using the correct API URL
- ✅ Check browser console for specific CORS error

### Issue 3: "404 Not Found"

**Problem:** API endpoint doesn't exist

**Solutions:**
- ✅ Verify endpoint path: `/api/auth/forgot-password` (not `/forgot-password`)
- ✅ Check Railway logs to see if the route is registered
- ✅ Test with: `curl -X POST https://your-railway-app.railway.app/api/auth/forgot-password -H "Content-Type: application/json" -d '{"email":"test@example.com"}'`

### Issue 4: Password Reset Email Not Received

**Problem:** Email not being sent

**Solutions:**
- ✅ Check Railway logs for email sending errors
- ✅ Verify SMTP credentials are set in Railway environment variables:
  - `SMTP_SERVER`
  - `SMTP_PORT`
  - `SMTP_EMAIL`
  - `SMTP_PASSWORD`
- ✅ Check spam/junk folder
- ✅ Verify email address exists in database

### Issue 5: "Invalid or Expired Token"

**Problem:** Token validation fails

**Solutions:**
- ✅ Tokens expire after 1 hour
- ✅ Tokens can only be used once
- ✅ Check if token was already used
- ✅ Verify token format in URL

## Testing the API Endpoints

### Test Forgot Password

```bash
curl -X POST https://your-railway-app.railway.app/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com"}'
```

Expected response:
```json
{
  "success": true,
  "message": "If the email exists, a password reset link has been sent"
}
```

### Test Reset Password

```bash
curl -X POST https://your-railway-app.railway.app/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your-token-here",
    "new_password": "newPassword123"
  }'
```

Expected response (success):
```json
{
  "success": true,
  "message": "Password has been reset successfully"
}
```

## Frontend Implementation Checklist

- [ ] Set API base URL in frontend config/environment variables
- [ ] Create forgot password form that calls `/api/auth/forgot-password`
- [ ] Create reset password page at `/reset-password` route
- [ ] Extract token from URL query parameter
- [ ] Create reset password form that calls `/api/auth/reset-password`
- [ ] Handle success/error responses from API
- [ ] Show appropriate messages to user
- [ ] Redirect to login page after successful reset

## Backend API Endpoints Summary

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register` | Create new account | No |
| POST | `/api/auth/login` | Get JWT token | No |
| GET | `/api/auth/me` | Get current user | Yes |
| POST | `/api/auth/forgot-password` | Request password reset | No |
| POST | `/api/auth/reset-password` | Reset password with token | No |

### Request/Response Examples

**Register:**
```json
POST /api/auth/register
{
  "username": "john",
  "email": "john@example.com",
  "password": "password123",
  "full_name": "John Doe"
}
```

**Login:**
```json
POST /api/auth/login
{
  "username": "john",
  "password": "password123"
}

Response:
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "john",
    "email": "john@example.com"
  }
}
```

**Authenticated Requests:**
```javascript
// Include token in Authorization header
fetch(`${API_BASE_URL}/api/auth/me`, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
```

## Next Steps

1. **Find your Railway API URL** and configure it in Lovable
2. **Test the endpoints** using curl or Postman
3. **Implement the frontend** following the examples above
4. **Check Railway logs** if something doesn't work
5. **Verify email configuration** for password reset emails

## Need Help?

- Check Railway deployment logs
- Test API endpoints directly with curl
- Verify environment variables in Railway
- Check browser console for frontend errors
- Review Railway service status

