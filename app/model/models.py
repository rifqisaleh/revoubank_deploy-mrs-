from app import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from app.model.base import Base

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
    balance = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('accounts', lazy=True))
    
class Transaction(Base):
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

    