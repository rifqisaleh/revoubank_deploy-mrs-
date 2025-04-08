from flask import jsonify
from decimal import Decimal
from app.model.base import get_db
from app.model.models import Account, Transaction, User, Bill
from app.services.invoice.invoice_generator import generate_invoice
from app.services.email.utils import send_email_async
from app.core.logger import logger
from app.core.auth import get_current_user
from app.utils.email_invoice import send_invoice_with_email
from app.utils.verification import verify_card_number

def handle_deposit(db, current_user, amount, receiver_id):
    
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")

    account = db.query(Account).filter_by(id=receiver_id).first()
    if not account:
        raise LookupError("Account not found")

    if account.user_id != current_user["id"]:
        raise PermissionError("Unauthorized to deposit to this account")

    account.balance += Decimal(str(amount))

    transaction = Transaction(
        type="deposit",
        amount=float(amount),
        receiver_id=receiver_id
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    logger.info(f"✅ Deposit of ${amount} to account {receiver_id} by {current_user['username']}")

    send_invoice_with_email(transaction, user=current_user, account=account)


    return transaction, account


def handle_withdrawal(db, current_user, amount, sender_id):
    if amount <= 0:
        logger.warning(f"⚠️ Invalid withdrawal amount by user {current_user['username']}")
        raise ValueError("Withdrawal amount must be greater than zero")

    logger.info(f"💵 Withdrawal attempt by user {current_user['username']} from account {sender_id}")

    account = db.query(Account).filter_by(id=sender_id).first()
    if not account or account.user_id != current_user["id"]:
        raise PermissionError("Account not found or unauthorized")

    if account.balance < amount:
        raise ValueError("Insufficient funds")

    account.balance -= Decimal(str(amount))

    transaction = Transaction(
        type="withdrawal",
        amount=float(amount),
        sender_id=sender_id
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    send_invoice_with_email(transaction, user=current_user, account=account)

    return transaction, account



def handle_transfer (db, current_user, amount, sender_id, receiver_id):
    #current_user = get_current_user()

    if amount <= 0:
        logger.warning(f"⚠️ Invalid transfer amount by user {current_user['username']}")
        raise ValueError("Transfer amount must be greater than zero")

    logger.info(f"💸 Transfer attempt by user {current_user['username']} from account {sender_id} to account {receiver_id}")

    if not current_user:
        raise PermissionError("Account not found or unauthorized")

    sender = db.query(Account).filter_by(id=sender_id).first()
    receiver = db.query(Account).filter_by(id=receiver_id).first()

    if not sender or sender.user_id != current_user["id"]:
        raise PermissionError("Sender account not found or unauthorized")
    if not receiver:
         raise PermissionError("Receiver account not found")
    if sender.balance < amount:
        raise ValueError("Insufficient funds")
    
    if sender_id == receiver_id:
        raise ValueError("Sender and receiver cannot be the same")


    sender.balance -= Decimal(amount)
    receiver.balance += Decimal(amount)
    
    transaction = Transaction(
        type="transfer",
        amount=float(amount),
        sender_id=sender_id,
        receiver_id=receiver_id
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    send_invoice_with_email(transaction, user=current_user, account=sender)

    receiver_user = db.query(User).filter_by(id=receiver.user_id).first()
    if receiver_user and receiver_user.email:
        send_invoice_with_email(transaction, user={"username": receiver_user.username, "email": receiver_user.email}, account=receiver)

    return transaction, sender


def handle_external_deposit(db, current_user, data):
    amount = Decimal(data["amount"])
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")
    
    account = db.query(Account).filter_by(user_id=current_user["id"]).first()
    if not account:
        raise ValueError("User account not found")

    account.balance += amount

    transaction = Transaction(
        type="external_deposit",
        amount=float(amount),
        receiver_id=account.id,
        bank_name=data["bank_name"],
        external_account_number=data["account_number"]
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    logger.info(
        f"💸 External deposit of ${amount} from {data['bank_name']} by user {current_user['username']} (txn_id={transaction.id})"
    )

    send_invoice_with_email(transaction, user=current_user, account=account)

    return transaction, account


def handle_external_withdrawal(db, current_user, data):
    amount = Decimal(data["amount"])
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")
    
    account = db.query(Account).filter_by(user_id=current_user["id"]).first()
    if not account:
        raise ValueError("User account not found")
    
    account.balance -= Decimal(str(amount))

    # Store transaction
    transaction = Transaction(
        type="external_withdrawal",
        amount=float(amount),
        sender_id=account.id,
        bank_name=data["bank_name"],
        external_account_number=data["account_number"]
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    logger.info(
        f"💸 External withdrawal of ${amount} to {data['bank_name']} by user {current_user['username']} (txn_id={transaction.id})"
    )

    send_invoice_with_email(transaction, user=current_user, account=account)

    return transaction, account


def handle_pay_bill_with_card(db, current_user, bill_id, card_number):
    # Verify card format
    if not verify_card_number(card_number):
        raise ValueError("Invalid card number")

    # Fetch the bill
    bill = db.query(Bill).filter_by(id=bill_id, user_id=current_user["id"]).first()
    if not bill:
        raise LookupError("Bill not found")
    if bill.is_paid:
        logger.warning(f"⚠️ Attempt to pay already paid bill {bill_id} by user {current_user['username']}")
        raise ValueError("Bill is already paid")

    amount = bill.amount
    if amount <= 0:
        logger.error(f"❌ Invalid bill amount ${amount} for bill {bill_id}")
        raise ValueError("Bill amount must be greater than zero")

    # Fetch account
    account = db.query(Account).filter_by(user_id=current_user["id"]).first()
    if not account or account.balance < amount:
        logger.warning(f"⚠️ Insufficient balance for bill payment by user {current_user['username']}")
        raise ValueError("Insufficient balance or account not found")

    logger.info(f"💳 Processing bill payment of ${amount} for bill {bill_id} by user {current_user['username']}")

    # Deduct balance and mark bill as paid
    account.balance -= Decimal(str(amount))
    bill.is_paid = True

    # Create transaction
    transaction = Transaction(
        type="bill_payment",
        amount=float(amount),
        sender_id=account.id,
        biller_name=bill.biller_name,
        payment_method="credit_card"
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    logger.info(f"✅ Bill payment successful: ${amount} paid to {bill.biller_name} (txn_id={transaction.id})")

    send_invoice_with_email(transaction, user=current_user, account=account)
    return transaction, account



def handle_pay_bill_from_balance(db, current_user, bill_id):
    bill = db.query(Bill).filter_by(id=bill_id, user_id=current_user["id"]).first()
    if not bill:
        raise LookupError("Bill not found")
    if bill.is_paid:
        logger.warning(f"⚠️ Attempt to pay already paid bill {bill_id} by user {current_user['username']}")
        raise ValueError("Bill already paid")

    account = db.query(Account).filter_by(user_id=current_user["id"]).first()
    if not account or account.balance < bill.amount:
        logger.warning(f"⚠️ Insufficient balance for bill payment by user {current_user['username']}")
        raise ValueError("Insufficient balance or no account found")

    logger.info(f"💳 Processing bill payment of ${bill.amount} for bill {bill_id} by user {current_user['username']}")

    account.balance -= Decimal(str(bill.amount))
    bill.is_paid = True

    transaction = Transaction(
        type="bill_payment",
        amount=float(bill.amount),
        sender_id=account.id,
        biller_name=bill.biller_name,
        payment_method="account_balance"
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    logger.info(f"✅ Bill payment successful: ${bill.amount} paid to {bill.biller_name} (txn_id={transaction.id})")

    send_invoice_with_email(transaction, user=current_user, account=account)
    return transaction, account
