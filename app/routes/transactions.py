from flask import Blueprint, request, jsonify
from flasgger.utils import swag_from
from werkzeug.exceptions import BadRequest, NotFound
from decimal import Decimal
from datetime import datetime
from app.database.mock_database import get_mock_db, generate_transaction_id
from app.core.auth import get_current_user
from app.services.email.utils import send_email_async
from app.services.invoice.invoice_generator import generate_invoice

transactions_bp = Blueprint('transactions', __name__)
mock_db = get_mock_db()

@transactions_bp.before_request
def validate_content_type():
    """Ensure Content-Type is application/json for POST requests."""
    print("🔍 Request Headers:", request.headers)  # Debugging
    print("🔍 Content-Type:", request.content_type)  # Debugging

    if request.method in ['POST', 'PUT', 'PATCH']:
        if not request.content_type or 'application/json' not in request.content_type:
            request.environ['CONTENT_TYPE'] = 'application/json'

        try:
            request.get_json()
        except BadRequest:
            return jsonify({"detail": "Invalid JSON payload."}), 400


@transactions_bp.route('/deposit/', methods=['POST'])
@swag_from({
    "tags": ["transactions"],
    "summary": "Deposit Money",
    "description": "Deposits money into a user account.",
    "consumes": ["application/json"],  # ✅ Force Swagger to recognize JSON input
    "produces": ["application/json"],
    "parameters": [
        {
            "in": "body",  # ✅ Ensure parameters appear in the request body
            "name": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "example": 100,
                        "description": "The amount to deposit"
                    },
                    "receiver_id": {
                        "type": "integer",
                        "example": 1,
                        "description": "The ID of the receiver account"
                    }
                },
                "required": ["amount", "receiver_id"]
            }
        }
    ],
    "responses": {
        "200": {"description": "Deposit successful"},
        "400": {"description": "Invalid deposit amount"},
        "404": {"description": "Account not found"}
    },
    "security": [{"Bearer": []}]
})

