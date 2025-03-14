from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.database.mock_database import get_mock_db, generate_account_id, generate_transaction_id
from app.core.auth import get_current_user
from app.schemas import AccountCreate, AccountResponse
from decimal import Decimal
from datetime import datetime
from app.services.email.utils import send_email_async
from app.services.invoice.invoice_generator import generate_invoice

router = APIRouter()
mock_db = get_mock_db()

@router.post(
    "/", 
    response_model=AccountResponse,
    summary="Create a New Account",
    description="Creates a new account for the authenticated user. The initial balance is treated as an external deposit, generating a transaction and sending an email notification."
)
async def create_account(
    account: AccountCreate, 
    background_tasks: BackgroundTasks, 
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    if user_id not in mock_db["users"]:
        raise HTTPException(status_code=404, detail="User not found")
    
    account_id = generate_account_id()
    mock_db["accounts"][account_id] = {
        "id": account_id,
        "user_id": user_id,
        "account_type": account.account_type.value,
        "balance": Decimal(str(account.initial_balance))
    }
    
    transaction_id = generate_transaction_id()
    transaction_record = {
        "id": transaction_id,
        "sender_id": None,
        "receiver_id": account_id,
        "amount": account.initial_balance,
        "transaction_type": "EXTERNAL DEPOSIT (INITIAL BALANCE)",
        "date": datetime.utcnow().isoformat()
    }
    mock_db["transactions"].append(transaction_record)
    
    invoice_filename = f"external_deposit_{transaction_id}.pdf"
    invoice_path = generate_invoice(transaction_record, invoice_filename, current_user)
    
    email_subject = "Initial Account Deposit"
    email_body = f"""
        <p>Hello {current_user['username']},</p>
        <p>Your new account has been created successfully with an initial deposit of <strong>${account.initial_balance}</strong>.</p>
        <p>Please find your transaction invoice attached.</p>
    """
    background_tasks.add_task(
        send_email_async,
        subject=email_subject,
        recipient="user@example.com",
        body=email_body,
        attachment_path=invoice_path
    )
    
    return AccountResponse(
        id=account_id,
        user_id=user_id,
        account_type=account.account_type.value,
        balance=account.initial_balance
    )

@router.get(
    "/", 
    response_model=list[AccountResponse],
    summary="Retrieve All Accounts",
    description="Returns a list of all accounts owned by the authenticated user."
)
def list_accounts(current_user: dict = Depends(get_current_user)):
    return [
        AccountResponse(
            id=acc["id"],
            user_id=acc["user_id"],
            account_type=acc["account_type"],
            balance=acc["balance"]
        )
        for acc in mock_db["accounts"].values()
        if acc["user_id"] == current_user["id"]
    ]

@router.get(
    "/{id}", 
    response_model=AccountResponse,
    summary="Retrieve a Specific Account",
    description="Retrieves an account by its ID if it belongs to the authenticated user."
)
def get_account(id: int, current_user: dict = Depends(get_current_user)):
    account = mock_db["accounts"].get(id)
    if not account or account["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Account not found or unauthorized")
    return account

@router.put(
    "/{id}", 
    response_model=AccountResponse,
    summary="Update an Account",
    description="Updates the details of an account owned by the authenticated user."
)
def update_account(id: int, account_update: AccountCreate, current_user: dict = Depends(get_current_user)):
    account = mock_db["accounts"].get(id)
    if not account or account["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Account not found or unauthorized")
    
    account["balance"] = Decimal(str(account_update.initial_balance))
    account["account_type"] = account_update.account_type.value
    return account

@router.delete(
    "/{id}",
    summary="Delete an Account",
    description="Marks an account as deleted instead of removing it, preserving its transactions."
)
def delete_account(id: int, current_user: dict = Depends(get_current_user)):
    account = mock_db["accounts"].get(id)
    if not account or account["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Account not found or unauthorized")
    
    account["deleted"] = True  
    return {"message": "Account marked as deleted, transactions remain intact."}
