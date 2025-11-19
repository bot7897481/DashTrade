# Complete Azure VM Deployment Guide for DashTrade

## Overview

This guide will help you:
1. ✅ Set up Azure Linux VM
2. ✅ Install all dependencies
3. ✅ Configure PostgreSQL database
4. ✅ Deploy DashTrade application
5. ✅ Set up GitHub Actions for automatic deployment
6. ✅ Configure auto-start on VM reboot

---

## Important: VM Size Recommendation

**B1s (1GB RAM)** - You asked about this
- ❌ **NOT RECOMMENDED** - Too small for Streamlit + PostgreSQL + Python
- Will likely crash under load or when multiple users access

**B2s (2GB RAM)** - Minimum recommended
- ✅ Can handle Streamlit app
- ✅ Can run PostgreSQL
- ✅ Can handle 3-5 concurrent users
- 💰 Cost: ~$30-40/month

**B2ms (4GB RAM)** - Recommended for production
- ✅ Smooth performance
- ✅ Can handle 10-20 concurrent users
- ✅ Room for growth
- 💰 Cost: ~$60-80/month

**For this guide, I'll use B2s (2GB) as minimum.**

---

## Part 1: Create Azure VM

### Step 1: Create VM in Azure Portal

1. **Go to Azure Portal** (portal.azure.com)
2. Click **"+ Create a resource"**
3. Select **"Virtual Machine"**
4. Fill in the details:

**Basics Tab:**
```
Subscription: [Your subscription]
Resource Group: [Create new] → "DashTrade-RG"
VM Name: dashtrade-vm
Region: [Choose closest to your users]
Image: Ubuntu Server 22.04 LTS
Size: Standard_B2s (2 vCPUs, 4 GiB memory)
Authentication: SSH public key
Username: azureuser
SSH Key: [Generate new or use existing]
```

**Networking Tab:**
```
Virtual Network: [Create new] → "DashTrade-vnet"
Public IP: [Create new]
NIC network security group: Advanced
Configure network security group: [Create new]
```

**Add Inbound Port Rules:**
- ✅ SSH (22) - For management
- ✅ HTTP (80) - For web access
- ✅ HTTPS (443) - For secure web access
- ✅ Custom (5000) - For Streamlit app
- ✅ Custom (8080) - For webhook server

5. Click **"Review + Create"**
6. Click **"Create"**
7. **Download the SSH key** when prompted

Wait 2-3 minutes for VM to be created.

---

### Step 2: Get VM IP Address

1. Go to your VM in Azure Portal
2. Copy the **Public IP address** (e.g., 20.123.45.67)
3. Save this IP - you'll need it!

---

## Part 2: Connect to VM and Install Dependencies

### Step 1: Connect via SSH

**On Windows:**
```powershell
ssh -i path\to\your-key.pem azureuser@YOUR_VM_IP
```

**On Mac/Linux:**
```bash
chmod 400 ~/Downloads/your-key.pem
ssh -i ~/Downloads/your-key.pem azureuser@YOUR_VM_IP
```

---

### Step 2: Update System and Install Dependencies

Once connected to the VM, run these commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install Git
sudo apt install -y git

# Install Nginx (web server)
sudo apt install -y nginx

# Install system dependencies for Python packages
sudo apt install -y build-essential libpq-dev python3-pip

# Install pip for Python 3.11
curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.11
```

---

### Step 3: Configure PostgreSQL Database

```bash
# Switch to postgres user
sudo -u postgres psql

# Inside PostgreSQL prompt, run:
CREATE DATABASE dashtrade;
CREATE USER dashtradeuser WITH PASSWORD 'YourSecurePassword123!';
GRANT ALL PRIVILEGES ON DATABASE dashtrade TO dashtradeuser;
ALTER DATABASE dashtrade OWNER TO dashtradeuser;
\q

# Enable PostgreSQL to start on boot
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

**Save your database URL:**
```
DATABASE_URL=postgresql://dashtradeuser:YourSecurePassword123!@localhost:5432/dashtrade
```

---

## Part 3: Clone and Setup DashTrade Application

### Step 1: Clone Repository

```bash
# Create app directory
sudo mkdir -p /opt/dashtrade
sudo chown azureuser:azureuser /opt/dashtrade
cd /opt/dashtrade

# Clone your repository
git clone https://github.com/bot7897481/DashTrade.git .

# Checkout your branch
git checkout claude/learn-replit-01VJWXqcpk6TTxoc63oYcQHd
```

---

### Step 2: Create Python Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
# OR if you're using pyproject.toml:
pip install -e .
```

---

### Step 3: Create Environment Variables File

```bash
# Create .env file
nano /opt/dashtrade/.env
```

Add this content (update with your values):
```bash
# Database
DATABASE_URL=postgresql://dashtradeuser:YourSecurePassword123!@localhost:5432/dashtrade

# Encryption (generate this - see below)
ENCRYPTION_KEY=your-generated-encryption-key-here

