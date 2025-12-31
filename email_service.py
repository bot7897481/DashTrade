"""
Email Notification Service for DashTrade
Uses SMTP2GO API to send trade notifications
"""

import os
import logging
import requests
from typing import Dict, Optional
from datetime import datetime

from database import get_db_connection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# SMTP2GO API configuration
SMTP2GO_API_KEY = os.environ.get('SMTP2GO_API_KEY')
SMTP2GO_API_URL = 'https://api.smtp2go.com/v3/email/send'
FROM_EMAIL = os.environ.get('EMAIL_FROM', 'notifications@dashtrade.app')
FROM_NAME = os.environ.get('EMAIL_FROM_NAME', 'DashTrade')


class EmailService:
    """Send email notifications via SMTP2GO"""

    @staticmethod
    def is_configured() -> bool:
        """Check if email service is configured"""
        return bool(SMTP2GO_API_KEY)

    @staticmethod
    def send_email(to_email: str, subject: str, html_body: str, text_body: str = None) -> Dict:
        """
        Send an email via SMTP2GO API

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML content of email
            text_body: Plain text version (optional)

        Returns:
            dict: {'success': bool, 'message': str}
        """
        if not SMTP2GO_API_KEY:
            logger.warning("SMTP2GO_API_KEY not configured - email not sent")
            return {'success': False, 'message': 'Email service not configured'}

        try:
            payload = {
                'api_key': SMTP2GO_API_KEY,
                'to': [to_email],
                'sender': f"{FROM_NAME} <{FROM_EMAIL}>",
                'subject': subject,
                'html_body': html_body,
            }

            if text_body:
                payload['text_body'] = text_body

            response = requests.post(SMTP2GO_API_URL, json=payload, timeout=10)
            data = response.json()

            if response.status_code == 200 and data.get('data', {}).get('succeeded', 0) > 0:
                logger.info(f"Email sent successfully to {to_email}: {subject}")
                return {'success': True, 'message': 'Email sent'}
            else:
                error_msg = data.get('data', {}).get('failures', [{}])[0].get('error', 'Unknown error')
                logger.error(f"Failed to send email: {error_msg}")
                return {'success': False, 'message': error_msg}

        except Exception as e:
            logger.error(f"Email send error: {e}")
            return {'success': False, 'message': str(e)}

    @staticmethod
    def log_email(user_id: int, email_type: str, subject: str, recipient_email: str,
                  trade_id: int = None, status: str = 'sent', error_message: str = None):
        """Log email to database for tracking"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO email_notifications_log
                        (user_id, email_type, subject, recipient_email, trade_id, status, error_message)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (user_id, email_type, subject, recipient_email, trade_id, status, error_message))
                    conn.commit()
        except Exception as e:
            logger.error(f"Failed to log email: {e}")


class TradeNotificationService:
    """Send trade-related email notifications"""

    @staticmethod
    def get_user_notification_settings(user_id: int) -> Optional[Dict]:
        """Get user's email notification preferences"""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT email, email_notifications_enabled, notify_on_trade,
                               notify_on_error, notify_on_risk_event, notify_daily_summary
                        FROM users WHERE id = %s
                    """, (user_id,))
                    return dict(cur.fetchone()) if cur.rowcount > 0 else None
        except Exception as e:
            logger.error(f"Error getting notification settings: {e}")
            return None

    @staticmethod
    def send_trade_executed_email(user_id: int, trade_data: Dict) -> bool:
        """
        Send email notification when a trade is executed

        Args:
            user_id: User ID
            trade_data: Trade details dict with keys:
                - symbol, action, quantity, filled_price, status
                - bot_name, timeframe, order_id
        """
        # Check if user wants notifications
        settings = TradeNotificationService.get_user_notification_settings(user_id)
        if not settings:
            return False

        if not settings.get('email_notifications_enabled') or not settings.get('notify_on_trade'):
            logger.debug(f"Trade notifications disabled for user {user_id}")
            return False

        email = settings.get('email')
        if not email:
            return False

        # Build email content
        symbol = trade_data.get('symbol', 'N/A')
        action = trade_data.get('action', 'N/A')
        quantity = trade_data.get('quantity', trade_data.get('filled_qty', 'N/A'))
        price = trade_data.get('filled_price', trade_data.get('filled_avg_price', 'N/A'))
        status = trade_data.get('status', 'executed')
        bot_name = trade_data.get('bot_name', trade_data.get('strategy_name', 'Bot'))
        timeframe = trade_data.get('timeframe', '')
        order_id = trade_data.get('order_id', 'N/A')
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

        # Determine emoji and color based on action
        if action.upper() == 'BUY':
            action_emoji = '🟢'
            action_color = '#22c55e'
        elif action.upper() == 'SELL':
            action_emoji = '🔴'
            action_color = '#ef4444'
        else:
            action_emoji = '🟡'
            action_color = '#eab308'

        subject = f"{action_emoji} Trade Executed: {action} {symbol}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f3f4f6; padding: 20px; }}
                .container {{ max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); color: white; padding: 24px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 24px; }}
                .trade-badge {{ display: inline-block; background: {action_color}; color: white; padding: 8px 16px; border-radius: 20px; font-weight: bold; font-size: 18px; }}
                .details {{ margin-top: 20px; }}
                .detail-row {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #e5e7eb; }}
                .detail-label {{ color: #6b7280; }}
                .detail-value {{ font-weight: 600; color: #111827; }}
                .footer {{ background: #f9fafb; padding: 16px 24px; text-align: center; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>DashTrade</h1>
                    <p style="margin: 8px 0 0 0; opacity: 0.9;">Trade Notification</p>
                </div>
                <div class="content">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <span class="trade-badge">{action_emoji} {action} {symbol}</span>
                    </div>

                    <div class="details">
                        <div class="detail-row">
                            <span class="detail-label">Symbol</span>
                            <span class="detail-value">{symbol}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Action</span>
                            <span class="detail-value" style="color: {action_color};">{action}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Quantity</span>
                            <span class="detail-value">{quantity}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Fill Price</span>
                            <span class="detail-value">${price}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Status</span>
                            <span class="detail-value">{status}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Bot</span>
                            <span class="detail-value">{bot_name} {timeframe}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Order ID</span>
                            <span class="detail-value" style="font-size: 11px;">{order_id}</span>
                        </div>
                        <div class="detail-row" style="border-bottom: none;">
                            <span class="detail-label">Time</span>
                            <span class="detail-value">{timestamp}</span>
                        </div>
                    </div>
                </div>
                <div class="footer">
                    <p>This is an automated notification from DashTrade.</p>
                    <p>You can manage your notification preferences in Settings.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
Trade Executed: {action} {symbol}

Symbol: {symbol}
Action: {action}
Quantity: {quantity}
Fill Price: ${price}
Status: {status}
Bot: {bot_name} {timeframe}
Order ID: {order_id}
Time: {timestamp}

---
This is an automated notification from DashTrade.
        """

        # Send email
        result = EmailService.send_email(email, subject, html_body, text_body)

        # Log the email
        EmailService.log_email(
            user_id=user_id,
            email_type='trade_executed',
            subject=subject,
            recipient_email=email,
            trade_id=trade_data.get('trade_id'),
            status='sent' if result['success'] else 'failed',
            error_message=result.get('message') if not result['success'] else None
        )

        return result['success']

    @staticmethod
    def send_trade_error_email(user_id: int, error_data: Dict) -> bool:
        """Send email when a trade fails"""
        settings = TradeNotificationService.get_user_notification_settings(user_id)
        if not settings:
            return False

        if not settings.get('email_notifications_enabled') or not settings.get('notify_on_error'):
            return False

        email = settings.get('email')
        if not email:
            return False

        symbol = error_data.get('symbol', 'N/A')
        action = error_data.get('action', 'N/A')
        error_message = error_data.get('error', 'Unknown error')
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

        subject = f"⚠️ Trade Failed: {action} {symbol}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f3f4f6; padding: 20px; }}
                .container {{ max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: #dc2626; color: white; padding: 24px; text-align: center; }}
                .content {{ padding: 24px; }}
                .error-box {{ background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 16px; margin: 16px 0; }}
                .footer {{ background: #f9fafb; padding: 16px 24px; text-align: center; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚠️ Trade Error</h1>
                </div>
                <div class="content">
                    <p>A trade execution failed for <strong>{symbol}</strong>.</p>

                    <div class="error-box">
                        <strong>Error:</strong><br>
                        {error_message}
                    </div>

                    <p><strong>Action:</strong> {action}</p>
                    <p><strong>Time:</strong> {timestamp}</p>
                </div>
                <div class="footer">
                    <p>Please check your bot configuration and Alpaca account.</p>
                </div>
            </div>
        </body>
        </html>
        """

        result = EmailService.send_email(email, subject, html_body)

        EmailService.log_email(
            user_id=user_id,
            email_type='trade_error',
            subject=subject,
            recipient_email=email,
            status='sent' if result['success'] else 'failed',
            error_message=result.get('message') if not result['success'] else None
        )

        return result['success']

    @staticmethod
    def send_risk_event_email(user_id: int, risk_data: Dict) -> bool:
        """Send email when risk limit is hit"""
        settings = TradeNotificationService.get_user_notification_settings(user_id)
        if not settings:
            return False

        if not settings.get('email_notifications_enabled') or not settings.get('notify_on_risk_event'):
            return False

        email = settings.get('email')
        if not email:
            return False

        symbol = risk_data.get('symbol', 'N/A')
        event_type = risk_data.get('event_type', 'Risk Event')
        threshold = risk_data.get('threshold', 'N/A')
        current_value = risk_data.get('current_value', 'N/A')
        action_taken = risk_data.get('action_taken', 'None')
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

        subject = f"🚨 Risk Alert: {symbol} - {event_type}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f3f4f6; padding: 20px; }}
                .container {{ max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: #f59e0b; color: white; padding: 24px; text-align: center; }}
                .content {{ padding: 24px; }}
                .alert-box {{ background: #fffbeb; border: 1px solid #fcd34d; border-radius: 8px; padding: 16px; margin: 16px 0; }}
                .footer {{ background: #f9fafb; padding: 16px 24px; text-align: center; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 Risk Alert</h1>
                </div>
                <div class="content">
                    <div class="alert-box">
                        <strong>{event_type}</strong> triggered for <strong>{symbol}</strong>
                    </div>

                    <p><strong>Threshold:</strong> {threshold}%</p>
                    <p><strong>Current Value:</strong> {current_value}%</p>
                    <p><strong>Action Taken:</strong> {action_taken}</p>
                    <p><strong>Time:</strong> {timestamp}</p>
                </div>
                <div class="footer">
                    <p>Your bot has been automatically disabled to protect your capital.</p>
                </div>
            </div>
        </body>
        </html>
        """

        result = EmailService.send_email(email, subject, html_body)

        EmailService.log_email(
            user_id=user_id,
            email_type='risk_event',
            subject=subject,
            recipient_email=email,
            status='sent' if result['success'] else 'failed',
            error_message=result.get('message') if not result['success'] else None
        )

        return result['success']
