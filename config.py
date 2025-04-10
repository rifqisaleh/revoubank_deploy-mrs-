from dotenv import load_dotenv
load_dotenv()

import os 

print("🔍 CONFIG: DATABASE_URL =", os.getenv("DATABASE_URL"))

from datetime import timedelta


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
    SECRET_KEY = os.environ["SECRET_KEY"]
    DATABASE_URL = os.environ["DATABASE_URL"]
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    
    MAX_FAILED_ATTEMPTS = 4
    LOCK_DURATION = timedelta(minutes=15)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    LOG_LEVEL = "INFO"

class ProductionConfig(Config):
    LOG_LEVEL = "WARNING"    

    


