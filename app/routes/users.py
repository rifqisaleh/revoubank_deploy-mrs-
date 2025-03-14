from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.database.mock_database import get_mock_db, generate_user_id
from app.utils.user import hash_password
from app.core.auth import get_current_user

router = APIRouter()
mock_db = get_mock_db()

class UserCreate(BaseModel):
    """Schema for user registration and profile update."""
    username: str
    password: str
    email: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

class UserResponse(BaseModel):
    """Schema for returning user data."""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

@router.post("/", response_model=UserResponse, summary="Register a New User", tags=["Users"])
async def register_user(user: UserCreate):
    """
    Register a new user.

    - **username**: Unique identifier for the user.
    - **password**: User password (hashed).
    - **email**: User email (must be unique).
    - **full_name**: Optional full name.
    - **phone_number**: Optional phone number.

    Raises:
    - 400 if the username or email is already taken.
    """
    if any(u["username"] == user.username for u in mock_db["users"].values()):
        raise HTTPException(status_code=400, detail="Username already taken")

    if any(u.get("email") == user.email for u in mock_db["users"].values()):
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = generate_user_id()
    hashed_password = hash_password(user.password)

    mock_db["users"][user_id] = {
        "id": user_id,
        "username": user.username,
        "password": hashed_password,
        "email": user.email,
        "full_name": user.full_name,
        "phone_number": user.phone_number,
        "failed_attempts": 0,
        "is_locked": False,
        "locked_time": None
    }

    return {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "phone_number": user.phone_number
    }

@router.get("/", response_model=list[UserResponse], summary="List All Users", tags=["Users"])
def list_users():
    """
    Retrieves all users in the mock database.

    Returns a list of all registered users.
    """
    return list(mock_db["users"].values())

@router.get("/me", response_model=UserResponse, summary="Get Profile of Current User", tags=["Users"])
def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Retrieves the profile of the currently authenticated user.

    - Requires authentication.
    - Returns the user's ID, username, email, full name, and phone number.
    """
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "full_name": current_user.get("full_name"),
        "phone_number": current_user.get("phone_number")
    }

@router.put("/me", response_model=UserResponse, summary="Update Profile of Current User", tags=["Users"])
def update_profile(updated_user: UserCreate, current_user: dict = Depends(get_current_user)):
    """
    Updates the profile of the currently authenticated user.

    - Requires authentication.
    - Can update username, password, email, full name, and phone number.

    Raises:
    - 404 if the user is not found.
    """
    user = mock_db["users"].get(current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user["username"] = updated_user.username
    user["password"] = hash_password(updated_user.password)
    user["email"] = updated_user.email
    user["full_name"] = updated_user.full_name
    user["phone_number"] = updated_user.phone_number

    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "full_name": user["full_name"],
        "phone_number": user["phone_number"]
    }

@router.delete("/{user_id}", summary="Delete User", tags=["Users"])
def delete_user(user_id: int):
    """
    Deletes a user from the mock database.

    - Requires user ID.
    - If successful, returns a confirmation message.

    Raises:
    - 404 if the user is not found.
    """
    if user_id not in mock_db["users"]:
        raise HTTPException(status_code=404, detail="User not found")

    del mock_db["users"][user_id]
    return {"message": "User deleted successfully"}
