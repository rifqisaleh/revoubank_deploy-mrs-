import pytest
import random
from fastapi.testclient import TestClient
from app.main import app
from app.database.mock_database import reset_dummy_data, get_mock_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    """ Reset the mock database before each test but allow admin user """
    reset_dummy_data()
    mock_db = get_mock_db()

    # ✅ Ensure only the admin user remains
    assert list(mock_db["users"].keys()) == [1], "Mock database not properly reset!"
    assert mock_db["accounts"] == {}, "Mock database accounts not reset!"
    assert mock_db["transactions"] == [], "Mock database transactions not reset!"

@pytest.fixture
def test_user():
    return {
        "username": f"testuser_{random.randint(1000, 9999)}",  # Unique username
        "password": "securepassword",
        "email": f"testuser_{random.randint(1000, 9999)}@example.com",  # Unique email
        "full_name": "Test User",
        "phone_number": "1234567890"
    }

def test_register_user(test_user):
    response = client.post("/users/", json=test_user)
    assert response.status_code == 200, f"Error: {response.json()}"
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]

def test_register_duplicate_username(test_user):
    response1 = client.post("/users/", json=test_user)
    assert response1.status_code == 200, f"User registration failed: {response1.json()}"

    response2 = client.post("/users/", json=test_user)
    assert response2.status_code == 400, f"Unexpected Response: {response2.json()}"
    assert response2.json()["detail"] == "Username already taken"

def test_get_users(test_user):
    response = client.post("/users/", json=test_user)
    assert response.status_code == 200, f"User registration failed: {response.json()}"

    response = client.get("/users/")
    assert response.status_code == 200
    users = response.json()
    assert any(user["username"] == test_user["username"] for user in users), "Test user not found in user list"

def test_delete_user(test_user):
    response = client.post("/users/", json=test_user)
    assert response.status_code == 200, f"User registration failed: {response.json()}"

    user_id = response.json()["id"]

    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 200, f"User deletion failed: {response.json()}"
    assert response.json()["message"] == "User deleted successfully"

    response = client.get("/users/")
    assert response.status_code == 200
    assert not any(user["username"] == test_user["username"] for user in response.json()), "Deleted user still exists"
