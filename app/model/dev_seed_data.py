# app/mock_database.py

import json
import os
from decimal import Decimal
from datetime import datetime
from app.utils.user import hash_password  
from app.config import Config

DATABASE_URL = Config.DATABASE_URL
DB_FILE = "mock_db.json"

mock_db = {
    "users": {
        1: {
            "id": 1,
            "username": "admin",
            "password": hash_password("admin123"),
            "email": "admin@example.com",  
            "full_name": "Admin User",
            "phone_number": "1234567890",
            "failed_attempts": 0,
            "is_locked": False,
            "locked_time": None
        },
        2: {
            "id": 2,
            "username": "testuser",
            "password": hash_password("test123"),
            "email": "testuser@example.com",  
            "full_name": "Test User",
            "phone_number": "0987654321",
            "failed_attempts": 0,
            "is_locked": False,
            "locked_time": None
        }
    },
    "accounts": {
        1: {
            "id": 1,
            "user_id": 1,
            "account_type": "savings",
            "balance": Decimal("1000.00")
        },
        2: {
            "id": 2,
            "user_id": 2,
            "account_type": "checking",
            "balance": Decimal("500.00")
        }
    },
    "transactions": [
        {
            "id": 2,
            "sender_id": 2,   
            "receiver_id": 1,
            "amount": Decimal("100.00"),
            "transaction_type": "TRANSFER",
            "date": datetime.utcnow().isoformat()
        }
    ]
}

# ✅ Auto-incrementing counters
user_id_counter = 3
account_id_counter = 3
transaction_id_counter = 3

# Load and Save functions
def load_mock_db():
    global mock_db, user_id_counter, account_id_counter, transaction_id_counter
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            mock_db["users"] = {int(k): v for k, v in data.get("users", {}).items()}
            mock_db["accounts"] = {int(k): {
                **v, 
                "balance": Decimal(v["balance"])
            } for k, v in data.get("accounts", {}).items()}
            mock_db["transactions"] = [{
                **txn, 
                "amount": Decimal(txn["amount"])
            } for txn in data.get("transactions", [])]

            user_id_counter = data.get("user_id_counter", user_id_counter)
            account_id_counter = data.get("account_id_counter", account_id_counter)
            transaction_id_counter = data.get("transaction_id_counter", transaction_id_counter)

def save_mock_db(db=None):
    """Save the mock database state."""
    if db is None:
        db = mock_db
    with open(DB_FILE, "w") as f:
        json.dump({
            "users": db["users"],
            "accounts": {
                k: {
                    **v, 
                    "balance": str(v["balance"])
                } for k, v in db["accounts"].items()
            },
            "transactions": [
                {
                    **txn,
                    "amount": str(txn["amount"])
                } for txn in db["transactions"]
            ],
            "user_id_counter": user_id_counter,
            "account_id_counter": account_id_counter,
            "transaction_id_counter": transaction_id_counter,
        }, f, default=str)

# Load the mock_db initially from file
load_mock_db()

# Existing functions preserved exactly
def get_mock_db():
    return mock_db

def generate_user_id():
    global user_id_counter
    user_id = user_id_counter
    user_id_counter += 1
    save_mock_db()
    return user_id

def generate_account_id():
    global account_id_counter
    account_id = account_id_counter
    account_id_counter += 1
    save_mock_db()
    return account_id

def generate_transaction_id():
    global transaction_id_counter
    transaction_id = transaction_id_counter
    transaction_id_counter += 1
    save_mock_db()
    return transaction_id

def reset_dummy_data():
    global mock_db, user_id_counter, account_id_counter, transaction_id_counter

    mock_db = {
        "users": {
            1: {
                "id": 1,
                "username": "admin",
                "password": hash_password("admin123"),
                "email": "admin@example.com",
                "full_name": "Admin User",
                "phone_number": "1234567890",
                "failed_attempts": 0,
                "is_locked": False,
                "locked_time": None,
            },
            2: {
                "id": 2,
                "username": "testuser",
                "password": hash_password("test123"),
                "email": "testuser@example.com",
                "full_name": "Test User",
                "phone_number": "0987654321",
                "failed_attempts": 0,
                "is_locked": False,
                "locked_time": None,
            }
        },
        "accounts": {
            1: {
                "id": 1,
                "user_id": 1,
                "account_type": "savings",
                "balance": Decimal("1000.00")
            },
            2: {
                "id": 2,
                "user_id": 2,
                "account_type": "checking",
                "balance": Decimal("500.00")
            }
        },
        "transactions": [
            {
                "id": 2,
                "sender_id": 2,
                "receiver_id": 1,
                "amount": Decimal("100.00"),
                "transaction_type": "TRANSFER",
                "date": datetime.utcnow().isoformat()
            }
        ]
    }

    user_id_counter = 3
    account_id_counter = 3
    transaction_id_counter = 3

    save_mock_db()
