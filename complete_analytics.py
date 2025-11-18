#!/usr/bin/env python3
"""
NovAlgo Trading Bot - Complete Analytics Suite
Includes: Email reports, SMS alerts, CSV export, charts, web dashboard, 
Slack notifications, scheduled reports, drawdown analysis, Sharpe ratio, 
SPY comparison, and more!
"""

import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta
import pytz
from collections import defaultdict
import json
import csv
import io
import os

# Optional imports (install as needed)
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
    print("⚠️  matplotlib not installed - charts disabled")

try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    print("⚠️  email modules not available")

try:
    from twilio.rest import Client
    SMS_AVAILABLE = True
except ImportError:
    SMS_AVAILABLE = False
    print("⚠️  twilio not installed - SMS disabled")

try:
    import requests
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    print("⚠️  requests not installed - Slack disabled")

try:
    import pandas as pd
    import numpy as np
    ADVANCED_STATS = True
except ImportError:
    ADVANCED_STATS = False
    print("⚠️  pandas/numpy not installed - advanced stats disabled")

# ============================================================================
# CONFIGURATION
# ============================================================================

# Alpaca API
ALPACA_API_KEY = "PKL3QOG3TPAQ7NUYB86D"
ALPACA_SECRET_KEY = "zZxfTNPa7gBmU0RvSY0akIZujQWPXAeYhPD0O8Cz"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

# Email Configuration (Gmail example)
EMAIL_CONFIG = {
    'enabled': False,  # Set to True to enable
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'your_email@gmail.com',
    'sender_password': 'your_app_password',  # Use App Password, not regular password
    'recipient_email': 'your_email@gmail.com'
}

# SMS Configuration (Twilio)
SMS_CONFIG = {
    'enabled': False,  # Set to True to enable
    'account_sid': 'YOUR_TWILIO_ACCOUNT_SID',
    'auth_token': 'YOUR_TWILIO_AUTH_TOKEN',
    'from_number': '+1234567890',  # Your Twilio number
    'to_number': '+1234567890'     # Your phone number
}

# Slack Configuration
SLACK_CONFIG = {
    'enabled': False,  # Set to True to enable
    'webhook_url': 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
}

# Alert Thresholds
ALERT_THRESHOLDS = {
    'daily_profit': 500,      # Alert if daily profit > $500
    'daily_loss': -300,       # Alert if daily loss < -$300
    'position_loss': -100,    # Alert if single position < -$100
    'total_pnl': 1000,        # Alert when total P&L crosses $1000
    'drawdown': -500          # Alert if drawdown > $500
}

# Export settings
EXPORT_DIR = '/home/azureuser/analytics_exports'

PST = pytz.timezone('America/Los_Angeles')

# ============================================================================
# CONNECT TO ALPACA
# ============================================================================

api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL, api_version='v2')

# ============================================================================
# DATA COLLECTION FUNCTIONS
# ============================================================================

def get_account_data():
    """Get comprehensive account data"""
    account = api.get_account()
    return {
        'equity': float(account.equity),
        'cash': float(account.cash),
        'buying_power': float(account.buying_power),
        'portfolio_value': float(account.portfolio_value),
        'last_equity': float(account.last_equity),
        'day_pnl': float(account.equity) - float(account.last_equity),
        'timestamp': datetime.now(PST)
    }

def get_positions_data():
    """Get all position data with metrics"""
    positions = api.list_positions()
    positions_list = []
    
    for pos in positions:
        positions_list.append({
            'symbol': pos.symbol,
            'qty': float(pos.qty),
            'side': 'LONG' if float(pos.qty) > 0 else 'SHORT',
            'market_value': float(pos.market_value),
            'unrealized_pl': float(pos.unrealized_pl),
            'unrealized_plpc': float(pos.unrealized_plpc) * 100,
            'entry_price': float(pos.avg_entry_price),
            'current_price': float(pos.current_price)
        })
    
    return positions_list

