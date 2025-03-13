import pytest
import random
from fastapi.testclient import TestClient
from app.main import app
from app.core.auth import create_access_token
from app.database.mock_database import reset_dummy_data, get_mock_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    """ Reset the mock database before each test """
    reset_dummy_data()
    mock_db = get_mock_db()
    assert 1 in mock_db["users"], "Admin user is missing after reset!"
    mock_db["users"][1]["email"] = "admin@example.com"  # Ensure email is present
    mock_db["users"][1]["full_name"] = "Admin User"  # Ensure full_name is present

@pytest.fixture
def test_user():
    return {
        "username": "admin",  # Use existing admin user
        "password": "admin123",  # Admin's correct password
        "email": "admin@example.com",
        "full_name": "Admin User",
        "phone_number": "1234567890"
    }

def test_authenticate_user(test_user):
    response = client.post("/token", data={
        "username": test_user["username"],
        "password": test_user["password"]
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})

    if response.status_code != 200:
        print(f"Auth Error: {response.json()}")  # Debugging output

    assert response.status_code == 200, f"Response: {response.json()}"
    assert "access_token" in response.json()

def test_authenticate_invalid_user(test_user):
    response = client.post("/token", data={
        "username": test_user["username"],
        "password": "wrongpassword"
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})

    if response.status_code not in [400, 401]:
        print(f"Invalid Auth Error: {response.json()}")  # Debugging output

    assert response.status_code in [400, 401]  # Adjusted to handle different error codes

def test_get_current_user(test_user):
    token = create_access_token({"sub": "1"})  # Use correct user ID (Admin User)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/me", headers=headers)

    if response.status_code != 200:
        print(f"Profile Fetch Error: {response.json()}")  # Debugging output

    assert response.status_code == 200, f"Response: {response.json()}"
    user_data = response.json()
    assert user_data["username"] == "admin"
    assert "email" in user_data, "Email field missing!"  # Ensure email is present