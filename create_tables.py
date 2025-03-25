from app.app import app
from app import db
from app.model import models

with app.app_context():
    db.create_all()
    print("✅ Tables created.")
