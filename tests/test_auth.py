import pytest
from app.core.auth import authenticate_user
from app.utils.user import hash_password
from app.model.models import User  # Import the User class
from app.utils.token import generate_verification_token
from flask import url_for  # Import url_for for generating URLs
from unittest.mock import patch

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


def test_login_blocked_for_unverified_user(client):
    # Register a new user (same as above)
    response = client.post('/users/', json={
        "email": "unverified@mail.com",
        "full_name": "Unverified User",
        "password": "Unverified123",
        "phone_number": "081234567890",
        "username": "unverified"
    })

    # Login with the newly registered user (but not verified)
    login_response = client.post('/login', json={
        "username": "unverified",  # Fixed: use the same username as registered
        "password": "Unverified123"
    })

    # Assert that login fails due to unverified account
    assert login_response.status_code == 403
    assert "Account not verified. Please check your email." in login_response.get_data(as_text=True)



@patch("app.routes.users.send_email_async")
def test_login_after_verification(mock_send_email, client):
    # Register a new user
    response = client.post('/users/', json={
        "email": "verifieduser@mail.com",
        "full_name": "Verified User",
        "password": "Verified123",
        "phone_number": "081234567890",
        "username": "verifieduser"
    })

    assert response.status_code == 201

    # Simulate email verification
    token = generate_verification_token("verifieduser@mail.com")
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    client.get(verify_url)

    # Try login
    login_response = client.post('/login', json={
        "username": "verifieduser",  # Fixed: use the same username as registered
        "password": "Verified123"
    })

    assert login_response.status_code == 200
    assert "access_token" in login_response.json
