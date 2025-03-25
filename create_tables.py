from app import app, db
from app.model.models import models # Ensure models are imported

with app.app_context():
    db.create_all()
    print("✅ Tables created successfully.")
