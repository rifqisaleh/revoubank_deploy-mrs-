from app import create_app
from app.database.db import db
from app.model import User, Account, Transaction
from app.model.models import Base  # For Transaction models using declarative_base

app = create_app()

with app.app_context():
    print("🔍 Creating db.Model tables...")
    db.create_all()  # Handles User, Account

    print("🔍 Creating Base metadata tables...")
    Base.metadata.create_all(db.engine)  # Handles Transaction, ExternalTransaction, BillPayment

    print("✅ All tables created.")
