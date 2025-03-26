from app.database.db import db
from app.database.db import SessionLocal

def get_db():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

def create_tables():
    from app.model import models  # ensure models are loaded
    db.create_all()
