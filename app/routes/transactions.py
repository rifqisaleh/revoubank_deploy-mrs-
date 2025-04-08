from flask import Blueprint, request, jsonify
from app.core.logger import logger
from flasgger.utils import swag_from
from werkzeug.exceptions import BadRequest, NotFound
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from app.model.base import get_db
from app.model.models import Account, Transaction, User
from app.core.auth import get_current_user
from app.services.transactions.core import handle_deposit, handle_withdrawal, handle_transfer
from app.core.authorization import role_required
from app.utils.pagination import apply_pagination

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.before_request
def validate_content_type():
    """Ensure Content-Type is application/json for POST requests."""
   

    if request.method in ['POST', 'PUT', 'PATCH']:
        if not request.content_type or 'application/json' not in request.content_type:
            request.environ['CONTENT_TYPE'] = 'application/json'

        try:
            request.get_json()
        except BadRequest:
            return jsonify({"detail": "Invalid JSON payload."}), 400


@transactions_bp.route('/deposit/', methods=['POST'])
@role_required('user')
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
    db = next(get_db())
    current_user = get_current_user()

    if not request.is_json:
        return jsonify({"detail": "Unsupported Media Type"}), 415

    try:
        data = request.get_json()
        amount = Decimal(str(data.get("amount")))
        receiver_id = int(data.get("receiver_id"))
        current_user = get_current_user()

        logger.info(f"📥 Deposit attempt by {current_user['username']} to account {receiver_id}")

        transaction, account = handle_deposit(db, current_user, amount, receiver_id)

        return jsonify({
            "message": "Deposit successful",
            "transaction_id": transaction.id,
            "balance": account.balance
        })

    except ValueError as e:
        db.rollback()
        logger.warning(f"⚠️ {e}")
        return jsonify({"detail": str(e)}), 400
    except LookupError:
        db.rollback()
        return jsonify({"detail": "Account not found"}), 404
    except PermissionError:
        db.rollback()
        return jsonify({"detail": "Unauthorized"}), 403
    except Exception as e:
        db.rollback()
        logger.error("❌ Error during deposit", exc_info=True)
        return jsonify({"detail": "Internal Server Error"}), 500



@transactions_bp.route('/withdraw/', methods=['POST'])
@role_required('user')
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
    db = next(get_db())
    
    if not request.is_json:
        return jsonify({"detail": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415

    try:
        data = request.get_json()
       
        if not data or "amount" not in data or "sender_id" not in data:
            return jsonify({"detail": "Missing required fields: amount and sender_id"}), 400

        try:
            data = request.get_json()
            amount = Decimal(str(data["amount"]))
            sender_id = int(data["sender_id"])
            current_user = get_current_user()
        except (ValueError, TypeError, Decimal.InvalidOperation):
            return jsonify({"detail": "Invalid amount or sender_id format"}), 400

        transaction, account = handle_withdrawal(db, current_user, amount, sender_id)

        logger.info(
                    f"✅ Withdrawal of ${amount} successful from account {sender_id} by user {current_user['username']} - Transaction ID: {transaction.id}"
)


        return jsonify({
            "message": "Withdrawal successful",
            "transaction_id": transaction.id,
            "balance": account.balance
        })

    except (TypeError, ValueError) as e:
        db.rollback()
        print(f"❌ Error in withdrawal: {e}")
        logger.error("❌ Error during withdrawal", exc_info=True)
        return jsonify({"detail": "Invalid JSON format or data types"}), 400
        


    
    
@transactions_bp.route('/transfer/', methods=['POST'])
@role_required('user')
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
    db = next(get_db())

    if not request.is_json:
        return jsonify({"detail": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415

    try:
        data = request.get_json()

        if not data or "sender_id" not in data or "receiver_id" not in data or "amount" not in data:
            return jsonify({"detail": "Missing required fields: sender_id, receiver_id, amount"}), 400

        try:
            amount = Decimal(str(data["amount"]))
            sender_id = int(data["sender_id"])
            receiver_id = int(data["receiver_id"])
        except (ValueError, TypeError, Decimal.InvalidOperation):
            return jsonify({"detail": "Invalid amount, sender_id, or receiver_id format"}), 400

        current_user = get_current_user()

        result = handle_transfer(db, current_user, amount, sender_id, receiver_id)

        if isinstance(result, tuple):
            transaction, sender = result
        else:
            # If handle_transfer returns a response instead of transaction
            return result  

        return jsonify({
            "message": "Transfer successful",
            "transaction_id": transaction.id,
            "sender_balance": sender.balance
        })

    except Exception as e:
        db.rollback()
        logger.error("❌ Error during transfer", exc_info=True)
        return jsonify({"detail": f"Internal Server Error: {str(e)}"}), 500



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
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"detail": "Unauthorized"}), 401
    
    logger.info(f"🔍 Fetching transactions for user {current_user['username']}")

    db = next(get_db())

    accounts = db.query(Account).filter_by(user_id=current_user["id"]).all()
    account_ids = [acc.id for acc in accounts]

    if not account_ids:
        return jsonify([])

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    transactions_query = db.query(Transaction).filter(
        (Transaction.sender_id.in_(account_ids)) |
        (Transaction.receiver_id.in_(account_ids))
    ).order_by(Transaction.timestamp.desc())

    total, transactions = apply_pagination(transactions_query, page, per_page)

    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "transactions": [t.as_dict() for t in transactions]
    })



