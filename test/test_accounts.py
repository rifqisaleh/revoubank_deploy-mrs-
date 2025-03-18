import pytest
import json
from flask import Flask
from app.routes.accounts import accounts_bp
from app.database.mock_database import get_mock_db, reset_dummy_data
from app.core.auth import create_access_token

# Initialize a test Flask app
app = Flask(__name__)
app.register_blueprint(accounts_bp, url_prefix="/accounts")
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

# Test Account Creation
def test_create_account(client, auth_header):
    new_account = {
        "account_type": "savings",
        "initial_balance": 1000.00
    }
    response = client.post("/accounts/", data=json.dumps(new_account), headers=auth_header, content_type="application/json")
    assert response.status_code == 201
    assert response.json["account_type"] == "savings"

# Test Listing Accounts
def test_list_accounts(client, auth_header):
    response = client.get("/accounts/", headers=auth_header)
    assert response.status_code == 200
    assert isinstance(response.json, list)

# Test Getting Specific Account
def test_get_account(client, auth_header):
    response = client.get("/accounts/2", headers=auth_header)
    assert response.status_code in [200, 404]  # 200 if account exists, 404 if not

# Test Updating Account
def test_update_account(client, auth_header):
    updated_data = {
        "account_type": "checking",
        "balance": 1500.00
    }
    response = client.put("/accounts/2", data=json.dumps(updated_data), headers=auth_header, content_type="application/json")
    assert response.status_code in [200, 404]  # 200 if account exists, 404 if not

# Test Deleting Account
def test_delete_account(client, auth_header):
    response = client.delete("/accounts/2", headers=auth_header)
    assert response.status_code in [200, 404]  # 200 if account exists, 404 if not
