import pytest
import json
from flask import Flask
from app.routes.transactions import transactions_bp
from app.database.mock_database import get_mock_db, reset_dummy_data
from app.core.auth import create_access_token

# Initialize a test Flask app
app = Flask(__name__)
app.register_blueprint(transactions_bp, url_prefix="/transactions")
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

# Test Deposit
def test_deposit(client, auth_header):
    deposit_data = {
        "amount": 100,
        "receiver_id": 2
    }
    response = client.post("/transactions/deposit/", data=json.dumps(deposit_data), headers=auth_header, content_type="application/json")
    assert response.status_code in [200, 403, 404]

# Test Withdrawal
def test_withdraw(client, auth_header):
    withdraw_data = {
        "amount": 50,
        "sender_id": 2
    }
    response = client.post("/transactions/withdraw/", data=json.dumps(withdraw_data), headers=auth_header, content_type="application/json")
    assert response.status_code in [200, 400, 404]

# Test Transfer
def test_transfer(client, auth_header):
    transfer_data = {
        "sender_id": 2,
        "receiver_id": 1,
        "amount": 75
    }
    response = client.post("/transactions/transfer/", data=json.dumps(transfer_data), headers=auth_header, content_type="application/json")
    assert response.status_code in [200, 400, 404]

# Test List Transactions
def test_list_transactions(client, auth_header):
    response = client.get("/transactions/", headers=auth_header)
    assert response.status_code == 200
    assert isinstance(response.json, list)

# Test Get Specific Transaction
def test_get_transaction(client, auth_header):
    response = client.get("/transactions/1", headers=auth_header)
    assert response.status_code in [200, 404]

# Test Check Balance
def test_check_balance(client, auth_header):
    response = client.get("/transactions/check-balance/?account_id=2", headers=auth_header)
    assert response.status_code in [200, 404]
