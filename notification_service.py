"""
Notification Service
Handles sending email alerts via SMTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

class NotificationService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SMTP_EMAIL')
        self.sender_password = os.getenv('SMTP_PASSWORD')
        
    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = True) -> bool:
        """
        Send an email notification
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            is_html: Whether body is HTML
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.sender_email or not self.sender_password:
            print("⚠️ SMTP credentials not configured")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
            
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

    @staticmethod
    def get_alert_template(symbol: str, alert_type: str, message: str, price: float) -> str:
        """Generate HTML template for trade alert"""
        color = "#00c853" if "bullish" in alert_type.lower() or "above" in alert_type.lower() or "long" in alert_type.lower() else "#ff1744"
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
                <div style="background-color: {color}; color: white; padding: 20px; text-align: center;">
                    <h2 style="margin: 0;">🚀 Trade Alert: {symbol}</h2>
                </div>
                <div style="padding: 20px;">
                    <p style="font-size: 18px;"><strong>Alert Type:</strong> {alert_type}</p>
                    <p style="font-size: 16px;">{message}</p>
                    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 4px; margin: 20px 0;">
                        <p style="margin: 0; font-size: 24px; font-weight: bold;">Current Price: ${price:.2f}</p>
                    </div>
                    <p style="color: #666; font-size: 12px;">
                        This is an automated alert from DashTrade. 
                        <a href="#">Open Dashboard</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
