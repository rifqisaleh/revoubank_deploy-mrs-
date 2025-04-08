from flask import Blueprint, request, jsonify, make_response
from app.core.logger import logger
from flasgger.utils import swag_from
from app.model.models import Account
from app.model.models import db
from app.model.base import get_db
from app.core.auth import get_current_user
from app.core.authorization import role_required
from app.schemas import AccountCreate, AccountResponse
from decimal import Decimal
from datetime import datetime
from app.services.accounts.core import create_account_logic, list_user_accounts_logic, get_user_account_by_id_logic, update_user_account_logic, delete_user_account_logic
from app.utils.pagination import apply_pagination
from uuid import uuid4

accounts_bp = Blueprint('accounts', __name__)


@accounts_bp.route("/", methods=["POST"])
@role_required("user")
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
        "201": {
            "description": "Account created successfully",
            "schema": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "user_id": {"type": "integer", "example": 1},
                    "account_type": {"type": "string", "example": "savings"},
                    "balance": {"type": "number", "example": 1000.00},
                    "account_number": {"type": "string", "example": "a8efa499-7"}
                }
            }
        },
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
        db = next(get_db())
        data = request.get_json()

        account_response = create_account_logic(db, current_user, data)
        return jsonify(account_response.dict()), 201

    except Exception as e:
        return make_response(jsonify({"detail": str(e)}), 400)

@accounts_bp.route("/", methods=["GET"])
@role_required("admin")
@swag_from({
    'tags': ['accounts'],
    'summary': 'List user accounts',
    'description': 'Retrieves all bank accounts associated with the authenticated user.',
    'parameters': [
        {"name": "page", "in": "query", "type": "integer", "required": False, "default": 1},
        {"name": "per_page", "in": "query", "type": "integer", "required": False, "default": 10}
    ],
    'responses': {
        200: {'description': 'List of accounts retrieved successfully'},
        401: {'description': 'Unauthorized'}
    }
})
def list_user_accounts():
    db = next(get_db())
    current_user = get_current_user()

    try:
        query = db.query(Account).filter_by(is_deleted=False)
        total, paginated_accounts = apply_pagination(query)

        return jsonify({
            "total": total,
            "page": request.args.get("page", 1, type=int),
            "per_page": request.args.get("per_page", 10, type=int),
            "accounts": [acc.as_dict() for acc in paginated_accounts]
        })

    except Exception as e:
        logger.error(f"❌ Failed to retrieve accounts: {str(e)}")
        return jsonify({"detail": "Failed to retrieve accounts"}), 500



@accounts_bp.route("/<int:id>", methods=["GET"])
@role_required("user")
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
    db = next(get_db())

    if not current_user:
        return make_response(jsonify({"detail": "Unauthorized"}), 401)

    try:
        account_data = get_user_account_by_id_logic(db, current_user, id)
        return jsonify(account_data)
    except LookupError as e:
        return make_response(jsonify({"detail": str(e)}), 404)
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
    db = next(get_db())
    current_user = get_current_user()

    if not request.is_json:
        return make_response(jsonify({"detail": "Unsupported Media Type"}), 415)
    if not current_user:
        return make_response(jsonify({"detail": "Unauthorized"}), 401)

    try:
        update_data = request.get_json()
        updated_account = update_user_account_logic(db, current_user, id, update_data)
        return jsonify({
            "message": "Account updated successfully",
            "account": updated_account
        }), 200

    except LookupError as e:
        return make_response(jsonify({"detail": str(e)}), 404)
    except Exception as e:
        db.rollback()
        return make_response(jsonify({"detail": str(e)}), 400)



@accounts_bp.route("/<int:id>", methods=["DELETE"])
@role_required("user")
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
    db = next(get_db())
    current_user = get_current_user()

    if not current_user:
        return make_response(jsonify({"detail": "Unauthorized"}), 401)

    try:
        result = delete_user_account_logic(db, current_user, id)
        return jsonify(result)
    except LookupError as e:
        return make_response(jsonify({"detail": str(e)}), 404)
    except Exception as e:
        db.rollback()
        return make_response(jsonify({"detail": str(e)}), 500)

