from decimal import Decimal
from flask import jsonify, request
from app.model.models import Account
from app.core.logger import logger
from app.schemas import AccountResponse, AccountCreate
from app.utils.pagination import apply_pagination
from uuid import uuid4


def create_account_logic(db, current_user, data):
    # Validate input using Pydantic
    account_data = AccountCreate(**data)

    new_account = Account(
        user_id=current_user["id"],
        account_type=account_data.account_type.value,
        balance=Decimal(str(account_data.initial_balance)),
        account_number=uuid4().hex[:10]
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return AccountResponse(
        id=new_account.id,
        user_id=new_account.user_id,
        account_type=new_account.account_type,
        balance=float(new_account.balance),
        account_number=new_account.account_number
    )


def list_user_accounts_logic(db, current_user):
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    query = db.query(Account).filter_by(user_id=current_user["id"], is_deleted=False)
    total, accounts = apply_pagination(query, page, per_page)

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "accounts": [AccountResponse(
            id=acc.id,
            user_id=acc.user_id,
            account_type=acc.account_type,
            balance=float(acc.balance),
            account_number=acc.account_number
        ).dict() for acc in accounts]
    }


def get_user_account_by_id_logic(db, current_user, account_id):
    account = db.query(Account).filter_by(
        id=account_id,
        user_id=current_user["id"],
        is_deleted=False
    ).first()

    if not account:
        raise LookupError("Account not found or unauthorized")

    return AccountResponse(
        id=account.id,
        user_id=account.user_id,
        account_type=account.account_type,
        balance=float(account.balance),
        account_number=account.account_number
    ).dict()

def update_user_account_logic(db, current_user, account_id, update_data: dict):
    account = db.query(Account).filter_by(
        id=account_id,
        user_id=current_user["id"],
        is_deleted=False
    ).first()

    if not account:
        raise LookupError("Account not found or unauthorized")

    account_update = AccountCreate(**update_data)
    account.balance = Decimal(str(account_update.initial_balance))
    account.account_type = account_update.account_type.value

    db.commit()
    db.refresh(account)

    return AccountResponse(
        id=account.id,
        user_id=account.user_id,
        account_type=account.account_type,
        balance=float(account.balance),
        account_number=account.account_number
    ).dict()


def delete_user_account_logic(db, current_user, account_id):
    account = db.query(Account).filter_by(
        id=account_id,
        user_id=current_user["id"],
        is_deleted=False
    ).first()

    if not account:
        raise LookupError("Account not found or unauthorized")

    account.is_deleted = True
    db.commit()
    return {"message": "Account marked as deleted, transactions remain intact."}
