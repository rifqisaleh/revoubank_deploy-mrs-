import pytest
import json
from flask import Flask
from app.routes.users import users_bp
from app.database.mock_database import get_mock_db, reset_dummy_data
from app.core.auth import create_access_token

# Initialize a test Flask app
app = Flask(__name__)
app.register_blueprint(users_bp, url_prefix="/users")
mock_db = get_mock_db()

@pytest.fixture
def client():
    reset_dummy_data()  # Ensure a clean database before each test
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_header():
    token = create_access_token({"sub": "2"})  # User ID 2 (testuser)
    return {"Authorization": f"Bearer {token}"}

# Test User Registration
def test_register_user(client):
    new_user = {
        "username": "newuser",
        "password": "newpassword",
        "email": "newuser@example.com",
        "full_name": "New User",
        "phone_number": "1231231234"
    }
    response = client.post("/users/", data=json.dumps(new_user), content_type="application/json")
    assert response.status_code == 201
    assert response.json["username"] == "newuser"

# Test User List Retrieval
def test_list_users(client, auth_header):
    response = client.get("/users/", headers=auth_header)
    assert response.status_code == 200
    assert any(user["username"] == "testuser" for user in response.json)

# Test Getting User Profile
def test_get_profile(client, auth_header):
    response = client.get("/users/me", headers=auth_header)
    assert response.status_code == 200
    assert response.json["username"] == "testuser"

# Test Updating User Profile
def test_update_profile(client, auth_header):
    updated_data = {
        "username": "updateduser",
        "password": "updatedpassword",
        "email": "updated@example.com",
        "full_name": "Updated User",
        "phone_number": "9876543210"
    }
    response = client.put("/users/me", data=json.dumps(updated_data), headers=auth_header, content_type="application/json")
    assert response.status_code == 200
    assert response.json["username"] == "updateduser"

# Test User Deletion
def test_delete_user(client, auth_header):
    response = client.delete("/users/2", headers=auth_header)
    assert response.status_code == 200
    assert response.json["message"] == "User deleted successfully"
