from fastapi import APIRouter, Depends, HTTPException
from app.mock_database import get_mock_db, generate_account_id  # ✅ Import mock database & ID generator
from app.auth import get_current_user
from app.schemas import AccountCreate, AccountResponse
from decimal import Decimal

router = APIRouter()
mock_db = get_mock_db()  # ✅ Get mock database

# ✅ Create New Account
@router.post("/", response_model=AccountResponse)
def create_account(account: AccountCreate, current_user: dict = Depends(get_current_user)):
    """Creates a new account for the authenticated user in the mock database."""
    
    # ✅ Check if user exists
    user_id = current_user["id"]
    if user_id not in mock_db["users"]:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Use auto-increment function for account ID
    account_id = generate_account_id()

    # ✅ Create a new account entry
    mock_db["accounts"][account_id] = {
        "id": account_id,
        "user_id": user_id,
        "account_type": account.account_type.value,  # ✅ Store as string
        "balance": Decimal(str(account.initial_balance))  # ✅ Ensure decimal consistency
    }

    return AccountResponse(
        id=account_id,
        user_id=user_id,
        account_type=account.account_type.value,
        balance=account.initial_balance
    )

# ✅ Get All Accounts for Authenticated User
@router.get("/", response_model=list[AccountResponse])
def list_accounts(current_user: dict = Depends(get_current_user)):
    """Retrieves all accounts owned by the authenticated user."""
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

# ✅ Get Specific Account
@router.get("/{id}", response_model=AccountResponse)
def get_account(id: int, current_user: dict = Depends(get_current_user)):
    """Retrieves a specific account by ID (Authorization required)."""
    account = mock_db["accounts"].get(id)
    if not account or account["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Account not found or unauthorized")
    return account

# ✅ Update Account
@router.put("/{id}", response_model=AccountResponse)
def update_account(id: int, account_update: AccountCreate, current_user: dict = Depends(get_current_user)):
    """Updates an account owned by the authenticated user."""
    account = mock_db["accounts"].get(id)
    if not account or account["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Account not found or unauthorized")

    account["balance"] = Decimal(str(account_update.initial_balance))
    account["account_type"] = account_update.account_type.value

    return account

# ✅ Delete Account
@router.delete("/{id}")
def delete_account(id: int, current_user: dict = Depends(get_current_user)):
    """Marks an account as deleted instead of removing it, preserving its transactions."""

    account = mock_db["accounts"].get(id)
    if not account or account["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Account not found or unauthorized")

    # ✅ Instead of deleting, mark the account as inactive
    account["deleted"] = True  # ✅ Add a new key to mark deleted accounts

    return {"message": "Account marked as deleted, transactions remain intact."}

