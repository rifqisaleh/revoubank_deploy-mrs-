import os
from datetime import datetime, timedelta
from typing import Optional
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request, create_access_token
from app.core.extensions import limiter
from flask import request, jsonify, abort
from dotenv import load_dotenv
from app.database.dependency import get_db
from app.model.models import User
from app.utils.user import verify_password


# Load environment variables from .env file
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
ALGORITHM = "HS256"
MAX_FAILED_ATTEMPTS = int(os.getenv("MAX_FAILED_ATTEMPTS", 3))
LOCK_DURATION = timedelta(minutes=int(os.getenv("LOCK_DURATION_MINUTES", 15)))

# Generate access token for a user
def generate_access_token(user):
    return create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        additional_claims={"role": user.role} 
    )
    

# Authenticate User (via DB)
def authenticate_user(username: str, password: str, db=None):
    if db is None:
        from app.database.dependency import get_db
        db = next(get_db())

    user = db.query(User).filter_by(username=username).first()
    if not user:
        return None

    # Check for lockout
    if user.is_locked:
        if user.locked_time and datetime.utcnow() > user.locked_time + LOCK_DURATION:
            user.is_locked = False
            user.failed_attempts = 0
            db.commit()
        else:
            abort(403, description="Account is locked. Please wait or contact support.")

    if not verify_password(password, user.password):
        user.failed_attempts += 1
        if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
            user.is_locked = True
            user.locked_time = datetime.utcnow()
            db.commit()
            abort(403, description="Account locked due to multiple failed attempts.")
        db.commit()
        abort(401, description=f"Invalid password. {MAX_FAILED_ATTEMPTS - user.failed_attempts} attempts left.")

    # Successful login
    user.failed_attempts = 0
    user.is_locked = False
    user.locked_time = None
    db.commit()

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "phone_number": user.phone_number
    }


# Extract current user from JWT
def get_current_user():
    verify_jwt_in_request()
    user_id = get_jwt_identity()
    with get_db() as db:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            abort(401, description="User not found")

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "phone_number": user.phone_number
        }