# app/routes/external_transactions.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from decimal import Decimal
from datetime import datetime
from app.database.mock_database import get_mock_db, generate_transaction_id
from app.core.auth import get_current_user
from app.services.email.utils import send_email_async
from app.services.invoice.invoice_generator import generate_invoice

router = APIRouter()

mock_db = get_mock_db()

@router.post("/external/deposit/")
async def external_deposit(
    bank_name: str,
    account_number: str,
    amount: Decimal,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    user_account = next(
        (acc for acc in mock_db["accounts"].values() if acc["user_id"] == current_user["id"]),
        None
    )

    if not user_account:
        raise HTTPException(status_code=404, detail="RevouBank account not found.")

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero.")

    # Simulate receiving money clearly
    user_account["balance"] += amount

    transaction = {
        "id": generate_transaction_id(),
        "sender_id": None,  # External bank
        "receiver_id": user_account["id"],
        "amount": amount,
        "transaction_type": f"EXTERNAL DEPOSIT - {bank_name.upper()}",
        "date": datetime.utcnow().isoformat()
    }

    mock_db["transactions"].append(transaction)

    invoice_filename = f"external_deposit_{transaction['id']}.pdf"
    invoice_path = generate_invoice(transaction, invoice_filename, current_user)

    email_subject = "External Deposit Received"
    email_body = f"""
        <p>Hello {current_user['username']},</p>
        <p>You have successfully received an external deposit from <strong>{bank_name}</strong> (Account: {account_number}) of amount <strong>${amount}</strong>.</p>
        <p>Please find your invoice attached.</p>
    """

    background_tasks.add_task(
        send_email_async,
        subject=email_subject,
        recipient="user@example.com",
        body=email_body,
        attachment_path=invoice_path
    )

    return {"message": f"Successfully deposited ${amount} from {bank_name}."}

@router.post("/external/withdraw/")
async def external_withdraw(
    bank_name: str,
    account_number: str,
    amount: Decimal,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    user_account = next(
        (acc for acc in mock_db["accounts"].values() if acc["user_id"] == current_user["id"]),
        None
    )

    if not user_account:
        raise HTTPException(status_code=404, detail="RevouBank account not found.")

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero.")
    if user_account["balance"] < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance.")

    # Simulate withdrawing money clearly
    user_account["balance"] -= amount

    transaction = {
        "id": generate_transaction_id(),
        "sender_id": user_account["id"],
        "receiver_id": None,  # External bank
        "amount": amount,
        "transaction_type": f"EXTERNAL WITHDRAWAL - {bank_name.upper()}",
        "date": datetime.utcnow().isoformat()
    }

    mock_db["transactions"].append(transaction)

    invoice_filename = f"external_withdraw_{transaction['id']}.pdf"
    invoice_path = generate_invoice(transaction, invoice_filename, current_user)

    email_subject = f"External Withdrawal to {bank_name}"
    email_body = f"""
        <p>Hello {current_user['username']},</p>
        <p>You have successfully withdrawn <strong>${amount}</strong> from your RevouBank account to your external account at <strong>{bank_name}</strong>.</p>
        <p>Please find your invoice attached.</p>
    """

    background_tasks.add_task(
        send_email_async,
        subject=email_subject,
        recipient="user@example.com",
        body=email_body,
        attachment_path=invoice_path
    )

    user_account["balance"] -= amount

    return {"message": f"Withdrawal of ${amount} to {bank_name} successful."}
