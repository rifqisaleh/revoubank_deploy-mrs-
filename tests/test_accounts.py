import pytest
from flask import current_app
from app.model.models import User, Account
from app.routes.accounts import accounts_bp
from unittest.mock import patch, MagicMock
from app.routes import accounts as accounts_module
from flask_jwt_extended import create_access_token

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
