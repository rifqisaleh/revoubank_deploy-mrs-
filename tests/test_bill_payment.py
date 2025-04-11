import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from app.services.transactions.core import (
    handle_pay_bill_with_card,
    handle_pay_bill_from_balance
)
from app.model.models import Account, Bill

def test_handle_pay_bill_with_card_success(seeded_db):
    bill = Bill(
        id=1,
        user_id=1,
        biller_name="Telkom",
        amount=100,
        is_paid=False,
        due_date=datetime.utcnow() + timedelta(days=7),
        account_id=1
    )
    seeded_db.add(bill)
    seeded_db.commit()

    current_user = {"id": 1, "username": "testuser"}
    card_number = "4111111111111111"

    transaction, account = handle_pay_bill_with_card(seeded_db, current_user, bill_id=1, card_number=card_number)

    assert transaction.amount == 100
    assert transaction.biller_name == "Telkom"
    assert transaction.payment_method == "credit_card"
    assert account.balance == Decimal("900")

    updated_bill = seeded_db.query(Bill).filter_by(id=1).first()
    assert updated_bill.is_paid is True


def test_handle_pay_bill_with_card_invalid_card(seeded_db):
    bill = Bill(
        id=2,
        user_id=1,
        biller_name="PLN",
        amount=150,
        is_paid=False,
        due_date=datetime.utcnow() + timedelta(days=7),
        account_id=1
    )
    seeded_db.add(bill)
    seeded_db.commit()

    current_user = {"id": 1, "username": "testuser"}
    invalid_card = "1234"

    with pytest.raises(ValueError):
        handle_pay_bill_with_card(seeded_db, current_user, bill_id=2, card_number=invalid_card)


def test_handle_pay_bill_from_balance_success(seeded_db):
    bill = Bill(
        id=3,
        user_id=1,
        biller_name="BPJS",
        amount=200,
        is_paid=False,
        due_date=datetime.utcnow() + timedelta(days=7),
        account_id=1
    )
    seeded_db.add(bill)
    seeded_db.commit()

    current_user = {"id": 1, "username": "testuser"}

    transaction, account = handle_pay_bill_from_balance(seeded_db, current_user, bill_id=3)

    assert transaction.amount == 200
    assert transaction.payment_method == "account_balance"
    assert account.balance == Decimal("800")

    updated_bill = seeded_db.query(Bill).filter_by(id=3).first()
    assert updated_bill.is_paid is True


def test_handle_pay_bill_from_balance_insufficient_funds(seeded_db):
    account = seeded_db.query(Account).filter_by(id=1).first()
    account.balance = 50
    seeded_db.commit()

    bill = Bill(
        id=4,
        user_id=1,
        biller_name="Indihome",
        amount=100,
        is_paid=False,
        due_date=datetime.utcnow() + timedelta(days=7),
        account_id=1
    )
    seeded_db.add(bill)
    seeded_db.commit()

    current_user = {"id": 1, "username": "testuser"}

    with pytest.raises(ValueError):
        handle_pay_bill_from_balance(seeded_db, current_user, bill_id=4)
