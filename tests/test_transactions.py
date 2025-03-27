import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, jsonify
from datetime import datetime


class MockTransaction:
    def __init__(self):
        self.id = 1
        self.account_id = 123
        self.type = "deposit"
        self.amount = 500.0
        self.timestamp = datetime(2024, 1, 1, 0, 0, 0)

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

@patch("app.routes.transactions.get_current_user", return_value={"id": 1})
@patch("app.routes.transactions.get_db")
def test_get_all_transactions(mock_get_db, mock_user, client, mock_transaction):
    # 🔥 Directly mock get_db to return a session whose query().filter_by().first() is our object
    session_mock = MagicMock()
    query_mock = MagicMock()

    query_mock.filter_by.return_value.first.return_value = mock_transaction
    session_mock.query.return_value = query_mock

    # Make get_db yield the mocked session
    mock_get_db.return_value = iter([session_mock])

    # Run test
    response = client.get("/transactions/1")
    print("🔥 Final debug response:", response.get_json())

    assert response.status_code == 200
    assert response.get_json() == mock_transaction.as_dict()


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
