# How to Fix Password Reset Email Issue

## Problem
Password reset emails are not being sent because SMTP credentials are not configured in Railway.

## Solution: Configure SMTP in Railway

### Step 1: Set Up Gmail App Password (Recommended)

If you're using Gmail:

1. Go to your Google Account: https://myaccount.google.com/
2. Click **Security** in the left sidebar
3. Enable **2-Step Verification** (if not already enabled)
4. After enabling 2FA, go back to Security
5. Search for "App passwords" or go to: https://myaccount.google.com/apppasswords
6. Select "Mail" and your device
7. Click **Generate**
8. Copy the 16-character password (save it securely)

### Step 2: Add Environment Variables to Railway

1. Go to Railway Dashboard: https://railway.app/dashboard
2. Select your project: **DashTrade**
3. Click on your **API service**
4. Go to the **Variables** tab
5. Add these variables:

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
```

**Important Notes:**
- For Gmail, use port `587` with TLS
- Use the **App Password** (16 characters), NOT your regular Gmail password
- Replace `your-email@gmail.com` with your actual Gmail address

### Step 3: Alternative Email Providers

#### Using Outlook/Hotmail:
```
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_EMAIL=your-email@outlook.com
SMTP_PASSWORD=your-password
```

#### Using SendGrid:
```
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_EMAIL=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

#### Using Mailgun:
```
SMTP_SERVER=smtp.mailgun.org
SMTP_PORT=587
SMTP_EMAIL=your-mailgun-email
SMTP_PASSWORD=your-mailgun-password
```

### Step 4: Redeploy Your Service

After adding the environment variables:
1. Railway will automatically redeploy your service
2. Wait for deployment to complete (check the "Deployments" tab)
3. The service will now have access to SMTP credentials

### Step 5: Test the Password Reset

Once deployed, test it:

**Option A: Using the test script**
```bash
python3 test_password_reset_api.py https://your-railway-app.railway.app
```

**Option B: Using curl**
```bash
curl -X POST https://your-railway-app.railway.app/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"your-test-email@example.com"}'
```

**Option C: From your frontend**
- Go to your login page
- Click "Forgot Password"
- Enter your email
- Check your inbox (and spam folder)

### Step 6: Verify in Railway Logs

1. Go to Railway Dashboard → Your Service → Deployments
2. Click on the latest deployment
3. View logs and look for:
   - ✅ `Password reset email sent to [email]` = Success
   - ❌ `⚠️ SMTP credentials not configured` = Variables not set
   - ❌ `Failed to send email` = Wrong credentials

## Troubleshooting

### Issue: "SMTP credentials not configured"
- **Solution**: Environment variables are not set in Railway. Go back to Step 2.

### Issue: "Failed to send email"
- **Cause**: Wrong credentials or email provider blocking
- **Solutions**:
  - For Gmail: Make sure you're using an App Password, not regular password
  - Check if 2FA is enabled (required for Gmail App Passwords)
  - Try a different email provider
  - Check Railway logs for specific error messages

### Issue: "Connection refused" or timeout
- **Cause**: Firewall or port issue
- **Solutions**:
  - Verify `SMTP_PORT=587` (not 465 or 25)
  - Make sure Railway allows outbound SMTP connections

### Issue: Email goes to spam
- **Solution**: This is normal for first-time emails. Check your spam folder.

### Issue: Token expired
- **Cause**: Reset tokens expire after 1 hour
- **Solution**: Request a new password reset

## Security Best Practices

1. ✅ Use App Passwords (for Gmail/Outlook) instead of account passwords
2. ✅ Store credentials in Railway environment variables (never in code)
3. ✅ Enable 2FA on your email account
4. ✅ Use a dedicated email account for sending automated emails
5. ❌ Never commit SMTP credentials to git

## Next Steps

After configuring SMTP:
1. Test password reset from your frontend
2. Check spam folder for the email
3. Verify the reset link works
4. Update your frontend reset URL if needed

## Getting Help

If you're still having issues:
1. Check Railway logs for specific error messages
2. Run `python3 check_password_reset.py` to see token activity
3. Verify all 4 SMTP variables are set in Railway
4. Try a different email provider

## Quick Test Commands

**Check if API is running:**
```bash
curl https://your-railway-app.railway.app/health
```

**Test forgot password:**
```bash
curl -X POST https://your-railway-app.railway.app/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
```

Expected response:
```json
{
  "success": true,
  "message": "If the email exists, a password reset link has been sent"
}
```
