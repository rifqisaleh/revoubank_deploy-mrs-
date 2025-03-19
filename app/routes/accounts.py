from flask import Blueprint, request, jsonify, make_response
from flasgger.utils import swag_from
from app.database.mock_database import get_mock_db, generate_account_id, generate_transaction_id, save_mock_db
from app.core.auth import get_current_user
from app.schemas import AccountCreate, AccountResponse
from decimal import Decimal
from datetime import datetime
from app.services.email.utils import send_email_async
from app.services.invoice.invoice_generator import generate_invoice

accounts_bp = Blueprint('accounts', __name__)
mock_db = get_mock_db()

@accounts_bp.route("/", methods=["POST"])
@swag_from({
    "tags": ["accounts"],
    "summary": "Create a new bank account",
    "description": "Creates a bank account for an authenticated user.",
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
                    "account_type": {
                        "type": "string",
                        "example": "savings",
                        "description": "Type of account (savings/checking)"
                    },
                    "initial_balance": {
                        "type": "number",
                        "example": 1000.00,
                        "description": "Initial balance for the account"
                    }
                },
                "required": ["account_type", "initial_balance"]
            }
        }
    ],
    "responses": {
        "201": {"description": "Account created successfully"},
        "401": {"description": "Unauthorized"},
        "404": {"description": "User not found"}
    }
})
def create_account():
    """Creates a bank account for the authenticated user."""
    print("🔍 Raw Request Body:", request.get_data(as_text=True))  # Debugging

    if not request.is_json:
        return make_response(jsonify({"detail": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415)

    try:
        current_user = get_current_user()
        if not current_user:
            return make_response(jsonify({"detail": "Unauthorized"}), 401)

        user_id = current_user["id"]
        if user_id not in mock_db["users"]:
            return make_response(jsonify({"detail": "User not found"}), 404)

        data = request.get_json()
        account = AccountCreate(**data)

        account_id = generate_account_id()
        mock_db["accounts"][account_id] = {
            "id": account_id,
            "user_id": user_id,
            "account_type": account.account_type.value,
            "balance": Decimal(str(account.initial_balance))
        }
        save_mock_db()  # ✅ Save to JSON so it persists

        return jsonify(AccountResponse(
            id=account_id,
            user_id=user_id,
            account_type=account.account_type.value,
            balance=account.initial_balance
        ).dict()), 201

    except (TypeError, ValueError):
        return make_response(jsonify({"detail": "Invalid JSON format or data types"}), 400)


@accounts_bp.route("/", methods=["GET"])
@swag_from({
    'tags': ['accounts'],
    'summary': 'List user accounts',
    'description': 'Retrieves all bank accounts associated with the authenticated user.',
    'responses': {
        200: {'description': 'List of accounts retrieved successfully'},
        401: {'description': 'Unauthorized'}
    }
})
def list_accounts():
    """Retrieves all accounts associated with the authenticated user."""
    current_user = get_current_user()
    if not current_user:
        return make_response(jsonify({"detail": "Unauthorized"}), 401)
    
    accounts = [
        AccountResponse(
            id=acc["id"],
            user_id=acc["user_id"],
            account_type=acc["account_type"],
            balance=acc["balance"]
        ).dict()
        for acc in mock_db["accounts"].values()
        if acc["user_id"] == current_user["id"]
    ]
    return jsonify(accounts)

@accounts_bp.route("/<int:id>", methods=["GET"])
@swag_from({
    'tags': ['accounts'],
    'summary': 'Retrieve a specific account',
    'description': 'Fetches details of a specific account owned by the authenticated user.',
    'parameters': [
        {'name': 'id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Account details retrieved successfully'},
        401: {'description': 'Unauthorized'},
        404: {'description': 'Account not found or unauthorized'}
    }
})
def get_account(id):
    """Fetches details of a specific account for the authenticated user."""
    current_user = get_current_user()
    if not current_user:
        return make_response(jsonify({"detail": "Unauthorized"}), 401)
    
    account = mock_db["accounts"].get(id)
    if not account or account["user_id"] != current_user["id"]:
        return make_response(jsonify({"detail": "Account not found or unauthorized"}), 404)
    
    return jsonify(account)

@accounts_bp.route("/<int:id>", methods=["PUT"])
@swag_from({
    "tags": ["accounts"],
    "summary": "Update an account",
    "description": "Updates account details (such as balance) for an authenticated user.",
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "parameters": [
        {
            "in": "path",  # ✅ This defines `id` in the URL
            "name": "id",
            "required": True,
            "schema": {
                "type": "integer"
            },
            "description": "ID of the account to update"
        },
        {
            "in": "body",
            "name": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "account_type": {
                        "type": "string",
                        "example": "checking",
                        "description": "Updated account type"
                    },
                    "balance": {
                        "type": "number",
                        "example": 1500.00,
                        "description": "Updated account balance"
                    }
                },
                "required": ["account_type", "balance"]
            }
        }
    ],
    "responses": {
        "200": {"description": "Account updated successfully"},
        "401": {"description": "Unauthorized"},
        "404": {"description": "Account not found or unauthorized"}
    }
})

def update_account(id):
    """Updates an account for the authenticated user."""
    print(f"🔍 Request Headers: {request.headers}")
    print(f"🔍 Raw Request Body: {request.get_data(as_text=True)}")

    if not request.is_json:
        return make_response(jsonify({"detail": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415)

    current_user = get_current_user()
    if not current_user:
        return make_response(jsonify({"detail": "Unauthorized"}), 401)

    try:
        print(f"🔍 All Accounts: {mock_db['accounts']}")
        print(f"🔍 Searching for Account ID: {id}")

        account = mock_db["accounts"].get(id)

        if account:
            print(f"🔍 Checking account ownership: Account User ID: {account.get('user_id')}, Current User ID: {current_user.get('id')}")

        if not account or account.get("user_id") != current_user.get("id"):
            return make_response(jsonify({"detail": "Account not found or unauthorized"}), 404)

        data = request.get_json()
        account_update = AccountCreate(**data)

        account["balance"] = Decimal(str(account_update.initial_balance))
        account["account_type"] = account_update.account_type.value
        save_mock_db()  # ✅ Persist account updates

        return jsonify({"message": "Account updated successfully", "account": account}), 200

    except (TypeError, ValueError) as e:
        print(f"❌ Error parsing JSON: {e}")
        return make_response(jsonify({"detail": "Invalid JSON format or data types"}), 400)


@accounts_bp.route("/<int:id>", methods=["DELETE"])
@swag_from({
    'tags': ['accounts'],
    'summary': 'Delete an account',
    'description': 'Deletes an account for the authenticated user (soft delete).',
    'parameters': [
        {'name': 'id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Account marked as deleted'},
        401: {'description': 'Unauthorized'},
        404: {'description': 'Account not found or unauthorized'}
    }
})

def delete_account(id):
    """Marks an account as deleted (soft delete) for the authenticated user."""
    current_user = get_current_user()
    if not current_user:
        return make_response(jsonify({"detail": "Unauthorized"}), 401)
    
    account = mock_db["accounts"].get(id)
    if not account or account["user_id"] != current_user["id"]:
        return make_response(jsonify({"detail": "Account not found or unauthorized"}), 404)
    
    account["deleted"] = True
    save_mock_db()  # ✅ Persist soft delete

    return jsonify({"message": "Account marked as deleted, transactions remain intact."})
