# app/routes/auth.py
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.core.extensions import limiter
from app.utils.user import verify_password
from app.model.models import User
from app.database.dependency import get_db  
from app.services.email.utils import send_email_async
from app.core.auth import generate_access_token
from config import Config
from datetime import datetime



auth_bp = Blueprint("auth", __name__)

# Login
@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
@swag_from({
    "tags": ["auth"],
    "summary": "Login. Authenticate user and generate JWT token",
    "parameters": [
        {
            "name": "username",
            "in": "formData",
            "type": "string",
            "required": True
        },
        {
            "name": "password",
            "in": "formData",
            "type": "string",
            "required": True
        }
    ],
    "responses": {
        "200": {"description": "Returns access token"},
        "400": {"description": "Incorrect username or password"},
        "403": {"description": "Account is locked"}
    }
})
def login():
    """
    Login. Authenticate user and generate JWT token
    """
    form_data = request.form
    username = form_data.get("username")
    password = form_data.get("password")

    with get_db() as db:
        user = db.query(User).filter_by(username=username).first()

        if not user:
            return jsonify({
                "detail": "Incorrect username or password.",
                "attempts_left": Config.MAX_FAILED_ATTEMPTS
            }), 400

        if user.is_locked:
            if user.locked_time and datetime.utcnow() > user.locked_time + Config.LOCK_DURATION:
                user.is_locked = False
                user.failed_attempts = 0
                db.commit()
            else:
                return jsonify({
                    "detail": "Account is locked due to multiple failed login attempts. Please try again later."
                }), 403

        if not verify_password(password, user.password):
            user.failed_attempts += 1

            if user.failed_attempts >= Config.MAX_FAILED_ATTEMPTS:
                user.is_locked = True
                user.locked_time = datetime.utcnow()

                send_email_async(
                    subject="Your RevouBank Account is Locked",
                    recipient=user.email,
                    body=f"""
                    Dear {username},

                    Your RevouBank account has been locked due to multiple failed login attempts.
                    Please wait 15 minutes before trying again.

                    - RevouBank Support
                    """
                )

            db.commit()

            attempts_left = max(0, Config.MAX_FAILED_ATTEMPTS - user.failed_attempts)
            return jsonify({
                "detail": "Incorrect username or password.",
                "attempts_left": attempts_left
            }), 400

        # Successful login
        user.failed_attempts = 0
        user.is_locked = False
        user.locked_time = None
        db.commit()

        access_token = generate_access_token(user)

    return jsonify({"access_token": access_token, "token_type": "bearer"})


@auth_bp.route("/logout", methods=["POST"])
@swag_from({
    "tags": ["auth"],
    "summary": "Logout (client-side only)",
    "description": "This route simply tells clients to delete the token. JWTs are stateless.",
    "responses": {
        "200": {"description": "Logout successful (token should be deleted client-side)"}
    }
})
def logout():
    return jsonify({"message": "Logout successful. Please delete your token on the client side."}), 200