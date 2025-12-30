#!/usr/bin/env python3
"""
DashTrade API Server Runner
REST API for React frontend
"""
import os
import sys

PORT = int(os.environ.get('PORT', 8081))

if __name__ == '__main__':
    print("=" * 60)
    print("DASHTRADE - API Server")
    print(f"   Port: {PORT}")
    print("   REST API for React frontend")
    print("=" * 60)

    # Import and run the API server
    from api_server import app
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
