# DashTrade Authentication Setup Guide

## Overview

DashTrade now includes a complete authentication system to secure your trading dashboard and provide multi-user support with data isolation.

## Features

- **Secure Login System**: Username and password authentication with bcrypt hashing
- **User Registration**: Self-service account creation
- **Data Isolation**: Each user has their own watchlist, alerts, and preferences
- **Session Management**: Secure session handling with logout functionality
- **Password Security**: Minimum 6 characters with bcrypt encryption

## Setup Instructions

### Step 1: Install Dependencies

The required dependencies have already been added to `pyproject.toml`:
- `bcrypt>=4.0.1` - Password hashing
- `streamlit-authenticator>=0.3.3` - Authentication components

Install them using:
```bash
pip install -e .
```

Or if using Poetry:
```bash
poetry install
```

### Step 2: Run Database Migration

**IMPORTANT**: Run this migration script **ONCE** to update your database schema:

```bash
python migrate_database.py
```

This script will:
1. Create the `users` table
2. Add `user_id` column to existing tables (watchlist, alerts, user_preferences)
3. Update constraints and indexes
4. Preserve existing data (if any)

**Note**: Existing data will remain in the database but won't be visible until assigned to a user. Consider it archived/legacy data.

### Step 3: Start the Application

Run the application normally:
```bash
streamlit run app.py
```

## Usage

### First Time Setup

1. **Access the Application**: Navigate to your Streamlit URL
2. **Register**: Click "Create New Account"
3. **Fill Registration Form**:
   - Username (minimum 3 characters)
   - Email address
   - Full name (optional)
   - Password (minimum 6 characters)
   - Confirm password
4. **Login**: After registration, return to login page and enter credentials

### Daily Usage

1. **Login**: Enter your username and password
2. **Access Dashboard**: Full access to all trading features
3. **Logout**: Click the "🚪 Logout" button in the sidebar when done

### Your Data

Each user has completely isolated:
- **Watchlist**: Your personal stock watchlist
- **Alerts**: Your custom price and indicator alerts
- **Preferences**: Your personal settings and configurations

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### Updated Tables
All data tables now include `user_id`:
- `watchlist` - Stocks tracked by each user
- `alerts` - Price and indicator alerts per user
- `user_preferences` - User-specific settings

## Security Features

1. **Password Hashing**: All passwords encrypted with bcrypt
2. **No Plain Text Storage**: Passwords never stored in plain text
3. **Session Management**: Secure session state handling
4. **User Isolation**: Database-level data separation
5. **Input Validation**: Username, email, and password requirements

## Troubleshooting

### Migration Issues

**Error: "DATABASE_URL not set"**
```bash
export DATABASE_URL="postgresql://user:password@host:port/database"
```

**Error: "Table already exists"**
- Safe to ignore if migration was run before
- Script is idempotent (safe to run multiple times)

### Login Issues

**"Invalid username or password"**
- Check username spelling (case-insensitive)
- Verify password is correct
- Try password reset (future feature)

**"Account is disabled"**
- Contact administrator to reactivate account

### Registration Issues

**"Username already exists"**
- Choose a different username
- Usernames must be unique across all users

**"Email already registered"**
- Use a different email address
- Check if you already have an account

## Files Added/Modified

### New Files
- `auth.py` - Authentication module with UserDB class
- `migrate_database.py` - Database migration script
- `AUTHENTICATION_SETUP.md` - This setup guide

### Modified Files
- `app.py` - Added login/register UI and authentication checks
- `database.py` - Updated all methods to include user_id parameter
- `pyproject.toml` - Added bcrypt and streamlit-authenticator dependencies

## Development Notes

### Adding User-Specific Features

When adding new database tables, always include `user_id`:
```python
CREATE TABLE new_table (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    -- other columns
)
```

### Accessing Current User

In the main app, user information is available via:
```python
user_id = st.session_state['user']['id']
username = st.session_state['user']['username']
email = st.session_state['user']['email']
```

## Future Enhancements

Potential authentication improvements:
- [ ] Password reset functionality
- [ ] Email verification
- [ ] Two-factor authentication (2FA)
- [ ] OAuth integration (Google, GitHub)
- [ ] Admin panel for user management
- [ ] Role-based access control (RBAC)
- [ ] Session timeout settings
- [ ] Password strength meter
- [ ] Account deletion/deactivation

## Support

If you encounter issues:
1. Check the migration script output for errors
2. Verify DATABASE_URL is correctly set
3. Ensure PostgreSQL is running and accessible
4. Check application logs for detailed error messages

## Security Best Practices

1. **Environment Variables**: Store DATABASE_URL in environment variables, never commit to git
2. **Strong Passwords**: Enforce password complexity in production
3. **HTTPS**: Always use HTTPS in production deployments
4. **Regular Updates**: Keep dependencies updated for security patches
5. **Backup**: Regular database backups to prevent data loss

---

**Authentication System Version**: 1.0
**Last Updated**: 2025-10-28
**Compatible with**: DashTrade v1.0+
