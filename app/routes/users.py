from flask import Blueprint, request, jsonify, abort
from flasgger.utils import swag_from
from pydantic import BaseModel, ValidationError
from typing import Optional
from app.database.mock_database import get_mock_db, generate_user_id, save_mock_db
from app.utils.user import hash_password
from app.core.auth import get_current_user

users_bp = Blueprint('users', __name__)
mock_db = get_mock_db()

class UserCreate(BaseModel):
    """Schema for user registration and profile update."""
    username: str
    password: str
    email: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

@users_bp.route("/", methods=["POST"])
@swag_from({
    "tags": ["users"],
    "summary": "Register a new user",
    "description": "Creates a new user account.",
    "security": [],
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
                    "username": {
                        "type": "string",
                        "example": "john_doe",
                        "description": "The username of the new user"
                    },
                    "password": {
                        "type": "string",
                        "example": "securepassword123",
                        "description": "The password for the new user"
                    },
                    "email": {
                        "type": "string",
                        "example": "john.doe@example.com",
                        "description": "User's email address"
                    },
                    "full_name": {
                        "type": "string",
                        "example": "John Doe",
                        "description": "User's full name (optional)"
                    },
                    "phone_number": {
                        "type": "string",
                        "example": "1234567890",
                        "description": "User's phone number (optional)"
                    }
                },
                "required": ["username", "password", "email"]
            }
        }
    ],
    "responses": {
        "201": {"description": "User registered successfully"},
        "400": {"description": "Validation error or duplicate username/email"}
    }
})
def register_user():
    """Registers a new user."""
    print("🔍 Raw Request Body:", request.get_data(as_text=True))  # Debugging

    if not request.is_json:
        return jsonify({"detail": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415

    try:
        user_data = UserCreate(**request.get_json())
        print("🔍 Parsed JSON Data:", user_data.dict())  # Debugging

        if any(u["username"] == user_data.username for u in mock_db["users"].values()):
            return jsonify({"detail": "Username already taken"}), 400

        if any(u.get("email") == user_data.email for u in mock_db["users"].values()):
            return jsonify({"detail": "Email already registered"}), 400

        user_id = generate_user_id()
        hashed_password = hash_password(user_data.password)

        mock_db["users"][user_id] = {
            "id": user_id,
            "username": user_data.username,
            "password": hashed_password,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "phone_number": user_data.phone_number,
            "failed_attempts": 0,
            "is_locked": False,
            "locked_time": None
        }

        save_mock_db()  # ✅ Persist user data to mock_db.json

        return jsonify({
            "id": user_id,
            "username": user_data.username,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "phone_number": user_data.phone_number
        }), 201

    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400


@users_bp.route("/", methods=["GET"])
@swag_from({
    "tags": ["users"],
    'summary': 'List all users',
    'description': 'Retrieves all registered users in the system.',
    'responses': {
        200: {'description': 'List of users retrieved successfully'}
    }
})
def list_users():
    """Retrieves all users in the mock database."""
    current_user = get_current_user()  # Added authentication check
    if not current_user:
        abort(401, description="Unauthorized")
    return jsonify(list(mock_db["users"].values()))

@users_bp.route("/me", methods=["GET"])
@swag_from({
    'summary': 'Get user profile',
    'description': 'Retrieves the profile of the authenticated user.',
    'responses': {
        200: {'description': 'User profile retrieved successfully'},
        401: {'description': 'Unauthorized'}
    }
})
def get_profile():
    """Retrieves the profile of the currently authenticated user."""
    current_user = get_current_user()
    if not current_user:
        abort(401, description="Unauthorized")

    return jsonify({
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "full_name": current_user.get("full_name"),
        "phone_number": current_user.get("phone_number")
    })

@users_bp.route("/me", methods=["PUT"])
@swag_from({
    "tags": ["users"],
    "summary": "Update user profile",
    "description": "Updates the profile information of the authenticated user.",
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
                    "username": {
                        "type": "string",
                        "example": "new_username",
                        "description": "Updated username"
                    },
                    "password": {
                        "type": "string",
                        "example": "new_secure_password",
                        "description": "Updated password"
                    },
                    "email": {
                        "type": "string",
                        "example": "new_email@example.com",
                        "description": "Updated email address"
                    },
                    "full_name": {
                        "type": "string",
                        "example": "New Full Name",
                        "description": "Updated full name"
                    },
                    "phone_number": {
                        "type": "string",
                        "example": "9876543210",
                        "description": "Updated phone number"
                    }
                },
                "required": ["username", "password", "email"]
            }
        }
    ],
    "responses": {
        "200": {"description": "User profile updated successfully"},
        "401": {"description": "Unauthorized"},
        "404": {"description": "User not found"}
    }
})
def update_profile():
    """Updates the profile of the currently authenticated user."""
    print("🔍 Raw Request Body:", request.get_data(as_text=True))  # Debugging

    if not request.is_json:
        return jsonify({"detail": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415

    current_user = get_current_user()
    if not current_user:
        return jsonify({"detail": "Unauthorized"}), 401

    try:
        updated_user = UserCreate(**request.get_json())
        print("🔍 Parsed JSON Data:", updated_user.dict())  # Debugging

        user = mock_db["users"].get(current_user["id"])
        if not user:
            return jsonify({"detail": "User not found"}), 404

        user["username"] = updated_user.username
        user["password"] = hash_password(updated_user.password)
        user["email"] = updated_user.email
        user["full_name"] = updated_user.full_name
        user["phone_number"] = updated_user.phone_number

        return jsonify({
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "phone_number": user["phone_number"]
        })

    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

@users_bp.route("/<int:user_id>", methods=["DELETE"])
@swag_from({
    "tags": ["users"],
    'summary': 'Delete a user',
    'description': 'Deletes a user from the system.',
    'parameters': [
        {'name': 'user_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'User deleted successfully'},
        404: {'description': 'User not found'}
    }
})
def delete_user(user_id):
    """Deletes a user from the mock database."""
    current_user = get_current_user()  # Added authentication check
    if not current_user:
        abort(401, description="Unauthorized")

    if user_id not in mock_db["users"]:
        abort(404, description="User not found")

    del mock_db["users"][user_id]
    return jsonify({"message": "User deleted successfully"})
