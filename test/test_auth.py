import os
import pytest
from datetime import datetime, timedelta
from jose import jwt
from flask import Flask
from app.core.auth import create_access_token, authenticate_user, get_current_user
from app.database.mock_database import get_mock_db
from app.utils.user import verify_password

# Load environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Mock Flask request context
app = Flask(__name__)
mock_db = get_mock_db()

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_user():
    return {
        "id": 1,
        "username": "testuser",
        "password": "hashed_password",
        "email": "test@example.com",
        "full_name": "Test User",
        "phone_number": "1234567890",
        "failed_attempts": 0,
        "is_locked": False,
    }

# Test token creation
def test_create_access_token():
    data = {"sub": "1"}
    token = create_access_token(data)
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "1"
    assert "exp" in decoded

def test_authenticate_user_success(mock_user):
    user = authenticate_user("testuser", "test123")  # Use correct plain password
    assert user is not None
    assert user["username"] == "testuser"


def test_authenticate_user_wrong_password(mock_user):
    mock_db["users"][mock_user["id"]] = mock_user
    with pytest.raises(Exception):
        authenticate_user("testuser", "wrong_password")

def test_authenticate_user_locked_account(mock_user):
    mock_user["is_locked"] = True
    mock_user["locked_time"] = datetime.now() - timedelta(minutes=5)
    mock_db["users"][mock_user["id"]] = mock_user
    with pytest.raises(Exception):
        authenticate_user("testuser", "hashed_password")

def test_get_current_user(client, mock_user):
    mock_db["users"][mock_user["id"]] = mock_user
    token = create_access_token({"sub": str(mock_user["id"])});
    with app.test_request_context(headers={"Authorization": f"Bearer {token}"}):
        user = get_current_user()
        assert user["username"] == "testuser"
