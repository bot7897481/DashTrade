#!/usr/bin/env python3
"""
DashTrade API Server Runner
REST API for React frontend
Uses gunicorn for production deployment
"""
import os
import sys

PORT = int(os.environ.get('PORT', 8080))

if __name__ == '__main__':
    print("=" * 60)
    print("DASHTRADE - API Server")
    print(f"   Port: {PORT}")
    print("   REST API for React frontend")
    print("=" * 60)

    # Use gunicorn for production
    os.system(f'gunicorn api_server:app --bind 0.0.0.0:{PORT} --workers 2 --timeout 120')
