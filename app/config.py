import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    MOCK_EMAIL = os.getenv("MOCK_EMAIL", "True").lower() == "true"
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.elasticemail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 2525))  # Convert to int
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

# Security & Database Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "f2d49c89bb3df7c107c9dd473bc36a8177fbf528bce83d012f4db34d1b6d0dbe")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///revoubank.db")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    


    
