import pytest
from app.model.models import User, Account

@pytest.fixture
def test_user(test_db):
    user = User(
        username="johndoe",
        full_name="John Doe",
        email="johndoe@example.com",
        password="securepassword",
    )
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
def test_account(test_db, test_user):
    account = Account(
        user_id=test_user.id,
        account_type="Checking",
        balance=1000.0,
        account_number="1234567890"
    )
    test_db.add(account)
    test_db.commit()
    return account


def test_create_account(test_db, test_user):
    account = Account(
        user_id=test_user.id,
        account_type="Savings",
        balance=5000.0,
        account_number="0987654321"
    )
    test_db.add(account)
    test_db.commit()

    retrieved = test_db.query(Account).filter_by(account_number="0987654321").first()
    assert retrieved is not None
    assert retrieved.account_type == "Savings"
    assert retrieved.balance == 5000.0


def test_list_accounts(test_db, test_account):
    accounts = test_db.query(Account).all()
    assert isinstance(accounts, list)
    assert test_account in accounts


def test_get_account(test_db, test_account):
    retrieved = test_db.query(Account).filter_by(id=test_account.id).first()
    assert retrieved is not None
    assert retrieved.id == test_account.id


def test_update_account(test_db, test_account):
    test_account.balance = 2000.0
    test_db.commit()

    updated = test_db.query(Account).filter_by(id=test_account.id).first()
    assert updated.balance == 2000.0


def test_delete_account(test_db, test_account):
    test_db.delete(test_account)
    test_db.commit()

    deleted = test_db.query(Account).filter_by(id=test_account.id).first()
    assert deleted is None
