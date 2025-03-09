from pydantic import BaseModel

# Schema for user registration
class UserCreate(BaseModel):
    username: str
    password: str

# Schema for login
class UserLogin(BaseModel):
    username: str
    password: str

# Response model (without password hash)
class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True
