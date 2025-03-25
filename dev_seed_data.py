from app import create_app
from app.database.db import db
from app.model.models import User, Account, Transaction
from app.utils.user import hash_password
from datetime import datetime

app = create_app()

with app.app_context():
    print("🔄 Seeding database...")

    # Clear existing data (dev only)
    Transaction.query.delete()
    Account.query.delete()
    User.query.delete()
    db.session.commit()

    # Create users
    admin = User(
        username="admin",
        password=hash_password("admin123"),
        email="admin@example.com",
        full_name="Admin User",
        phone_number="1234567890"
    )

    testuser = User(
        username="testuser",
        password=hash_password("test123"),
        email="testuser@example.com",
        full_name="Test User",
        phone_number="0987654321"
    )

    db.session.add_all([admin, testuser])
    db.session.commit()

    # Create accounts
    admin_account = Account(
        user_id=admin.id,
        account_type="savings",
        balance=1000.00
    )

    test_account = Account(
        user_id=testuser.id,
        account_type="checking",
        balance=500.00
    )

    db.session.add_all([admin_account, test_account])
    db.session.commit()

    # Create sample transaction
    transaction = Transaction(
        type="TRANSFER",
        amount=100.00,
        sender_id=test_account.id,
        receiver_id=admin_account.id,
        timestamp=datetime.utcnow()
    )

    db.session.add(transaction)
    db.session.commit()

    print("✅ Seed data inserted successfully.")
