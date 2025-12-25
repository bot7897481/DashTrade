#!/usr/bin/env python3
"""
DashTrade Streamlit Server
Runs only Streamlit - webhooks are handled by separate service
"""
import os
import sys

PORT = int(os.environ.get('PORT', 8080))

if __name__ == '__main__':
    print("=" * 60)
    print("🤖 DASHTRADE - Streamlit App")
    print(f"   Port: {PORT}")
    print("=" * 60)

    # Run Streamlit
    os.system(f'{sys.executable} -m streamlit run app.py '
              f'--server.port {PORT} '
              f'--server.address 0.0.0.0 '
              f'--server.headless true '
              f'--browser.gatherUsageStats false')
