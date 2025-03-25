from app import create_app
from app.database.db import db  # or from app import db, depending on your setup
from app.model import models  # Make sure this import triggers all model declarations

app = create_app()

with app.app_context():
    db.create_all()
    print("✅ Tables created.")
