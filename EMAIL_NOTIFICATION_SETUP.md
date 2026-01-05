# Email Notification Setup - Order Submitted Alerts

## ✅ What Was Added

Email notifications are now sent automatically when orders are **submitted** (BUY, SELL, or CLOSE).

---

## 🔧 Implementation

### Email Service Integration

**File:** `bot_engine.py`

**Added:**
- Import of `TradeNotificationService` from `email_service.py`
- Email notification calls after each order is submitted:
  - ✅ BUY orders
  - ✅ SELL orders  
  - ✅ CLOSE orders

### How It Works

1. **Order Submitted** → Email notification sent immediately
2. **User Preferences Checked** → Email service checks:
   - `email_notifications_enabled` = true
   - `notify_on_trade` = true
3. **Email Sent** → If both are enabled, email is sent
4. **Logged** → Email is logged to `email_notifications_log` table

---

## 📧 Email Content

### Email Subject
- **BUY:** `🟢 Trade Executed: BUY BTC/USD`
- **SELL:** `🔴 Trade Executed: SELL BTC/USD`
- **CLOSE:** `🟡 Trade Executed: CLOSE BTC/USD`

### Email Body Includes:
- Symbol (e.g., BTC/USD)
- Action (BUY/SELL/CLOSE)
- Quantity (if available)
- Expected/Fill Price
- Status (SUBMITTED)
- Bot Name (Symbol + Timeframe)
- Order ID
- Timestamp

---

## ⚙️ User Preferences

### API Endpoint: `GET /api/settings/notifications`

**Response:**
```json
{
  "email": "user@example.com",
  "email_notifications_enabled": true,
  "notify_on_trade": true,
  "notify_on_error": true,
  "notify_on_risk_event": true,
  "notify_daily_summary": false
}
```

### Update Preferences: `PUT /api/settings/notifications`

**Request Body:**
```json
{
  "email_notifications_enabled": true,
  "notify_on_trade": true
}
```

**To Enable Order Notifications:**
- Set `email_notifications_enabled` = `true`
- Set `notify_on_trade` = `true`

---

## 🔐 Email Service Configuration

### Required Environment Variables

**For SMTP2GO (Recommended):**
```bash
SMTP2GO_API_KEY=your_api_key_here
EMAIL_FROM=notifications@novalgo.org
EMAIL_FROM_NAME=DashTrade
```

**For SMTP (Alternative):**
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

---

## 📋 Email Notification Flow

### When Order is Submitted:

```
1. Order submitted to Alpaca
   ↓
2. Check user notification settings
   ↓
3. If enabled:
   - Get user email
   - Build email template
   - Send via SMTP2GO/SMTP
   - Log to database
   ↓
4. Continue with trade logging
```

### Email Service Logic:

```python
# In email_service.py - send_trade_executed_email()
1. Get user settings from database
2. Check: email_notifications_enabled AND notify_on_trade
3. If both true → Send email
4. Log email to email_notifications_log table
```

---

## 🎯 Frontend Integration

### Enable/Disable Notifications

**Update User Settings:**
```javascript
// Enable order notifications
await fetch('/api/settings/notifications', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email_notifications_enabled: true,
    notify_on_trade: true
  })
});
```

**Check Current Settings:**
```javascript
const response = await fetch('/api/settings/notifications', {
  headers: { 'Authorization': `Bearer ${token}` }
});

const settings = await response.json();
// settings.notify_on_trade - true/false
// settings.email_notifications_enabled - true/false
```

---

## 📊 Email Logging

All emails are logged to `email_notifications_log` table:

**Fields:**
- `user_id` - User who received email
- `email_type` - 'trade_executed', 'trade_error', 'risk_event'
- `subject` - Email subject
- `recipient_email` - Email address
- `trade_id` - Related trade ID (if applicable)
- `status` - 'sent' or 'failed'
- `error_message` - Error details (if failed)
- `created_at` - Timestamp

---

## ✅ Testing

### Test Email Notification

**API Endpoint:** `POST /api/settings/notifications/test`

**Request:**
```json
{}
```

**Response:**
```json
{
  "success": true,
  "message": "Test email sent successfully"
}
```

---

## 🎨 Email Template

The email uses a professional HTML template with:
- ✅ Branded header (DashTrade)
- ✅ Color-coded action badges (Green for BUY, Red for SELL, Yellow for CLOSE)
- ✅ Trade details in organized layout
- ✅ Order ID and timestamp
- ✅ Link to manage preferences

---

## 📝 Summary

**What Happens Now:**
1. ✅ User enables `notify_on_trade` in frontend settings
2. ✅ Order is submitted (BUY/SELL/CLOSE)
3. ✅ Email notification sent immediately
4. ✅ Email logged to database

**Email Service:**
- ✅ Checks user preferences automatically
- ✅ Respects `email_notifications_enabled` flag
- ✅ Respects `notify_on_trade` flag
- ✅ Handles errors gracefully (won't break trading)

**No Action Required:**
- Email service is already configured
- Notifications work automatically
- User can enable/disable via frontend settings

---

## 🔧 Troubleshooting

### Emails Not Sending?

1. **Check Environment Variables:**
   - `SMTP2GO_API_KEY` must be set (or SMTP credentials)

2. **Check User Settings:**
   ```sql
   SELECT email_notifications_enabled, notify_on_trade 
   FROM users WHERE id = USER_ID;
   ```

3. **Check Email Logs:**
   ```sql
   SELECT * FROM email_notifications_log 
   WHERE user_id = USER_ID 
   ORDER BY created_at DESC;
   ```

4. **Check Logs:**
   - Look for "Failed to send email notification" warnings
   - Check Railway logs for SMTP errors

---

**Email notifications are now active!** Users will receive emails when orders are submitted, if they have notifications enabled in their settings. 📧✅

