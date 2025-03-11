# app/mock_database.py

from typing import Dict, List
from decimal import Decimal
from datetime import datetime
from app.schemas import TransactionType

# Mock database as in-memory dictionaries
mock_db = {
    "users": {},        
    "accounts": {},      
    "transactions": []  
}

# Auto-incrementing counters for IDs
user_id_counter = 1
account_id_counter = 1
transaction_id_counter = 1

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
    mock_db = {
        "users": {},
        "accounts": {},
        "transactions": []
    }
    user_id_counter = 1
    account_id_counter = 1
    transaction_id_counter = 1
