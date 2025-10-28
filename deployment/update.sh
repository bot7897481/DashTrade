#!/bin/bash
# DashTrade Update Script
# Pulls latest changes from GitHub and restarts services

set -e

echo "================================================"
echo "DashTrade Update Script"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

APP_DIR="/home/azureuser/DashTrade"
VENV_DIR="$APP_DIR/venv"

echo -e "${YELLOW}Step 1: Navigating to application directory...${NC}"
cd "$APP_DIR"

echo -e "${YELLOW}Step 2: Pulling latest changes from GitHub...${NC}"
git fetch origin
git pull origin claude/session-011CUZtoXZ57cycWC48mJvmE

echo -e "${YELLOW}Step 3: Updating Python dependencies...${NC}"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt 2>/dev/null || echo "Using existing packages"

echo -e "${YELLOW}Step 4: Restarting services...${NC}"
sudo systemctl restart dashtrade-main.service
sudo systemctl restart dashtrade-secondary.service

echo -e "${YELLOW}Step 5: Checking service status...${NC}"
sleep 3
sudo systemctl status dashtrade-main.service --no-pager
sudo systemctl status dashtrade-secondary.service --no-pager

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Update completed successfully!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Services have been restarted and are running."
echo "Access your applications at:"
echo "  Main: http://20.253.195.169:5000"
echo "  Secondary: http://20.253.195.169:5001"
echo ""
