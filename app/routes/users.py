from flask import Blueprint, request, jsonify, abort
from flasgger.utils import swag_from
from pydantic import BaseModel, ValidationError
from typing import Optional
from app.model.models import User
from app import db
from app.utils.user import hash_password
from app.core.auth import get_current_user


users_bp = Blueprint('users', __name__)

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
    if not request.is_json:
        return jsonify({"detail": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415

    try:
        user_data = UserCreate(**request.get_json())

        # Check if username/email already exists
        if User.query.filter_by(username=user_data.username).first():
            return jsonify({"detail": "Username already taken"}), 400
        if User.query.filter_by(email=user_data.email).first():
            return jsonify({"detail": "Email already registered"}), 400

        new_user = User(
            username=user_data.username,
            password=hash_password(user_data.password),
            email=user_data.email,
            full_name=user_data.full_name,
            phone_number=user_data.phone_number
        )
        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "phone_number": new_user.phone_number
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
    current_user = get_current_user()
    if not current_user:
        abort(401, description="Unauthorized")

    users = User.query.all()
    return jsonify([
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "phone_number": u.phone_number
        } for u in users
    ])
    
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
    
    user = User.query.get(get_current_user()["id"])
    if not user:
        abort(401, description="Unauthorized")

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "phone_number": user.phone_number
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
                    "username": {"type": "string", "example": "new_username"},
                    "password": {"type": "string", "example": "new_secure_password"},
                    "email": {"type": "string", "example": "new_email@example.com"},
                    "full_name": {"type": "string", "example": "New Full Name"},
                    "phone_number": {"type": "string", "example": "9876543210"}
                },
                "required": ["username", "password", "email"]
            }
        }
    ],
    "responses": {
        "200": {"description": "User profile updated successfully"},
        "401": {"description": "Unauthorized"},
        "400": {"description": "Duplicate username or email"},
        "404": {"description": "User not found"}
    }
})

def update_profile():
    if not request.is_json:
        return jsonify({"detail": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415

    current_user = get_current_user()
    if not current_user:
        return jsonify({"detail": "Unauthorized"}), 401

    try:
        updated_user = UserCreate(**request.get_json())
        user = User.query.get(current_user["id"])

        if not user:
            return jsonify({"detail": "User not found"}), 404

        # ✅ Check if username or email is used by someone else
        if User.query.filter(User.username == updated_user.username, User.id != user.id).first():
            return jsonify({"detail": "Username already taken"}), 400

        if User.query.filter(User.email == updated_user.email, User.id != user.id).first():
            return jsonify({"detail": "Email already registered"}), 400

        # Update user fields
        user.username = updated_user.username
        user.password = hash_password(updated_user.password)
        user.email = updated_user.email
        user.full_name = updated_user.full_name
        user.phone_number = updated_user.phone_number

        db.session.commit()

        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "phone_number": user.phone_number
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
    current_user = get_current_user()
    if not current_user:
        abort(401, description="Unauthorized")

    user = User.query.get(user_id)
    if not user:
        abort(404, description="User not found")

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"})
