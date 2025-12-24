#!/bin/bash
# DashTrade Startup Script
# Runs both Streamlit (main UI) and Webhook Server

echo "================================================"
echo "🤖 DASHTRADE STARTUP"
echo "================================================"

# Start webhook server in background on port 8080
echo "Starting Webhook Server on port 8080..."
python webhook_server.py &
WEBHOOK_PID=$!

# Give it time to start
sleep 2

# Start Streamlit on the Railway-assigned PORT (default 5000)
echo "Starting Streamlit on port ${PORT:-5000}..."
streamlit run app.py --server.port ${PORT:-5000} --server.address 0.0.0.0 --server.headless true

# If Streamlit exits, also kill webhook server
kill $WEBHOOK_PID 2>/dev/null
