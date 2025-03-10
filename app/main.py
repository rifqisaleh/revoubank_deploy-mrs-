from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, Account, Transaction  
from app.schemas import (
    UserCreate, UserResponse, UserLogin, AccountCreate, 
    AccountResponse, TransactionCreate, TransactionType, TransactionResponse
)
from app.utils import hash_password, verify_password
from fastapi.middleware.cors import CORSMiddleware
from decimal import Decimal
from typing import List, Optional
from app.auth import get_current_user, authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm




app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ User Registration
@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = hash_password(user.password)
    db_user = User(username=user.username, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer"}

# ✅ Get Authenticated User Profile
@app.get("/users/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

# ✅ Update Profile
@app.put("/users/me", response_model=UserResponse)
def update_profile(updated_user: UserCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.username = updated_user.username
    current_user.password_hash = hash_password(updated_user.password)
    db.commit()
    db.refresh(current_user)
    return current_user

# ✅ Get All Accounts for Authenticated User
@app.get("/accounts", response_model=List[AccountResponse])
def list_accounts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Account).filter(Account.user_id == current_user.id).all()

# ✅ Get Specific Account (Authorization required)
@app.get("/accounts/{id}", response_model=AccountResponse)
def get_account(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == id, Account.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

# ✅ Create New Account
@app.post("/accounts/", response_model=AccountResponse)
def create_account(account: AccountCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_account = Account(
        user_id=current_user.id,
        account_type=account.account_type,
        balance=account.initial_balance
    )
    
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    
    return db_account

# ✅ Update Account Details
@app.put("/accounts/{id}", response_model=AccountResponse)
def update_account(id: int, account_update: AccountCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == id, Account.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    account.balance = account_update.initial_balance
    db.commit()
    db.refresh(account)
    
    return account

# ✅ Delete Account
@app.delete("/accounts/{id}")
def delete_account(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == id, Account.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    db.delete(account)
    db.commit()
    
    return {"detail": "Account deleted"}

# ✅ Get List of Transactions (Optional Filters)
@app.get("/transactions", response_model=List[TransactionResponse])
def list_transactions(
    account_id: Optional[int] = None, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    query = db.query(Transaction).join(Account).filter(Account.user_id == current_user.id)

    if account_id:
        query = query.filter(Transaction.sender_id == account_id)
    if start_date and end_date:
        query = query.filter(Transaction.date.between(start_date, end_date))
    
    return query.all()

#  Get Specific Transaction (Authorization required)
@app.get("/transactions/{id}", response_model=TransactionResponse)
def get_transaction(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    transaction = db.query(Transaction).join(Account).filter(Account.user_id == current_user.id, Transaction.id == id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@app.post("/transactions/deposit/", response_model=TransactionResponse)
def deposit(transaction: TransactionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if transaction.transaction_type != TransactionType.DEPOSIT:
        raise HTTPException(status_code=400, detail="Invalid transaction type")

    if transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Deposit amount must be greater than zero")

    account = db.query(Account).filter(Account.id == transaction.receiver_id, Account.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found or unauthorized")

    account.balance += Decimal(str(transaction.amount))

    db_transaction = Transaction(
        receiver_id=transaction.receiver_id,
        amount=Decimal(str(transaction.amount)),
        transaction_type=TransactionType.DEPOSIT
    )

    db.add(db_transaction)
    db.commit()
    db.refresh(account)
    db.refresh(db_transaction)

    return db_transaction


# ✅ Withdraw Funds
@app.post("/transactions/withdraw/", response_model=TransactionResponse)
def withdraw(transaction: TransactionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if transaction.transaction_type != TransactionType.WITHDRAWAL:
        raise HTTPException(status_code=400, detail="Invalid transaction type")

    account = db.query(Account).filter(Account.id == transaction.sender_id, Account.user_id == current_user.id).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.balance < transaction.amount or transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid withdrawal amount")

    account.balance -= transaction.amount

    db_transaction = Transaction(
        sender_id=account.id,
        amount=transaction.amount,
        transaction_type=TransactionType.WITHDRAWAL
    )

    db.add(db_transaction)
    db.commit()
    db.refresh(account)
    db.refresh(db_transaction)

    return db_transaction


# ✅ Transfer Funds
@app.post("/transactions/transfer/", response_model=TransactionResponse)
def transfer(transaction: TransactionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if transaction.transaction_type != TransactionType.TRANSFER:
        raise HTTPException(status_code=400, detail="Invalid transaction type")

    sender = db.query(Account).filter(Account.id == transaction.sender_id, Account.user_id == current_user.id).first()
    receiver = db.query(Account).filter(Account.id == transaction.receiver_id).first()

    if not sender:
        raise HTTPException(status_code=404, detail="Sender account not found or not authorized")
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver account not found")
    if sender.balance < transaction.amount or transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Insufficient funds or invalid amount")

    sender.balance -= transaction.amount
    receiver.balance += transaction.amount

    db_transaction = Transaction(
        sender_id=sender.id,
        receiver_id=receiver.id,
        amount=transaction.amount,
        transaction_type=TransactionType.TRANSFER
    )

    db.add(db_transaction)
    db.commit()
    db.refresh(sender)
    db.refresh(receiver)
    db.refresh(db_transaction)

    return db_transaction

