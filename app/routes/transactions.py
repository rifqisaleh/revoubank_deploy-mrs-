from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional
from app.database.mock_database import get_mock_db, generate_transaction_id
from app.core.auth import get_current_user
from app.services.email.utils import send_email_async
from app.services.invoice.invoice_generator import generate_invoice

router = APIRouter()

mock_db = get_mock_db()

class TransactionCreate(BaseModel):
    sender_id: Optional[int] = None
    receiver_id: Optional[int] = None
    amount: Decimal
    transaction_type: str

@router.post("/deposit/")
async def deposit(transaction: TransactionCreate, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    if transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Deposit amount must be greater than zero")

    account = mock_db["accounts"].get(transaction.receiver_id)
    if not account or account["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Account not found or unauthorized")

    account["balance"] += Decimal(str(transaction.amount))

    transaction_record = {
        "id": generate_transaction_id(),
        "receiver_id": transaction.receiver_id,
        "amount": transaction.amount,
        "transaction_type": "DEPOSIT",
        "date": datetime.utcnow().isoformat()
    }

    mock_db["transactions"].append(transaction_record)

    invoice_filename = f"deposit_invoice_{transaction_record['id']}.pdf"
    invoice_path = generate_invoice(transaction_record, invoice_filename, current_user)

    email_subject = "Deposit Successful"
    email_body = f"""
        <p>Hello {current_user['username']},</p>
        <p>You successfully deposited <strong>${transaction.amount}</strong> into your RevouBank account.</p>
        <p>Invoice attached.</p>
    """

    background_tasks.add_task(
        send_email_async,
        subject=email_subject,
        recipient="user@example.com",
        body=email_body,
        attachment_path=invoice_path
    )

    return {"message": "Deposit successful", "account": account}

@router.post("/withdraw/")
async def withdraw(transaction: TransactionCreate, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    account = mock_db["accounts"].get(transaction.sender_id)
    if not account or account["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Account not found or unauthorized")

    if account["balance"] < transaction.amount or transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Insufficient funds or invalid amount")

    account["balance"] -= transaction.amount

    transaction_record = {
        "id": generate_transaction_id(),
        "sender_id": transaction.sender_id,
        "receiver_id": None,
        "amount": transaction.amount,
        "transaction_type": "WITHDRAWAL",
        "date": datetime.utcnow().isoformat()
    }

    mock_db["transactions"].append(transaction_record)

    invoice_filename = f"withdrawal_{transaction_record['id']}.pdf"
    invoice_path = generate_invoice(transaction_record, invoice_filename, current_user)

    email_subject = "Withdrawal Successful"
    email_body = f"""
        <p>Hello {current_user['username']},</p>
        <p>You successfully withdrew <strong>${transaction.amount}</strong> from your RevouBank account.</p>
        <p>Your invoice is attached.</p>
    """

    background_tasks.add_task(
        send_email_async,
        subject=email_subject,
        recipient="user@example.com",
        body=email_body,
        attachment_path=invoice_path
    )

    return {"message": "Withdrawal successful", "account": account}

@router.post("/transfer/")
async def transfer(transaction: TransactionCreate, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    sender = mock_db["accounts"].get(transaction.sender_id)
    receiver = mock_db["accounts"].get(transaction.receiver_id)

    if not sender or sender["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Sender account not found or unauthorized")
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver account not found")
    if sender["balance"] < transaction.amount or transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Insufficient funds or invalid amount")

    sender["balance"] -= transaction.amount
    receiver["balance"] += transaction.amount

    transaction_record = {
        "id": generate_transaction_id(),
        "sender_id": sender["id"],
        "receiver_id": receiver["id"],
        "amount": transaction.amount,
        "transaction_type": "TRANSFER",
        "date": datetime.utcnow().isoformat()
    }

    mock_db["transactions"].append(transaction_record)

    invoice_filename = f"transfer_invoice_{transaction_record['id']}.pdf"
    invoice_path = generate_invoice(transaction_record, invoice_filename, current_user)

    email_subject = "Transfer Successful"
    email_body = f"""
        <p>Hello {current_user['username']},</p>
        <p>You transferred <strong>${transaction.amount}</strong> successfully.</p>
        <p>Your invoice is attached.</p>
    """

    background_tasks.add_task(
        send_email_async,
        subject=email_subject,
        recipient="user@example.com",
        body=email_body,
        attachment_path=invoice_path
    )

    return {
        "message": "Transfer successful",
        "accounts": {"sender": sender, "receiver": receiver}
    }

@router.get("/")
def list_transactions(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]

    return [
        t for t in mock_db["transactions"]
        if (t.get("receiver_id") and mock_db["users"].get(user_id))
        or (t.get("sender_id") and mock_db["users"].get(user_id))
    ]

@router.get("/check-balance/")
def check_balance(account_id: int, current_user: dict = Depends(get_current_user)):
    account = mock_db["accounts"].get(account_id)
    if not account or account["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Account not found or unauthorized")
    
    return {"account_id": account_id, "balance": account["balance"]}
