from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.mock_database import get_mock_db, generate_user_id
from app.utils import hash_password
from app.auth import get_current_user

router = APIRouter()
mock_db = get_mock_db()

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

# ✅ Register a New User
@router.post("/", response_model=UserResponse)
def register_user(user: UserCreate):
    """Registers a new user in the mock database."""
    if any(u["username"] == user.username for u in mock_db["users"].values()):
        raise HTTPException(status_code=400, detail="Username already taken")

    user_id = generate_user_id()
    mock_db["users"][user_id] = {
        "id": user_id,
        "username": user.username,
        "password": hash_password(user.password),
        "failed_attempts": 0,
        "is_locked": False
    }
    
    return {"id": user_id, "username": user.username}

# ✅ List All Users
@router.get("/", response_model=list[UserResponse])
def list_users():
    """Retrieves all users in the mock database."""
    return list(mock_db["users"].values())

# ✅ Get Profile of Current User
@router.get("/me", response_model=UserResponse)
def get_profile(current_user: dict = Depends(get_current_user)):
    """Retrieves the profile of the currently authenticated user."""
    return {"id": current_user["id"], "username": current_user["username"]}

# ✅ Update Profile of Current User
@router.put("/me", response_model=UserResponse)
def update_profile(updated_user: UserCreate, current_user: dict = Depends(get_current_user)):
    """Updates the profile of the currently authenticated user."""
    user = mock_db["users"].get(current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user["username"] = updated_user.username
    user["password"] = hash_password(updated_user.password)

    return {"id": user["id"], "username": user["username"]}

# ✅ Delete User
@router.delete("/{user_id}")
def delete_user(user_id: int):
    """Deletes a user from the mock database."""
    if user_id not in mock_db["users"]:
        raise HTTPException(status_code=404, detail="User not found")
    
    del mock_db["users"][user_id]
    return {"message": "User deleted successfully"}
