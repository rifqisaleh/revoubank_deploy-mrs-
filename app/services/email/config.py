# app/email/config.py

from fastapi_mail import ConnectionConfig
import os
from dotenv import load_dotenv

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.mailtrap.io"),
    MAIL_FROM_NAME="RevouBank",
    MAIL_STARTTLS=True,   
    MAIL_SSL_TLS=False,   
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)