@transactions_bp.route('/<int:user_id>', methods=['GET'])
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

def get_transaction_for_user(user_id):
    """Fetches a specific transaction by user ID."""
    current_user = get_current_user()

    if not current_user or current_user["id"] != user_id:
        logger.warning(f"⛔ User {current_user['username']} attempted to access transactions belonging to another user")
        return jsonify({"detail": "Unauthorized"}), 401
    
    logger.info(f"🔍 Transactions retrieved for user {current_user['username']}")

    db = next(get_db())

    # 🔍 DEBUG: Show all account IDs for the user
    accounts = db.query(Account).filter_by(user_id=user_id).all()
    account_ids = [acc.id for acc in accounts]
    

    # 🔍 DEBUG: Show matching transactions
    transactions = db.query(Transaction).filter(
        (Transaction.sender_id.in_(account_ids)) |
        (Transaction.receiver_id.in_(account_ids))
    ).all()
    

    return jsonify([t.as_dict() for t in transactions])



@transactions_bp.route('/check-balance/', methods=['GET'])
@role_required('user')
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
        logger.warning(f"⚠️ Transaction {id} not found for user {current_user['username']}")
        return jsonify({"detail": "Unauthorized"}), 401
    
    logger.info(f"🔍 Checking balance for user {current_user['username']}")

    account_id = request.args.get('account_id', type=int)
    db = next(get_db())
    account = db.query(Account).filter_by(id=account_id, user_id=current_user["id"]).first()

    if not account:
        raise NotFound("Account not found or unauthorized")

    return jsonify({"account_id": account_id, "balance": account.balance})

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
        logger.warning(f"⚠️ Transaction {id} not found for user {current_user['username']}")
        return jsonify({"detail": "Unauthorized"}), 401
    
    logger.info(f"🔍 Checking balance for transaction {id} for user {current_user['username']}")

    db = next(get_db())
    transaction = db.query(Transaction).filter_by(id=id).first()

    if not transaction:
        return jsonify({"detail": "Transaction not found"}), 404

    account_id = transaction.receiver_id or transaction.sender_id
    if not account_id:
        return jsonify({"detail": "Transaction does not involve a specific account"}), 400

    account = db.query(Account).filter_by(id=account_id).first()
    if not account:
        return jsonify({"detail": "Account not found"}), 404

    return jsonify({"transaction_id": id, "balance": account.balance})
