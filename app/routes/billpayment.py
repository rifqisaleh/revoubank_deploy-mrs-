from flask import Blueprint, request, jsonify, send_file
from app.core.logger import logger
from flasgger.utils import swag_from
from decimal import Decimal
from datetime import datetime
from app.model.base import get_db
from app.core.auth import get_current_user
from app.core.authorization import role_required
from app.utils.verification import verify_card_number
from app.services.email.utils import send_email_async
from app.services.invoice.invoice_generator import generate_invoice
from app.model.models import Account, Transaction, Bill

billpayment_bp = Blueprint('billpayment', __name__, url_prefix="/bills")

@billpayment_bp.route("/pay/card", methods=["POST"])
@role_required('user')
@swag_from({
    "tags": ["bill payment"],
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
    db = next(get_db())

    if not request.is_json:
        logger.warning("📤 Unsupported Media Type in credit card bill payment")
        return jsonify({"detail": "Unsupported Media Type"}), 415

    try:
        data = request.get_json()
        required_fields = {"biller_name", "amount", "card_number"}

        missing = required_fields - set(data.keys())
        if missing:
            logger.warning(f"🚫 Missing fields in bill payment: {', '.join(missing)}")
            return jsonify({"detail": f"Missing fields: {', '.join(missing)}"}), 400

        amount = Decimal(data["amount"])
        if amount <= 0:
            logger.warning(f"🚫 Invalid bill amount: {amount}")
            return jsonify({"detail": "Amount must be greater than zero"}), 400

        current_user = get_current_user()
        account = db.query(Account).filter_by(user_id=current_user["id"]).first()

        if not account:
            logger.warning(f"🧾 No account found for user: {current_user['username']}")
            return jsonify({"detail": "User account not found"}), 404

        if account.balance < amount:
            logger.warning(f"💰 Insufficient balance for user {current_user['username']} - has ${account.balance}, needs ${amount}")
            return jsonify({"detail": "Insufficient balance"}), 400

        # Subtract amount from user account
        account.balance -= Decimal(str(amount))

        # Create transaction record
        transaction = Transaction(
            type="bill_payment",
            amount=float(amount),
            sender_id=account.id,
            biller_name=data["biller_name"],
            payment_method="credit_card"
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        logger.info(
            f"✅ Bill payment of ${amount} to {data['biller_name']} using credit card by user {current_user['username']} (txn_id={transaction.id})"
        )

        # Generate invoice
        invoice_filename = f"invoice_{transaction.id}.pdf"
        invoice_path = generate_invoice(
            transaction_details=transaction.as_dict(),
            filename=invoice_filename,
            user=current_user
        )

        # Send confirmation email with invoice
        send_email_async(
            subject="Bill Payment Confirmation & Invoice",
            recipient=current_user["email"],
            body=f"""
            Dear {current_user['username']},

            Your bill payment of ${amount} to {data['biller_name']} using a credit card has been processed.
            Transaction ID: {transaction.id}

            Invoice attached. Thank you for using RevouBank.
            """,
            attachment_path=invoice_path
        )

        return jsonify({
            "message": f"Successfully paid ${amount} to {data['biller_name']} with credit card",
            "transaction_id": transaction.id,
            "balance": account.balance
        })

    except Exception as e:
        db.rollback()
        logger.error("❌ Error occurred during bill payment with card", exc_info=True)
        return jsonify({"detail": f"Error: {str(e)}"}), 400




@billpayment_bp.route("/<int:bill_id>/pay", methods=["POST"])
@role_required('user')
@swag_from({
    "tags": ["bill payment"],
    "summary": "Pay a bill using account balance",
    "description": "Allows users to pay their bills using their account balance.",
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "parameters": [
        {
            "name": "bill_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "The ID of the bill to pay"
        }
    ],
    "responses": {
        "200": {"description": "Bill payment successful"},
        "400": {"description": "Insufficient funds"},
        "404": {"description": "User account not found"}
    }
})

def pay_bill_from_balance(bill_id):
    db = next(get_db())
    try:
        current_user = get_current_user()

        bill = db.query(Bill).filter_by(id=bill_id, user_id=current_user["id"]).first()
        if not bill:
            logger.warning(f"❌ Bill ID {bill_id} not found for user {current_user['username']}")
            return jsonify({"detail": "Bill not found"}), 404
        if bill.is_paid:
            logger.info(f"ℹ️ Bill ID {bill_id} already paid by user {current_user['username']}")
            return jsonify({"detail": "Bill already paid"}), 400

        account = db.query(Account).filter_by(user_id=current_user["id"]).first()
        if not account:
            logger.warning(f"🚫 No account found for user {current_user['username']}")
            return jsonify({"detail": "Insufficient balance or no account found"}), 400
        if account.balance < bill.amount:
            logger.warning(f"💸 Insufficient balance for user {current_user['username']}: balance=${account.balance}, required=${bill.amount}")
            return jsonify({"detail": "Insufficient balance or no account found"}), 400

        # Deduct balance
        if account.balance < Decimal(str(bill.amount)):
            logger.warning(f"⚠️ Balance check failed again (redundant): user {current_user['username']}")
            return jsonify({"detail": "Insufficient funds"}), 400
        account.balance -= Decimal(str(bill.amount))
        bill.is_paid = True

        # Log transaction
        transaction = Transaction(
            type="bill_payment",
            amount=float(bill.amount),
            sender_id=account.id,
            biller_name=bill.biller_name,
            payment_method="account_balance"
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        logger.info(
            f"✅ Bill payment of ${bill.amount} to {bill.biller_name} using account balance by user {current_user['username']} (txn_id={transaction.id})"
        )

        # Generate invoice
        invoice_filename = f"invoice_{transaction.id}.pdf"
        invoice_path = generate_invoice(
            transaction_details=transaction.as_dict(),
            filename=invoice_filename,
            user=current_user
        )

        # Send email
        send_email_async(
            subject="Bill Payment Confirmation & Invoice",
            recipient=current_user["email"],
            body=f"""
            Dear {current_user['username']},

            Your bill payment of ${bill.amount} to {bill.biller_name} using your account balance has been processed.
            Transaction ID: {transaction.id}

            Please find your invoice attached.

            Thank you for using RevouBank.
            """,
            attachment_path=invoice_path
        )

        return jsonify({
            "message": f"Successfully paid ${bill.amount} to {bill.biller_name} from account balance",
            "transaction_id": transaction.id,
            "balance": account.balance
        })

    except Exception as e:
        db.rollback()
        logger.error("❌ Error occurred during bill payment from balance", exc_info=True)
        return jsonify({"detail": f"Error: {str(e)}"}), 400
