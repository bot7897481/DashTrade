#!/usr/bin/env python3
"""
NovAlgo Trading Bot - PRODUCTION VERSION with Database Trade Logging
Multi-Timeframe Trading with Performance Tracking & Real-time Status Updates
"""

from flask import Flask, request, jsonify
import alpaca_trade_api as tradeapi
import logging
from datetime import datetime, timedelta
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import threading
import time
import pytz
from trade_logger import TradeLogger

# ============================================================================
# CONFIGURATION
# ============================================================================

ALPACA_API_KEY = "PKL3QOG3TPAQ7NUYB86D"
ALPACA_SECRET_KEY = "zZxfTNPa7gBmU0RvSY0akIZujQWPXAeYhPD0O8Cz"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
WEBHOOK_SECRET = "my_secret_key_123"

GOOGLE_SHEET_ID = "1OltaqcoHrm0mvAiT9L1IS4XsVJZGErqnB1ZzKi5Wvk8"
CREDENTIALS_FILE = "/home/azureuser/credentials.json"

# Production settings
PRODUCTION_PORT = 80
PST = pytz.timezone('America/Los_Angeles')

# Global cache for tracking positions per symbol+timeframe
position_tracker = {}
config_row_map = {}  # Maps (symbol, timeframe) -> row number in sheet

# ============================================================================
# GOOGLE SHEETS FUNCTIONS
# ============================================================================

def get_google_sheets_client():
    """Get authenticated Google Sheets client"""
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    return gspread.authorize(creds)

def update_order_status(symbol, timeframe, status, message=""):
    """Update Order Status and Last Updated columns in Google Sheets"""
    try:
        key = (symbol, timeframe)
        if key not in config_row_map:
            return
        
        row_num = config_row_map[key]
        timestamp = datetime.now(PST).strftime("%Y-%m-%d %I:%M:%S %p PST")
        
        client = get_google_sheets_client()
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        
        sheet.update(f'E{row_num}', status)
        sheet.update(f'F{row_num}', timestamp)
        
        if message:
            logger.info(f"📝 Status: {symbol} {timeframe} - {status} ({message})")
        else:
            logger.info(f"📝 Status: {symbol} {timeframe} - {status}")
            
    except Exception as e:
        logger.error(f"❌ Sheet update error: {e}")

def get_stock_config():
    """Read stock configuration from Google Sheets"""
    try:
        client = get_google_sheets_client()
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        records = sheet.get_all_records()
        
        global config_row_map
        config_row_map = {}
        
        active_stocks = {}
        for idx, record in enumerate(records, start=2):
            active = record.get('active')
            if active == True or str(active).upper() == 'TRUE':
                symbol = str(record.get('symbol', '')).upper()
                position_size = int(record.get('position_size', 0))
                timeframe = str(record.get('Time Frame', ''))
                
                if symbol and position_size > 0 and timeframe:
                    key = (symbol, timeframe)
                    active_stocks[key] = position_size
                    config_row_map[key] = idx
        
        logger.info(f"✅ Loaded {len(active_stocks)} configurations")
        return active_stocks
    except Exception as e:
        logger.error(f"❌ Google Sheets error: {e}")
        return {}

