from flask import Blueprint, request, jsonify
from app.core.logger import logger
from flasgger.utils import swag_from
from app.services.transactions.core import handle_pay_bill_from_balance, handle_pay_bill_with_card
from app.model.base import get_db
from app.core.auth import get_current_user
from app.core.authorization import role_required




billpayment_bp = Blueprint('billpayment', __name__, url_prefix="/bills")

@billpayment_bp.route("/<int:bill_id>/pay/card", methods=["POST"])
@role_required('user')
@swag_from({
    "tags": ["Bill Payment"],
    "summary": "Pay a bill using a credit card",
    "description": "Allows users to pay their bills using a credit card.",
    "consumes": ["application/json"],
    "produces": ["application/json"],
    'parameters': [
        {
            'name': 'bill_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID of the bill to be paid'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'card_number': {
                        'type': 'string',
                        'example': '4111111111111111'
                    }
                },
                'required': ['card_number']
            }
        }
    ],
    "responses": {
        "200": {"description": "Bill payment successful"},
        "400": {"description": "Invalid credit card or insufficient funds"},
        "404": {"description": "User account not found"}
    }
})

def pay_bill_with_card(bill_id):
    """Handles bill payment using a credit card."""
    db = next(get_db())
    try:
        current_user = get_current_user()

        if not request.is_json:
            return jsonify({"detail": "Unsupported Media Type"}), 415

        data = request.get_json()
        card_number = data.get("card_number")

        if not card_number:
            return jsonify({"detail": "Missing card_number"}), 400

        transaction, account = handle_pay_bill_with_card(db, current_user, bill_id, card_number)

        return jsonify({
            "message": f"Successfully paid ${transaction.amount} to {transaction.biller_name} using credit card",
            "transaction_id": transaction.id,
            "balance": account.balance
        })

    except Exception as e:
        db.rollback()
        logger.error("❌ Error during bill payment with card", exc_info=True)
        return jsonify({"detail": str(e)}), 400



@billpayment_bp.route("/<int:bill_id>/pay", methods=["POST"])
@role_required('user')
@swag_from({
    "tags": ["Bill Payment"],
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
    """Handles bill payment using current user's account balance."""
    db = next(get_db())
    try:
        current_user = get_current_user()
        transaction, account = handle_pay_bill_from_balance(db, current_user, bill_id)
        return jsonify({
            "message": f"Successfully paid ${transaction.amount} to {transaction.biller_name} from account balance",
            "transaction_id": transaction.id,
            "balance": account.balance
        })

    except Exception as e:
        db.rollback()
        logger.error("❌ Error during bill payment from balance", exc_info=True)
        return jsonify({"detail": str(e)}), 400