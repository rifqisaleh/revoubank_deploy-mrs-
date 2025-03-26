
import pytest
import warnings
from decimal import Decimal
from app.model.models import User, Account, Transaction, Bill, Budget
from app.model.base import db

warnings.filterwarnings("ignore", category=DeprecationWarning)


def test_user_query(test_app):
    with test_app.app_context():
        user = User.query.filter_by(username="john_doe").first()
        assert user is not None
        assert user.email == "john@example.com"  # ✅ OR 'john.doe@example.com' if you update seed

def test_account_balance(test_app):
    with test_app.app_context():
        user = User.query.filter_by(username="john_doe").first()
        account = Account.query.filter_by(user_id=user.id).first()
        assert account is not None
        assert isinstance(account.balance, (float, Decimal))  # ✅ Accept Decimal too

def test_transaction_exists(test_app):
    with test_app.app_context():
        tx = Transaction.query.filter_by(type="deposit").first()
        assert tx is not None
        assert tx.amount > 0

def test_bill_existence(test_app):
    with test_app.app_context():
        user = User.query.filter_by(username="john_doe").first()
        bill = Bill.query.filter_by(user_id=user.id).first()
        assert bill is not None
        assert isinstance(bill.is_paid, bool)

def test_budget_entry(test_app):
    with test_app.app_context():
        user = User.query.filter_by(username="john_doe").first()
        budget = Budget.query.filter_by(user_id=user.id).first()
        assert budget is not None
        assert budget.amount >= 0
