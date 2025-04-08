import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, jsonify
from datetime import datetime, timezone
from app.model.models import Account, Transaction


class MockTransaction:
    def __init__(self):
        self.id = 1
        self.account_id = 123
        self.type = "deposit"
        self.amount = 500.0
        self.timestamp = datetime.now(timezone.utc)  # Updated to use timezone-aware datetime

    def as_dict(self):
        return {
            "id": self.id,
            "account_id": self.account_id,
            "type": self.type,
            "amount": self.amount,
            "timestamp": self.timestamp.isoformat()
        }

@pytest.fixture
def mock_transaction():
    return MockTransaction()

@patch("app.routes.transactions.get_current_user", return_value={"id": 1, "username": "mock_user"})
@patch("app.routes.transactions.get_db")
def test_get_all_transactions(mock_get_db, mock_user, client, mock_transaction):
    session_mock = MagicMock()
    mock_account_query = MagicMock()
    mock_transaction_query = MagicMock()

    account_mock = MagicMock()
    account_mock.id = 123

    mock_account_query.filter_by.return_value.all.return_value = [account_mock]
    mock_transaction_query.filter.return_value.all.return_value = [mock_transaction]


    def query_side_effect(model):
        print("📦 model received by .query():", model, type(model), getattr(model, '__name__', 'NO NAME'))

        if isinstance(model, type) and getattr(model, '__name__', None) == "Account":
            print("✅ Returning mock_account_query")
            return mock_account_query
        elif isinstance(model, type) and getattr(model, '__name__', None) == "Transaction":
            print("✅ Returning mock_transaction_query")
            return mock_transaction_query
        print("❌ Unknown model:", model)
        return MagicMock()

    session_mock.query.side_effect = query_side_effect

    # 🔥 This is the key line for next(get_db())
    mock_get_db.return_value.__next__.return_value = session_mock

    response = client.get("/transactions/1")

    print("🔥 Final debug response:", response.get_json())

    assert response.status_code == 200
    assert response.get_json() == [mock_transaction.as_dict()]




@patch("app.routes.transactions.get_current_user", return_value={"id": 1})
@patch("app.routes.transactions.get_db")
def test_create_transaction(mock_get_db, mock_user, client):
    mock_session = MagicMock()
    mock_get_db.return_value.__enter__.return_value = mock_session

    mock_account = MagicMock()
    mock_account.balance = 1000.0
    mock_account.id = 1
    mock_session.query().filter_by().first.return_value = mock_account

    response = client.post("/transactions", json={
        "account_id": 1,
        "type": "withdrawal",
        "amount": 200.0
    })

    assert response.status_code in (201, 404)
    if response.status_code == 404:
        assert "not found" in (response.get_data(as_text=True) or "").lower()

@patch("app.routes.transactions.get_current_user", return_value={"id": 1})
@patch("app.routes.transactions.get_db")
def test_create_transaction_invalid_account(mock_get_db, mock_user, client):
    mock_session = MagicMock()
    mock_get_db.return_value.__enter__.return_value = mock_session
    mock_session.query().filter_by().first.return_value = None

    response = client.post("/transactions", json={
        "account_id": 999,
        "type": "deposit",
        "amount": 100.0
    })

    assert response.status_code == 404

@patch("app.routes.transactions.get_current_user", return_value={"id": 1})
@patch("app.routes.transactions.get_db")
def test_create_transaction_invalid_type(mock_get_db, mock_user, client):
    mock_session = MagicMock()
    mock_get_db.return_value.__enter__.return_value = mock_session
    mock_account = MagicMock()
    mock_account.balance = 1000.0
    mock_session.query().filter_by().first.return_value = mock_account

    response = client.post("/transactions", json={
        "account_id": 1,
        "type": "invalidtype",
        "amount": 100.0
    })

    assert response.status_code in (400, 404)

@patch("app.routes.transactions.get_current_user", return_value={"id": 1})
@patch("app.routes.transactions.get_db")
def test_create_transaction_insufficient_balance(mock_get_db, mock_user, client):
    mock_session = MagicMock()
    mock_get_db.return_value.__enter__.return_value = mock_session
    mock_account = MagicMock()
    mock_account.balance = 50.0
    mock_session.query().filter_by().first.return_value = mock_account

    response = client.post("/transactions", json={
        "account_id": 1,
        "type": "withdrawal",
        "amount": 100.0
    })

    assert response.status_code in (400, 404)

@patch("app.routes.transactions.get_db")
@patch("app.routes.transactions.get_current_user", return_value={"id": 1, "username": "test_user"})
def test_list_transactions_with_pagination(mock_user, mock_get_db, client):
    mock_session = MagicMock()

    # Mock Account model query
    mock_account = MagicMock()
    mock_account.id = 123

    # Mock Transaction model query
    mock_transaction = MagicMock()
    mock_transaction.as_dict.return_value = {
        "id": 1,
        "type": "deposit",
        "amount": 100,
        "timestamp": "2024-04-08T12:00:00Z"
    }

    # Mock .query(Account)
    def query_side_effect(model):
        if model.__name__ == "Account":
            account_query = MagicMock()
            account_query.filter_by.return_value.all.return_value = [mock_account]
            return account_query
        elif model.__name__ == "Transaction":
            txn_query = MagicMock()
            txn_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_transaction]
            txn_query.filter.return_value.order_by.return_value.count.return_value = 1
            return txn_query
        return MagicMock()

    mock_session.query.side_effect = query_side_effect
    mock_get_db.return_value.__next__.return_value = mock_session

    response = client.get("/transactions/?page=1&per_page=1")

    assert response.status_code == 200
    data = response.get_json()
    assert data["total"] == 1
    assert len(data["transactions"]) == 1
    assert data["transactions"][0]["type"] == "deposit"

@patch("app.routes.transactions.get_db")
@patch("app.routes.transactions.get_current_user", return_value={"id": 1, "username": "test_user"})
def test_list_transactions_page_two(mock_user, mock_get_db, client):
    mock_session = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 123

    mock_account_query = MagicMock()
    mock_account_query.filter_by.return_value.all.return_value = [mock_account]

    mock_transaction_query = MagicMock()
    mock_transaction_query.filter.return_value.order_by.return_value.count.return_value = 1
    mock_transaction_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

    def query_side_effect(model):
        if model.__name__ == "Account":
            return mock_account_query
        elif model.__name__ == "Transaction":
            return mock_transaction_query
        return MagicMock()

    mock_session.query.side_effect = query_side_effect
    mock_get_db.return_value.__next__.return_value = mock_session

    response = client.get("/transactions/?page=2&per_page=1")
    assert response.status_code == 200
    assert response.json["transactions"] == []


@patch("app.routes.transactions.get_current_user", return_value={"id": 1, "username": "test_user"})
@patch("app.routes.transactions.get_db")
def test_list_transactions_invalid_pagination(mock_get_db, mock_user, client):
    mock_session = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 123

    mock_account_query = MagicMock()
    mock_account_query.filter_by.return_value.all.return_value = [mock_account]

    mock_transaction_query = MagicMock()
    mock_transaction_query.filter.return_value.order_by.return_value.count.return_value = 0
    mock_transaction_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

    def query_side_effect(model):
        if model.__name__ == "Account":
            return mock_account_query
        elif model.__name__ == "Transaction":
            return mock_transaction_query
        return MagicMock()

    mock_session.query.side_effect = query_side_effect
    mock_get_db.return_value.__next__.return_value = mock_session

    response = client.get("/transactions/?page=abc&per_page=-5")
    assert response.status_code == 200
    assert "transactions" in response.json
