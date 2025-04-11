from decimal import Decimal
import pytest
from app.services.transactions.core import (
    handle_deposit, handle_withdrawal, handle_transfer
)
from app.model.models import Account, Transaction


def test_handle_deposit_success(seeded_db):
    current_user = {"id": 1, "username": "testuser", "email": "test@example.com"}
    amount = 100
    receiver_id = 1

    transaction, account = handle_deposit(seeded_db, current_user, amount, receiver_id)

    assert isinstance(transaction, Transaction)
    assert transaction.amount == amount
    assert transaction.receiver_id == receiver_id

    updated_account = seeded_db.query(Account).filter_by(id=receiver_id).first()
    assert updated_account.balance == Decimal("1100")


def test_handle_deposit_invalid_amount(seeded_db):
    current_user = {"id": 1, "username": "testuser"}
    with pytest.raises(ValueError):
        handle_deposit(seeded_db, current_user, 0, 1)


def test_handle_withdrawal_success(seeded_db):
    current_user = {"id": 1, "username": "testuser"}
    amount = 100
    sender_id = 1

    transaction, account = handle_withdrawal(seeded_db, current_user, amount, sender_id)

    assert transaction.amount == amount
    assert transaction.sender_id == sender_id
    assert account.balance == Decimal("900")


def test_handle_withdrawal_insufficient_funds(seeded_db):
    current_user = {"id": 1, "username": "testuser"}
    with pytest.raises(ValueError):
        handle_withdrawal(seeded_db, current_user, 10000, 1)


def test_handle_transfer_success(seeded_db):
    # Setup another account for transfer
    receiver = Account(
        id=2,
        user_id=1,
        balance=0,
        account_type="savings",
        account_number="9876543210"
    )
    seeded_db.add(receiver)
    seeded_db.commit()

    current_user = {"id": 1, "username": "testuser", "email": "test@example.com"}
    transaction, sender = handle_transfer(seeded_db, current_user, 200, 1, 2)

    assert transaction.amount == 200
    assert transaction.sender_id == 1
    assert transaction.receiver_id == 2

    assert sender.balance == Decimal("800")
    receiver_updated = seeded_db.query(Account).filter_by(id=2).first()
    assert receiver_updated.balance == Decimal("200")


def test_handle_transfer_same_account(seeded_db):
    current_user = {"id": 1, "username": "testuser", "email": "test@example.com"}
    with pytest.raises(ValueError):
        handle_transfer(seeded_db, current_user, 100, 1, 1)