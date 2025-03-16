import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from flask import request, jsonify, abort
from dotenv import load_dotenv
from app.database.mock_database import get_mock_db
from app.utils.user import verify_password

# Load environment variables from .env file
load_dotenv()

# Get secret key and token expiration time from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")  # Make sure .env contains SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
ALGORITHM = "HS256"

# Get mock database
mock_db = get_mock_db()

# Create JWT Access Token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Authenticate User Credentials (Using Dictionary Instead of Database)
def authenticate_user(username, password):
    LOCK_DURATION = timedelta(minutes=15)
    user = next((u for u in mock_db["users"].values() if u["username"] == username), None)
    if not user:
        return None

    # Check if the account is locked and unlock if lock duration passed
    if user["is_locked"]:
        locked_time = user.get("locked_time")
        if locked_time and datetime.now() > locked_time + LOCK_DURATION:
            user["is_locked"] = False
            user["failed_attempts"] = 0
        else:
            abort(403, description="Account is locked. Please wait or contact support.")

    if not verify_password(password, user["password"]):
        user["failed_attempts"] += 1
        if user["failed_attempts"] >= 3:
            user["is_locked"] = True
            user["locked_time"] = datetime.now()
            abort(403, description="Account locked due to multiple failed attempts.")

        abort(401, description=f"Invalid password. {3 - user['failed_attempts']} attempts left.")

    user["failed_attempts"] = 0
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user.get("email"),  # Ensure email is returned
        "full_name": user.get("full_name"),
        "phone_number": user.get("phone_number"),
    }

# Extract Current User from JWT Token (Using Dictionary)
def get_current_user():
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        abort(401, description="Could not validate credentials")
    token = token.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")  # Ensure user ID is stored as a string
        if user_id is None:
            abort(401, description="Could not validate credentials")
    except JWTError:
        abort(401, description="Could not validate credentials")

    user = mock_db["users"].get(int(user_id))
    if user is None:
        abort(401, description="Could not validate credentials")

    # Ensure all required fields are included
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user.get("email"),  # Fix: Include email
        "full_name": user.get("full_name"),
        "phone_number": user.get("phone_number"),
    }
