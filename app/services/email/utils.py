import os
import threading
import sys
from flask_mail import Message
from app.core.extensions import mail
from flask import current_app
from config import Config

def send_email(subject, recipient, body, attachment_path=None):
    if Config.MOCK_EMAIL:
        print("📧 [MOCK EMAIL] Triggered")
        print(f"📧 [MOCK EMAIL] To: {recipient}")
        print(f"📧 [MOCK EMAIL] Subject: {subject}")
        print(f"📧 [MOCK EMAIL] Body:\n{body}")
        sys.stdout.flush()  # 🚨 THIS is the real fix
        return

    msg = Message(subject=subject, recipients=[recipient], html=body)

    if attachment_path and os.path.exists(attachment_path):
        with current_app.open_resource(attachment_path) as fp:
            msg.attach(
                filename=os.path.basename(attachment_path),
                content_type="application/pdf",
                data=fp.read()
            )

    try:
        mail.send(msg)
        print(f"📧 Email sent to {recipient}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")

def send_email_async(subject: str, recipient: str, body: str, attachment_path: str = None):
    """Send email asynchronously with mock mode support."""
    if Config.MOCK_EMAIL:
        send_email(subject, recipient, body, attachment_path)
    else:
        thread = threading.Thread(target=send_email, args=(subject, recipient, body, attachment_path))
        thread.start()