def update_performance_dashboard():
    """Update Performance tab with trade statistics"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        activities = api.get_activities(
            activity_types='FILL',
            date=start_date.strftime('%Y-%m-%d')
        )
        
        stats = {}
        
        for activity in activities:
            symbol = activity.symbol
            side = activity.side
            qty = float(activity.qty)
            price = float(activity.price)
            
            if symbol not in stats:
                stats[symbol] = {
                    'trades': [],
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'total_pnl': 0,
                    'best_trade': 0,
                    'worst_trade': 0
                }
            
            stats[symbol]['trades'].append({
                'side': side,
                'qty': qty,
                'price': price,
                'time': activity.transaction_time
            })
        
        for symbol, data in stats.items():
            trades = sorted(data['trades'], key=lambda x: x['time'])
            position = 0
            entry_price = 0
            
            for trade in trades:
                if trade['side'] == 'buy':
                    if position == 0:
                        entry_price = trade['price']
                    position += trade['qty']
                elif trade['side'] == 'sell':
                    if position > 0:
                        pnl = (trade['price'] - entry_price) * trade['qty']
                        data['total_pnl'] += pnl
                        data['total_trades'] += 1
                        
                        if pnl > 0:
                            data['winning_trades'] += 1
                        elif pnl < 0:
                            data['losing_trades'] += 1
                        
                        if pnl > data['best_trade']:
                            data['best_trade'] = pnl
                        if pnl < data['worst_trade']:
                            data['worst_trade'] = pnl
                        
                        position -= trade['qty']
        
        client = get_google_sheets_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        sheet_data = []
        
        for symbol, data in stats.items():
            if data['total_trades'] > 0:
                win_rate = (data['winning_trades'] / data['total_trades'] * 100)
                avg_pnl = data['total_pnl'] / data['total_trades']
                
                sheet_data.append([
                    symbol,
                    data['total_trades'],
                    data['winning_trades'],
                    data['losing_trades'],
                    f"{win_rate:.1f}%",
                    f"${data['total_pnl']:.2f}",
                    f"${avg_pnl:.2f}",
                    f"${data['best_trade']:.2f}",
                    f"${data['worst_trade']:.2f}",
                    datetime.now(PST).strftime("%Y-%m-%d %H:%M:%S PST")
                ])
        
        if len(sheet_data) > 0:
            perf_sheet = spreadsheet.worksheet('Performance')
            perf_sheet.batch_clear(['A2:J100'])
            perf_sheet.update(f'A2:J{len(sheet_data)+1}', sheet_data)
            logger.info(f"✅ Performance updated: {len(sheet_data)} symbols")
        
    except Exception as e:
        logger.error(f"❌ Performance update error: {e}")

def performance_updater():
    """Background thread that updates performance every 5 minutes"""
    time.sleep(60)
    while True:
        try:
            update_performance_dashboard()
        except Exception as e:
            logger.error(f"❌ Performance updater error: {e}")
        time.sleep(300)

# ============================================================================
# SETUP
# ============================================================================

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL, api_version='v2')
    logger.info("✅ Alpaca connected (PAPER TRADING)")
    account = api.get_account()
    logger.info(f"💰 Account: ${float(account.buying_power):,.2f}")
except Exception as e:
    logger.error(f"❌ Alpaca error: {e}")
    exit(1)

# Initialize Trade Logger
try:
    trade_logger = TradeLogger('/home/azureuser/trades.db')
    logger.info("✅ Trade Logger initialized - Database ready")
except Exception as e:
    logger.error(f"❌ Trade Logger error: {e}")
    trade_logger = None

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_crypto_symbol(symbol):
    """Normalize crypto symbol to Alpaca format (e.g., BTCUSD -> BTC/USD)"""
    if not symbol:
        return symbol
    symbol_upper = symbol.upper()
    # Already in correct format
    if '/' in symbol_upper:
        return symbol_upper
    # Convert BTCUSD to BTC/USD
    if symbol_upper.endswith('USD') and len(symbol_upper) >= 6:
        base = symbol_upper[:-3]
        return f"{base}/USD"
    return symbol_upper

def get_current_position(symbol):
    try:
        positions = api.list_positions()
        # Build list of possible symbol formats to check (for crypto)
        symbols_to_check = [symbol]
        normalized = normalize_crypto_symbol(symbol)
        if normalized != symbol:
            symbols_to_check.append(normalized)
            # Also check reverse (if symbol has /, check without)
            if '/' in symbol:
                symbols_to_check.append(symbol.replace('/', ''))
        
        for position in positions:
            if position.symbol in symbols_to_check:
                return position
        return None
    except Exception as e:
        logger.error(f"Error getting position: {e}")
        return None

def close_position(symbol, timeframe):
    try:
        position = get_current_position(symbol)
        if position:
            qty = abs(float(position.qty))
            side = "LONG" if float(position.qty) > 0 else "SHORT"
            avg_price = float(position.avg_entry_price)
            
            # Normalize symbol for crypto (BTCUSD -> BTC/USD)
            # Use the actual position symbol to ensure we close the correct one
            position_symbol = position.symbol
            symbols_to_try = [position_symbol]
            
            # Also try normalized version if different
            normalized = normalize_crypto_symbol(symbol)
            if normalized != position_symbol and normalized not in symbols_to_try:
                symbols_to_try.append(normalized)
            if symbol != position_symbol and symbol not in symbols_to_try:
                symbols_to_try.append(symbol)
            
            # Try closing with each symbol format
            closing_order = None
            last_error = None
            for sym in symbols_to_try:
                try:
                    logger.info(f"🔴 Attempting to close position with symbol: {sym}")
                    closing_order = api.close_position(sym)
                    logger.info(f"✅ CLOSED: {symbol} {timeframe} - {side} ({qty} shares) using symbol {sym}")
                    break
                except Exception as e:
                    last_error = e
                    logger.warning(f"⚠️ Could not close with symbol {sym}: {e}")
                    continue
            
            if not closing_order:
                logger.error(f"❌ Failed to close position for {symbol}: {last_error}")
                return False
            
            # Wait a moment for the order to fill
            time.sleep(2)
            
            # Get the closing order details to log the actual fill price
            try:
                filled_order = api.get_order(closing_order.id)
                if filled_order.status == 'filled':
                    fill_price = float(filled_order.filled_avg_price)
                    
                    # Log to database
                    if trade_logger:
                        # Log as opposite side (closing long = sell, closing short = buy)
                        close_side = 'sell' if side == 'LONG' else 'buy'
                        trade_logger.log_trade(
                            symbol=symbol,
                            side=close_side,
                            quantity=qty,
                            price=fill_price,
                            timeframe=timeframe,
                            order_id=closing_order.id,
                            status='FILLED',
                            notes=f'Closed {side} position'
                        )
                        logger.info(f"📊 Trade logged to database: CLOSE {symbol}")
            except Exception as e:
                logger.error(f"❌ Error logging close trade: {e}")
            
            key = (symbol, timeframe)
            if key in position_tracker:
                del position_tracker[key]
            
            update_order_status(symbol, timeframe, "WAITING", "Position closed")
            return True
        return False
    except Exception as e:
        logger.error(f"❌ Error closing: {e}")
        return False

def place_order(symbol, side, timeframe, qty=None, notional=None):
    try:
        logger.info(f"📤 {side.upper()} order: {symbol} {timeframe}")
        
        update_order_status(symbol, timeframe, "ORDER SUBMITTED", f"{side.upper()} order sent")
        
        if notional:
            order = api.submit_order(
                symbol=symbol,
                notional=notional,
                side=side,
                type='market',
                time_in_force='day'
            )
            logger.info(f"✅ ORDER SUBMITTED: {side.upper()} ${notional:,} {symbol} {timeframe} - ID: {order.id}")
        else:
            order = api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type='market',
                time_in_force='day'
            )
            logger.info(f"✅ ORDER SUBMITTED: {side.upper()} {qty} shares {symbol} {timeframe} - ID: {order.id}")
        
        key = (symbol, timeframe)
        position_tracker[key] = {
            'side': side,
            'order_id': order.id,
            'timestamp': datetime.now()
        }
        
        # Check order status and log to database
        time.sleep(2)
        try:
            filled_order = api.get_order(order.id)
            if filled_order.status == 'filled':
                update_order_status(symbol, timeframe, "FILLED", f"{side.upper()} executed")
                logger.info(f"✅ ORDER FILLED: {symbol} {timeframe}")
                
                # Log trade to database
                if trade_logger:
                    fill_qty = float(filled_order.filled_qty)
                    fill_price = float(filled_order.filled_avg_price)
                    
                    trade_logger.log_trade(
                        symbol=symbol,
                        side=side,
                        quantity=fill_qty,
                        price=fill_price,
                        timeframe=timeframe,
                        order_id=order.id,
                        status='FILLED',
                        notes=f'Market order executed'
                    )
                    logger.info(f"📊 Trade logged to database: {side.upper()} {fill_qty} {symbol} @ ${fill_price:.2f}")
                    
            elif filled_order.status == 'partially_filled':
                update_order_status(symbol, timeframe, "PARTIAL FILL")
        except Exception as e:
            logger.error(f"❌ Error checking order status: {e}")
        
        return order
        
    except Exception as e:
        logger.error(f"❌ ORDER FAILED: {symbol} {timeframe} - {e}")
        update_order_status(symbol, timeframe, "FAILED", str(e))
        return None

def get_stock_price(symbol):
    try:
        trade = api.get_latest_trade(symbol)
        return float(trade.price)
    except Exception as e:
        logger.error(f"❌ Price error {symbol}: {e}")
        return None

# ============================================================================
# TRADING LOGIC
# ============================================================================

def execute_long_signal(symbol, timeframe, position_size):
    logger.info(f"🟢 LONG: {symbol} {timeframe} - ${position_size:,}")
    
    current_position = get_current_position(symbol)
    
    if current_position and float(current_position.qty) < 0:
        logger.info(f"⚠️ Closing SHORT first: {symbol} {timeframe}")
        close_position(symbol, timeframe)
    
    if current_position and float(current_position.qty) > 0:
        logger.info(f"ℹ️ Already LONG: {symbol} {timeframe}")
        update_order_status(symbol, timeframe, "ALREADY LONG", "Skipped")
        return {"status": "skipped", "reason": "Already long"}
    
    order = place_order(symbol, 'buy', timeframe, notional=position_size)
    
    if order:
        return {
            "status": "success",
            "action": "BUY",
            "symbol": symbol,
            "timeframe": timeframe,
            "amount": position_size,
            "order_id": order.id
        }
    
    return {"status": "error", "reason": "Order failed"}

def execute_short_signal(symbol, timeframe, position_size):
    logger.info(f"🔴 SHORT: {symbol} {timeframe} - ${position_size:,}")
    
    current_position = get_current_position(symbol)
    
    if current_position and float(current_position.qty) > 0:
        logger.info(f"⚠️ Closing LONG first: {symbol} {timeframe}")
        close_position(symbol, timeframe)
    
    if current_position and float(current_position.qty) < 0:
        logger.info(f"ℹ️ Already SHORT: {symbol} {timeframe}")
        update_order_status(symbol, timeframe, "ALREADY SHORT", "Skipped")
        return {"status": "skipped", "reason": "Already short"}
    
    price = get_stock_price(symbol)
    if not price:
        update_order_status(symbol, timeframe, "FAILED", "No price")
        return {"status": "error", "reason": "No price"}
    
    qty = int(position_size / price)
    order = place_order(symbol, 'sell', timeframe, qty=qty)
    
    if order:
        return {
            "status": "success",
            "action": "SELL",
            "symbol": symbol,
            "timeframe": timeframe,
            "quantity": qty,
            "order_id": order.id
        }
    
    return {"status": "error", "reason": "Order failed"}

def execute_close_signal(symbol, timeframe):
    logger.info(f"⚪ CLOSE: {symbol} {timeframe}")
    
    if close_position(symbol, timeframe):
        return {
            "status": "success",
            "action": "CLOSE",
            "symbol": symbol,
            "timeframe": timeframe
        }
    
    return {"status": "info", "reason": "No position"}

# ============================================================================
# WEBHOOK
# ============================================================================

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data"}), 400
        
        logger.info("="*60)
        logger.info(f"📨 WEBHOOK: {json.dumps(data)}")
        
        if data.get('secret') != WEBHOOK_SECRET:
            logger.warning("⚠️ Invalid secret")
            return jsonify({"error": "Invalid secret"}), 401
        
        stock_config = get_stock_config()
        
        action = data.get('action', '').upper()
        symbol = data.get('symbol', '').upper()
        timeframe = data.get('timeframe', '')
        
        key = (symbol, timeframe)
        
        if key not in stock_config:
            logger.warning(f"⚠️ {symbol} {timeframe} not in config")
            return jsonify({
                "status": "skipped",
                "reason": f"{symbol} {timeframe} not active"
            }), 200
        
        position_size = stock_config[key]
        
        if action in ['BUY', 'LONG']:
            result = execute_long_signal(symbol, timeframe, position_size)
        elif action in ['SELL', 'SHORT']:
            result = execute_short_signal(symbol, timeframe, position_size)
        elif action == 'CLOSE':
            result = execute_close_signal(symbol, timeframe)
        else:
            logger.warning(f"⚠️ Unknown action: {action}")
            return jsonify({"error": f"Unknown action: {action}"}), 400
        
        logger.info("="*60)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(PST).isoformat(),
        "database": "connected" if trade_logger else "disconnected"
    }), 200

@app.route('/config', methods=['GET'])
def config():
    stock_config = get_stock_config()
    return jsonify({
        "active_configs": len(stock_config),
        "stocks": [f"{s} {tf}" for (s, tf) in stock_config.keys()]
    }), 200

@app.route('/positions', methods=['GET'])
def positions():
    try:
        positions = api.list_positions()
        position_data = []
        
        for pos in positions:
            position_data.append({
                "symbol": pos.symbol,
                "qty": pos.qty,
                "side": "LONG" if float(pos.qty) > 0 else "SHORT",
                "market_value": pos.market_value,
                "unrealized_pl": pos.unrealized_pl,
                "unrealized_plpc": f"{float(pos.unrealized_plpc)*100:.2f}%"
            })
        
        return jsonify({
            "positions": position_data,
            "count": len(position_data)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/database/summary', methods=['GET'])
def database_summary():
    """Get database trade summary"""
    if not trade_logger:
        return jsonify({"error": "Database not connected"}), 500
    
    try:
        summary = trade_logger.get_summary(days=30)
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/database/ledger', methods=['GET'])
def database_ledger():
    """Get trade ledger from database"""
    if not trade_logger:
        return jsonify({"error": "Database not connected"}), 500
    
    try:
        days = int(request.args.get('days', 30))
        ledger = trade_logger.get_trade_ledger(days=days)
        return jsonify({"ledger": ledger, "count": len(ledger)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("🚀 NovAlgo Trading Bot - PRODUCTION with Database Logging")
    logger.info("="*60)
    logger.info(f"🌐 Port: {PRODUCTION_PORT}")
    logger.info(f"📊 Database: {'✅ Connected' if trade_logger else '❌ Disconnected'}")
    
    config = get_stock_config()
    logger.info(f"📋 Active: {len(config)}")
    for (symbol, timeframe), size in config.items():
        logger.info(f"   ✅ {symbol} {timeframe}: ${size:,}")
    
    logger.info("="*60)
    
    perf_thread = threading.Thread(target=performance_updater, daemon=True)
    perf_thread.start()
    logger.info("📊 Performance: Updates every 5 min")
    
    logger.info("✅ BOT IS LIVE WITH DATABASE LOGGING!")
    logger.info("="*60)
    
    app.run(host='0.0.0.0', port=PRODUCTION_PORT, debug=False)
