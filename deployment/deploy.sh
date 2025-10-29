#!/bin/bash
# DashTrade Deployment Script for Azure VM
# This script sets up the complete application environment

set -e  # Exit on error

echo "================================================"
echo "DashTrade Deployment Script"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/home/azureuser/DashTrade"
APP_USER="azureuser"
PYTHON_VERSION="python3"
VENV_DIR="$APP_DIR/venv"

echo -e "${YELLOW}Step 1: Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y

echo -e "${YELLOW}Step 2: Installing required system packages...${NC}"
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    postgresql \
    postgresql-contrib \
    nginx \
    supervisor

echo -e "${YELLOW}Step 3: Checking if application directory exists...${NC}"
if [ -d "$APP_DIR" ]; then
    echo -e "${GREEN}Application directory exists. Pulling latest changes...${NC}"
    cd "$APP_DIR"
    git pull origin claude/session-011CUZtoXZ57cycWC48mJvmE
else
    echo -e "${GREEN}Cloning repository...${NC}"
    cd /home/azureuser
    git clone https://github.com/bot7897481/DashTrade.git
    cd "$APP_DIR"
    git checkout claude/session-011CUZtoXZ57cycWC48mJvmE
fi

echo -e "${YELLOW}Step 4: Creating Python virtual environment...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON_VERSION -m venv "$VENV_DIR"
    echo -e "${GREEN}Virtual environment created${NC}"
else
    echo -e "${GREEN}Virtual environment already exists${NC}"
fi

echo -e "${YELLOW}Step 5: Activating virtual environment and installing dependencies...${NC}"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt 2>/dev/null || echo -e "${YELLOW}requirements.txt not found, installing core packages...${NC}"

# Install core packages if requirements.txt doesn't exist
pip install streamlit pandas numpy yfinance plotly sqlalchemy psycopg2-binary requests alpha-vantage

echo -e "${YELLOW}Step 6: Setting up PostgreSQL database...${NC}"
sudo -u postgres psql -c "SELECT 1 FROM pg_database WHERE datname = 'dashtrade'" | grep -q 1 || \
sudo -u postgres psql -c "CREATE DATABASE dashtrade;"

sudo -u postgres psql -c "SELECT 1 FROM pg_roles WHERE rolname = 'dashtrade_user'" | grep -q 1 || \
sudo -u postgres psql -c "CREATE USER dashtrade_user WITH PASSWORD 'DashTrade2024!';"

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE dashtrade TO dashtrade_user;"
sudo -u postgres psql -d dashtrade -c "GRANT ALL ON SCHEMA public TO dashtrade_user;"

echo -e "${GREEN}Database setup completed${NC}"

echo -e "${YELLOW}Step 6.5: Creating environment file...${NC}"
if [ ! -f "$APP_DIR/.env" ]; then
    cat > "$APP_DIR/.env" <<EOF
DATABASE_URL=postgresql://dashtrade_user:DashTrade2024!@localhost:5432/dashtrade
ALPHA_VANTAGE_API_KEY=
EOF
    chmod 600 "$APP_DIR/.env"
    echo -e "${GREEN}.env file created${NC}"
else
    echo -e "${GREEN}.env file already exists${NC}"
fi

echo -e "${YELLOW}Step 7: Creating systemd service files...${NC}"

# Service for Port 5000 (Main Dashboard)
sudo tee /etc/systemd/system/dashtrade-main.service > /dev/null <<EOF
[Unit]
Description=DashTrade Main Dashboard (Port 5000)
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$VENV_DIR/bin/streamlit run app.py --server.port 5000 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=10
StandardOutput=append:/var/log/dashtrade-main.log
StandardError=append:/var/log/dashtrade-main-error.log

[Install]
WantedBy=multi-user.target
EOF

# Service for Port 5001 (Secondary Dashboard - if you have another app)
# Note: Update the script name if different from app.py
sudo tee /etc/systemd/system/dashtrade-secondary.service > /dev/null <<EOF
[Unit]
Description=DashTrade Secondary Dashboard (Port 5001)
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$VENV_DIR/bin/streamlit run app.py --server.port 5001 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=10
StandardOutput=append:/var/log/dashtrade-secondary.log
StandardError=append:/var/log/dashtrade-secondary-error.log

[Install]
WantedBy=multi-user.target
EOF

# Create log files
sudo touch /var/log/dashtrade-main.log /var/log/dashtrade-main-error.log
sudo touch /var/log/dashtrade-secondary.log /var/log/dashtrade-secondary-error.log
sudo chown $APP_USER:$APP_USER /var/log/dashtrade-*.log

echo -e "${GREEN}Systemd service files created${NC}"

echo -e "${YELLOW}Step 8: Configuring firewall...${NC}"
sudo ufw allow 5000/tcp
sudo ufw allow 5001/tcp
sudo ufw allow 22/tcp
sudo ufw --force enable

echo -e "${YELLOW}Step 9: Reloading systemd and enabling services...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable dashtrade-main.service
sudo systemctl enable dashtrade-secondary.service

echo -e "${YELLOW}Step 10: Starting services...${NC}"
sudo systemctl restart dashtrade-main.service
sudo systemctl restart dashtrade-secondary.service

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Application URLs:"
echo "  Main Dashboard: http://20.253.195.169:5000"
echo "  Secondary Dashboard: http://20.253.195.169:5001"
echo ""
echo "Service Management Commands:"
echo "  Check status: sudo systemctl status dashtrade-main"
echo "  View logs: sudo journalctl -u dashtrade-main -f"
echo "  Restart: sudo systemctl restart dashtrade-main"
echo ""
echo "Database Connection:"
echo "  Host: localhost"
echo "  Database: dashtrade"
echo "  User: dashtrade_user"
echo "  Password: DashTrade2024!"
echo ""
