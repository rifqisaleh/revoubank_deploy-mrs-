from flask import Blueprint, request, jsonify
from threading import Thread
from flasgger.utils import swag_from
from decimal import Decimal
from datetime import datetime
from app.model.base import get_db
from app.model.models import Account, Transaction
from app.core.auth import get_current_user
from app.services.email.utils import send_email_async
from app.services.invoice.invoice_generator import generate_invoice

external_transaction_bp = Blueprint('external_transaction', __name__)


def run_background_task(func, *args, **kwargs):
    thread = Thread(target=func, args=args, kwargs=kwargs)
    thread.start()

@external_transaction_bp.route("/external/deposit/", methods=["POST"])
@swag_from({
    "tags": ["external transactions"],
    "summary": "Deposit from external bank",
    "description": "Handles deposits from an external bank account into a RevouBank account.",
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
                    "bank_name": {
                        "type": "string",
                        "example": "Bank of America",
                        "description": "Name of the external bank"
                    },
                    "account_number": {
                        "type": "string",
                        "example": "123456789",
                        "description": "External bank account number"
                    },
                    "amount": {
                        "type": "number",
                        "example": 250.75,
                        "description": "Amount to deposit"
                    }
                },
                "required": ["bank_name", "account_number", "amount"]
            }
        }
    ],
    "responses": {
        "200": {"description": "Deposit successful"},
        "400": {"description": "Invalid deposit amount"},
        "404": {"description": "RevouBank account not found"}
    }
})

def external_deposit():
    db = next(get_db())

    if not request.is_json:
        return jsonify({"detail": "Unsupported Media Type"}), 415

    try:
        data = request.get_json()
        required_fields = {"bank_name", "account_number", "amount"}

        missing = required_fields - set(data.keys())
        if missing:
            return jsonify({"detail": f"Missing fields: {', '.join(missing)}"}), 400


        amount = Decimal(data["amount"])
        if amount <= 0:
            return jsonify({"detail": "Amount must be greater than zero"}), 400

        current_user = get_current_user()
        account = db.query(Account).filter_by(user_id=current_user["id"]).first()

        if not account:
            return jsonify({"detail": "User account not found"}), 404

        # Update balance
        account.balance += Decimal(str(amount))

        # Store transaction
        transaction = Transaction(
            type="external_deposit",
            amount=float(amount),
            receiver_id=account.id,
            bank_name=data["bank_name"],
            external_account_number=data["account_number"]
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        # Generate invoice
        invoice_filename = f"invoice_{transaction.id}.pdf"
        invoice_path = generate_invoice(
            transaction_details=transaction.as_dict(),
            filename=invoice_filename,
            user=current_user
        )

        # Send email
        send_email_async(
            subject="External Deposit Confirmation & Invoice",
            recipient=current_user["email"],
            body=f"""
            Dear {current_user['username']},

            A deposit of ${amount} was made from {data['bank_name']} into your account.
            Transaction ID: {transaction.id}
            New Balance: ${account.balance}

            Invoice is attached.

            Thank you for using RevouBank.
            """,
            attachment_path=invoice_path
        )

        return jsonify({
            "message": f"Successfully deposited ${amount} from {data['bank_name']}",
            "transaction_id": transaction.id,
            "balance": account.balance
        })

    except Exception as e:
        db.rollback()
        return jsonify({"detail": f"Error: {str(e)}"}), 400



@external_transaction_bp.route("/external/withdraw/", methods=["POST"])
@swag_from({
    "tags": ["external transactions"],
    "summary": "Withdraw to external bank",
    "description": "Handles withdrawals from a RevouBank account to an external bank account.",
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
                    "bank_name": {
                        "type": "string",
                        "example": "Bank of America",
                        "description": "Name of the external bank"
                    },
                    "account_number": {
                        "type": "string",
                        "example": "123456789",
                        "description": "External bank account number"
                    },
                    "amount": {
                        "type": "number",
                        "example": 150.50,
                        "description": "Amount to withdraw"
                    }
                },
                "required": ["bank_name", "account_number", "amount"]
            }
        }
    ],
    "responses": {
        "200": {"description": "Withdrawal successful"},
        "400": {"description": "Insufficient funds"},
        "404": {"description": "RevouBank account not found"}
    }
})

def external_withdraw():
    db = next(get_db())

    if not request.is_json:
        return jsonify({"detail": "Unsupported Media Type"}), 415

    try:
        data = request.get_json()
        required_fields = {"bank_name", "account_number", "amount"}

        if not all(field in data for field in required_fields):
            return jsonify({"detail": f"Missing fields: {required_fields - data.keys()}"}), 400

        amount = Decimal(data["amount"])
        if amount <= 0:
            return jsonify({"detail": "Amount must be greater than zero"}), 400

        current_user = get_current_user()
        account = db.query(Account).filter_by(user_id=current_user["id"]).first()

        if not account:
            return jsonify({"detail": "User account not found"}), 404
        if account.balance < amount:
            return jsonify({"detail": "Insufficient balance"}), 400

        # Update balance
        account.balance -= Decimal(str(amount))

        # Store transaction
        transaction = Transaction(
            type="external_withdrawal",
            amount=float(amount),
            sender_id=account.id,
            bank_name=data["bank_name"],
            external_account_number=data["account_number"]
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        # Generate invoice
        invoice_filename = f"invoice_{transaction.id}.pdf"
        invoice_path = generate_invoice(
            transaction_details=transaction.as_dict(),
            filename=invoice_filename,
            user=current_user
        )

        # Send email
        send_email_async(
            subject="External Withdrawal Confirmation & Invoice",
            recipient=current_user["email"],
            body=f"""
            Dear {current_user['username']},

            A withdrawal of ${amount} has been made to {data['bank_name']}.
            Transaction ID: {transaction.id}
            New Balance: ${account.balance}

            Please find your invoice attached.

            Thank you for using RevouBank.
            """,
            attachment_path=invoice_path
        )

        return jsonify({
            "message": f"Withdrawal of ${amount} to {data['bank_name']} successful",
            "transaction_id": transaction.id,
            "balance": account.balance
        })

    except Exception as e:
        db.rollback()
        return jsonify({"detail": f"Error: {str(e)}"}), 400