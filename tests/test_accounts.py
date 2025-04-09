import pytest
import uuid
from flask import current_app, url_for
from app.model.models import User, Account
from app.routes.accounts import accounts_bp
from unittest.mock import patch, MagicMock
from app.routes import accounts as accounts_module
from flask_jwt_extended import create_access_token
from app.services.email.utils import send_email_async
from app.utils.token import generate_verification_token

@pytest.fixture
def test_user(test_db):
    user = User(
        username="johndoe",
        full_name="John Doe",
        email="johndoe@example.com",
        password="securepassword",
    )
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
def test_account(test_db, test_user):
    account = Account(
        user_id=test_user.id,
        account_type="Checking",
        balance=1000.0,
        account_number="1234567890"
    )
    test_db.add(account)
    test_db.commit()
    return account


def test_create_account(test_db, test_user):
    account = Account(
        user_id=test_user.id,
        account_type="Savings",
        balance=5000.0,
        account_number="0987654321"
    )
    test_db.add(account)
    test_db.commit()

    retrieved = test_db.query(Account).filter_by(account_number="0987654321").first()
    assert retrieved is not None
    assert retrieved.account_type == "Savings"
    assert retrieved.balance == 5000.0


def test_list_accounts(test_db, test_account):
    accounts = test_db.query(Account).all()
    assert isinstance(accounts, list)
    assert test_account in accounts


def test_get_account(test_db, test_account):
    retrieved = test_db.query(Account).filter_by(id=test_account.id).first()
    assert retrieved is not None
    assert retrieved.id == test_account.id


def test_update_account(test_db, test_account):
    test_account.balance = 2000.0
    test_db.commit()

    updated = test_db.query(Account).filter_by(id=test_account.id).first()
    assert updated.balance == 2000.0


def test_delete_account(test_db, test_account):
    test_db.delete(test_account)
    test_db.commit()

    deleted = test_db.query(Account).filter_by(id=test_account.id).first()
    assert deleted is None


@patch.object(accounts_module, "role_required", lambda *roles: (lambda f: f))
@patch("app.routes.accounts.get_current_user", return_value={"id": 1, "username": "admin_user", "role": "admin"})
@patch("app.routes.accounts.get_db")
@patch("app.core.authorization.verify_jwt_in_request", return_value=None)
@patch("app.core.authorization.get_jwt", return_value={"role": "admin"})
def test_list_user_accounts_with_pagination(mock_verify, mock_get_jwt, mock_get_db, mock_user, client):
    mock_db = MagicMock()

    account_data = {
        "id": 1,
        "user_id": 1,
        "account_type": "savings",
        "balance": 1000.0,
        "account_number": "abc123",
        "is_deleted": False
    }

    class MockAccount:
        def __init__(self, data):
            self.__dict__.update(data)

        def as_dict(self):
            return {
                "id": self.id,
                "user_id": self.user_id,
                "account_type": self.account_type,
                "balance": self.balance,
                "account_number": self.account_number
            }

    mock_account = MockAccount(account_data)
    account_query = MagicMock()
    account_query.count.return_value = 1
    account_query.offset.return_value = account_query
    account_query.limit.return_value = account_query
    account_query.all.return_value = [mock_account]

    mock_db.query.return_value.filter_by.return_value = account_query
    mock_get_db.return_value.__next__.return_value = mock_db

    response = client.get("/accounts/?page=1&per_page=1")

    assert response.status_code == 200
    assert response.json["accounts"][0]["account_number"] == "abc123"


@patch("app.routes.users.send_email_async")  # Patch where send_email_async is being used
def test_register_user_sends_email(mock_send_email, test_db, client):
    # Register a new user
    response = client.post('/users/', json={
        "email": "testuser@mail.com",
        "full_name": "Test User",
        "password": "TestPassword123",
        "phone_number": "081234567890",
        "username": "testuser"
    })

    # Ensure registration succeeded
    assert response.status_code == 201
    assert response.json["email"] == "testuser@mail.com"
    
    # Check that the mock email sending function was called
    mock_send_email.assert_called_once()  # Ensure the email sending was triggered


@patch("app.routes.users.send_email_async")  # Patch send_email_async where it's used in app/routes/users.py
def test_verify_email(mock_send_email, client):
    # Generate a unique username for each test run
    unique_username = f"testuser_{uuid.uuid4().hex}"
    unique_email = f"{uuid.uuid4().hex}@test.com"  # Unique email address

    # Register a new user
    response = client.post('/users/', json={
        "email": unique_email,
        "full_name": "Test User",
        "password": "TestPassword123",
        "phone_number": "081234567890",
        "username": unique_username  # Use the unique username
    })
    
    print("Registration Response Data:", response.get_data(as_text=True))
    
    # Ensure registration succeeded
    assert response.status_code == 201
    assert response.json["email"] == unique_email  # Compare to the unique email used in the test

    # Get the actual token from the registration response
    user_data = response.json
    token = generate_verification_token(user_data['email'])  # Replace with real token generation

    # Generate the verification URL using the token
    verify_url = url_for('auth.verify_email', token=token, _external=True)

    # Simulate email verification process
    response = client.get(verify_url)

    # Check that email verification worked
    assert response.status_code == 200
    assert "Email verified successfully" in response.get_data(as_text=True)