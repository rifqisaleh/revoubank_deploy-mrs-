# app/routes/auth.py
from app.core.logger import logger
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.core.extensions import limiter
from app.utils.user import verify_password
from app.model.models import User
from app.database.dependency import get_db  
from app.services.email.utils import send_email_async
from app.core.auth import generate_access_token
from app.utils.token import confirm_verification_token
from config import Config
from datetime import datetime
from collections import OrderedDict


auth_bp = Blueprint("auth", __name__)

login_schema = {
    "type": "object",
    "properties": OrderedDict([
        ("username", {"type": "string"}),
        ("password", {"type": "string"})
    ]),
    "required": ["username", "password"]
    }

# Login
@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
@swag_from({
    "tags": ["Auth"],
    "summary": "Login. Authenticate user and generate JWT token",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                    "password": {"type": "string"}
                },
                "required": ["username", "password"]
            }
        }
    ],
    "consumes": ["application/json"],
    "responses": {
        "200": {"description": "Returns access token"},
        "400": {"description": "Incorrect username or password"},
        "403": {"description": "Account is locked"}
    }
})

def login():
    username = "<unknown>"  # Fallback value
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")


        logger.info(f"🔐 Login attempt for user: {username}")

        # Check if the user exists
        with get_db() as db:
            user = db.query(User).filter_by(username=username).first()

            if not user:
                logger.warning(f"❌ Login failed: username '{username}' not found")
                return jsonify({
                    "detail": "Incorrect username or password.",
                    "attempts_left": Config.MAX_FAILED_ATTEMPTS
                }), 400

            # If account is locked, handle the lock logic
            if user.is_locked:
                if user.locked_time and datetime.utcnow() > user.locked_time + Config.LOCK_DURATION:
                    user.is_locked = False
                    user.failed_attempts = 0
                    db.commit()
                    logger.info(f"🔓 Account unlocked: {username}")
                else:
                    logger.warning(f"🔒 Login blocked: account '{username}' is locked")
                    return jsonify({
                        "detail": "Account is locked due to multiple failed login attempts. Please try again later."
                    }), 403

            # Check the password
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
                    logger.warning(f"🔒 Account locked due to too many failed attempts: {username}")
                db.commit()

                attempts_left = max(0, Config.MAX_FAILED_ATTEMPTS - user.failed_attempts)
                logger.warning(f"❌ Incorrect password for user '{username}' — {attempts_left} attempts left")
                return jsonify({
                    "detail": "Incorrect username or password.",
                    "attempts_left": attempts_left
                }), 400

            # Verify email before logging in
            if not user.is_verified:
                logger.warning(f"⚠️ Login blocked: account '{username}' not verified")
                return jsonify({"detail": "Account not verified. Please check your email."}), 403

            # If verification is successful, clear any failed attempts and proceed with login
            user.failed_attempts = 0
            user.is_locked = False
            user.locked_time = None
            db.commit()

            access_token = generate_access_token(user)
            logger.info(f"✅ Login successful for user: {username}")
            return jsonify({"access_token": access_token, "token_type": "bearer"})

    except Exception as e:
        logger.error(f"🔥 Unexpected error during login for {username}", exc_info=e)
        return jsonify({"detail": "Internal server error"}), 500


@auth_bp.route("/verify/<token>", methods=["GET"])
def verify_email(token):
    print("verify_email using get_db:", get_db)
    email = confirm_verification_token(token)
    if not email:
        return jsonify({"message": "Invalid or expired verification link."}), 400

    with get_db() as db:
        user = db.query(User).filter_by(email=email).first()
        if not user:
            return jsonify({"message": "User not found."}), 404
        if user.is_verified:
            return jsonify({"message": "Account already verified."}), 200

        user.is_verified = True
        db.commit()

        return jsonify({"message": "✅ Email verified successfully. You can now log in."}), 200    



@auth_bp.route("/logout", methods=["POST"])
@swag_from({
    "tags": ["Auth"],
    "summary": "Logout (client-side only)",
    "description": "This route simply tells clients to delete the token. JWTs are stateless.",
    "responses": {
        "200": {"description": "Logout successful (token should be deleted client-side)"}
    }
})
def logout():
    return jsonify({"message": "Logout successful. Please delete your token on the client side."}), 200