#!/usr/bin/env python3
"""
DashTrade Combined Server
Runs Flask webhook endpoints alongside Streamlit using threading
Flask handles /webhook, /system-webhook, /health endpoints
Streamlit handles everything else via subprocess
"""
import os
import sys
import subprocess
import threading
import time
from flask import Flask, request, jsonify, redirect
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get ports
MAIN_PORT = int(os.environ.get('PORT', 5000))
STREAMLIT_PORT = MAIN_PORT + 1  # Internal Streamlit port

# Create Flask app for webhooks
app = Flask(__name__)

# Import webhook handlers
from webhook_server import (
    webhook, system_webhook, health, test_webhook,
    forward_to_outgoing_webhooks
)

# Register webhook routes on this Flask app
app.add_url_rule('/webhook', 'webhook', webhook, methods=['POST'])
app.add_url_rule('/system-webhook', 'system_webhook', system_webhook, methods=['POST'])
app.add_url_rule('/health', 'health', health, methods=['GET'])
app.add_url_rule('/test-webhook', 'test_webhook', test_webhook, methods=['POST'])

# Redirect all other routes to Streamlit
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy_to_streamlit(path):
    """Redirect non-API requests to Streamlit"""
    return redirect(f'http://localhost:{STREAMLIT_PORT}/{path}', code=302)


def run_streamlit():
    """Run Streamlit as subprocess"""
    logger.info(f"Starting Streamlit on internal port {STREAMLIT_PORT}...")
    subprocess.run([
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port', str(STREAMLIT_PORT),
        '--server.address', '127.0.0.1',  # Only internal access
        '--server.headless', 'true',
        '--browser.gatherUsageStats', 'false'
    ])


def run_flask():
    """Run Flask as main server"""
    logger.info(f"Starting Flask webhook server on port {MAIN_PORT}...")
    app.run(host='0.0.0.0', port=MAIN_PORT, debug=False, use_reloader=False)


if __name__ == '__main__':
    print("=" * 60)
    print("🤖 DASHTRADE COMBINED SERVER")
    print("=" * 60)
    print(f"Main port: {MAIN_PORT}")
    print(f"Streamlit internal port: {STREAMLIT_PORT}")
    print("=" * 60)

    # Start Streamlit in background thread
    streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
    streamlit_thread.start()

    # Give Streamlit time to start
    time.sleep(3)
    logger.info("Streamlit started")

    # Run Flask in main thread (handles webhooks + proxies to Streamlit)
    run_flask()