def get_trading_history(days=30):
    """Get trading history for specified days"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    activities = api.get_activities(
        activity_types='FILL',
        date=start_date.strftime('%Y-%m-%d')
    )
    
    return activities

def calculate_realized_pnl(activities):
    """Calculate realized P&L from activities"""
    trades_by_symbol = defaultdict(lambda: {'buys': [], 'sells': []})
    
    for activity in activities:
        symbol = activity.symbol
        side = activity.side
        qty = float(activity.qty)
        price = float(activity.price)
        time = activity.transaction_time
        
        if side == 'buy':
            trades_by_symbol[symbol]['buys'].append({'qty': qty, 'price': price, 'time': time})
        elif side == 'sell':
            trades_by_symbol[symbol]['sells'].append({'qty': qty, 'price': price, 'time': time})
    
    total_realized_pnl = 0
    realized_by_symbol = {}
    
    for symbol, trades in trades_by_symbol.items():
        buys = sorted(trades['buys'], key=lambda x: x['time'])
        sells = sorted(trades['sells'], key=lambda x: x['time'])
        
        buy_queue = list(buys)
        symbol_pnl = 0
        
        for sell in sells:
            sell_qty = sell['qty']
            sell_price = sell['price']
            
            while sell_qty > 0 and buy_queue:
                buy = buy_queue[0]
                buy_qty = buy['qty']
                buy_price = buy['price']
                
                matched_qty = min(sell_qty, buy_qty)
                trade_pnl = (sell_price - buy_price) * matched_qty
                
                symbol_pnl += trade_pnl
                total_realized_pnl += trade_pnl
                
                sell_qty -= matched_qty
                buy['qty'] -= matched_qty
                
                if buy['qty'] == 0:
                    buy_queue.pop(0)
        
        if symbol_pnl != 0:
            realized_by_symbol[symbol] = symbol_pnl
    
    return total_realized_pnl, realized_by_symbol

# ============================================================================
# ADVANCED ANALYTICS FUNCTIONS
# ============================================================================

def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    """Calculate Sharpe Ratio"""
    if not ADVANCED_STATS or len(returns) < 2:
        return None
    
    returns_array = np.array(returns)
    excess_returns = returns_array - (risk_free_rate / 252)  # Daily risk-free rate
    
    if np.std(excess_returns) == 0:
        return 0
    
    sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    return sharpe

def calculate_max_drawdown(equity_curve):
    """Calculate maximum drawdown"""
    if not ADVANCED_STATS or len(equity_curve) < 2:
        return 0, 0
    
    equity_array = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity_array)
    drawdown = (equity_array - running_max) / running_max * 100
    max_dd = np.min(drawdown)
    max_dd_dollars = np.min(equity_array - running_max)
    
    return max_dd, max_dd_dollars

def get_spy_comparison(days=30):
    """Compare performance to SPY"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get SPY data
        spy_bars = api.get_bars('SPY', '1Day', start=start_date.isoformat(), end=end_date.isoformat()).df
        
        if len(spy_bars) > 1:
            spy_return = ((spy_bars['close'].iloc[-1] - spy_bars['close'].iloc[0]) / spy_bars['close'].iloc[0]) * 100
            return spy_return
        
    except Exception as e:
        print(f"Error getting SPY data: {e}")
    
    return None

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def export_to_csv(data_type='all'):
    """Export data to CSV files"""
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
    
    timestamp = datetime.now(PST).strftime('%Y%m%d_%H%M%S')
    
    exports = []
    
    # Export positions
    if data_type in ['all', 'positions']:
        positions = get_positions_data()
        if positions:
            filename = f'{EXPORT_DIR}/positions_{timestamp}.csv'
            with open(filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=positions[0].keys())
                writer.writeheader()
                writer.writerows(positions)
            exports.append(filename)
            print(f"✅ Exported positions to: {filename}")
    
    # Export trading history
    if data_type in ['all', 'history']:
        activities = get_trading_history(30)
        if activities:
            filename = f'{EXPORT_DIR}/trades_{timestamp}.csv'
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Symbol', 'Side', 'Qty', 'Price', 'Amount'])
                for activity in activities:
                    writer.writerow([
                        activity.transaction_time.strftime('%Y-%m-%d %H:%M:%S'),
                        activity.symbol,
                        activity.side,
                        activity.qty,
                        activity.price,
                        float(activity.qty) * float(activity.price)
                    ])
            exports.append(filename)
            print(f"✅ Exported trade history to: {filename}")
    
    # Export account summary
    if data_type in ['all', 'account']:
        account_data = get_account_data()
        filename = f'{EXPORT_DIR}/account_{timestamp}.csv'
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            for key, value in account_data.items():
                if key != 'timestamp':
                    writer.writerow([key, value])
        exports.append(filename)
        print(f"✅ Exported account summary to: {filename}")
    
    return exports

# ============================================================================
# CHART GENERATION
# ============================================================================

