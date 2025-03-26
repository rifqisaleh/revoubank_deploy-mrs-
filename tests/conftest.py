import pytest
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import create_app, db, get_db
from app.model.models import User, Account

TEST_DATABASE_URI = "sqlite:///:memory:"

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
    # Seed one user and account with all required fields
    user = User(username="testuser", email="test@example.com", password="testpass")
    db.session.add(user)
    db.session.commit()

    account = Account(
        user_id=user.id,
        account_type="savings",
        balance=1000.0
    )
    db.session.add(account)
    db.session.commit()

@pytest.fixture(autouse=True)
def override_get_db(monkeypatch):
    engine = create_engine(TEST_DATABASE_URI)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    @contextmanager
    def override():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # ✅ Patch the real get_db function from your app/__init__.py
    monkeypatch.setattr(get_db, "__code__", override.__code__)
