import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from flask import request, jsonify, abort
from dotenv import load_dotenv

from app.model.base import get_db
from app.model.models import User
from app.utils.user import verify_password

# Load environment variables from .env file
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
ALGORITHM = "HS256"
MAX_FAILED_ATTEMPTS = int(os.getenv("MAX_FAILED_ATTEMPTS", 3))
LOCK_DURATION = timedelta(minutes=int(os.getenv("LOCK_DURATION_MINUTES", 15)))


# Create JWT Access Token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Authenticate User (via DB)
def authenticate_user(username: str, password: str):
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
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        abort(401, description="Missing or invalid token")

    token = token.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            abort(401, description="Invalid token payload")
    except JWTError:
        abort(401, description="Invalid token")

    db = next(get_db())
    user = db.query(User).filter_by(id=int(user_id)).first()
    if not user:
        abort(401, description="User not found")

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "phone_number": user.phone_number
    }
