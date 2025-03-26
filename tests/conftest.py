import pytest
from app import create_app, db
from flask import Flask

# Use in-memory SQLite for testing
TEST_DATABASE_URI = "sqlite:///:memory:"

@pytest.fixture
def test_app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": TEST_DATABASE_URI,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False
    })

    with app.app_context():
        db.create_all()  # Create schema in-memory
        yield app
        db.session.remove()
        db.drop_all()  # Clean up after test
