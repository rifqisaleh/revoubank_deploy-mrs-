from flask import Blueprint, request, jsonify
from app.core.logger import logger
from threading import Thread
from flasgger.utils import swag_from
from decimal import Decimal
from datetime import datetime
from app.model.base import get_db
from app.model.models import Account, Transaction
from app.core.auth import get_current_user
from app.services.email.utils import send_email_async
from app.services.invoice.invoice_generator import generate_invoice
from app.services.transactions.core import handle_external_deposit, handle_external_withdrawal
from app.core.authorization import role_required

external_transaction_bp = Blueprint('external_transaction', __name__)


def run_background_task(func, *args, **kwargs):
    thread = Thread(target=func, args=args, kwargs=kwargs)
    thread.start()

@external_transaction_bp.route("/external/deposit/", methods=["POST"])
@role_required('user')
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
    current_user = get_current_user()

    if not request.is_json:
        logger.warning("❗ Unsupported media type for external deposit request")
        return jsonify({"detail": "Unsupported Media Type"}), 415

    data = request.get_json()
    required_fields = {"bank_name", "account_number", "amount"}
    missing = required_fields - set(data.keys())
    if missing:
        logger.warning(f"🚫 Missing fields in external deposit: {', '.join(missing)}")
        return jsonify({"detail": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        transaction, account = handle_external_deposit(db, current_user, data)

        return jsonify({
            "message": f"Successfully deposited ${data['amount']} from {data['bank_name']}",
            "transaction_id": transaction.id,
            "balance": account.balance
        })

    except ValueError as e:
        return jsonify({"detail": str(e)}), 400
    except Exception:
        db.rollback()
        logger.error("❌ Unhandled error during external deposit", exc_info=True)
        return jsonify({"detail": "Internal Server Error"}), 500



@external_transaction_bp.route("/external/withdraw/", methods=["POST"])
@role_required('user')
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
    current_user = get_current_user()

    if not request.is_json:
        logger.warning("❗ Unsupported media type for external withdrawal request")
        return jsonify({"detail": "Unsupported Media Type"}), 415
    
    data = request.get_json()
    required_fields = {"bank_name", "account_number", "amount"}

    missing = required_fields - set(data.keys())
    if missing:
        logger.warning(f"🚫 Missing fields in external withdrawal: {', '.join(missing)}")
        return jsonify({"detail": f"Missing fields: {', '.join(missing)}"}), 400

      
    try:
        transaction, account = handle_external_withdrawal(db, current_user, data)
        return jsonify({
            "message": f"Withdrawal of ${data['amount']} to {data['bank_name']} successful",
            "transaction_id": transaction.id,
            "balance": account.balance
        })

    except Exception as e:
        db.rollback()
        logger.error("❌ Error during external withdrawal", exc_info=True)
        return jsonify({"detail": f"Error: {str(e)}"}), 400
