from pydantic import BaseModel
from decimal import Decimal
from enum import Enum
from typing import Optional

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

class AccountType(str, Enum):
    SAVINGS = "savings"
    CHECKING = "checking"

class AccountCreate(BaseModel):
    user_id: int
    account_type: AccountType
    initial_balance: Decimal = Decimal(0)

class AccountResponse(BaseModel):
    id: int
    user_id: int
    account_type: AccountType
    balance: Decimal

    class Config:
        from_attributes = True

# Transaction Types Enum
class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    TRANSFER = "transfer"

# Schema for Creating a Transaction
class TransactionCreate(BaseModel):
    sender_id: Optional[int] = None  
    receiver_id: Optional[int] = None  
    amount: Decimal
    transaction_type: TransactionType
    
    class Config:
        from_attributes = True
        json_encoders = {Decimal: lambda v: str(v)}

# Schema for Returning Transaction Data
class TransactionResponse(BaseModel):
    id: int
    sender_id: int | None
    receiver_id: int | None
    amount: Decimal
    transaction_type: TransactionType

    class Config:
        from_attributes = True