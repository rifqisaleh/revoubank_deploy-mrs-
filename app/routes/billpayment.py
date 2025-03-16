from flask import Blueprint, request, jsonify, send_file
from flasgger.utils import swag_from
from decimal import Decimal
from datetime import datetime
from app.database.mock_database import get_mock_db, generate_transaction_id
from app.core.auth import get_current_user
from app.utils.verification import verify_card_number
from app.services.email.utils import send_email_async
from app.services.invoice.invoice_generator import generate_invoice

billpayment_bp = Blueprint('billpayment', __name__)
mock_db = get_mock_db()

@billpayment_bp.route("/billpayment/card/", methods=["POST"])
@swag_from({
    "summary": "Pay a bill using a credit card",
    "description": "Allows users to pay their bills using a credit card.",
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "parameters": [
        {
            "in": "body",
            "name": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "biller_name": {
                        "type": "string",
                        "example": "Electric Company",
                        "description": "The name of the biller"
                    },
                    "amount": {
                        "type": "number",
                        "example": 100.50,
                        "description": "The amount to pay"
                    },
                    "card_number": {
                        "type": "string",
                        "example": "4111111111111111",
                        "description": "The credit card number used for payment"
                    }
                },
                "required": ["biller_name", "amount", "card_number"]
            }
        }
    ],
    "responses": {
        "200": {"description": "Bill payment successful"},
        "400": {"description": "Invalid credit card or insufficient funds"},
        "404": {"description": "User account not found"}
    }
})
def pay_bill_with_card():
    """Handles bill payments using a credit card."""
    print("🔍 Raw Request Body:", request.get_data(as_text=True))  # Debugging

    if not request.is_json:
        return jsonify({"detail": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415

    try:
        data = request.get_json()
        print("🔍 Parsed JSON Data:", data)  # Debugging

        if not data or "biller_name" not in data or "amount" not in data or "card_number" not in data:
            return jsonify({"detail": "Missing required fields: biller_name, amount, card_number"}), 400

        amount = Decimal(data["amount"])
        if amount <= 0:
            return jsonify({"detail": "Amount must be greater than zero."}), 400

        current_user = get_current_user()
        user_account = next(
            (acc for acc in mock_db["accounts"].values() if acc["user_id"] == current_user["id"]),
            None
        )

        if not user_account:
            return jsonify({"detail": "User account not found."}), 404
        if user_account["balance"] < amount:
            return jsonify({"detail": "Insufficient balance."}), 400

        user_account["balance"] -= amount

        return jsonify({"message": f"Successfully paid ${amount} to {data['biller_name']} using a credit card."})

    except (TypeError, ValueError):
        return jsonify({"detail": "Invalid JSON format or data types"}), 400


@billpayment_bp.route("/billpayment/balance/", methods=["POST"])
@swag_from({
    "summary": "Pay a bill using account balance",
    "description": "Allows users to pay their bills using their account balance.",
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "parameters": [
        {
            "in": "body",
            "name": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "biller_name": {
                        "type": "string",
                        "example": "Water Utility",
                        "description": "The name of the biller"
                    },
                    "amount": {
                        "type": "number",
                        "example": 75.25,
                        "description": "The amount to pay"
                    }
                },
                "required": ["biller_name", "amount"]
            }
        }
    ],
    "responses": {
        "200": {"description": "Bill payment successful"},
        "400": {"description": "Insufficient funds"},
        "404": {"description": "User account not found"}
    }
})
def pay_bill_with_balance():
    """Handles bill payments using account balance."""
    print("🔍 Raw Request Body:", request.get_data(as_text=True))  # Debugging

    if not request.is_json:
        return jsonify({"detail": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415

    try:
        data = request.get_json()
        print("🔍 Parsed JSON Data:", data)  # Debugging

        if not data or "biller_name" not in data or "amount" not in data:
            return jsonify({"detail": "Missing required fields: biller_name, amount"}), 400

        amount = Decimal(data["amount"])
        if amount <= 0:
            return jsonify({"detail": "Amount must be greater than zero."}), 400

        current_user = get_current_user()
        user_account = next(
            (acc for acc in mock_db["accounts"].values() if acc["user_id"] == current_user["id"]),
            None
        )

        if not user_account:
            return jsonify({"detail": "User account not found."}), 404
        if user_account["balance"] < amount:
            return jsonify({"detail": "Insufficient balance."}), 400

        user_account["balance"] -= amount

        return jsonify({"message": f"Successfully paid ${amount} to {data['biller_name']} using account balance."})

    except (TypeError, ValueError):
        return jsonify({"detail": "Invalid JSON format or data types"}), 400