# Optional: Alpha Vantage API
ALPHA_VANTAGE_API_KEY=your-key-here
```

**Generate Encryption Key:**
```bash
cd /opt/dashtrade
source venv/bin/activate
python3 encryption.py
# Copy the output and paste it in .env file
```

Save and exit (Ctrl+X, Y, Enter)

---

### Step 4: Initialize Database

```bash
cd /opt/dashtrade
source venv/bin/activate

# Load environment variables
export $(cat .env | xargs)

# Create user tables
python3 setup_database.py

# Create bot tables
python3 setup_bot_database.py
```

---

## Part 4: Configure Application as System Service

This makes your app start automatically when the VM reboots.

### Step 1: Create Streamlit Service

```bash
sudo nano /etc/systemd/system/dashtrade-streamlit.service
```

Add this content:
```ini
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
```

---

### Step 2: Create Webhook Service

```bash
sudo nano /etc/systemd/system/dashtrade-webhook.service
```

Add this content:
```ini
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
```

---

### Step 3: Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable dashtrade-streamlit
sudo systemctl enable dashtrade-webhook

# Start services
sudo systemctl start dashtrade-streamlit
sudo systemctl start dashtrade-webhook

# Check status
sudo systemctl status dashtrade-streamlit
sudo systemctl status dashtrade-webhook
```

---

### Step 4: Configure Nginx as Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/dashtrade
```

Add this content:
```nginx
server {
    listen 80;
    server_name YOUR_VM_IP;  # Replace with your VM IP or domain

    # Streamlit app
    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Webhook endpoint
    location /webhook {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable the site:
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/dashtrade /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## Part 5: Test the Deployment

### Step 1: Access Your App

Open your browser and go to:
```
http://YOUR_VM_IP
```

You should see the DashTrade login page!

---

### Step 2: Check Logs if Issues

```bash
# Streamlit logs
sudo journalctl -u dashtrade-streamlit -f

# Webhook logs
sudo journalctl -u dashtrade-webhook -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
```

---

## Part 6: GitHub Actions CI/CD Setup

Now let's set up automatic deployment when you push to GitHub!

### Step 1: Create SSH Deploy Key on VM

```bash
# On the VM, generate SSH key
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/github_deploy
# Press Enter for no passphrase

# Display private key (save this for GitHub Secrets)
cat ~/.ssh/github_deploy
# Copy the entire output

# Display public key
cat ~/.ssh/github_deploy.pub
```

---

### Step 2: Add Deployment Script on VM

```bash
sudo nano /opt/dashtrade/deploy.sh
```

Add this content:
```bash
#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Navigate to app directory
cd /opt/dashtrade

# Pull latest changes
echo "📥 Pulling latest code from GitHub..."
git fetch origin
git checkout claude/learn-replit-01VJWXqcpk6TTxoc63oYcQHd
git pull origin claude/learn-replit-01VJWXqcpk6TTxoc63oYcQHd

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt 2>/dev/null || pip install -e .

# Load environment variables
export $(cat .env | xargs)

# Run database migrations if needed
echo "🗄️ Checking database..."
python3 setup_bot_database.py 2>/dev/null || echo "Database already set up"

# Restart services
echo "🔄 Restarting services..."
sudo systemctl restart dashtrade-streamlit
sudo systemctl restart dashtrade-webhook

# Wait for services to start
sleep 5

# Check service status
if systemctl is-active --quiet dashtrade-streamlit; then
    echo "✅ Streamlit service running"
else
    echo "❌ Streamlit service failed"
    sudo journalctl -u dashtrade-streamlit -n 50
    exit 1
fi

if systemctl is-active --quiet dashtrade-webhook; then
    echo "✅ Webhook service running"
else
    echo "❌ Webhook service failed"
    sudo journalctl -u dashtrade-webhook -n 50
    exit 1
fi

echo "🎉 Deployment completed successfully!"
```

Make it executable:
```bash
chmod +x /opt/dashtrade/deploy.sh
```

---

### Step 3: Allow azureuser to Restart Services

```bash
# Allow azureuser to restart services without password
sudo visudo
```

Add this line at the end:
```
azureuser ALL=(ALL) NOPASSWD: /bin/systemctl restart dashtrade-streamlit, /bin/systemctl restart dashtrade-webhook, /bin/systemctl status dashtrade-streamlit, /bin/systemctl status dashtrade-webhook
```

Save and exit (Ctrl+X, Y, Enter)

---

## Part 7: Configure GitHub Actions

Now let's set up the GitHub workflow!

### Summary

**What we've covered:**
1. ✅ Azure VM setup (B2s recommended, 2GB RAM)
2. ✅ PostgreSQL database installation
3. ✅ Application deployment
4. ✅ Systemd services for auto-restart
5. ✅ Nginx reverse proxy
6. ✅ Deployment script

**Next step:** I'll create the GitHub Actions workflow file. This will automatically deploy to your Azure VM whenever you push code to GitHub.

**Cost estimate:**
- **B2s VM**: ~$35/month
- **Storage**: ~$5/month
- **Bandwidth**: ~$5/month
- **Total**: ~$45/month (much cheaper than Replit!)

Ready for the GitHub Actions setup?
