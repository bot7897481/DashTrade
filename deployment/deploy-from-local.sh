#!/bin/bash
# Deploy to Azure VM from Local Machine
# Usage: ./deploy-from-local.sh

set -e

echo "================================================"
echo "Deploying DashTrade to Azure VM"
echo "================================================"
echo ""

# Configuration
VM_IP="20.253.195.169"
VM_USER="azureuser"
VM_PASSWORD="Automat2sucess^"

echo "Connecting to Azure VM at $VM_IP..."
echo ""

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "Installing sshpass..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install hudochenkov/sshpass/sshpass
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo apt-get update && sudo apt-get install -y sshpass
    else
        echo "Please install sshpass manually"
        exit 1
    fi
fi

echo "Deploying application..."
echo ""

# Run deployment on remote VM
sshpass -p "$VM_PASSWORD" ssh -o StrictHostKeyChecking=no $VM_USER@$VM_IP << 'ENDSSH'
set -e

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
echo "Deployment completed on VM!"

ENDSSH

echo ""
echo "================================================"
echo "Deployment Successful! 🎉"
echo "================================================"
echo ""
echo "Your applications are now running at:"
echo "  Main Dashboard: http://$VM_IP:5000"
echo "  Secondary Dashboard: http://$VM_IP:5001"
echo ""
echo "To check status, SSH into the VM and run:"
echo "  ssh $VM_USER@$VM_IP"
echo "  sudo systemctl status dashtrade-main"
echo ""
