#!/usr/bin/env python3
"""
DashTrade Combined Server
Uses nginx-unit style routing: Flask handles API routes, proxies rest to Streamlit
Both run on the SAME external port (required for Railway)
"""
import os
import sys
import logging
import subprocess
import threading
import time
from datetime import datetime

from flask import Flask, request, jsonify, Response
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ports - Railway exposes 8501, we use that for Flask proxy
EXTERNAL_PORT = int(os.environ.get('PORT', 8501))
STREAMLIT_INTERNAL_PORT = 8502  # Internal Streamlit port

# Create Flask app
app = Flask(__name__)

# Try to import webhook dependencies
try:
    from bot_database import (
        BotConfigDB, WebhookTokenDB, SystemStrategyDB,
        UserStrategySubscriptionDB, UserOutgoingWebhookDB
    )
    from bot_engine import TradingEngine
    WEBHOOK_ENABLED = True
    logger.info("Webhook dependencies loaded")
except ImportError as e:
    WEBHOOK_ENABLED = False
    logger.warning(f"Webhook dependencies not available: {e}")


# ============================================================================
# WEBHOOK ROUTES (handled by Flask)
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'DashTrade',
        'webhook_enabled': WEBHOOK_ENABLED,
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/test-webhook', methods=['POST'])
def test_webhook():
    data = request.get_json() or {}
    logger.info(f"Test webhook received: {data}")
    return jsonify({
        'status': 'test_received',
        'your_data': data,
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'Test successful! Use /webhook?token=YOUR_TOKEN for trading.'
    })


@app.route('/webhook', methods=['POST'])
def webhook():
    if not WEBHOOK_ENABLED:
        return jsonify({'error': 'Webhook not available'}), 503

    try:
        token = request.args.get('token')
        if not token:
            return jsonify({'error': 'Missing token'}), 401

        user_id = WebhookTokenDB.get_user_by_token(token)
        if not user_id:
            return jsonify({'error': 'Invalid token'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400

        action = data.get('action', '').upper()
        symbol = data.get('symbol', '').upper()
        timeframe = data.get('timeframe', '')

        if not all([action, symbol, timeframe]):
            return jsonify({'error': 'Missing fields', 'required': ['action', 'symbol', 'timeframe']}), 400

        if action not in ['BUY', 'SELL', 'CLOSE']:
            return jsonify({'error': f'Invalid action: {action}'}), 400

        logger.info(f"WEBHOOK: User {user_id} - {action} {symbol} {timeframe}")

        bot_config = BotConfigDB.get_bot_by_symbol_timeframe(user_id, symbol, timeframe, signal_source='webhook')

        if not bot_config:
            return jsonify({'status': 'skipped', 'reason': 'No webhook bot found'})

        if not bot_config['is_active']:
            return jsonify({'status': 'skipped', 'reason': 'Bot disabled'})

        engine = TradingEngine(user_id)
        result = engine.execute_trade(bot_config, action)

        return jsonify({
            'status': result.get('status'),
            'action': action,
            'symbol': symbol,
            'timestamp': datetime.utcnow().isoformat(),
            **result
        })

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/system-webhook', methods=['POST'])
def system_webhook():
    if not WEBHOOK_ENABLED:
        return jsonify({'error': 'Webhook not available'}), 503

    try:
        token = request.args.get('token')
        if not token or not token.startswith('sys_'):
            return jsonify({'error': 'Invalid system token'}), 401

        strategy = SystemStrategyDB.get_strategy_by_token(token)
        if not strategy:
            return jsonify({'error': 'Invalid strategy token'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400

        action = data.get('action', '').upper()
        symbol = data.get('symbol', '').upper()

        if not action or not symbol:
            return jsonify({'error': 'Missing action or symbol'}), 400

        if action not in ['BUY', 'SELL', 'CLOSE']:
            return jsonify({'error': f'Invalid action'}), 400

        logger.info(f"SYSTEM: {strategy['name']} - {action} {symbol}")

        SystemStrategyDB.increment_signal_count(strategy['id'])
        subscribers = UserStrategySubscriptionDB.get_strategy_subscribers(strategy['id'])

        if not subscribers:
            return jsonify({'status': 'no_subscribers'})

        successful, failed = 0, 0
        for sub in subscribers:
            try:
                bots = BotConfigDB.get_user_bots(sub['user_id'])
                bot = next((b for b in bots if b['id'] == sub['bot_config_id']), None)
                if bot and bot['is_active']:
                    engine = TradingEngine(sub['user_id'])
                    result = engine.execute_trade(bot, action)
                    successful += 1 if result.get('status') == 'success' else 0
                    failed += 1 if result.get('status') != 'success' else 0
            except:
                failed += 1

        return jsonify({
            'status': 'executed',
            'strategy': strategy['name'],
            'subscribers': len(subscribers),
            'successful': successful,
            'failed': failed
        })

    except Exception as e:
        logger.error(f"System webhook error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# PROXY ALL OTHER REQUESTS TO STREAMLIT
# ============================================================================

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def proxy_to_streamlit(path):
    """Proxy all non-webhook requests to Streamlit"""
    streamlit_url = f'http://127.0.0.1:{STREAMLIT_INTERNAL_PORT}/{path}'

    try:
        # Forward the request to Streamlit
        resp = requests.request(
            method=request.method,
            url=streamlit_url,
            headers={k: v for k, v in request.headers if k.lower() != 'host'},
            data=request.get_data(),
            cookies=request.cookies,
            params=request.args,
            allow_redirects=False,
            stream=True,
            timeout=30
        )

        # Build response
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(k, v) for k, v in resp.raw.headers.items() if k.lower() not in excluded_headers]

        return Response(resp.content, resp.status_code, headers)

    except requests.exceptions.ConnectionError:
        return "Streamlit is starting...", 503
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return f"Proxy error: {e}", 500


# ============================================================================
# STREAMLIT RUNNER
# ============================================================================

def run_streamlit():
    """Run Streamlit on internal port"""
    logger.info(f"Starting Streamlit on internal port {STREAMLIT_INTERNAL_PORT}")
    subprocess.run([
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port', str(STREAMLIT_INTERNAL_PORT),
        '--server.address', '127.0.0.1',
        '--server.headless', 'true',
        '--browser.gatherUsageStats', 'false'
    ])


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("🤖 DASHTRADE COMBINED SERVER")
    print(f"   External Port: {EXTERNAL_PORT}")
    print(f"   Streamlit Internal: {STREAMLIT_INTERNAL_PORT}")
    print(f"   Webhooks: {'Enabled' if WEBHOOK_ENABLED else 'Disabled'}")
    print("=" * 60)

    # Start Streamlit in background thread
    streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
    streamlit_thread.start()

    # Wait for Streamlit to start
    logger.info("Waiting for Streamlit to start...")
    time.sleep(5)

    # Run Flask on external port (handles webhooks + proxies to Streamlit)
    logger.info(f"Starting Flask proxy on port {EXTERNAL_PORT}")
    app.run(host='0.0.0.0', port=EXTERNAL_PORT, debug=False, threaded=True)
