-- DashTrade Database Setup Script
-- Run this as postgres user: sudo -u postgres psql < database_setup.sql

-- Create database
CREATE DATABASE IF NOT EXISTS dashtrade;

-- Create user
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'dashtrade_user') THEN
        CREATE USER dashtrade_user WITH PASSWORD 'DashTrade2024!';
    END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE dashtrade TO dashtrade_user;

-- Connect to database
\c dashtrade

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO dashtrade_user;

-- Create tables (if database.py doesn't auto-create them)
CREATE TABLE IF NOT EXISTS watchlist (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(255),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    condition_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    triggered_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS user_preferences (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant table privileges
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dashtrade_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO dashtrade_user;

-- Insert default preferences
INSERT INTO user_preferences (key, value) VALUES
    ('account_balance', '10000.0'),
    ('risk_per_trade', '2.0')
ON CONFLICT (key) DO NOTHING;

\echo 'Database setup completed successfully!'
