# DashTrade Deployment Guide

Complete guide for deploying DashTrade with authentication to production.

## Prerequisites

- PostgreSQL database (local or cloud-hosted)
- Python 3.11+
- Git (for version control)

## Step-by-Step Deployment

### 1. Database Setup

You need a PostgreSQL database. Choose one of the following options:

#### Option A: Replit Built-in PostgreSQL (Recommended for Replit)

1. Your Replit project already has PostgreSQL enabled (see `.replit` file)
2. Go to your Replit project
3. Click on "Secrets" (🔒) in the left sidebar
4. Add a new secret:
   - **Key**: `DATABASE_URL`
   - **Value**: `postgresql://replit:password@localhost:5432/dashtrade`

#### Option B: Free Cloud PostgreSQL (Recommended for Production)

**Neon.tech (Recommended)**
1. Go to https://neon.tech
2. Sign up for free account
3. Create a new project
4. Copy the connection string
5. Add to Replit Secrets or environment variables

**Other Options:**
- **Supabase** (https://supabase.com) - 500 MB free
- **ElephantSQL** (https://elephantsql.com) - 20 MB free
- **Railway** (https://railway.app) - Free tier

#### Option C: Local PostgreSQL

```bash
# Install PostgreSQL
# macOS: brew install postgresql
# Ubuntu: sudo apt-get install postgresql

# Create database
createdb dashtrade

# Set environment variable
export DATABASE_URL='postgresql://username:password@localhost:5432/dashtrade'
```

### 2. Verify Database Connection

Run the setup checker:

```bash
python setup_database.py
```

You should see:
```
✓ DATABASE_URL is set
✓ Successfully connected to database!
✓ PostgreSQL version: PostgreSQL 16.x
```

### 3. Install Dependencies

```bash
# Using pip
pip install -e .

# Or using Poetry
poetry install
```

### 4. Run Database Migration

**IMPORTANT**: Run this only ONCE to set up the database schema:

```bash
python migrate_database.py
```

You'll be asked to confirm. Type `yes` to proceed.

Expected output:
```
1. Creating users table...
   ✓ Users table created
2. Migrating watchlist table...
   ✓ Added user_id column to watchlist
3. Migrating alerts table...
   ✓ Added user_id column to alerts
4. Migrating user_preferences table...
   ✓ Added user_id column to user_preferences
5. Creating indexes...
   ✓ Indexes created

✓ Migration completed successfully!
```

### 5. Configure Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and add your settings:
```env
DATABASE_URL=postgresql://user:password@host:5432/database
ALPHA_VANTAGE_API_KEY=your_key_here  # Optional
```

### 6. Start the Application

```bash
streamlit run app.py --server.port 5000
```

Or use the Replit Run button.

### 7. Create Your First User

1. Navigate to your app URL
2. Click "Create New Account"
3. Fill in:
   - Username (min 3 characters)
   - Email address
   - Full Name (optional)
   - Password (min 6 characters)
4. Click "Create Account"
5. Login with your credentials

## Security Configuration

### HTTPS Setup

#### For Replit Deployment

Replit automatically provides HTTPS for all deployed apps. No additional configuration needed!

#### For Custom Deployment (with Nginx)

Create Nginx configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Get free SSL certificate from Let's Encrypt:
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

#### For Docker Deployment

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - ALPHA_VANTAGE_API_KEY=${ALPHA_VANTAGE_API_KEY}
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: unless-stopped
```

### Security Best Practices

1. **Strong Passwords**
   - Enforce minimum 8 characters in production
   - Consider password complexity requirements

2. **Environment Variables**
   - Never commit `.env` file to git
   - Use Replit Secrets for sensitive data
   - Rotate database passwords regularly

3. **Database Security**
   - Use strong database passwords
   - Enable SSL for database connections
   - Limit database access by IP if possible

4. **Application Security**
   - XSRF protection is enabled in config
   - CORS is disabled for security
   - Session state is secure

5. **Regular Updates**
   - Keep dependencies updated
   - Monitor security advisories
   - Update PostgreSQL regularly

## Production Checklist

Before going live, verify:

- [ ] DATABASE_URL is set correctly
- [ ] Database migration completed successfully
- [ ] Can create a test user account
- [ ] Can login with test credentials
- [ ] HTTPS is enabled (automatic on Replit)
- [ ] Environment variables are in Secrets (not in code)
- [ ] `.env` file is in `.gitignore`
- [ ] Created a backup strategy for database
- [ ] Tested all features (watchlist, alerts, analysis)
- [ ] Set up monitoring/logging (optional)

## Replit-Specific Setup

### Using Replit Secrets

1. Click the lock icon 🔒 in left sidebar
2. Add secrets:
   ```
   DATABASE_URL=postgresql://...
   ALPHA_VANTAGE_API_KEY=your_key
   ```

3. Access in Python:
   ```python
   import os
   db_url = os.getenv('DATABASE_URL')
   ```

### Replit Always-On

For 24/7 availability:
1. Upgrade to Replit Hacker plan
2. Enable "Always On" for your Repl
3. Your app will never sleep

### Custom Domain (Replit)

1. Go to your Repl settings
2. Click on "Domains"
3. Add your custom domain
4. Configure DNS records as shown
5. HTTPS is automatic!

## Troubleshooting

### "DATABASE_URL not set"
```bash
# Check if set
echo $DATABASE_URL

# Set temporarily
export DATABASE_URL='postgresql://...'

# Add to Replit Secrets for persistence
```

### "Could not connect to database"
- Verify PostgreSQL is running
- Check connection string format
- Ensure database exists
- Check firewall rules

### "Migration failed"
- Ensure DATABASE_URL is correct
- Check database permissions
- Verify PostgreSQL version (16+ recommended)
- Try running migration again (it's safe)

### "Password too weak"
- Minimum 6 characters required
- Update validation in `auth.py` if needed

### Port already in use
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or use different port
streamlit run app.py --server.port 8501
```

## Monitoring & Maintenance

### Database Backups

**For cloud PostgreSQL:**
- Most providers have automatic backups
- Set up daily backup schedules
- Test restore process periodically

**For local PostgreSQL:**
```bash
# Create backup
pg_dump -U username dashtrade > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -U username dashtrade < backup_20251028.sql
```

### Application Logs

Streamlit logs to stdout. Capture with:
```bash
streamlit run app.py 2>&1 | tee app.log
```

### Performance Monitoring

- Monitor database connection pool
- Track query performance
- Set up alerts for errors
- Monitor API rate limits (Alpha Vantage)

## Scaling

### Horizontal Scaling

For high traffic:
1. Use managed PostgreSQL (connection pooling)
2. Deploy multiple Streamlit instances
3. Use load balancer (Nginx/Caddy)
4. Cache frequently accessed data

### Vertical Scaling

- Upgrade server resources
- Increase database memory
- Optimize database queries
- Add database indexes

## Support & Resources

- **DashTrade Docs**: See `AUTHENTICATION_SETUP.md`
- **Streamlit Docs**: https://docs.streamlit.io
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Replit Docs**: https://docs.replit.com

---

**Last Updated**: 2025-10-28
**Version**: 1.0
