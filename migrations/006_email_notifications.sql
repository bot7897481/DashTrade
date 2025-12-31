-- Migration 006: Email Notification Preferences
-- Adds email notification settings for trade alerts

-- Add notification columns to users table if they don't exist
DO $$
BEGIN
    -- Email notifications master toggle
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'users' AND column_name = 'email_notifications_enabled') THEN
        ALTER TABLE users ADD COLUMN email_notifications_enabled BOOLEAN DEFAULT FALSE;
    END IF;

    -- Notify on trade execution
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'users' AND column_name = 'notify_on_trade') THEN
        ALTER TABLE users ADD COLUMN notify_on_trade BOOLEAN DEFAULT TRUE;
    END IF;

    -- Notify on trade errors
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'users' AND column_name = 'notify_on_error') THEN
        ALTER TABLE users ADD COLUMN notify_on_error BOOLEAN DEFAULT TRUE;
    END IF;

    -- Notify on risk limit hit
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'users' AND column_name = 'notify_on_risk_event') THEN
        ALTER TABLE users ADD COLUMN notify_on_risk_event BOOLEAN DEFAULT TRUE;
    END IF;

    -- Daily summary email
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'users' AND column_name = 'notify_daily_summary') THEN
        ALTER TABLE users ADD COLUMN notify_daily_summary BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- Create email log table to track sent emails
CREATE TABLE IF NOT EXISTS email_notifications_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    email_type VARCHAR(50) NOT NULL,  -- trade_executed, trade_error, risk_event, daily_summary
    subject VARCHAR(255),
    recipient_email VARCHAR(255),
    trade_id INTEGER REFERENCES bot_trades(id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'sent',  -- sent, failed, queued
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for quick lookups
CREATE INDEX IF NOT EXISTS idx_email_log_user_id ON email_notifications_log(user_id);
CREATE INDEX IF NOT EXISTS idx_email_log_created_at ON email_notifications_log(created_at);

COMMENT ON COLUMN users.email_notifications_enabled IS 'Master toggle for all email notifications';
COMMENT ON COLUMN users.notify_on_trade IS 'Send email when trade is executed';
COMMENT ON COLUMN users.notify_on_error IS 'Send email when trade fails';
COMMENT ON COLUMN users.notify_on_risk_event IS 'Send email when risk limit is hit';
COMMENT ON COLUMN users.notify_daily_summary IS 'Send daily trading summary email';
