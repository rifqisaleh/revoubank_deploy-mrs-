import pytest
from datetime import date, datetime, timezone  # Updated import
from app.model.models import User, Account, Transaction, Budget, TransactionCategory, Bill

@pytest.fixture
def new_user():
    return User(
        username="testuser",
        password="hashedpassword",
        email="testuser@example.com",
        full_name="Test User",
        phone_number="1234567890"
    )

@pytest.fixture
def new_account(new_user):
    return Account(
        user=new_user,
        account_type="savings",
        balance=1000.00
    )

@pytest.fixture
def new_transaction(new_account):
    return Transaction(
        type="deposit",
        amount=500.0,
        sender=new_account,
        receiver=new_account
    )

@pytest.fixture
def new_budget(new_user):
    return Budget(
        user_id=new_user.id,
        category="Groceries",
        amount=200.0,
        start_date=datetime.now(timezone.utc),  # Updated to use timezone-aware datetime
        end_date=datetime.now(timezone.utc)    # Updated to use timezone-aware datetime
    )

@pytest.fixture
def new_category(new_user):
    return TransactionCategory(
        user_id=new_user.id,
        name="Shopping"
    )

@pytest.fixture
def new_bill(new_user, new_account):
    return Bill(
        user_id=new_user.id,
        biller_name="Electric Co.",
        due_date=datetime.now(timezone.utc),  # Updated to use timezone-aware datetime
        amount=75.0,
        account_id=new_account.id
    )

def test_user_model_query(test_db, new_user):
    test_db.add(new_user)
    test_db.commit()
    user = test_db.query(User).filter_by(username="testuser").first()
    assert user is not None
    assert user.email == "testuser@example.com"

def test_account_model_query(test_db, new_user, new_account):
    test_db.add(new_user)
    test_db.flush()
    test_db.add(new_account)
    test_db.commit()
    account = test_db.query(Account).filter_by(user_id=new_user.id).first()
    assert account is not None
    assert account.balance == 1000.00

def test_transaction_model_query(test_db, new_user, new_account, new_transaction):
    test_db.add(new_user)
    test_db.flush()
    test_db.add(new_account)
    test_db.flush()
    test_db.add(new_transaction)
    test_db.commit()
    transaction = test_db.query(Transaction).filter_by(type="deposit").first()
    assert transaction is not None
    assert transaction.amount == 500.0

def test_budget_model_query(test_db, new_user, new_budget):
    test_db.add(new_user)
    test_db.flush()
    new_budget.user_id = new_user.id  # <-- Fix here
    test_db.add(new_budget)
    test_db.commit()

    budget = test_db.query(Budget).filter_by(category="Groceries").first()
    assert budget is not None
    assert budget.amount == 200.0


def test_transaction_category_query(test_db, new_user, new_category):
    test_db.add(new_user)
    test_db.flush()
    new_category.user_id = new_user.id  # <-- Fix here
    test_db.add(new_category)
    test_db.commit()

    category = test_db.query(TransactionCategory).filter_by(name="Shopping").first()
    assert category is not None
    assert category.user_id == new_user.id


def test_bill_model_query(test_db, new_user, new_account, new_bill):
    test_db.add(new_user)
    test_db.flush()
    new_account.user_id = new_user.id  # <-- Fix here
    test_db.add(new_account)
    test_db.flush()
    new_bill.user_id = new_user.id     # <-- Fix here
    new_bill.account_id = new_account.id  # <-- Fix here
    test_db.add(new_bill)
    test_db.commit()

    bill = test_db.query(Bill).filter_by(biller_name="Electric Co.").first()
    assert bill is not None
    assert bill.amount == 75.0
