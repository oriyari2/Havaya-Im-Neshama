from __future__ import annotations

import re


EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def login_email(value: object) -> str:
    cleaned = str(value or "").strip().lower()
    if len(cleaned) > 254 or not EMAIL.match(cleaned):
        raise ValueError("כתובת הדוא״ל אינה תקינה.")
    return cleaned


def account_password(value: object, confirmation: object) -> str:
    password = str(value or "")
    if not password:
        raise ValueError("יש להזין סיסמה.")
    if not str(confirmation or ""):
        raise ValueError("יש להזין אימות סיסמה.")
    if not 8 <= len(password) <= 128 or password != password.strip():
        raise ValueError("הסיסמה חייבת להכיל 8 עד 128 תווים ללא רווחים בתחילה או בסוף.")
    if any(not character.isprintable() for character in password):
        raise ValueError("הסיסמה מכילה תווים שאינם נתמכים.")
    if password != str(confirmation or ""):
        raise ValueError("אימות הסיסמה אינו תואם.")
    return password
