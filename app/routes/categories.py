from flask import Blueprint, request, jsonify
from flasgger.utils import swag_from
from app.model.base import get_db
from app.core.auth import get_current_user
from app.model.models import TransactionCategory

categories_bp = Blueprint("categories", __name__, url_prefix="/categories")


@categories_bp.route("/", methods=["POST"])
@swag_from({
    "tags": ["transaction categories"],
    "summary": "Create a transaction category",
    "parameters": [
        {
            "in": "body",
            "name": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "example": "Groceries"}
                },
                "required": ["name"]
            }
        }
    ],
    "responses": {
        "200": {"description": "Category created"},
        "400": {"description": "Invalid input"}
    }
})
def create_category():
    db = next(get_db())
    current_user = get_current_user()
    data = request.get_json()

    category = TransactionCategory(name=data["name"], user_id=current_user["id"])
    db.add(category)
    db.commit()
    return jsonify({"message": "Category created", "category_id": category.id})


@categories_bp.route("/", methods=["GET"])
@swag_from({
    "tags": ["transaction categories"],
    "summary": "Get all categories",
    "responses": {
        "200": {"description": "List of categories"}
    }
})
def get_categories():
    db = next(get_db())
    current_user = get_current_user()
    categories = db.query(TransactionCategory).filter_by(user_id=current_user["id"]).all()

    return jsonify([{
        "id": c.id,
        "name": c.name
    } for c in categories])


@categories_bp.route("/<int:category_id>", methods=["PUT"])
@swag_from({
    "tags": ["transaction categories"],
    "summary": "Update a transaction category",
    "parameters": [
        {"name": "category_id", "in": "path", "type": "integer", "required": True},
        {
            "in": "body",
            "name": "body",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"}
                }
            }
        }
    ],
    "responses": {
        "200": {"description": "Category updated"},
        "404": {"description": "Category not found"}
    }
})
def update_category(category_id):
    db = next(get_db())
    current_user = get_current_user()
    category = db.query(TransactionCategory).filter_by(id=category_id, user_id=current_user["id"]).first()

    if not category:
        return jsonify({"detail": "Category not found"}), 404

    data = request.get_json()
    if "name" in data:
        category.name = data["name"]
    db.commit()
    return jsonify({"message": "Category updated"})


@categories_bp.route("/<int:category_id>", methods=["DELETE"])
@swag_from({
    "tags": ["transaction categories"],
    "summary": "Delete a transaction category",
    "parameters": [
        {"name": "category_id", "in": "path", "type": "integer", "required": True}
    ],
    "responses": {
        "200": {"description": "Category deleted"},
        "404": {"description": "Category not found"}
    }
})
def delete_category(category_id):
    db = next(get_db())
    current_user = get_current_user()
    category = db.query(TransactionCategory).filter_by(id=category_id, user_id=current_user["id"]).first()

    if not category:
        return jsonify({"detail": "Category not found"}), 404

    db.delete(category)
    db.commit()
    return jsonify({"message": "Category deleted"})
