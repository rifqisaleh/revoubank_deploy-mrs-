from flask import Blueprint, request, jsonify
from flasgger.utils import swag_from
from app.model.base import get_db
from app.core.auth import get_current_user
from app.core.authorization import role_required
from app.model.models import Budget
from decimal import Decimal

budgets_bp = Blueprint("budgets", __name__, url_prefix="/budgets")


@budgets_bp.route("/", methods=["POST"])
@role_required('user')
@swag_from({
    "tags": ["budgets"],
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
    db = next(get_db())
    current_user = get_current_user()
    data = request.get_json()

    try:
        budget = Budget(
            user_id=current_user["id"],
            category=data["category"],
            amount=Decimal(data["amount"])
        )
        db.add(budget)
        db.commit()
        return jsonify({"message": "Budget created", "budget_id": budget.id}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"detail": str(e)}), 400


@budgets_bp.route("/", methods=["GET"])
@swag_from({
    "tags": ["budgets"],
    "summary": "Get all budgets",
    "responses": {
        "200": {"description": "List of budgets"}
    }
})
def get_budgets():
    db = next(get_db())
    current_user = get_current_user()
    budgets = db.query(Budget).filter_by(user_id=current_user["id"]).all()

    return jsonify([{
        "id": b.id,
        "category": b.category,
        "amount": float(b.amount)
    } for b in budgets])


@budgets_bp.route("/<int:budget_id>", methods=["PUT"])
@role_required('user')
@swag_from({
    "tags": ["budgets"],
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
    budget = db.query(Budget).filter_by(id=budget_id, user_id=current_user["id"]).first()

    if not budget:
        return jsonify({"detail": "Budget not found"}), 404

    data = request.get_json()
    if "category" in data:
        budget.category = data["category"]
    if "amount" in data:
        budget.amount = Decimal(data["amount"])

    db.commit()
    return jsonify({"message": "Budget updated"}), 200


@budgets_bp.route("/<int:budget_id>", methods=["DELETE"])
@role_required('user')
@swag_from({
    "tags": ["budgets"],
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
    budget = db.query(Budget).filter_by(id=budget_id, user_id=current_user["id"]).first()

    if not budget:
        return jsonify({"detail": "Budget not found"}), 404

    db.delete(budget)
    db.commit()
    return jsonify({"message": "Budget deleted"}), 200
