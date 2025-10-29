# DashTrade Azure VM Deployment Guide

Complete guide for deploying DashTrade to Azure VM (Ubuntu 22.04)

## Server Information
- **IP Address:** 20.253.195.169
- **Username:** azureuser
- **OS:** Ubuntu 22.04 LTS
- **Ports:** 5000 (Main), 5001 (Secondary)

---

## Quick Deploy (One-Command Installation)

SSH into your Azure VM and run:

```bash
curl -sSL https://raw.githubusercontent.com/bot7897481/DashTrade/claude/session-011CUZtoXZ57cycWC48mJvmE/deployment/quick-deploy.sh | bash
```

**OR** Manual step-by-step installation below:

---

## Manual Installation

### Step 1: SSH into Your VM

```bash
ssh azureuser@20.253.195.169
```

### Step 2: Clone the Repository

```bash
cd ~
git clone https://github.com/bot7897481/DashTrade.git
cd DashTrade
git checkout claude/session-011CUZtoXZ57cycWC48mJvmE
```

### Step 3: Run Deployment Script

```bash
chmod +x deployment/deploy.sh
./deployment/deploy.sh
```

This script will:
- ✅ Update system packages
- ✅ Install Python 3, PostgreSQL, and dependencies
- ✅ Create a Python virtual environment
- ✅ Install all required Python packages
- ✅ Set up PostgreSQL database
- ✅ Create systemd services for auto-start
- ✅ Configure firewall rules
- ✅ Start the applications

### Step 4: Verify Installation

Check that services are running:

```bash
sudo systemctl status dashtrade-main
sudo systemctl status dashtrade-secondary
```

### Step 5: Access Your Applications

Open in your browser:
- **Main Dashboard:** http://20.253.195.169:5000
- **Secondary Dashboard:** http://20.253.195.169:5001

---

## Managing Your Applications

### Service Commands

**Check Status:**
```bash
sudo systemctl status dashtrade-main
sudo systemctl status dashtrade-secondary
```

**Start Services:**
```bash
sudo systemctl start dashtrade-main
sudo systemctl start dashtrade-secondary
```

**Stop Services:**
```bash
sudo systemctl stop dashtrade-main
sudo systemctl stop dashtrade-secondary
```

**Restart Services:**
```bash
sudo systemctl restart dashtrade-main
sudo systemctl restart dashtrade-secondary
```

**View Logs:**
```bash
# Real-time logs
sudo journalctl -u dashtrade-main -f

# View log files
tail -f /var/log/dashtrade-main.log
tail -f /var/log/dashtrade-main-error.log
```

---

## Updating Your Application

When you push new changes to GitHub, update your VM:

```bash
cd ~/DashTrade
./deployment/update.sh
```

This will:
- Pull latest changes from GitHub
- Update dependencies
- Restart services

---

## Database Management

### Connect to Database

```bash
sudo -u postgres psql -d dashtrade
```

### Database Credentials

- **Host:** localhost
- **Port:** 5432
- **Database:** dashtrade
- **Username:** dashtrade_user
- **Password:** DashTrade2024!

### Useful Database Commands

```sql
-- List all tables
\dt

-- View watchlist
SELECT * FROM watchlist;

-- View alerts
SELECT * FROM alerts;

-- View preferences
SELECT * FROM user_preferences;
```

---

## Troubleshooting

### Services Won't Start

1. **Check logs:**
   ```bash
   sudo journalctl -u dashtrade-main -n 50
   ```

2. **Check database connection:**
   ```bash
   sudo -u postgres psql -c "SELECT 1"
   ```

3. **Verify environment file:**
   ```bash
   cat ~/DashTrade/.env
   ```

### Port Already in Use

```bash
# Find what's using the port
sudo lsof -i :5000
sudo lsof -i :5001

# Kill the process
sudo kill -9 <PID>
```

### Database Issues

**Reset database:**
```bash
sudo -u postgres psql <<EOF
DROP DATABASE dashtrade;
CREATE DATABASE dashtrade;
GRANT ALL PRIVILEGES ON DATABASE dashtrade TO dashtrade_user;
EOF
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R azureuser:azureuser ~/DashTrade

# Fix log permissions
sudo chown azureuser:azureuser /var/log/dashtrade-*.log
```

---

## Firewall Configuration

### Current Rules

```bash
sudo ufw status
```

### Open Additional Ports

```bash
sudo ufw allow <PORT>/tcp
sudo ufw reload
```

### Azure Network Security Group

Make sure these ports are open in Azure Portal:
- **Port 22** - SSH
- **Port 5000** - Main Dashboard
- **Port 5001** - Secondary Dashboard

**Steps in Azure Portal:**
1. Go to your VM → Networking
2. Add inbound port rule
3. Destination port: 5000, 5001
4. Protocol: TCP
5. Action: Allow

---

## Auto-Start on Boot

Services are configured to auto-start on system reboot. To verify:

```bash
sudo systemctl is-enabled dashtrade-main
sudo systemctl is-enabled dashtrade-secondary
```

Both should show: `enabled`

---

## Environment Variables

Edit the `.env` file to customize settings:

```bash
nano ~/DashTrade/.env
```

**Available variables:**
```
DATABASE_URL=postgresql://dashtrade_user:DashTrade2024!@localhost:5432/dashtrade
ALPHA_VANTAGE_API_KEY=your_key_here
```

After editing, restart services:
```bash
sudo systemctl restart dashtrade-main dashtrade-secondary
```

---

## Performance Optimization

### Increase Memory for Streamlit

Edit systemd service:
```bash
sudo nano /etc/systemd/system/dashtrade-main.service
```

Add under `[Service]`:
```
Environment="STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200"
Environment="STREAMLIT_SERVER_MAX_MESSAGE_SIZE=200"
```

Reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart dashtrade-main
```

---

## Backup and Restore

### Backup Database

```bash
sudo -u postgres pg_dump dashtrade > ~/dashtrade_backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
sudo -u postgres psql dashtrade < ~/dashtrade_backup_20251028.sql
```

---

## Security Recommendations

1. **Change default database password:**
   ```bash
   sudo -u postgres psql -c "ALTER USER dashtrade_user PASSWORD 'new_secure_password';"
   ```
   Update in `.env` file accordingly.

2. **Enable SSH key authentication** (disable password auth)

3. **Set up fail2ban:**
   ```bash
   sudo apt install fail2ban
   sudo systemctl enable fail2ban
   ```

4. **Regular updates:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

---

## Monitoring

### System Resources

```bash
# CPU and Memory
htop

# Disk usage
df -h

# Service resource usage
systemctl status dashtrade-main
```

### Application Metrics

Check Streamlit metrics at:
- http://20.253.195.169:5000/_stcore/health

---

## Support

For issues or questions:
1. Check logs: `/var/log/dashtrade-*.log`
2. Review systemd journal: `sudo journalctl -u dashtrade-main`
3. Check GitHub issues: https://github.com/bot7897481/DashTrade/issues

---

## Quick Reference Commands

```bash
# Deploy/Update
cd ~/DashTrade && ./deployment/update.sh

# Restart all services
sudo systemctl restart dashtrade-main dashtrade-secondary

# View all logs
sudo journalctl -u dashtrade-main -u dashtrade-secondary -f

# Check database
sudo -u postgres psql -d dashtrade

# System status
sudo systemctl status dashtrade-main dashtrade-secondary
```

---

**Deployment completed successfully! 🎉**

Access your dashboards at:
- **Main:** http://20.253.195.169:5000
- **Secondary:** http://20.253.195.169:5001
