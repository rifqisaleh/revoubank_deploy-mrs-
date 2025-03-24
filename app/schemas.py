from pydantic import BaseModel, field_validator, EmailStr
from decimal import Decimal
from enum import Enum
from typing import Optional


# =============================
# User Schemas
# =============================

class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str]
    password: Optional[str]
    email: Optional[EmailStr]
    full_name: Optional[str]
    phone_number: Optional[str]


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str]
    phone_number: Optional[str]

    class Config:
        from_attributes = True


# =============================
# Account Schemas
# =============================

class AccountType(str, Enum):
    SAVINGS = "savings"
    CHECKING = "checking"


class AccountCreate(BaseModel):
    account_type: AccountType
    initial_balance: Decimal = Decimal(0)


class AccountResponse(BaseModel):
    id: int
    user_id: int
    account_type: AccountType
    balance: Decimal

    class Config:
        from_attributes = True


# =============================
# Transaction Schemas
# =============================

class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"


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


class TransactionResponse(BaseModel):
    id: int
    sender_id: Optional[int]
    receiver_id: Optional[int]
    amount: Decimal
    transaction_type: TransactionType

    class Config:
        from_attributes = True


# =============================
# External Transaction Schemas
# =============================

class ExternalTransactionCreate(BaseModel):
    bank_name: str
    account_number: str
    amount: Decimal


# =============================
# Bill Payment Schemas
# =============================

class BillPaymentWithCardCreate(BaseModel):
    biller_name: str
    amount: Decimal
    card_number: str


class BillPaymentWithBalanceCreate(BaseModel):
    biller_name: str
    amount: Decimal
