from fastapi_mail import ConnectionConfig
import os
from dotenv import load_dotenv

# Load environment variables from .env (only locally, not in deployment)
load_dotenv()

# Email Configuration
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

# Security & Database Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")  # Mock DB default
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
