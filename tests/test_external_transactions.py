import pytest
from decimal import Decimal
from app.services.transactions.core import (
    handle_external_deposit,
    handle_external_withdrawal
)
from app.model.models import Account, Transaction

def test_external_deposit_success(seeded_db):
    current_user = {"id": 1, "username": "testuser", "email": "test@example.com"}
    data = {
        "amount": "200.00",
        "bank_name": "Bank Mandiri",
        "account_number": "999888777"
    }

    transaction, account = handle_external_deposit(seeded_db, current_user, data)

    assert transaction.amount == 200.00
    assert transaction.type == "external_deposit"
    assert transaction.bank_name == "Bank Mandiri"
    assert account.balance == Decimal("1200.00")


def test_external_deposit_invalid_amount(seeded_db):
    current_user = {"id": 1, "username": "testuser"}
    data = {
        "amount": "0",
        "bank_name": "Bank BCA",
        "account_number": "123"
    }

    with pytest.raises(ValueError):
        handle_external_deposit(seeded_db, current_user, data)


def test_external_withdrawal_success(seeded_db):
    current_user = {"id": 1, "username": "testuser", "email": "test@example.com"}
    data = {
        "amount": "300.00",
        "bank_name": "Bank BRI",
        "account_number": "112233"
    }

    transaction, account = handle_external_withdrawal(seeded_db, current_user, data)

    assert transaction.amount == 300.00
    assert transaction.type == "external_withdrawal"
    assert transaction.bank_name == "Bank BRI"
    assert account.balance == Decimal("700.00")


def test_external_withdrawal_insufficient_funds(seeded_db):
    current_user = {"id": 1, "username": "testuser"}
    data = {
        "amount": "9999.00",
        "bank_name": "Bank Mega",
        "account_number": "000999"
    }

    with pytest.raises(ValueError):
        handle_external_withdrawal(seeded_db, current_user, data)