def deposit():
    """Handles deposits for authenticated users."""
    if not request.is_json:
        return jsonify({"detail": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415

    try:
        data = request.get_json()
        print("🔍 Parsed JSON Data:", data)

        if not data or "amount" not in data or "receiver_id" not in data:
            return jsonify({"detail": "Missing required fields: amount and receiver_id"}), 400

        if data["amount"] <= 0:
            return jsonify({"detail": "Deposit amount must be greater than zero"}), 400

        current_user = get_current_user()
        if not current_user:
            return jsonify({"detail": "Unauthorized"}), 401

        account = mock_db["accounts"].get(data["receiver_id"])
        if not account or account["user_id"] != current_user["id"]:
            return jsonify({"detail": "Account not found or unauthorized"}), 404

        account["balance"] += Decimal(str(data["amount"]))

        # 🔹 Generate transaction ID (Fix applied)
        transaction_id = max((t["id"] for t in mock_db["transactions"]), default=0) + 1

        # 🔹 Store transaction
        new_transaction = {
            "id": transaction_id,
            "type": "deposit",
            "receiver_id": data["receiver_id"],
            "amount": data["amount"],
            "timestamp": datetime.utcnow().isoformat()
        }
        mock_db["transactions"].append(new_transaction)  # Append to list ✅

        return jsonify({
            "message": "Deposit successful",
            "transaction_id": transaction_id,
            "balance": account["balance"]
        })

    except (TypeError, ValueError):
        return jsonify({"detail": "Invalid JSON format or data types"}), 400


@transactions_bp.route('/withdraw/', methods=['POST'])
@swag_from({
    "tags": ["transactions"],
    "summary": "Withdraw Money",
    "description": "Withdraws money from a user account.",
    "consumes": ["application/json"],  # ✅ Ensure Swagger UI accepts JSON input
    "produces": ["application/json"],
    "parameters": [
        {
            "in": "body",  # ✅ Forces Swagger UI to show input fields
            "name": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "example": 50,
                        "description": "Amount to withdraw"
                    },
                    "sender_id": {
                        "type": "integer",
                        "example": 1,
                        "description": "The ID of the sender account"
                    }
                },
                "required": ["amount", "sender_id"]
            }
        }
    ],
    "responses": {
        "200": {"description": "Withdrawal successful"},
        "400": {"description": "Insufficient funds"},
        "404": {"description": "Account not found"}
    },
    "security": [{"Bearer": []}]
})
def withdraw():
    """Handles withdrawals for authenticated users."""
    if not request.is_json:
        return jsonify({"detail": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415

    try:
        data = request.get_json()
        print("🔍 Parsed JSON Data:", data)

        if not data or "amount" not in data or "sender_id" not in data:
            return jsonify({"detail": "Missing required fields: amount and sender_id"}), 400

        if data["amount"] <= 0:
            return jsonify({"detail": "Withdrawal amount must be greater than zero"}), 400

        current_user = get_current_user()
        if not current_user:
            return jsonify({"detail": "Unauthorized"}), 401

        account = mock_db["accounts"].get(data["sender_id"])
        if not account or account["user_id"] != current_user["id"]:
            return jsonify({"detail": "Account not found or unauthorized"}), 404

        if account["balance"] < data["amount"]:
            return jsonify({"detail": "Insufficient funds"}), 400

        account["balance"] -= Decimal(str(data["amount"]))

        # 🔹 Generate transaction ID (Fix applied)
        transaction_id = max((t["id"] for t in mock_db["transactions"]), default=0) + 1

        # 🔹 Store transaction
        new_transaction = {
            "id": transaction_id,
            "type": "withdrawal",
            "sender_id": data["sender_id"],
            "amount": data["amount"],
            "timestamp": datetime.utcnow().isoformat()
        }
        mock_db["transactions"].append(new_transaction)  # Append to list ✅

        return jsonify({
            "message": "Withdrawal successful",
            "transaction_id": transaction_id,
            "balance": account["balance"]
        })

    except (TypeError, ValueError):
        return jsonify({"detail": "Invalid JSON format or data types"}), 400
    
    
@transactions_bp.route('/transfer/', methods=['POST'])
@swag_from({
    "tags": ["transactions"],
    "summary": "Transfer Money",
    "description": "Transfers money between two accounts.",
    "consumes": ["application/json"],  # ✅ Ensure Swagger UI accepts JSON input
    "produces": ["application/json"],
    "parameters": [
        {
            "in": "body",  # ✅ Forces Swagger UI to show input fields
            "name": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "sender_id": {
                        "type": "integer",
                        "example": 1,
                        "description": "The ID of the sender account"
                    },
                    "receiver_id": {
                        "type": "integer",
                        "example": 2,
                        "description": "The ID of the receiver account"
                    },
                    "amount": {
                        "type": "number",
                        "example": 75,
                        "description": "Amount to transfer"
                    }
                },
                "required": ["sender_id", "receiver_id", "amount"]
            }
        }
    ],
    "responses": {
        "200": {"description": "Transfer successful"},
        "400": {"description": "Insufficient funds or invalid amount"},
        "404": {"description": "Sender or receiver account not found"}
    },
    "security": [{"Bearer": []}]
})
def transfer():
    """Handles fund transfers between accounts."""
    print("🔍 Raw Request Body:", request.get_data(as_text=True))  # Debugging

    if not request.is_json:
        return jsonify({"detail": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415

    try:
        data = request.get_json()
        print("🔍 Parsed JSON Data:", data)  # Debugging

        if not data or "sender_id" not in data or "receiver_id" not in data or "amount" not in data:
            return jsonify({"detail": "Missing required fields: sender_id, receiver_id, amount"}), 400

        if data["amount"] <= 0:
            return jsonify({"detail": "Transfer amount must be greater than zero"}), 400

        current_user = get_current_user()
        if not current_user:
            return jsonify({"detail": "Unauthorized"}), 401

        sender = mock_db["accounts"].get(data["sender_id"])
        receiver = mock_db["accounts"].get(data["receiver_id"])

        if not sender or sender["user_id"] != current_user["id"]:
            return jsonify({"detail": "Sender account not found or unauthorized"}), 404
        if not receiver:
            return jsonify({"detail": "Receiver account not found"}), 404
        if sender["balance"] < data["amount"]:
            return jsonify({"detail": "Insufficient funds"}), 400

        # Deduct from sender, add to receiver
        sender["balance"] -= Decimal(str(data["amount"]))
        receiver["balance"] += Decimal(str(data["amount"]))

        # 🔹 Generate transaction ID (Fix applied)
        transaction_id = max((t["id"] for t in mock_db["transactions"]), default=0) + 1

        # 🔹 Store transaction
        new_transaction = {
            "id": transaction_id,
            "type": "transfer",
            "sender_id": sender["user_id"],
            "receiver_id": receiver["user_id"],
            "amount": data["amount"],
            "timestamp": datetime.utcnow().isoformat()
        }
        mock_db["transactions"].append(new_transaction)  # Append to list ✅

        print("✅ Transaction Saved:", new_transaction)  # Debugging Output

        return jsonify({
            "message": "Transfer successful",
            "transaction_id": transaction_id,
            "sender_balance": sender["balance"],
            "receiver_balance": receiver["balance"]
        })

    except (TypeError, ValueError):
        return jsonify({"detail": "Invalid JSON format or data types"}), 400
    
    
@transactions_bp.route('/', methods=['GET'])
@swag_from({
    'tags': ['transactions'],
    'summary': 'List Transactions',
    'description': 'Fetches all transactions associated with the authenticated user.',
    'responses': {
        200: {'description': 'Transaction list retrieved'}
    },
    'security': [{"Bearer": []}]  # 🔒 Require authentication
})
def list_transactions():
    """Fetches all transactions for the authenticated user."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"detail": "Unauthorized"}), 401

    print("🔍 All Transactions:", mock_db["transactions"])  # Debugging

    return jsonify(mock_db["transactions"])

@transactions_bp.route('/<int:id>', methods=['GET'])
@swag_from({
    'tags': ['transactions'],
    'summary': 'Retrieve transaction by ID',
    'description': 'Fetches details of a specific transaction by ID.',
    'parameters': [
        {'name': 'id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Transaction details retrieved successfully'},
        404: {'description': 'Transaction not found'}
    },
    'security': [{"Bearer": []}]  # 🔒 Require authentication
})

def get_transaction(id):
    """Fetches a specific transaction by ID."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"detail": "Unauthorized"}), 401

    print("🔍 Checking transaction ID:", id)  # Debugging

    # Corrected retrieval logic
    transaction = next((t for t in mock_db["transactions"] if t["id"] == id), None)

    if not transaction:
        print("❌ Transaction Not Found!")
        return jsonify({"detail": "Transaction not found"}), 404

    return jsonify(transaction)


@transactions_bp.route('/check-balance/', methods=['GET'])
@swag_from({
    'tags': ['transactions'],
    'summary': 'Check Account Balance',
    'description': 'Fetches the balance of a user account.',
    'parameters': [
        {'name': 'account_id', 'in': 'query', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Balance retrieved'},
        404: {'description': 'Account not found or unauthorized'}
    },
    'security': [{"Bearer": []}]  # 🔒 Require authentication
})
def check_balance():
    """Fetches the current balance of an account owned by the user."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"detail": "Unauthorized"}), 401
    account_id = request.args.get('account_id', type=int)
    account = mock_db["accounts"].get(account_id)
    if not account or account["user_id"] != current_user["id"]:
        raise NotFound("Account not found or unauthorized")

    return jsonify({"account_id": account_id, "balance": account["balance"]})

@transactions_bp.route('/<int:id>/check-balance', methods=['GET'])
@swag_from({
    'tags': ['transactions'],
    'summary': 'Check balance for a specific transaction',
    'description': 'Fetches the balance related to a specific transaction.',
    'parameters': [
        {'name': 'id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Balance retrieved successfully'},
        404: {'description': 'Transaction not found'}
    },
    'security': [{"Bearer": []}]  # 🔒 Require authentication
})

def check_transaction_balance(id):
    """Fetch the balance of a specific transaction."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"detail": "Unauthorized"}), 401

    print("🔍 Checking balance for transaction ID:", id)  # Debugging

    # Find the transaction in the list
    transaction = next((t for t in mock_db["transactions"] if t["id"] == id), None)

    if not transaction:
        return jsonify({"detail": "Transaction not found"}), 404

    # Identify the account involved
    account_id = transaction.get("receiver_id") or transaction.get("sender_id")
    if not account_id:
        return jsonify({"detail": "Transaction does not involve a specific account"}), 400

    # Retrieve the account balance
    account = mock_db["accounts"].get(account_id)
    if not account:
        return jsonify({"detail": "Account not found"}), 404

    return jsonify({"transaction_id": id, "balance": account["balance"]})
