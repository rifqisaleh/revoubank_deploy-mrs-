from flask import Blueprint, request, jsonify
from flasgger.utils import swag_from
from app.model.base import get_db
from app.core.auth import get_current_user
from app.core.authorization import role_required
from app.model.models import Bill
from decimal import Decimal
from datetime import datetime
from app.core.logger import logger



bills_bp = Blueprint("bills", __name__, url_prefix="/bills")


@bills_bp.route("/", methods=["POST"])
@role_required('user')
@swag_from({
    "tags": ["Bills"],
    "summary": "Create a new bill",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "biller_name": {"type": "string", "example": "Water Utility"},
                    "due_date": {"type": "string", "example": "2025-03-31"},
                    "amount": {"type": "number", "example": 75.25},
                    "account_id": {"type": "integer", "example": 1}
                },
                "required": ["biller_name", "due_date", "amount", "account_id"]
            }
        }
    ],
    "responses": {
        "200": {"description": "Bill created successfully"},
        "400": {"description": "Invalid input or missing fields"}
    }
})
def create_bill():
    db = next(get_db())
    data = request.get_json()
    current_user = get_current_user()
    logger.info(f"Attempting to create bill for user {current_user['id']}")

    try:
        bill = Bill(
            user_id=current_user["id"],
            biller_name=data["biller_name"],
            due_date=datetime.fromisoformat(data["due_date"]),
            amount=Decimal(data["amount"]),
            account_id=data["account_id"]
        )
        db.add(bill)
        db.commit()
        logger.info(f"Bill {bill.id} created successfully for user {current_user['id']}")
        return jsonify({"message": "Bill created", "bill_id": bill.id}), 200

    except Exception as e:
        logger.error(f"Error creating bill for user {current_user['id']}: {str(e)}")
        db.rollback()
        return jsonify({"detail": str(e)}), 400


@bills_bp.route("/", methods=["GET"])
@role_required('user')
@swag_from({
    "tags": ["Bills"],
    "summary": "Get all bills for current user",
    "responses": {
        "200": {"description": "List of bills"}
    }
})
def get_bills():
    db = next(get_db())
    current_user = get_current_user()
    logger.info(f"Fetching all bills for user {current_user['id']}")
    
    try:
        bills = db.query(Bill).filter_by(user_id=current_user["id"]).all()
        logger.info(f"Successfully retrieved {len(bills)} bills for user {current_user['id']}")
        return jsonify([{
            "id": bill.id,
            "biller_name": bill.biller_name,
            "due_date": bill.due_date.isoformat(),
            "amount": float(bill.amount),
            "is_paid": bill.is_paid
        } for bill in bills]), 200
    except Exception as e:
        logger.error(f"Error fetching bills for user {current_user['id']}: {str(e)}")
        return jsonify({"detail": "Error fetching bills"}), 500


@bills_bp.route("/<int:bill_id>", methods=["PUT"])
@role_required('user')
@swag_from({
    "tags": ["Bills"],
    "summary": "Update a bill",
    "parameters": [
        {
            "name": "bill_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "Bill ID"
        },
        {
            "name": "body",
            "in": "body",
            "schema": {
                "type": "object",
                "properties": {
                    "biller_name": {"type": "string"},
                    "due_date": {"type": "string"},
                    "amount": {"type": "number"}
                }
            }
        }
    ],
    "responses": {
        "200": {"description": "Bill updated"},
        "404": {"description": "Bill not found"}
    }
})
def update_bill(bill_id):
    db = next(get_db())
    current_user = get_current_user()
    logger.info(f"Attempting to update bill {bill_id} for user {current_user['id']}")

    bill = db.query(Bill).filter_by(id=bill_id, user_id=current_user["id"]).first()

    if not bill:
        logger.warning(f"Bill {bill_id} not found for user {current_user['id']}")
        return jsonify({"detail": "Bill not found"}), 404

    try:
        data = request.get_json()

        if "biller_name" in data:
            bill.biller_name = data["biller_name"]
        if "due_date" in data:
            bill.due_date = datetime.fromisoformat(data["due_date"])
        if "amount" in data:
            bill.amount = Decimal(data["amount"])

        db.commit()
        logger.info(f"Bill {bill_id} successfully updated by user {current_user['id']}")
        return jsonify({"message": "Bill updated"}), 200
    except Exception as e:
        logger.error(f"Error updating bill {bill_id}: {str(e)}")
        db.rollback()
        return jsonify({"detail": "Error updating bill"}), 500


@bills_bp.route("/<int:bill_id>", methods=["DELETE"])
@role_required('user')
@swag_from({
    "tags": ["Bills"],
    "summary": "Delete a bill",
    "parameters": [
        {
            "name": "bill_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "Bill ID"
        }
    ],
    "responses": {
        "200": {"description": "Bill deleted"},
        "404": {"description": "Bill not found"}
    }
})
def delete_bill(bill_id):
    db = next(get_db())
    current_user = get_current_user()
    logger.info(f"Attempting to delete bill {bill_id} for user {current_user['id']}")
    
    bill = db.query(Bill).filter_by(id=bill_id, user_id=current_user["id"]).first()

    if not bill:
        logger.warning(f"Bill {bill_id} not found for user {current_user['id']}")
        return jsonify({"detail": "Bill not found"}), 404

    try:
        db.delete(bill)
        db.commit()
        logger.info(f"Bill {bill_id} successfully deleted by user {current_user['id']}")
        return jsonify({"message": "Bill deleted"}), 200
    except Exception as e:
        logger.error(f"Error deleting bill {bill_id}: {str(e)}")
        db.rollback()
        return jsonify({"detail": "Error deleting bill"}), 500
