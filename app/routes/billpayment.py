from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from decimal import Decimal
from datetime import datetime
from app.database.mock_database import get_mock_db, generate_transaction_id
from app.core.auth import get_current_user
from app.utils.verification import verify_card_number
from app.services.email.utils import send_email_async
from app.services.invoice.invoice_generator import generate_invoice

router = APIRouter()

mock_db = get_mock_db()

@router.post(
    "/billpayment/card/",
    summary="Pay Bill with Credit Card",
    description="Allows users to pay their bills using a credit card. "
                "The endpoint verifies the card number, deducts the amount from the user's account, "
                "and generates an invoice for the transaction."
)
async def pay_bill_with_card(
    biller_name: str,
    amount: Decimal,
    card_number: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    if not verify_card_number(card_number):
        raise HTTPException(status_code=400, detail="Invalid credit card number provided.")

    user_account = next(
        (acc for acc in mock_db["accounts"].values() if acc["user_id"] == current_user["id"]),
        None
    )
    if not user_account:
        raise HTTPException(status_code=404, detail="User account not found.")

    if user_account["balance"] < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance.")

    user_account["balance"] -= amount

    transaction = {
        "id": generate_transaction_id(),
        "sender_id": user_account["id"],
        "receiver_id": None,
        "amount": amount,
        "transaction_type": f"BILL PAYMENT (CARD) - {biller_name.upper()}",
        "date": datetime.utcnow().isoformat()
    }

    mock_db["transactions"].append(transaction)

    invoice_filename = f"invoice_{transaction['id']}.pdf"
    invoice_path = generate_invoice(transaction, invoice_filename, current_user)

    email_subject = f"Bill Payment Invoice - {biller_name}"
    email_body = f"""
        <p>Hello {current_user['username']},</p>
        <p>You have successfully paid your bill ({biller_name}) of <strong>${amount}</strong> using your credit card.</p>
        <p>Please find your invoice attached.</p>
        <p>Thank you for using RevouBank.</p>
    """

    background_tasks.add_task(
        send_email_async,
        subject=email_subject,
        recipient="user@example.com",
        body=email_body,
        attachment_path=invoice_path
    )

    return FileResponse(
        invoice_path,
        media_type='application/pdf',
        filename=invoice_filename
    )

@router.post(
    "/billpayment/balance/",
    summary="Pay Bill with Account Balance",
    description="Allows users to pay their bills using their account balance. "
                "The endpoint deducts the amount from the user's account, "
                "and generates an invoice for the transaction."
)
async def pay_bill_with_balance(
    biller_name: str,
    amount: Decimal,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    user_account = next(
        (acc for acc in mock_db["accounts"].values() if acc["user_id"] == current_user["id"]),
        None
    )
    if not user_account:
        raise HTTPException(status_code=404, detail="User account not found.")

    if user_account["balance"] < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance.")

    user_account["balance"] -= amount

    transaction = {
        "id": generate_transaction_id(),
        "sender_id": user_account["id"],
        "receiver_id": None,
        "amount": amount,
        "transaction_type": f"BILL PAYMENT (BALANCE) - {biller_name.upper()}",
        "date": datetime.utcnow().isoformat()
    }

    mock_db["transactions"].append(transaction)

    invoice_filename = f"invoice_{transaction['id']}.pdf"
    invoice_path = generate_invoice(transaction, invoice_filename, current_user)

    email_subject = f"Bill Payment Invoice - {biller_name}"
    email_body = f"""
        <p>Hello {current_user['username']},</p>
        <p>You have successfully paid your bill ({biller_name}) of <strong>${amount}</strong> using your account balance.</p>
        <p>Please find your invoice attached.</p>
        <p>Thank you for using RevouBank.</p>
    """

    background_tasks.add_task(
        send_email_async,
        subject=email_subject,
        recipient="user@example.com",
        body=email_body,
        attachment_path=invoice_path
    )

    return FileResponse(
        invoice_path,
        media_type='application/pdf',
        filename=invoice_filename
    )
