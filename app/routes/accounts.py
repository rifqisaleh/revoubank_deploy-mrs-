from flask import Blueprint, request, jsonify, make_response
from flasgger.utils import swag_from
from app.model.models import Account
from app.model.models import db
from app.core.auth import get_current_user
from app.schemas import AccountCreate, AccountResponse
from decimal import Decimal
from datetime import datetime
from app.services.email.utils import send_email_async
from app.services.invoice.invoice_generator import generate_invoice

accounts_bp = Blueprint('accounts', __name__)


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
    if not request.is_json:
        return make_response(jsonify({"detail": "Unsupported Media Type"}), 415)

    current_user = get_current_user()
    if not current_user:
        return make_response(jsonify({"detail": "Unauthorized"}), 401)

    try:
        data = request.get_json()
        account_data = AccountCreate(**data)

        new_account = Account(
            user_id=current_user["id"],
            account_type=account_data.account_type.value,
            balance=Decimal(str(account_data.initial_balance))
        )

        db.session.add(new_account)
        db.session.commit()

        return jsonify(AccountResponse(
            id=new_account.id,
            user_id=new_account.user_id,
            account_type=new_account.account_type,
            balance=float(new_account.balance)
        ).dict()), 201

    except Exception as e:
        return make_response(jsonify({"detail": str(e)}), 400)

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
    
    try:
        accounts = Account.query.filter_by(
            user_id=current_user["id"],
            is_deleted=False
        ).all()
        
        return jsonify([
            AccountResponse(
                id=acc.id,
                user_id=acc.user_id,
                account_type=acc.account_type,
                balance=float(acc.balance)
            ).dict()
            for acc in accounts
        ])
    except Exception as e:
        return make_response(jsonify({"detail": str(e)}), 500)

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
    
    try:
        account = Account.query.filter_by(
            id=id,
            user_id=current_user["id"],
            is_deleted=False
        ).first()
        
        if not account:
            return make_response(jsonify({"detail": "Account not found or unauthorized"}), 404)
        
        return jsonify(AccountResponse(
            id=account.id,
            user_id=account.user_id,
            account_type=account.account_type,
            balance=float(account.balance)
        ).dict())
    except Exception as e:
        return make_response(jsonify({"detail": str(e)}), 500)

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
    if not request.is_json:
        return make_response(jsonify({"detail": "Unsupported Media Type"}), 415)

    current_user = get_current_user()
    if not current_user:
        return make_response(jsonify({"detail": "Unauthorized"}), 401)

    try:
        account = Account.query.filter_by(
            id=id,
            user_id=current_user["id"],
            is_deleted=False
        ).first()

        if not account:
            return make_response(jsonify({"detail": "Account not found or unauthorized"}), 404)

        data = request.get_json()
        account_update = AccountCreate(**data)

        account.balance = Decimal(str(account_update.initial_balance))
        account.account_type = account_update.account_type.value
        
        db.session.commit()

        return jsonify({
            "message": "Account updated successfully",
            "account": AccountResponse(
                id=account.id,
                user_id=account.user_id,
                account_type=account.account_type,
                balance=float(account.balance)
            ).dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return make_response(jsonify({"detail": str(e)}), 400)


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
    
    try:
        account = Account.query.filter_by(
            id=id,
            user_id=current_user["id"],
            is_deleted=False
        ).first()
        
        if not account:
            return make_response(jsonify({"detail": "Account not found or unauthorized"}), 404)
        
        account.is_deleted = True
        db.session.commit()

        return jsonify({"message": "Account marked as deleted, transactions remain intact."})
    except Exception as e:
        db.session.rollback()
        return make_response(jsonify({"detail": str(e)}), 500)
