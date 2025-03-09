from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Account, User
from app.schemas import AccountCreate, AccountResponse

router = APIRouter()

@router.post("/accounts/", response_model=AccountResponse)
def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(User.id == account.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_account = Account(
        user_id=account.user_id, 
        account_type=account.account_type.value,  # ✅ Save as string
        balance=account.initial_balance
    )
    
    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return new_account

