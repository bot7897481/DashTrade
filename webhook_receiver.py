
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from notification_service import NotificationService
from auth import UserDB
import sqlite3

load_dotenv()

app = Flask(__name__)
notifier = NotificationService()

# Security secret - should be set in .env
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'my_secret_key_123')

@app.route('/webhook', methods=['POST'])
def tradingview_webhook():
    """
    Handle incoming webhooks from TradingView
    Expected JSON: {
        "action": "BUY" or "SELL",
        "symbol": "AAPL",
        "price": 150.00,
        "secret": "my_secret_key_123",
        "user_id": 1
    }
    """
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Verify secret
    if data.get('secret') != WEBHOOK_SECRET:
        return jsonify({"error": "Unauthorized"}), 401
    
    symbol = data.get('symbol')
    action = data.get('action')
    price = data.get('price', 0.0)
    user_id = data.get('user_id', 1) # Default to 1 for demo or find by other means
    
    print(f"🔔 Received Webhook: {action} {symbol} at ${price}")
    
    # Find user email and check if notifications enabled
    user = UserDB.get_user_by_id(user_id)
    if user and user.get('email_enabled'):
        email = user['email']
        subject = f"🚀 TradingView Alert: {action} {symbol}"
        
        # Use existing template
        html = notifier.get_alert_template(
            symbol,
            f"TradingView {action} Signal",
            f"Your TradingView alert has triggered a <b>{action}</b> signal for {symbol} at ${price:.2f}.",
            price
        )
        
        if notifier.send_email(email, subject, html):
            return jsonify({"status": "success", "message": "Email sent"}), 200
        else:
            return jsonify({"error": "Failed to send email"}), 500
            
    return jsonify({"status": "received", "message": "No notification sent (disabled or user not found)"}), 200

if __name__ == '__main__':
    # Run on a different port than Streamlit (8501)
    # Default Flask port is 5000
    port = int(os.environ.get('WEBHOOK_PORT', 5000))
    print(f"🚀 Webhook listener starting on port {port}...")
    app.run(host='0.0.0.0', port=port)
