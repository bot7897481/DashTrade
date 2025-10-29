"""
Notification Handler for Pine Script Signals
Sends webhook and email notifications when signals are detected
"""

import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
import json
from datetime import datetime


class NotificationHandler:
    """Handle webhook and email notifications for trading signals"""

    def __init__(self):
        self.webhook_url = None
        self.email_config = {
            'smtp_server': None,
            'smtp_port': None,
            'sender_email': None,
            'sender_password': None,
            'recipient_emails': []
        }

    def configure_webhook(self, webhook_url: str):
        """
        Configure webhook URL for notifications

        Args:
            webhook_url: The webhook URL to send POST requests to
        """
        self.webhook_url = webhook_url

    def configure_email(self, smtp_server: str, smtp_port: int,
                       sender_email: str, sender_password: str,
                       recipient_emails: list):
        """
        Configure email settings for notifications

        Args:
            smtp_server: SMTP server address (e.g., smtp.gmail.com)
            smtp_port: SMTP port (usually 587 for TLS)
            sender_email: Email address to send from
            sender_password: Email password or app password
            recipient_emails: List of email addresses to send to
        """
        self.email_config = {
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'sender_email': sender_email,
            'sender_password': sender_password,
            'recipient_emails': recipient_emails
        }

    def send_webhook(self, signal_data: Dict) -> bool:
        """
        Send webhook notification

        Args:
            signal_data: Dictionary containing signal information

        Returns:
            True if successful, False otherwise
        """
        if not self.webhook_url:
            return False

        try:
            # Prepare webhook payload
            payload = {
                'action': 'BUY' if signal_data['type'] == 'LONG' else 'SELL',
                'symbol': signal_data['symbol'],
                'type': signal_data['type'],
                'price': float(signal_data['price']),
                'volume': float(signal_data.get('volume', 0)),
                'rsi': float(signal_data.get('rsi', 0)),
                'timestamp': str(signal_data['timestamp']),
                'trend': signal_data.get('trend', 'unknown'),
                'secret': 'novalgoquot_trading_signals'  # You can customize this
            }

            # Send POST request
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            return response.status_code == 200

        except Exception as e:
            print(f"Webhook error: {str(e)}")
            return False

    def send_email(self, signal_data: Dict) -> bool:
        """
        Send email notification

        Args:
            signal_data: Dictionary containing signal information

        Returns:
            True if successful, False otherwise
        """
        if not all([
            self.email_config['smtp_server'],
            self.email_config['sender_email'],
            self.email_config['sender_password'],
            self.email_config['recipient_emails']
        ]):
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_config['sender_email']
            msg['To'] = ', '.join(self.email_config['recipient_emails'])

            signal_type = signal_data['type']
            symbol = signal_data['symbol']
            msg['Subject'] = f"🔔 {signal_type} Signal Alert: {symbol}"

            # Create HTML email body
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: {'#00c853' if signal_type == 'LONG' else '#ff1744'}; color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0;">{'🟢' if signal_type == 'LONG' else '🔴'} {signal_type} Signal Detected</h1>
                </div>

                <div style="padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 10px 10px;">
                    <h2 style="color: #333; margin-top: 0;">{symbol}</h2>

                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <tr style="background-color: #f5f5f5;">
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Signal Type:</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd; color: {'#00c853' if signal_type == 'LONG' else '#ff1744'};">
                                <strong>{signal_type}</strong>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Price:</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">${signal_data['price']:.2f}</td>
                        </tr>
                        <tr style="background-color: #f5f5f5;">
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Volume:</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{signal_data.get('volume', 0):,.0f}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>RSI:</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{signal_data.get('rsi', 0):.2f}</td>
                        </tr>
                        <tr style="background-color: #f5f5f5;">
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Trend:</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{signal_data.get('trend', 'N/A').title()}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Time:</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{signal_data['timestamp']}</td>
                        </tr>
                    </table>

                    <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin-top: 20px;">
                        <p style="margin: 0;"><strong>Action Recommended:</strong></p>
                        <p style="margin: 10px 0 0 0; font-size: 18px; color: {'#00c853' if signal_type == 'LONG' else '#ff1744'};">
                            {'📈 Consider BUYING' if signal_type == 'LONG' else '📉 Consider SELLING'}
                        </p>
                    </div>

                    <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
                        <p>This is an automated signal from NovAlgo - Pine Script Signal Monitor</p>
                        <p>⚠️ This is not financial advice. Always do your own research before trading.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Attach HTML body
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['sender_email'], self.email_config['sender_password'])
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"Email error: {str(e)}")
            return False

    def notify_signal(self, signal_data: Dict, send_webhook: bool = True, send_email: bool = True) -> Dict:
        """
        Send notifications for a signal

        Args:
            signal_data: Dictionary containing signal information
            send_webhook: Whether to send webhook notification
            send_email: Whether to send email notification

        Returns:
            Dictionary with notification results
        """
        results = {
            'webhook_sent': False,
            'email_sent': False,
            'errors': []
        }

        if send_webhook:
            results['webhook_sent'] = self.send_webhook(signal_data)
            if not results['webhook_sent']:
                results['errors'].append('Webhook failed')

        if send_email:
            results['email_sent'] = self.send_email(signal_data)
            if not results['email_sent']:
                results['errors'].append('Email failed')

        return results
