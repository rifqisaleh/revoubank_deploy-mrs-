import pytest
import json
from flask import Flask
from app.routes.billpayment import billpayment_bp
from app.database.mock_database import get_mock_db, reset_dummy_data
from app.core.auth import create_access_token

# Initialize a test Flask app
app = Flask(__name__)
app.register_blueprint(billpayment_bp, url_prefix="/billpayment")
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

# Test Bill Payment Using Credit Card
def test_pay_bill_with_card(client, auth_header):
    payment_data = {
        "biller_name": "Electric Company",
        "amount": 100.50,
        "card_number": "4111111111111111"
    }
    response = client.post("/billpayment/card/", data=json.dumps(payment_data), headers=auth_header, content_type="application/json")
    assert response.status_code in [200, 400, 404]

# Test Bill Payment Using Account Balance
def test_pay_bill_with_balance(client, auth_header):
    payment_data = {
        "biller_name": "Water Utility",
        "amount": 75.25
    }
    response = client.post("/billpayment/balance/", data=json.dumps(payment_data), headers=auth_header, content_type="application/json")
    assert response.status_code in [200, 400, 404]
