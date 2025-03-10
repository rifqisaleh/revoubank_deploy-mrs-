from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, Enum, DateTime
from sqlalchemy.orm import relationship
from decimal import Decimal
from app.database import Base
from enum import Enum as PyEnum
from datetime import datetime
from app.schemas import TransactionType

#  Define Enum for Transaction Types
class TransactionType(str, PyEnum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    failed_attempts = Column(Integer, default=0)
    is_locked = Column(Boolean, default=False)
    
    accounts = relationship("Account", back_populates="user")

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_type = Column(String, nullable=False)
    balance = Column(Numeric(10, 2), default=0)  
    
    user = relationship("User", back_populates="accounts")
    sent_transactions = relationship("Transaction", foreign_keys="[Transaction.sender_id]", back_populates="sender")
    received_transactions = relationship("Transaction", foreign_keys="[Transaction.receiver_id]", back_populates="receiver")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)  
    receiver_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)  
    amount = Column(Numeric(10, 2), nullable=False)  
    transaction_type = Column(Enum(TransactionType, name="transaction_type_enum_upper", create_type=False), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

    @property
    def amount_as_decimal(self):
        return Decimal(self.amount)

    sender = relationship("Account", foreign_keys=[sender_id], back_populates="sent_transactions")
    receiver = relationship("Account", foreign_keys=[receiver_id], back_populates="received_transactions")
