# app/utils/verification.py

import re

def verify_card_number(card_number: str) -> bool:
    # Mock logic: Cards starting with '4' are valid (16 digits, like Visa)
    pattern = r'^4\d{15}$'
    return bool(re.match(pattern, card_number))
