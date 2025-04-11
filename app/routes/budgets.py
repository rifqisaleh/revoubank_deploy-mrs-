from flask import Blueprint, request, jsonify
from flasgger.utils import swag_from
from app.model.base import get_db
from app.core.auth import get_current_user
from app.core.authorization import role_required
from app.model.models import Budget
from app.core.logger import logger
from decimal import Decimal

budgets_bp = Blueprint("budgets", __name__, url_prefix="/budgets")


@budgets_bp.route("/", methods=["POST"])
@role_required('user')
@swag_from({
    "tags": ["Budgets"],
    "summary": "Create a new budget",
    "parameters": [
        {
            "in": "body",
            "name": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "example": "Food"},
                    "amount": {"type": "number", "example": 500}
                },
                "required": ["category", "amount"]
            }
        }
    ],
    "responses": {
        "200": {"description": "Budget created"},
        "400": {"description": "Invalid input"}
    }
})
def create_budget():
    logger.info("Starting budget creation request")
    db = next(get_db())
    current_user = get_current_user()
    data = request.get_json()
    logger.info(f"Budget creation request data: category={data.get('category')}, amount={data.get('amount')}")
    logger.info(f"Attempting to create budget for user {current_user['id']}")

    try:
        budget = Budget(
            user_id=current_user["id"],
            category=data["category"],
            amount=Decimal(data["amount"])
        )
        db.add(budget)
        db.commit()
        logger.info(f"Budget {budget.id} created successfully for user {current_user['id']}")
        return jsonify({"message": "Budget created", "budget_id": budget.id}), 200
    except Exception as e:
        logger.error(f"Error creating budget for user {current_user['id']}: {str(e)}")
        db.rollback()
        return jsonify({"detail": str(e)}), 400


@budgets_bp.route("/", methods=["GET"])
@swag_from({
    "tags": ["Budgets"],
    "summary": "Get all budgets",
    "responses": {
        "200": {"description": "List of budgets"}
    }
})
def get_budgets():
    logger.info("Starting get all budgets request")
    db = next(get_db())
    current_user = get_current_user()
    logger.info(f"Fetching all budgets for user {current_user['id']}")
    
    try:
        budgets = db.query(Budget).filter_by(user_id=current_user["id"]).all()
        logger.info(f"Successfully retrieved {len(budgets)} budgets for user {current_user['id']}")
        return jsonify([{
            "id": b.id,
            "category": b.category,
            "amount": float(b.amount)
        } for b in budgets])
    except Exception as e:
        logger.error(f"Error fetching budgets for user {current_user['id']}: {str(e)}")
        return jsonify({"detail": "Error fetching budgets"}), 500


@budgets_bp.route("/<int:budget_id>", methods=["PUT"])
@role_required('user')
@swag_from({
    "tags": ["Budgets"],
    "summary": "Update a budget",
    "parameters": [
        {"name": "budget_id", "in": "path", "type": "integer", "required": True},
        {
            "in": "body",
            "name": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "amount": {"type": "number"}
                }
            }
        }
    ],
    "responses": {
        "200": {"description": "Budget updated"},
        "404": {"description": "Budget not found"}
    }
})
def update_budget(budget_id):
    db = next(get_db())
    current_user = get_current_user()
    logger.info(f"Attempting to update budget {budget_id} for user {current_user['id']}")

    budget = db.query(Budget).filter_by(id=budget_id, user_id=current_user["id"]).first()

    if not budget:
        logger.warning(f"Budget {budget_id} not found for user {current_user['id']}")
        return jsonify({"detail": "Budget not found"}), 404

    try:
        data = request.get_json()
        if "category" in data:
            budget.category = data["category"]
        if "amount" in data:
            budget.amount = Decimal(data["amount"])

        db.commit()
        logger.info(f"Budget {budget_id} successfully updated by user {current_user['id']}")
        return jsonify({"message": "Budget updated"}), 200
    except Exception as e:
        logger.error(f"Error updating budget {budget_id}: {str(e)}")
        db.rollback()
        return jsonify({"detail": "Error updating budget"}), 500


@budgets_bp.route("/<int:budget_id>", methods=["DELETE"])
@role_required('user')
@swag_from({
    "tags": ["Budgets"],
    "summary": "Delete a budget",
    "parameters": [
        {"name": "budget_id", "in": "path", "type": "integer", "required": True}
    ],
    "responses": {
        "200": {"description": "Budget deleted"},
        "404": {"description": "Budget not found"}
    }
})
def delete_budget(budget_id):
    db = next(get_db())
    current_user = get_current_user()
    logger.info(f"Attempting to delete budget {budget_id} for user {current_user['id']}")

    budget = db.query(Budget).filter_by(id=budget_id, user_id=current_user["id"]).first()

    if not budget:
        logger.warning(f"Budget {budget_id} not found for user {current_user['id']}")
        return jsonify({"detail": "Budget not found"}), 404

    try:
        db.delete(budget)
        db.commit()
        logger.info(f"Budget {budget_id} successfully deleted by user {current_user['id']}")
        return jsonify({"message": "Budget deleted"}), 200
    except Exception as e:
        logger.error(f"Error deleting budget {budget_id}: {str(e)}")
        db.rollback()
        return jsonify({"detail": "Error deleting budget"}), 500
