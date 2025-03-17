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
    message["Subject"] = str(Header(subject, "utf-8"))  # ✅ Proper UTF-8 encoding for subject

    # Attach email body with UTF-8 encoding
    message.attach(MIMEText(body, "html", "utf-8"))

    # Attach file only if provided and exists
    if attachment_path:
        if os.path.exists(attachment_path):
            try:
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(attachment_path)}")
                    message.attach(part)
            except Exception as e:
                print(f"⚠️ Warning: Could not attach file {attachment_path}: {e}")
        else:
            print(f"⚠️ Warning: Attachment file not found: {attachment_path}")

    # Retry sending the email up to 3 times if an error occurs
    for attempt in range(3):
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # Secure connection
                server.login(sender_email, sender_password)
                response = server.sendmail(sender_email, recipient, message.as_string())

            # ✅ Correctly handle SMTP response
            if isinstance(response, dict) and not response:  # Empty dictionary means success
                print(f"📧 Email sent to {recipient} successfully!")
                return
            else:
                print(f"⚠️ Warning: Unexpected SMTP response - {response}")

        except smtplib.SMTPException as e:
            print(f"❌ Error sending email (Attempt {attempt+1}): {e}")
            time.sleep(2)  # Wait before retrying

    print(f"❌ Failed to send email to {recipient} after 3 attempts.")

def send_email_async(subject: str, recipient: str, body: str, attachment_path: str = None):
    """Send email asynchronously using threading to avoid blocking the main process."""
    thread = threading.Thread(target=send_email, args=(subject, recipient, body, attachment_path))
    thread.start()