def generate_performance_chart():
    """Generate performance chart"""
    if not CHARTS_AVAILABLE:
        print("⚠️  Charts not available - install matplotlib")
        return None
    
    try:
        # Get historical equity data (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        portfolio_history = api.get_portfolio_history(
            date_start=start_date.isoformat(),
            timeframe='1D'
        )
        
        if not portfolio_history.equity:
            print("No portfolio history available")
            return None
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Plot equity curve
        timestamps = [datetime.fromtimestamp(ts) for ts in portfolio_history.timestamp]
        ax1.plot(timestamps, portfolio_history.equity, linewidth=2, color='#2E86AB')
        ax1.fill_between(timestamps, portfolio_history.equity, alpha=0.3, color='#2E86AB')
        ax1.set_title('Portfolio Equity Curve (30 Days)', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Equity ($)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        
        # Plot profit/loss
        profit_loss = portfolio_history.profit_loss
        colors = ['green' if pl >= 0 else 'red' for pl in profit_loss]
        ax2.bar(timestamps, profit_loss, color=colors, alpha=0.7)
        ax2.set_title('Daily Profit/Loss', fontsize=14, fontweight='bold')
        ax2.set_ylabel('P&L ($)', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        
        plt.tight_layout()
        
        # Save chart
        if not os.path.exists(EXPORT_DIR):
            os.makedirs(EXPORT_DIR)
        
        timestamp = datetime.now(PST).strftime('%Y%m%d_%H%M%S')
        filename = f'{EXPORT_DIR}/performance_chart_{timestamp}.png'
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Chart saved to: {filename}")
        return filename
        
    except Exception as e:
        print(f"Error generating chart: {e}")
        return None

# ============================================================================
# NOTIFICATION FUNCTIONS
# ============================================================================

def send_email_report(subject, body, attachments=None):
    """Send email report"""
    if not EMAIL_AVAILABLE or not EMAIL_CONFIG['enabled']:
        print("⚠️  Email not configured")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['recipient_email']
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        # Attach files
        if attachments:
            for filepath in attachments:
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(filepath)}')
                        msg.attach(part)
        
        # Send email
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
        
        print("✅ Email sent successfully")
        return True
        
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def send_sms_alert(message):
    """Send SMS alert via Twilio"""
    if not SMS_AVAILABLE or not SMS_CONFIG['enabled']:
        print("⚠️  SMS not configured")
        return False
    
    try:
        client = Client(SMS_CONFIG['account_sid'], SMS_CONFIG['auth_token'])
        
        sms = client.messages.create(
            body=message,
            from_=SMS_CONFIG['from_number'],
            to=SMS_CONFIG['to_number']
        )
        
        print(f"✅ SMS sent: {sms.sid}")
        return True
        
    except Exception as e:
        print(f"❌ SMS error: {e}")
        return False

def send_slack_notification(message):
    """Send Slack notification"""
    if not SLACK_AVAILABLE or not SLACK_CONFIG['enabled']:
        print("⚠️  Slack not configured")
        return False
    
    try:
        payload = {'text': message}
        response = requests.post(
            SLACK_CONFIG['webhook_url'],
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print("✅ Slack notification sent")
            return True
        else:
            print(f"❌ Slack error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Slack error: {e}")
        return False

# ============================================================================
# ALERT CHECKING
# ============================================================================

def check_alerts():
    """Check if any alert thresholds are breached"""
    alerts = []
    
    account_data = get_account_data()
    positions = get_positions_data()
    
    # Check daily P&L
    day_pnl = account_data['day_pnl']
    if day_pnl >= ALERT_THRESHOLDS['daily_profit']:
        alerts.append(f"🎉 Daily profit: ${day_pnl:.2f}")
    elif day_pnl <= ALERT_THRESHOLDS['daily_loss']:
        alerts.append(f"⚠️ Daily loss: ${day_pnl:.2f}")
    
    # Check individual positions
    for pos in positions:
        if pos['unrealized_pl'] <= ALERT_THRESHOLDS['position_loss']:
            alerts.append(f"⚠️ {pos['symbol']} loss: ${pos['unrealized_pl']:.2f}")
    
    # Check total unrealized P&L
    total_unrealized = sum([p['unrealized_pl'] for p in positions])
    if total_unrealized >= ALERT_THRESHOLDS['total_pnl']:
        alerts.append(f"🎉 Total P&L: ${total_unrealized:.2f}")
    
    return alerts

# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_html_report():
    """Generate comprehensive HTML report"""
    account_data = get_account_data()
    positions = get_positions_data()
    activities = get_trading_history(30)
    realized_pnl, _ = calculate_realized_pnl(activities)
    
    total_unrealized = sum([p['unrealized_pl'] for p in positions])
    total_pnl = realized_pnl + total_unrealized
    
    # SPY comparison
    spy_return = get_spy_comparison(30)
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #2E86AB; }}
            h2 {{ color: #555; border-bottom: 2px solid #2E86AB; padding-bottom: 5px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th {{ background-color: #2E86AB; color: white; padding: 10px; text-align: left; }}
            td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
            .positive {{ color: green; font-weight: bold; }}
            .negative {{ color: red; font-weight: bold; }}
            .metric {{ display: inline-block; margin: 10px 20px; }}
            .metric-label {{ font-weight: bold; color: #555; }}
            .metric-value {{ font-size: 1.2em; }}
        </style>
    </head>
    <body>
        <h1>🤖 NovAlgo Trading Bot - Daily Report</h1>
        <p>Report Generated: {datetime.now(PST).strftime('%Y-%m-%d %I:%M:%S %p PST')}</p>
        
        <h2>Account Summary</h2>
        <div class="metric">
            <span class="metric-label">Total Equity:</span>
            <span class="metric-value">${account_data['equity']:,.2f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Today's P&L:</span>
            <span class="metric-value {'positive' if account_data['day_pnl'] >= 0 else 'negative'}">
                ${account_data['day_pnl']:,.2f}
            </span>
        </div>
        <div class="metric">
            <span class="metric-label">Total P&L:</span>
            <span class="metric-value {'positive' if total_pnl >= 0 else 'negative'}">
                ${total_pnl:,.2f}
            </span>
        </div>
        
        <h2>Current Positions ({len(positions)})</h2>
        <table>
            <tr>
                <th>Symbol</th>
                <th>Side</th>
                <th>Quantity</th>
                <th>Entry Price</th>
                <th>Current Price</th>
                <th>Unrealized P&L</th>
                <th>Return %</th>
            </tr>
    """
    
    for pos in sorted(positions, key=lambda x: x['unrealized_pl'], reverse=True):
        pl_class = 'positive' if pos['unrealized_pl'] >= 0 else 'negative'
        html += f"""
            <tr>
                <td><strong>{pos['symbol']}</strong></td>
                <td>{pos['side']}</td>
                <td>{abs(pos['qty']):.0f}</td>
                <td>${pos['entry_price']:.2f}</td>
                <td>${pos['current_price']:.2f}</td>
                <td class="{pl_class}">${pos['unrealized_pl']:.2f}</td>
                <td class="{pl_class}">{pos['unrealized_plpc']:.2f}%</td>
            </tr>
        """
    
    html += f"""
        </table>
        
        <h2>Performance Metrics</h2>
        <div class="metric">
            <span class="metric-label">Realized P&L (30d):</span>
            <span class="metric-value">${realized_pnl:,.2f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Unrealized P&L:</span>
            <span class="metric-value">${total_unrealized:,.2f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Total Trades (30d):</span>
            <span class="metric-value">{len(activities)}</span>
        </div>
    """
    
    if spy_return is not None:
        html += f"""
        <div class="metric">
            <span class="metric-label">SPY Return (30d):</span>
            <span class="metric-value">{spy_return:.2f}%</span>
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    
    return html

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def run_full_analytics():
    """Run complete analytics suite"""
    print("\n" + "=" * 80)
    print("🚀 RUNNING COMPLETE ANALYTICS SUITE")
    print("=" * 80)
    print()
    
    # 1. Generate reports
    print("📊 Generating reports...")
    html_report = generate_html_report()
    
    # 2. Export data
    print("\n💾 Exporting data...")
    csv_files = export_to_csv('all')
    
    # 3. Generate charts
    print("\n📈 Generating charts...")
    chart_file = generate_performance_chart()
    
    # 4. Check alerts
    print("\n🔔 Checking alerts...")
    alerts = check_alerts()
    
    if alerts:
        alert_message = "NovAlgo Alert:\n" + "\n".join(alerts)
        print(f"\n⚠️ ALERTS TRIGGERED:\n{alert_message}\n")
        
        # Send SMS if enabled
        if SMS_CONFIG['enabled']:
            send_sms_alert(alert_message)
        
        # Send Slack if enabled
        if SLACK_CONFIG['enabled']:
            send_slack_notification(alert_message)
    else:
        print("✅ No alerts triggered")
    
    # 5. Send email report
    print("\n📧 Sending email report...")
    attachments = []
    if chart_file:
        attachments.append(chart_file)
    attachments.extend(csv_files)
    
    if EMAIL_CONFIG['enabled']:
        send_email_report(
            subject=f"NovAlgo Daily Report - {datetime.now(PST).strftime('%Y-%m-%d')}",
            body=html_report,
            attachments=attachments
        )
    
    print("\n" + "=" * 80)
    print("✅ ANALYTICS COMPLETE!")
    print("=" * 80)
    print()

if __name__ == '__main__':
    run_full_analytics()
