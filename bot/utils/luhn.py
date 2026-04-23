"bot/utils/luhn.py"

import secrets

def calculate_luhn_check_digit(digits: str) -> int:
    n = len(digits)
    total = 0
    for i in range(n):
        d = int(digits[n - 1 - i])
        if i % 2 != 0:
            d = d * 2
            if d > 9:
                d = d - 9
        total += d
    return (10 - (total % 10)) % 10

def generate_verification_code(telegram_user_id: int) -> str:
    base_digits = str(telegram_user_id % 999999999).zfill(9)
    salt = secrets.token_hex(2)[:3].upper()
    check_digit = calculate_luhn_check_digit(base_digits)

    p1 = base_digits[:3]
    p2 = base_digits[3:6]
    p3 = base_digits[6:]

    return f"{p1}-{p2}-{p3}{check_digit}{salt}"

def validate_luhn(code: str) -> bool:
    if not code or len(code) != 15:
        return False

    clean = code.replace("-", "")
    if len(clean) != 13:
        return False

    numeric_part = clean[:9]
    if not numeric_part.isdigit():
        return False

    check_digit_provided = clean[9]
    if not check_digit_provided.isdigit():
        return False

    actual_check_digit = calculate_luhn_check_digit(numeric_part)
    return int(check_digit_provided) == actual_check_digit
