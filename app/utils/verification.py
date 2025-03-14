# app/utils/verification.py

import re

def verify_card_number(card_number: str) -> bool:
    # Updated logic: Support Visa (starts with '4') and Mastercard (starts with '5')
    pattern = r'^(4\d{15}|5\d{15})$'
    return bool(re.match(pattern, card_number))
