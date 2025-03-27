from app.database.db import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Boolean, DateTime, event
import uuid
#from app.model.base import Base

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    full_name = db.Column(db.String(255))
    phone_number = db.Column(db.String(50))
    failed_attempts = db.Column(db.Integer, default=0)
    is_locked = db.Column(db.Boolean, default=False)
    locked_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    

class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)
    account_number = db.Column(db.String, nullable=False, unique=True)
    balance = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('accounts', lazy=True))

    # Ensure account_number is populated before insert
@event.listens_for(Account, 'before_insert')
def generate_account_number(mapper, connection, target):
    if target.account_number is None:
        target.account_number = str(uuid.uuid4())[:10]  # Generate a 10-character account number

    
class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sender_id = Column(Integer, ForeignKey('accounts.id'), nullable=True)
    receiver_id = Column(Integer, ForeignKey('accounts.id'), nullable=True)

    sender = relationship("Account", foreign_keys=[sender_id])
    receiver = relationship("Account", foreign_keys=[receiver_id])
    bank_name = Column(String(100), nullable=True)
    external_account_number = Column(String(100), nullable=True)
    biller_name = Column(String(100), nullable=True)
    payment_method = Column(String(50), nullable=True)


    
    def as_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "amount": self.amount,
            "timestamp": self.timestamp.isoformat(),
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "bank_name": self.bank_name,
            "external_account_number": self.external_account_number,
            "biller_name": self.biller_name,
            "payment_method": self.payment_method
        }

class Budget(db.Model):
    __tablename__ = 'budgets'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    #name = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class TransactionCategory(db.Model):
    __tablename__ = 'transaction_categories'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Bill(db.Model):
    __tablename__ = 'bills'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    biller_name = Column(String(100), nullable=False)
    due_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    is_paid = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)