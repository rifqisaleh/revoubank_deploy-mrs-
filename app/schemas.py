from pydantic import BaseModel, field_validator
from decimal import Decimal
from enum import Enum
from typing import Optional

#  User Registration Schema
class UserCreate(BaseModel):
    username: str
    password: str

#  User Login Schema
class UserLogin(BaseModel):
    username: str
    password: str

# User Response (without password hash)
class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True  

# Account Type Enum
class AccountType(str, Enum):
    SAVINGS = "savings"
    CHECKING = "checking"

# Account Creation Schema (user_id removed)
class AccountCreate(BaseModel):
    account_type: AccountType
    initial_balance: Decimal = Decimal(0)

# Account Response Schema
class AccountResponse(BaseModel):
    id: int
    user_id: int
    account_type: AccountType
    balance: Decimal

    class Config:
        from_attributes = True

# Transaction Types Enum
class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"

# Transaction Creation Schema
class TransactionCreate(BaseModel):
    sender_id: Optional[int] = None  
    receiver_id: Optional[int] = None  
    amount: Decimal
    transaction_type: TransactionType

    @field_validator("transaction_type", mode="before")
    @classmethod
    def convert_to_uppercase(cls, v):
        return v.upper() if isinstance(v, str) else v

    class Config:
        from_attributes = True

# Transaction Response Schema
class TransactionResponse(BaseModel):
    id: int
    sender_id: Optional[int] = None
    receiver_id: Optional[int] = None
    amount: Decimal
    transaction_type: TransactionType

    class Config:
        from_attributes = True
