from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.mock_database import get_mock_db, generate_transaction_id
from app.auth import get_current_user
from decimal import Decimal
from datetime import datetime
from typing import Optional

router = APIRouter()
mock_db = get_mock_db()

class TransactionCreate(BaseModel):
    sender_id: Optional[int] = None
    receiver_id: Optional[int] = None
    amount: Decimal
    transaction_type: str  # ✅ Enum removed since it's a dictionary-based system

@router.post("/deposit/")
def deposit(transaction: TransactionCreate, current_user: dict = Depends(get_current_user)):
    """Handles deposits using the mock database."""
    
    if transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Deposit amount must be greater than zero")

    account = mock_db["accounts"].get(transaction.receiver_id)
    if not account or account["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Account not found or unauthorized")

    account["balance"] += Decimal(str(transaction.amount))

    transaction_id = len(mock_db["transactions"]) + 1
    mock_db["transactions"].append({
        "id": transaction_id,
        "receiver_id": transaction.receiver_id,
        "amount": Decimal(str(transaction.amount)),
        "transaction_type": "DEPOSIT",
        "date": datetime.utcnow().isoformat()
    })

    return {"message": "Deposit successful", "account": account}

@router.post("/withdraw/")
def withdraw(transaction: TransactionCreate, current_user: dict = Depends(get_current_user)):
    """Processes a withdrawal transaction."""
    account = mock_db["accounts"].get(transaction.sender_id)
    if not account or account["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Account not found or unauthorized")
    
    if account["balance"] < transaction.amount or transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Insufficient funds or invalid amount")

    account["balance"] -= transaction.amount

    transaction_id = len(mock_db["transactions"]) + 1
    mock_db["transactions"].append({
        "id": transaction_id,
        "sender_id": transaction.sender_id,
        "amount": Decimal(str(transaction.amount)),
        "transaction_type": "WITHDRAWAL",
        "date": datetime.utcnow().isoformat()
    })

    return {"message": "Withdrawal successful", "account": account}

@router.post("/transfer/")
def transfer(transaction: TransactionCreate, current_user: dict = Depends(get_current_user)):
    """Processes a transfer transaction."""
    sender = mock_db["accounts"].get(transaction.sender_id)
    receiver = mock_db["accounts"].get(transaction.receiver_id)

    if not sender or sender["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Sender account not found or not authorized")
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver account not found")
    if sender["balance"] < transaction.amount or transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Insufficient funds or invalid amount")

    sender["balance"] -= transaction.amount
    receiver["balance"] += transaction.amount

    transaction_id = len(mock_db["transactions"]) + 1
    mock_db["transactions"].append({
        "id": transaction_id,
        "sender_id": sender["id"],
        "receiver_id": receiver["id"],
        "amount": transaction.amount,
        "transaction_type": "TRANSFER",
        "date": datetime.utcnow().isoformat()
    })

    return {"message": "Transfer successful", "accounts": {"sender": sender, "receiver": receiver}}

@router.get("/")
def list_transactions(current_user: dict = Depends(get_current_user)):
    """Retrieves all transactions associated with the authenticated user's accounts."""
    
    user_account_ids = [acc["id"] for acc in mock_db["accounts"].values() if acc["user_id"] == current_user["id"]]
    
    return [
        t for t in mock_db["transactions"]
        if t.get("receiver_id") in user_account_ids or t.get("sender_id") in user_account_ids
    ]
