#!/usr/bin/env python3
"""
DashTrade Webhook Server Runner
TradingView signal handler
"""
import os
import sys

PORT = int(os.environ.get('PORT', 8080))

if __name__ == '__main__':
    print("=" * 60)
    print("DASHTRADE - Webhook Server")
    print(f"   Port: {PORT}")
    print("   TradingView webhooks handler")
    print("=" * 60)

    # Import and run the webhook server
    from webhook_server import app
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
