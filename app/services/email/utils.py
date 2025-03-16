import os
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from app.config import Config  # Corrected import

def send_email(subject: str, recipient: str, body: str, attachment_path: str = None):
    sender_email = Config.MAIL_USERNAME  
    sender_password = Config.MAIL_PASSWORD
    smtp_server = Config.MAIL_SERVER
    smtp_port = Config.MAIL_PORT

    # Create the email message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient
    message["Subject"] = subject

    # Attach the email body
    message.attach(MIMEText(body, "html"))

    # Attach a file if provided
    if attachment_path:
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(attachment_path)}",
        )
        message.attach(part)

    # Send the email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient, message.as_string())
        print(f"Email sent to {recipient} successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

def send_email_async(subject: str, recipient: str, body: str, attachment_path: str = None):
    thread = threading.Thread(target=send_email, args=(subject, recipient, body, attachment_path))
    thread.start()
