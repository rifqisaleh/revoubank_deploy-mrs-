import os
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from app.config import Config  # Import configuration

def send_email(subject: str, recipient: str, body: str, attachment_path: str = None):
    """Mock or Real Email Sending Based on Config"""

    if Config.MOCK_EMAIL:
        print(f"📧 [MOCK] Email to {recipient} - Subject: {subject}")
        print(f"📧 [MOCK] Email Body: {body[:100]}...")  # Print first 100 chars for preview
        if attachment_path:
            print(f"📧 [MOCK] Attachment: {attachment_path}")
        return  # Skip real email sending

    sender_email = Config.MAIL_USERNAME  
    sender_password = Config.MAIL_PASSWORD
    smtp_server = Config.MAIL_SERVER
    smtp_port = Config.MAIL_PORT

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient
    message["Subject"] = str(Header(subject, "utf-8"))

    # Attach the email body with UTF-8 encoding
    message.attach(MIMEText(body, "html", "utf-8"))

    # Attach file only if provided and exists
    if attachment_path and os.path.exists(attachment_path):
        try:
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(attachment_path)}")
                message.attach(part)
        except Exception as e:
            print(f"⚠️ Warning: Could not attach file {attachment_path}: {e}")

    # Send the email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure connection
            server.login(sender_email, sender_password)
            response = server.sendmail(sender_email, recipient, message.as_string())

        # ✅ Handle SMTP response properly
        if not response:
            print(f"📧 Email sent to {recipient} successfully!")
        else:
            print(f"⚠️ Warning: SMTP response received - {response}")

    except smtplib.SMTPException as e:
        print(f"❌ Error sending email: {e}")

def send_email_async(subject: str, recipient: str, body: str, attachment_path: str = None):
    """Send email asynchronously with mock mode support."""
    if Config.MOCK_EMAIL:
        send_email(subject, recipient, body, attachment_path)  # Run it immediately in mock mode
    else:
        thread = threading.Thread(target=send_email, args=(subject, recipient, body, attachment_path))
        thread.start()
