import pytest
from app import create_app
from app.model.models import db as _db, User, Account, Transaction
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Use in-memory SQLite for fast and isolated tests
TEST_DATABASE_URL = "sqlite:///:memory:"

import pytest

# If your existing client fixture is named `client`
@pytest.fixture
def test_app(client):
    return client

@pytest.fixture
def test_client(client):
    return client


@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": TEST_DATABASE_URL,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    })

    with app.app_context():
        yield app

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    return engine

@pytest.fixture(scope="session")
def tables(test_engine):
    _db.metadata.create_all(bind=test_engine)
    yield
    _db.metadata.drop_all(bind=test_engine)

@pytest.fixture
def test_db(test_engine, tables):
    """Create a new database session for a test."""
    connection = test_engine.connect()
    transaction = connection.begin()

    session = sessionmaker(bind=connection)()
    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(app, test_db, monkeypatch):
    """
    Flask test client with test DB injected into the app context.
    """
    # Patch get_db to return our test_db session
    from app.routes import transactions

    def get_test_db():
        yield test_db

    monkeypatch.setattr(transactions, "get_db", get_test_db)

    with app.test_client() as client:
        yield client

# Optional fixture to insert test data
def seed_test_data(session):
    user = User(id=1, username="testuser", email="test@example.com", password="hashed")
    account = Account(id=1, user_id=1, balance=1000)
    transaction = Transaction(id=1, account_id=1, type="deposit", amount=500)

    session.add_all([user, account, transaction])
    session.commit()

@pytest.fixture
def seeded_db(test_db):
    seed_test_data(test_db)
    return test_db

@pytest.fixture(scope="function")
def init_database(test_engine, test_db):
    _db.metadata.create_all(bind=test_engine)
    yield
    test_db.rollback()
    _db.metadata.drop_all(bind=test_engine)
