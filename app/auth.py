import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from app.mock_database import get_mock_db
from app.utils import verify_password

#  Load environment variables from .env file
load_dotenv()

#  Get secret key and token expiration time from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")  # Make sure .env contains SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

#  Get mock database
mock_db = get_mock_db()

#  Create JWT Access Token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

#  Authenticate User Credentials (Using Dictionary Instead of Database)
def authenticate_user(username: str, password: str):
    user = next((u for u in mock_db["users"].values() if u["username"] == username), None)
    if not user or not verify_password(password, user["password"]):  # Assuming passwords are stored in plain text
        return None
    return user

# Extract Current User from JWT Token (Using Dictionary)
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Log the token for debugging
        print(f"Received token: {token}")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")  # Ensure user ID is stored as a string
        if user_id is None:
            print(f"Token missing 'sub' field: {token}")
            raise credentials_exception
        print(f"Decoded payload: {payload}")
    except JWTError as e:
        print(f"JWT decoding error: {e}")
        raise credentials_exception

    user = mock_db["users"].get(int(user_id))
    if user is None:
        print(f"User with ID {user_id} not found in mock database.")
        raise credentials_exception
    return user
