import os
import smtplib
from email.message import EmailMessage
from typing import Optional
import logging

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "your_email@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your_app_password")

def send_email_sync(to_email: str, subject: str, content: str, is_html: bool = False) -> bool:
    """
    Synchronous email sender used by Celery tasks.
    """
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = SMTP_USER
        msg['To'] = to_email

        if is_html:
            msg.add_alternative(content, subtype='html')
        else:
            msg.set_content(content)

        # Connect to SMTP server and send
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
            
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        raise e 