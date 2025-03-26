import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from app import create_app, db
from app.database import dependency as dependency_module
import app.database.db as db_module
from app.utils.user import hash_password

from app.model.models import User, Account, Transaction, Bill, Budget

TEST_DATABASE_URI = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URI)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def test_app():
    class TestConfig:
        TESTING = True
        SQLALCHEMY_DATABASE_URI = TEST_DATABASE_URI
        SQLALCHEMY_TRACK_MODIFICATIONS = False

    app = create_app(test_config=TestConfig.__dict__)

    with app.app_context():
        db.create_all()
        seed_test_data()
        yield app

def seed_test_data():
    user = User(
    username="testuser",
    email="test@example.com",
    password=hash_password("testpass")  # ✅ hashed password
)
    db.session.add(user)
    db.session.commit()

    account = Account(user_id=user.id, account_type="savings", balance=1000.0)
    db.session.add(account)
    db.session.commit()

    transaction = Transaction(type="deposit", amount=100)
    transaction.account = account  # ✅ Relationship-style assignment
    db.session.add(transaction)

    bill = Bill(amount=150.0, is_paid=False)
    bill.user = user  # ✅ set via relationship
    bill.title = "Electricity"  # <-- adjust to match actual column name if not `name`


    budget = Budget(user_id=user.id, category="Groceries", amount=300.0)
    db.session.add(budget)

    db.session.commit()

# ✅ Automatically override get_db + SessionLocal for all tests
@pytest.fixture(autouse=True)
def patch_db(monkeypatch):
    @contextmanager
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    monkeypatch.setattr("app.database.dependency.get_db", override_get_db)
    db_module.SessionLocal = TestingSessionLocal
