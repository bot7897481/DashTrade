#!/usr/bin/env python3
"""
DashTrade Unified Startup Script
Runs both Streamlit and Webhook Server together for Railway deployment
"""
import os
import sys
import subprocess
import threading
import time

def run_webhook_server():
    """Run the Flask webhook server in a background thread"""
    print("🚀 Starting Webhook Server on port 8080...")

    # Import and run the webhook server
    from webhook_server import app
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

def run_streamlit():
    """Run Streamlit as the main process"""
    port = os.environ.get('PORT', '5000')
    print(f"🚀 Starting Streamlit on port {port}...")

    # Run streamlit as subprocess
    subprocess.run([
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port', port,
        '--server.address', '0.0.0.0',
        '--server.headless', 'true'
    ])

if __name__ == '__main__':
    print("=" * 60)
    print("🤖 DASHTRADE UNIFIED STARTUP")
    print("=" * 60)

    # Start webhook server in background thread
    webhook_thread = threading.Thread(target=run_webhook_server, daemon=True)
    webhook_thread.start()

    # Give webhook server time to start
    time.sleep(2)
    print("✅ Webhook server started on port 8080")

    # Run Streamlit in main thread (this blocks)
    run_streamlit()
