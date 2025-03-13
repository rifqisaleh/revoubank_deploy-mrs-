from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.database.mock_database import get_mock_db, generate_user_id
from app.utils.user import hash_password
from app.core.auth import get_current_user

router = APIRouter()
mock_db = get_mock_db()

class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    
    
# Register a New User
@router.post("/", response_model=UserResponse)
async def register_user(user: UserCreate):
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

# List All Users
@router.get("/", response_model=list[UserResponse])
def list_users():
    """Retrieves all users in the mock database."""
    return list(mock_db["users"].values())

# Get Profile of Current User
@router.get("/me", response_model=UserResponse)
def get_profile(current_user: dict = Depends(get_current_user)):
    """Retrieves the profile of the currently authenticated user."""
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],  # Include email in the response
        "full_name": current_user.get("full_name"),
        "phone_number": current_user.get("phone_number")
    }

# Update Profile of Current User
@router.put("/me", response_model=UserResponse)
def update_profile(updated_user: UserCreate, current_user: dict = Depends(get_current_user)):
    """Updates the profile of the currently authenticated user."""
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

#  Delete User
@router.delete("/{user_id}")
def delete_user(user_id: int):
    """Deletes a user from the mock database."""
    if user_id not in mock_db["users"]:
        raise HTTPException(status_code=404, detail="User not found")
    
    del mock_db["users"][user_id]
    return {"message": "User deleted successfully"}
