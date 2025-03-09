from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, Account, Transaction  
from app.schemas import UserCreate, UserResponse, UserLogin, AccountCreate, AccountResponse, TransactionCreate, TransactionType, TransactionResponse  
from app.utils import hash_password, verify_password
from fastapi.middleware.cors import CORSMiddleware
from decimal import Decimal


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

#  User Registration Endpoint
@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Hash password before storing
    hashed_password = hash_password(user.password)
    db_user = User(username=user.username, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

#  User Login Endpoint
@app.post("/login/")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {"message": "Login successful"}

# Get User by ID
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    return db_user

# Account Creation Endpoint
@app.post("/accounts/", response_model=AccountResponse)
def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(User).filter(User.id == account.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create new account
    db_account = Account(
        user_id=account.user_id,
        account_type=account.account_type,
        balance=account.initial_balance
    )
    
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    
    return db_account

#Transaction Endpoints
@app.post("/transactions/deposit/", response_model=TransactionResponse)
def deposit(transaction: TransactionCreate, db: Session = Depends(get_db)):
    if transaction.transaction_type != TransactionType.DEPOSIT:
        raise HTTPException(status_code=400, detail="Invalid transaction type")

    account = db.query(Account).filter(Account.id == transaction.receiver_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Ensure balance is a Decimal before adding
    account.balance = Decimal(str(account.balance)) + Decimal(str(transaction.amount))

    db_transaction = Transaction(
        receiver_id=transaction.receiver_id,
        amount=Decimal(str(transaction.amount)),  # Store as Decimal
        transaction_type="deposit"
    )

    db.add(db_transaction)
    db.commit()
    db.refresh(account)
    db.refresh(db_transaction)  # Ensure transaction is fetched

    return db_transaction

@app.post("/transactions/withdraw/", response_model=TransactionResponse)
def withdraw(transaction: TransactionCreate, db: Session = Depends(get_db)):
    if transaction.transaction_type != TransactionType.WITHDRAW:
        raise HTTPException(status_code=400, detail="Invalid transaction type")
    
    account = db.query(Account).filter(Account.id == transaction.sender_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Ensure sufficient balance
    if account.balance < transaction.amount:  # No need to cast to float
        raise HTTPException(status_code=400, detail="Insufficient funds")

    account.balance -= transaction.amount  # Keep it as Decimal

    db_transaction = Transaction(
        sender_id=account.id,
        amount=transaction.amount,  # Keep it as Decimal
        transaction_type="withdraw"
    )

    db.add(db_transaction)
    db.commit()
    db.refresh(account)
    db.refresh(db_transaction)  # Ensure transaction is fetched properly

    return db_transaction

@app.post("/transactions/transfer/", response_model=TransactionResponse)
def transfer(transaction: TransactionCreate, db: Session = Depends(get_db)):
    if transaction.transaction_type != TransactionType.TRANSFER:
        raise HTTPException(status_code=400, detail="Invalid transaction type")

    sender = db.query(Account).filter(Account.id == transaction.sender_id).first()
    receiver = db.query(Account).filter(Account.id == transaction.receiver_id).first()

    if not sender or not receiver:
        raise HTTPException(status_code=404, detail="One or both accounts not found")

    if sender.balance < transaction.amount:  # No float conversion
        raise HTTPException(status_code=400, detail="Insufficient funds")

    sender.balance -= transaction.amount
    receiver.balance += transaction.amount

    db_transaction = Transaction(
        sender_id=sender.id,
        receiver_id=receiver.id,
        amount=transaction.amount,  # Keep it as Decimal
        transaction_type="transfer"
    )

    db.add(db_transaction)
    db.commit()
    db.refresh(sender)
    db.refresh(receiver)
    db.refresh(db_transaction)  # Ensure transaction is fetched properly

    return db_transaction
