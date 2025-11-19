# Quick Start: Deploy DashTrade to Azure VM

This is a simplified checklist. For detailed instructions, see `AZURE_DEPLOYMENT_GUIDE.md` and `GITHUB_ACTIONS_SETUP.md`.

---

## Part 1: Azure VM Setup (30 minutes)

### 1. Create VM
- [ ] Go to portal.azure.com
- [ ] Create Ubuntu 22.04 VM
- [ ] Size: **B2s** (2GB RAM) - minimum recommended
- [ ] Enable ports: 22, 80, 443, 5000, 8080
- [ ] Download SSH key
- [ ] Note down VM IP address

### 2. Connect to VM
```bash
ssh -i your-key.pem azureuser@YOUR_VM_IP
```

### 3. Install Dependencies (copy-paste all at once)
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install other tools
sudo apt install -y git nginx build-essential libpq-dev

# Install pip for Python 3.11
curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.11
```

### 4. Setup PostgreSQL
```bash
sudo -u postgres psql <<EOF
CREATE DATABASE dashtrade;
CREATE USER dashtradeuser WITH PASSWORD 'YourSecurePassword123!';
GRANT ALL PRIVILEGES ON DATABASE dashtrade TO dashtradeuser;
ALTER DATABASE dashtrade OWNER TO dashtradeuser;
\q
EOF

sudo systemctl enable postgresql
```

**Save your DATABASE_URL:**
```
postgresql://dashtradeuser:YourSecurePassword123!@localhost:5432/dashtrade
```

---

## Part 2: Deploy Application (10 minutes)

### 1. Clone Repository
```bash
sudo mkdir -p /opt/dashtrade
sudo chown azureuser:azureuser /opt/dashtrade
cd /opt/dashtrade
git clone https://github.com/bot7897481/DashTrade.git .
git checkout claude/learn-replit-01VJWXqcpk6TTxoc63oYcQHd
```

### 2. Setup Python Environment
```bash
cd /opt/dashtrade
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Create .env File
```bash
nano /opt/dashtrade/.env
```

Add (replace with your values):
```bash
DATABASE_URL=postgresql://dashtradeuser:YourSecurePassword123!@localhost:5432/dashtrade
ENCRYPTION_KEY=generate-this-below
```

Generate encryption key:
```bash
cd /opt/dashtrade
source venv/bin/activate
python3 encryption.py
# Copy output and add to .env file
```

### 4. Initialize Database
```bash
cd /opt/dashtrade
source venv/bin/activate
export $(cat .env | xargs)
python3 setup_database.py
python3 setup_bot_database.py
```

---

## Part 3: Configure Services (10 minutes)

### 1. Create Streamlit Service
```bash
sudo tee /etc/systemd/system/dashtrade-streamlit.service <<EOF
[Unit]
Description=DashTrade Streamlit Application
After=network.target postgresql.service

[Service]
Type=simple
User=azureuser
WorkingDirectory=/opt/dashtrade
Environment="PATH=/opt/dashtrade/venv/bin"
EnvironmentFile=/opt/dashtrade/.env
ExecStart=/opt/dashtrade/venv/bin/streamlit run app.py --server.port 5000 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 2. Create Webhook Service
```bash
sudo tee /etc/systemd/system/dashtrade-webhook.service <<EOF
[Unit]
Description=DashTrade Webhook Server
After=network.target postgresql.service

