from flask import Blueprint, request, jsonify
from flasgger.utils import swag_from
from werkzeug.exceptions import BadRequest, NotFound
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from app.model.base import get_db
from app.model.models import Account, Transaction, User
from app.core.auth import get_current_user
from app.services.email.utils import send_email_async
from app.services.invoice.invoice_generator import generate_invoice

transactions_bp = Blueprint('transactions', __name__)

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
    db = next(get_db())
    
    if not request.is_json:
        return jsonify({"detail": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415

    try:
        data = request.get_json()
        print("🔍 Parsed JSON Data:", data)

        if not isinstance(data, dict):
            return jsonify({"detail": "Invalid request format"}), 400

        amount = data.get("amount")
        receiver_id = data.get("receiver_id")

        if amount is None or receiver_id is None:
            return jsonify({"detail": "Missing required fields: amount and receiver_id"}), 400

        try:
            amount = Decimal(str(amount))
            receiver_id = int(receiver_id)
        except (ValueError, TypeError, Decimal.InvalidOperation):
            return jsonify({"detail": "Invalid amount or receiver_id format"}), 400

        if amount <= 0:
            return jsonify({"detail": "Deposit amount must be greater than zero"}), 400

        current_user = get_current_user()
        if not current_user:
            return jsonify({"detail": "Unauthorized"}), 401

        account = db.query(Account).filter_by(id=receiver_id).first()
        if not account:
            return jsonify({"detail": "Account not found"}), 404
            
        if account.user_id != current_user["id"]:
            return jsonify({"detail": "Unauthorized to deposit to this account"}), 403

        account.balance += Decimal(str(amount))
        
        transaction = Transaction(
            type="deposit",
            amount=float(amount),
            receiver_id=receiver_id
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        # Generate invoice
        invoice_filename = f"invoice_{transaction.id}.pdf"
        invoice_path = generate_invoice(
        transaction_details={
            "id": transaction.id,  # Ensure ID is included
            "transaction_type": transaction.type,
            "amount": str(amount),
            "timestamp": transaction.timestamp.isoformat()
    },
        filename=invoice_filename,
        user=current_user,
)


        # Send email with invoice attachment
        user_email = current_user.get("email")
        if user_email:
            print(f"📧 Sending email to {user_email} with invoice attached")

            send_email_async(
                subject="Deposit Confirmation & Invoice",
                recipient=user_email,
                body=f"""
                Dear {current_user['username']},
                
                Your deposit of ${amount} has been processed successfully.
                Transaction ID: {transaction.id}
                New Balance: ${account.balance}

                Please find your invoice attached.

                Thank you for using our service.
                """,
                attachment_path=invoice_path  # Attach invoice
            )
        else:
            print("⚠️ No email found for user, skipping email notification.")

        return jsonify({
            "message": "Deposit successful",
            "transaction_id": transaction.id,
            "balance": account.balance
        })

    except (TypeError, ValueError) as e:
        db.rollback()
        print(f"❌ Error in deposit: {e}")  # Debugging
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
    db = next(get_db())
    
    if not request.is_json:
        return jsonify({"detail": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415

    try:
        data = request.get_json()
        print("🔍 Parsed JSON Data:", data)

        if not data or "amount" not in data or "sender_id" not in data:
            return jsonify({"detail": "Missing required fields: amount and sender_id"}), 400

        try:
            amount = Decimal(str(data["amount"]))
            sender_id = int(data["sender_id"])
        except (ValueError, TypeError, Decimal.InvalidOperation):
            return jsonify({"detail": "Invalid amount or sender_id format"}), 400

        if amount <= 0:
            return jsonify({"detail": "Withdrawal amount must be greater than zero"}), 400

        current_user = get_current_user()
        if not current_user:
            return jsonify({"detail": "Unauthorized"}), 401

        account = db.query(Account).filter_by(id=sender_id).first()
        if not account or account.user_id != current_user["id"]:
            return jsonify({"detail": "Account not found or unauthorized"}), 404

        if account.balance < amount:
            return jsonify({"detail": "Insufficient funds"}), 400

        account.balance += Decimal(str(amount))
        
        transaction = Transaction(
            type="withdrawal",
            amount=float(amount),
            sender_id=sender_id
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        # Generate invoice
        invoice_filename = f"invoice_{transaction.id}.pdf"
        invoice_path = generate_invoice(
        transaction_details={
            "id": transaction.id,  # Ensure ID is included
            "transaction_type": transaction.type,
            "amount": str(amount),
            "timestamp": transaction.timestamp.isoformat()
    },
        filename=invoice_filename,
        user=current_user,
)

    # Send email with invoice attachment
        user_email = current_user.get("email")
        if user_email:
            print(f"📧 Sending email to {user_email} with invoice attached")

            send_email_async(
                subject="Withdrawal Confirmation & Invoice",
                recipient=user_email,
                body=f"""
                Dear {current_user['username']},
                
                Your deposit of ${amount} has been processed successfully.
                Transaction ID: {transaction.id}
                New Balance: ${account.balance}

                Please find your invoice attached.

                Thank you for using our service.
                """,
                attachment_path=invoice_path  # Attach invoice
            )
        else:
            print("⚠️ No email found for user, skipping email notification.")

        return jsonify({
            "message": "Withdrawal successful",
            "transaction_id": transaction.id,
            "balance": account.balance
        })

    except (TypeError, ValueError) as e:
        db.rollback()
        print(f"❌ Error in withdrawal: {e}")
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
    db = next(get_db())
    
    if not request.is_json:
        return jsonify({"detail": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415

    try:
        data = request.get_json()
        print("🔍 Parsed JSON Data:", data)

        if not data or "sender_id" not in data or "receiver_id" not in data or "amount" not in data:
            return jsonify({"detail": "Missing required fields: sender_id, receiver_id, amount"}), 400

        try:
            amount = Decimal(str(data["amount"]))
            sender_id = int(data["sender_id"])
            receiver_id = int(data["receiver_id"])
        except (ValueError, TypeError, Decimal.InvalidOperation):
            return jsonify({"detail": "Invalid amount, sender_id, or receiver_id format"}), 400

        if amount <= 0:
            return jsonify({"detail": "Transfer amount must be greater than zero"}), 400

        current_user = get_current_user()
        if not current_user:
            return jsonify({"detail": "Unauthorized"}), 401

        sender = db.query(Account).filter_by(id=sender_id).first()
        receiver = db.query(Account).filter_by(id=receiver_id).first()

        if not sender or sender.user_id != current_user["id"]:
            return jsonify({"detail": "Sender account not found or unauthorized"}), 404
        if not receiver:
            return jsonify({"detail": "Receiver account not found"}), 404
        if sender.balance < amount:
            return jsonify({"detail": "Insufficient funds"}), 400
        
        if sender_id == receiver_id:
            return jsonify({"detail": "Sender and receiver cannot be the same"}), 400


        sender.balance -= Decimal(amount)
        receiver.balance += Decimal(amount)
        
        transaction = Transaction(
            type="transfer",
            amount=float(amount),
            sender_id=sender_id,
            receiver_id=receiver_id
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        # 🔹 Generate invoice AFTER transaction is stored
        invoice_filename = f"invoice_{transaction.id}.pdf"
        invoice_path = generate_invoice(
            transaction_details={
                "id": transaction.id,
                "transaction_type": transaction.type,
                "amount": str(amount),
                "timestamp": transaction.timestamp.isoformat()
            },
            filename=invoice_filename,
            user=current_user
        )

        # Get receiver user details
        receiver_user = db.query(User).filter_by(id=receiver.user_id).first()

        # Send email to sender
        sender_email = current_user.get("email")
        if sender_email:
            print(f"📧 Sending transfer email to {sender_email} with invoice attached")

        send_email_async(
            subject="Transfer Confirmation - Sent",
            recipient=sender_email,
            body=f"""
                Dear {current_user['username']},
        
                Your transfer of ${amount} has been sent successfully.
                Transaction ID: {transaction.id}
                New Balance: ${sender.balance}

                Please find your invoice attached.

                Thank you for using our service.
                """,
                attachment_path=invoice_path
            )


        # Send email to receiver
        if receiver_user and receiver_user.email:
            receiver_email = receiver_user.email
            print(f"📧 Sending transfer email to {receiver_email} with invoice attached")

            send_email_async(
                subject="Transfer Confirmation - Received",
                recipient=receiver_email,
                body=f"""
                Dear {receiver_user.username},
                
                You have received a transfer of ${amount} from {current_user['username']}.
                Transaction ID: {transaction.id}
                New Balance: ${receiver.balance}

                Please find your invoice attached.

                Thank you for using our service.
                """,
                attachment_path=invoice_path  # Attach invoice
            )

        return jsonify({
            "message": "Transfer successful",
            "transaction_id": transaction.id,
            "sender_balance": sender.balance,
            "receiver_balance": receiver.balance
        })

    except (TypeError, ValueError) as e:
        db.rollback()
        print(f"❌ Error in transfer: {e}")
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
    current_user = get_current_user()
    print("🔑 Current User:", current_user)

    if not current_user:
        return jsonify({"detail": "Unauthorized"}), 401

    db = next(get_db())

    # Get the user's accounts
    accounts = db.query(Account).filter_by(user_id=current_user["id"]).all()
    account_ids = [acc.id for acc in accounts]
    print("🔍 Account IDs for User", current_user["id"], ":", account_ids)

    if not account_ids:
        return jsonify([])

    # Fix: Ensure the query properly fetches transactions for both sender and receiver
    transactions = db.query(Transaction).filter(
        (Transaction.sender_id.in_(account_ids)) | 
        (Transaction.receiver_id.in_(account_ids))
    ).order_by(Transaction.timestamp.desc()).all()  # Sort by timestamp for clarity

    print("🔍 Found Transactions:", [t.id for t in transactions])

    # Ensure transactions are serialized properly
    return jsonify([t.as_dict() for t in transactions])

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

def get_transaction_for_user(id):
    """Fetches a specific transaction by user ID."""
    current_user = get_current_user()
    if not current_user or current_user["id"] != id:
        return jsonify({"detail": "Unauthorized"}), 401

    db = next(get_db())

    # 🔍 DEBUG: Show all account IDs for the user
    accounts = db.query(Account).filter_by(user_id=id).all()
    account_ids = [acc.id for acc in accounts]
    print("🔍 Account IDs for User", id, ":", account_ids)

    # 🔍 DEBUG: Show matching transactions
    transactions = db.query(Transaction).filter(
        (Transaction.sender_id.in_(account_ids)) |
        (Transaction.receiver_id.in_(account_ids))
    ).all()
    print("🔍 Transactions found:", transactions)

    return jsonify([t.as_dict() for t in transactions])



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
        return jsonify({"detail": "Unauthorized"}), 401

    print("🔍 Checking balance for transaction ID:", id)  # Debugging

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
