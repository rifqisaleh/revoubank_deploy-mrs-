import pytest
from app.core.auth import authenticate_user

def test_authenticate_valid_user(test_app):
    from app import db
    user = authenticate_user("testuser", "testpass", db.session)
    assert user["username"] == "testuser"


def test_authenticate_invalid_user(test_app):
    from app import db
    user = authenticate_user("nonexistent", "wrongpass", db.session)
    assert user is None

