import pytest
from app.core.auth import authenticate_user
from app.utils.user import hash_password
from app.model.models import User  # Import the User class
from flask import url_for  # Import url_for for generating URLs

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
    login_response = client.post('/login', data={
        "username": "unverified",
        "password": "Unverified123"
    })

    # Assert that login fails due to unverified account
    assert login_response.status_code == 403
    assert "Account not verified. Please check your email." in login_response.get_data(as_text=True)


def test_login_after_verification(client, mock_send_email):
    # Register user and mock email sending
    response = client.post('/users/', json={
        "email": "verifieduser@mail.com",
        "full_name": "Verified User",
        "password": "Verified123",
        "phone_number": "081234567890",
        "username": "verifieduser"
    })
    
    # Simulate email verification process (you'll need to get the actual token here)
    token = "actual_token_from_email_verification"  # Replace with real token extraction logic
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    client.get(verify_url)  # Confirm the email

    # Now try logging in after verification
    login_response = client.post('/login', data={
        "username": "verifieduser",
        "password": "Verified123"
    })

    # Assert successful login
    assert login_response.status_code == 200
    assert "access_token" in login_response.json  # Ensure access token is returned

