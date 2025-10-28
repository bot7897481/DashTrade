#!/bin/bash
# DashTrade Quick Deploy Script
# Run with: curl -sSL https://raw.githubusercontent.com/bot7897481/DashTrade/claude/session-011CUZtoXZ57cycWC48mJvmE/deployment/quick-deploy.sh | bash

set -e

echo "================================================"
echo "DashTrade Quick Deploy"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please do not run as root. Run as azureuser."
    exit 1
fi

# Clone or update repository
if [ -d "$HOME/DashTrade" ]; then
    echo "Updating existing installation..."
    cd "$HOME/DashTrade"
    git fetch origin
    git checkout claude/session-011CUZtoXZ57cycWC48mJvmE
    git pull origin claude/session-011CUZtoXZ57cycWC48mJvmE
else
    echo "Installing DashTrade..."
    cd "$HOME"
    git clone https://github.com/bot7897481/DashTrade.git
    cd DashTrade
    git checkout claude/session-011CUZtoXZ57cycWC48mJvmE
fi

# Make deploy script executable
chmod +x deployment/deploy.sh

# Run deployment
./deployment/deploy.sh

echo ""
echo "Quick deploy completed!"
echo "Access your dashboards at:"
echo "  - http://20.253.195.169:5000"
echo "  - http://20.253.195.169:5001"
