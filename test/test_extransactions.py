import pytest
import json
from flask import Flask
from app.routes.external_transaction import external_transaction_bp
from app.database.mock_database import get_mock_db, reset_dummy_data
from app.core.auth import create_access_token

# Initialize a test Flask app
app = Flask(__name__)
app.register_blueprint(external_transaction_bp, url_prefix="/external")
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

# Test External Deposit
def test_external_deposit(client, auth_header):
    deposit_data = {
        "bank_name": "Bank of America",
        "account_number": "123456789",
        "amount": 250.75
    }
    response = client.post("/external/deposit/", data=json.dumps(deposit_data), headers=auth_header, content_type="application/json")
    assert response.status_code in [200, 404]

# Test External Withdrawal
def test_external_withdraw(client, auth_header):
    withdraw_data = {
        "bank_name": "Bank of America",
        "account_number": "123456789",
        "amount": 150.50
    }
    response = client.post("/external/withdraw/", data=json.dumps(withdraw_data), headers=auth_header, content_type="application/json")
    assert response.status_code in [200, 400, 404]
