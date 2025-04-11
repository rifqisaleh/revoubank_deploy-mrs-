import os
from dotenv import load_dotenv

# Load environment variables from .env.test
load_dotenv(dotenv_path=".env.test", override=True)

# ✅ Abort early if not using test DB
db_url = os.getenv("DATABASE_URL", "")
assert "sqlite" in db_url, f"❌ NOT using a test database! Current DATABASE_URL: {db_url}"

import pytest
import contextlib
from app import create_app
from app.model.models import db as _db, User, Account, Transaction
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql import text
from unittest.mock import patch

# Use in-memory SQLite for test database
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": TEST_DATABASE_URL,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "JWT_SECRET_KEY": "test-secret",
        "SERVER_NAME": "localhost:5000",  # Ensure external URLs can be generated
    })

    with app.app_context():
        _db.create_all()  # Ensure tables are created
        yield app
        _db.drop_all()  # Drop the tables after tests


# Change the test setup to ensure the database is created and used correctly
@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    return engine


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a new session with test db"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()



@pytest.fixture(scope="session")
def tables(test_engine):
    """Create all tables and clean them up after the tests"""
    _db.metadata.create_all(bind=test_engine)
    yield
    _db.metadata.drop_all(bind=test_engine)


@pytest.fixture
def test_db(test_engine, tables):
    """Create a new session with test db"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(app, test_db, monkeypatch):
    import contextlib
    from app.routes import transactions, accounts
    from app.routes import auth  # ✅ only auth uses get_db
    from app.database.db import db as _db
    from sqlalchemy.orm import scoped_session

    @contextlib.contextmanager
    def override_get_db():
        yield test_db

    # ✅ Only patch the modules that use get_db()
    monkeypatch.setattr(transactions, "get_db", override_get_db)
    monkeypatch.setattr(accounts, "get_db", override_get_db)
    monkeypatch.setattr(auth, "get_db", override_get_db)

    _db.session = scoped_session(lambda: test_db)

    with app.app_context():
        _db.create_all()

    with app.test_client() as client:
        yield client




# ✅ Fixed seed function
def seed_test_data(session):
    user = User(id=1, username="testuser", email="test@example.com", password="hashed")
    account = Account(
        id=1,
        user_id=1,
        balance=1000,
        account_type="savings",
        account_number="1234567890"
    )
    transaction = Transaction(
        id=1,
        sender_id=1,
        type="deposit",
        amount=500
    )
    session.add_all([user, account, transaction])
    session.commit()


@pytest.fixture
def seeded_db(test_db):
    """Seed the database with initial data"""
    seed_test_data(test_db)
    return test_db


@pytest.fixture(scope="function")
def init_database(test_engine, test_db):
    """Setup and cleanup for each test"""
    _db.metadata.create_all(bind=test_engine)
    yield
    test_db.rollback()
    _db.metadata.drop_all(bind=test_engine)


@pytest.fixture
def clean_db(seeded_db):
    """Cleanup test data between tests"""
    seeded_db.execute(text("DELETE FROM accounts"))
    seeded_db.execute(text("DELETE FROM users"))
    seeded_db.commit()


@pytest.fixture
def test_app(client):
    return client


@pytest.fixture
def test_client(client):
    return client

