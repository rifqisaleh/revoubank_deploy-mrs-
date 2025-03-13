# app/mock_database.py

from decimal import Decimal
from datetime import datetime
from app.utils.user import hash_password  # Ensure this import works
from app.config import DATABASE_URL

mock_db = {
    "users": {
        1: {
            "id": 1,
            "username": "admin",
            "password": hash_password("admin123"),
            "email": "admin@example.com",  # <-- Ensure email field exists
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
            "email": "testuser@example.com",  # <-- Ensure email field exists
            "full_name": "Test User",
            "phone_number": "0987654321",
            "failed_attempts": 0,
            "is_locked": False,
            "locked_time": None
        }
    }
    ,
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
transaction_id_counter = 2


def get_mock_db():
    """ Returns the mock database dictionary. """
    return mock_db

def generate_user_id():
    """ Generate a new user ID. """
    global user_id_counter
    user_id = user_id_counter
    user_id_counter += 1
    return user_id

def generate_account_id():
    """ Generate a new account ID. """
    global account_id_counter
    account_id = account_id_counter
    account_id_counter += 1
    return account_id

def generate_transaction_id():
    """ Generate a new transaction ID. """
    global transaction_id_counter
    transaction_id = transaction_id_counter
    transaction_id_counter += 1
    return transaction_id

def reset_dummy_data():
    """ Reset the dummy database for testing purposes. """
    global mock_db, user_id_counter, account_id_counter, transaction_id_counter

    # ✅ Ensure test users persist instead of completely clearing mock_db
    mock_db = {
        "users": {
            1: {  # ✅ Keep an admin/test user in the DB
                "id": 1,
                "username": "admin",
                "password": hash_password("admin123"),  # Ensure it's hashed
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

    user_id_counter = 3  # Ensure counters align with mock data
    account_id_counter = 3
    transaction_id_counter = 2
