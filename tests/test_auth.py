import pytest
from app.core.auth import authenticate_user
from app.utils.user import hash_password
from app.model.models import User  # Import the User class

def test_authenticate_valid_user(test_db):
    user = User(
        username="testuser",
        password=hash_password("testpass"),
        email="test@example.com",
        full_name="Test User",
        phone_number="123456789"
    )
    test_db.add(user)
    test_db.commit()

    result = authenticate_user("testuser", "testpass", test_db)
    assert result is not None
    assert result["username"] == "testuser"


def test_authenticate_invalid_user(test_db):
    from app.core.auth import authenticate_user

    result = authenticate_user("wronguser", "wrongpass", test_db)
    assert result is None