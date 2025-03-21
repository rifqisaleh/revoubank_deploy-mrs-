from flask import Blueprint, request, jsonify
from flasgger.utils import swag_from
from decimal import Decimal
from datetime import datetime
from threading import Thread
from app.database.mock_database import get_mock_db, generate_transaction_id, save_mock_db
from app.core.auth import get_current_user
from app.services.email.utils import send_email_async
from app.services.invoice.invoice_generator import generate_invoice

external_transaction_bp = Blueprint('external_transaction', __name__)
mock_db = get_mock_db()

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
    """Handles external deposits from another bank and generates an invoice."""
    if not request.is_json:
        return jsonify({"detail": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415

    try:
        data = request.get_json()
        print("🔍 Parsed JSON Data:", data)

        if not data or "bank_name" not in data or "account_number" not in data or "amount" not in data:
            return jsonify({"detail": "Missing required fields: bank_name, account_number, amount"}), 400

        amount = Decimal(data["amount"])
        if amount <= 0:
            return jsonify({"detail": "Amount must be greater than zero."}), 400

        current_user = get_current_user()
        user_account = next(
            (acc for acc in mock_db["accounts"].values() if acc["user_id"] == current_user["id"]),
            None
        )

        if not user_account:
            return jsonify({"detail": "RevouBank account not found."}), 404

        user_account["balance"] += amount

        # Generate transaction ID
        transaction_id = max((t["id"] for t in mock_db["transactions"]), default=0) + 1

        # Store transaction
        new_transaction = {
            "id": transaction_id,
            "type": "external_deposit",
            "transaction_type": "External Deposit",
            "bank_name": data["bank_name"],
            "amount": str(amount),
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": current_user["id"]
        }

        mock_db["transactions"].append(new_transaction)
        save_mock_db(mock_db)  # Save changes to mock database

        # Generate invoice
        invoice_filename = f"invoice_{transaction_id}.pdf"
        invoice_path = generate_invoice(
            transaction_details=new_transaction,
            filename=invoice_filename,
            user=current_user
        )

        # Send email with invoice attachment
        user_email = current_user.get("email")
        if user_email:
            print(f"📧 Sending external deposit email to {user_email} with invoice attached")

            send_email_async(
                subject="External Deposit Confirmation & Invoice",
                recipient=user_email,
                body=f"""
                Dear {current_user['username']},
                
                A deposit of ${amount} has been received from {data['bank_name']}.
                Transaction ID: {transaction_id}
                New Balance: ${user_account['balance']}

                Please find your invoice attached.

                Thank you for using our service.
                """,
                attachment_path=invoice_path  # Attach invoice
            )

        return jsonify({"message": f"Successfully deposited ${amount} from {data['bank_name']}."})

    except (TypeError, ValueError):
        return jsonify({"detail": "Invalid JSON format or data types"}), 400




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
    """Handles external withdrawals to another bank and generates an invoice."""
    if not request.is_json:
        return jsonify({"detail": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415

    try:
        data = request.get_json()
        print("🔍 Parsed JSON Data:", data)

        if not data or "bank_name" not in data or "account_number" not in data or "amount" not in data:
            return jsonify({"detail": "Missing required fields: bank_name, account_number, amount"}), 400

        amount = Decimal(data["amount"])
        if amount <= 0:
            return jsonify({"detail": "Amount must be greater than zero."}), 400

        current_user = get_current_user()
        user_account = next(
            (acc for acc in mock_db["accounts"].values() if acc["user_id"] == current_user["id"]),
            None
        )

        if not user_account:
            return jsonify({"detail": "RevouBank account not found."}), 404
        if user_account["balance"] < amount:
            return jsonify({"detail": "Insufficient balance."}), 400

        user_account["balance"] -= amount

        # Generate transaction ID
        transaction_id = max((t["id"] for t in mock_db["transactions"]), default=0) + 1

        # Store transaction
        new_transaction = {
            "id": transaction_id,
            "type": "external_withdrawal",
            "transaction_type": "External Withdrawal",  # Ensure this is included
            "bank_name": data["bank_name"],
            "amount": str(amount),
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": current_user["id"]
        }

        mock_db["transactions"].append(new_transaction)
        save_mock_db(mock_db)  # Save changes to mock database

        # Generate invoice
        invoice_filename = f"invoice_{transaction_id}.pdf"
        invoice_path = generate_invoice(
            transaction_details=new_transaction,
            filename=invoice_filename,
            user=current_user
        )

        # Send email with invoice attachment
        user_email = current_user.get("email")
        if user_email:
            print(f"📧 Sending external withdrawal email to {user_email} with invoice attached")

            send_email_async(
                subject="External Withdrawal Confirmation & Invoice",
                recipient=user_email,
                body=f"""
                Dear {current_user['username']},
                
                A withdrawal of ${amount} has been made to {data['bank_name']}.
                Transaction ID: {transaction_id}
                New Balance: ${user_account['balance']}

                Please find your invoice attached.

                Thank you for using our service.
                """,
                attachment_path=invoice_path  # Attach invoice
            )

        return jsonify({"message": f"Withdrawal of ${amount} to {data['bank_name']} successful."})

    except (TypeError, ValueError):
        return jsonify({"detail": "Invalid JSON format or data types"}), 400
