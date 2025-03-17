import os
import smtplib
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from app.config import Config  # Import configuration

def send_email(subject: str, recipient: str, body: str, attachment_path: str = None):
    sender_email = Config.MAIL_USERNAME  
    sender_password = Config.MAIL_PASSWORD
    smtp_server = Config.MAIL_SERVER
    smtp_port = Config.MAIL_PORT

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient
    message["Subject"] = str(Header(subject, "utf-8"))

    # Attach email body with UTF-8 encoding
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
    elif attachment_path:
        print(f"⚠️ Warning: Attachment file not found: {attachment_path}")

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure connection
            server.login(sender_email, sender_password)
            response = server.sendmail(sender_email, recipient, message.as_string())

        # ✅ Debugging Log
        print(f"🔍 SMTP Full Response: {response}")

        # ✅ Correct Handling of SMTP Responses
        if response == {}:  # Normal success case
            print(f"📧 Email successfully sent to {recipient}.")
        elif isinstance(response, tuple) and response[0] == 250:
            print(f"📧 Email successfully sent to {recipient} (SMTP 250 OK).")  # ✅ This is now correctly handled
        else:
            print(f"⚠️ Warning: Unexpected SMTP response, but email likely sent: {response}")

    except smtplib.SMTPException as e:
        # ✅ New Fix: Check if error is actually `(250, b'OK')`
        if isinstance(e.args, tuple) and e.args[0] == 250:
            print(f"📧 Email successfully sent to {recipient} (SMTP 250 OK, caught in exception).")
        else:
            print(f"❌ Real SMTP Exception: {e}")

def send_email_async(subject: str, recipient: str, body: str, attachment_path: str = None):
    """Send email asynchronously using threading to avoid blocking the main process."""
    thread = threading.Thread(target=send_email, args=(subject, recipient, body, attachment_path))
    thread.start()
