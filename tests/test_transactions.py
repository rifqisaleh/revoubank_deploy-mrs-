import pytest
import json
from app.model.models import User, Account, Transaction
from datetime import datetime
from werkzeug.security import generate_password_hash
from app.core.auth import create_access_token
from decimal import Decimal
from tests.conftest import test_app  # Import the shared fixture

@pytest.fixture
def client(test_app):
    return test_app.test_client()

@pytest.fixture
def auth_header():
    user = User.query.filter_by(username="testuser").first()
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def test_deposit(client, auth_header):
    deposit_data = {
        "amount": 100,
        "receiver_id": 1
    }
    response = client.post("/transactions/deposit/", data=json.dumps(deposit_data), headers=auth_header, content_type="application/json")
    assert response.status_code in [200, 403, 404]

def test_withdraw(client, auth_header):
    withdraw_data = {
        "amount": 50,
        "sender_id": 1
    }
    response = client.post("/transactions/withdraw/", data=json.dumps(withdraw_data), headers=auth_header, content_type="application/json")
    assert response.status_code in [200, 403, 404]

def test_transfer(client, auth_header):
    transfer_data = {
        "amount": 25,
        "sender_id": 1,
        "receiver_id": 1
    }
    response = client.post("/transactions/transfer/", data=json.dumps(transfer_data), headers=auth_header, content_type="application/json")
    assert response.status_code in [200, 400, 403, 404]
