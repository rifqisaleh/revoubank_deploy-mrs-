from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import Config  # Import database settings

# Load database URL from config.py
DATABASE_URL = Config.SQLALCHEMY_DATABASE_URI

# Create database engine
engine = create_engine(
    DATABASE_URL,
    pool_size=10,          # Allow up to 10 connections
    max_overflow=20,       # Allow extra temporary connections
    echo=True              # Enable SQL logging (for debugging)
)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()  #  Updated for SQLAlchemy 2.0

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test database connection
if __name__ == "__main__":
    try:
        with engine.connect() as conn:
            print(" Database connection successful!")
    except Exception as e:
        print(" Database connection failed:", e)
