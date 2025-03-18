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
    SECRET_KEY = os.getenv("SECRET_KEY", "84f4e045089970717269bb0c86ec9530e86080b3fb65c374bccd47c16e2bf3a2")
    DATABASE_URL = os.getenv("DATABASE_URL", "mock")  # Use 'mock' explicitly
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    

print(f"🔍 MOCK_EMAIL Loaded: {Config.MOCK_EMAIL}")
    