[Service]
Type=simple
User=azureuser
WorkingDirectory=/opt/dashtrade
Environment="PATH=/opt/dashtrade/venv/bin"
EnvironmentFile=/opt/dashtrade/.env
ExecStart=/opt/dashtrade/venv/bin/python webhook_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 3. Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable dashtrade-streamlit dashtrade-webhook
sudo systemctl start dashtrade-streamlit dashtrade-webhook
sudo systemctl status dashtrade-streamlit dashtrade-webhook
```

### 4. Configure Nginx
```bash
sudo tee /etc/nginx/sites-available/dashtrade <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_read_timeout 86400;
    }

    location /webhook {
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/dashtrade /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## Part 4: Test Deployment

**Open browser:**
```
http://YOUR_VM_IP
```

✅ You should see DashTrade login page!

---

## Part 5: GitHub Actions (10 minutes)

### 1. Create Deploy Script on VM
```bash
sudo tee /opt/dashtrade/deploy.sh <<'EOF'
#!/bin/bash
set -e
echo "🚀 Starting deployment..."
cd /opt/dashtrade
git fetch origin
git checkout claude/learn-replit-01VJWXqcpk6TTxoc63oYcQHd
git pull origin claude/learn-replit-01VJWXqcpk6TTxoc63oYcQHd
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
export $(cat .env | xargs)
python3 setup_bot_database.py 2>/dev/null || true
sudo systemctl restart dashtrade-streamlit dashtrade-webhook
sleep 5
sudo systemctl status dashtrade-streamlit --no-pager
sudo systemctl status dashtrade-webhook --no-pager
echo "🎉 Deployment completed!"
EOF

chmod +x /opt/dashtrade/deploy.sh
```

### 2. Allow Service Restart
```bash
echo "azureuser ALL=(ALL) NOPASSWD: /bin/systemctl restart dashtrade-streamlit, /bin/systemctl restart dashtrade-webhook, /bin/systemctl status dashtrade-streamlit, /bin/systemctl status dashtrade-webhook" | sudo tee -a /etc/sudoers.d/dashtrade
sudo chmod 0440 /etc/sudoers.d/dashtrade
```

### 3. Add GitHub Secrets

Go to: `https://github.com/bot7897481/DashTrade/settings/secrets/actions`

Add 3 secrets:
- `AZURE_SSH_KEY` = (your VM SSH private key)
- `AZURE_VM_IP` = (your VM IP address)
- `AZURE_SSH_USER` = `azureuser`

### 4. Push to Trigger Deployment
```bash
# In Claude Code
git add .
git commit -m "Test Azure deployment"
git push origin claude/learn-replit-01VJWXqcpk6TTxoc63oYcQHd
```

Watch deployment in GitHub Actions tab!

---

## Quick Commands Reference

### Check Service Status
```bash
sudo systemctl status dashtrade-streamlit
sudo systemctl status dashtrade-webhook
```

### View Logs
```bash
sudo journalctl -u dashtrade-streamlit -f
sudo journalctl -u dashtrade-webhook -f
```

### Restart Services
```bash
sudo systemctl restart dashtrade-streamlit
sudo systemctl restart dashtrade-webhook
```

### Manual Deployment
```bash
cd /opt/dashtrade
./deploy.sh
```

---

## Cost Summary

**B2s VM (2GB RAM):**
- ~$35/month
- Can handle 5-10 concurrent users
- Recommended for production

**B1s VM (1GB RAM):**
- ~$15/month
- ❌ NOT recommended - too small
- May crash under load

**GitHub Actions:**
- ✅ FREE for public repos
- ✅ 2000 minutes/month for private repos

---

## Troubleshooting

**App won't start:**
```bash
sudo journalctl -u dashtrade-streamlit -n 100
```

**Database errors:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql postgresql://dashtradeuser:YourPassword@localhost:5432/dashtrade
```

**Can't access from browser:**
```bash
# Check Nginx
sudo systemctl status nginx
sudo nginx -t

# Check firewall
sudo ufw status
```

---

## Success Checklist

- [ ] VM created and accessible
- [ ] PostgreSQL installed and running
- [ ] Python 3.11 installed
- [ ] Application cloned and dependencies installed
- [ ] .env file created with DATABASE_URL and ENCRYPTION_KEY
- [ ] Database tables created
- [ ] Services running (streamlit + webhook)
- [ ] Nginx configured
- [ ] Can access app at http://YOUR_VM_IP
- [ ] GitHub secrets configured
- [ ] GitHub Actions workflow running successfully

---

**Total Time:** ~1 hour
**Monthly Cost:** ~$45 (B2s VM)
**Result:** Automatic deployment on every git push! 🚀
