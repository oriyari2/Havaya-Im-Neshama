from __future__ import annotations

import re
from collections.abc import Mapping


EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def email_errors(value: object, *, required: bool) -> str | None:
    email = str(value or "").strip().lower()
    if not email:
        return "נא להזין כתובת דוא״ל." if required else None
    if len(email) > 254 or not EMAIL.match(email):
        return "כתובת הדוא״ל אינה תקינה."
    return None


def password_errors(values: Mapping[str, object]) -> dict[str, str]:
    password = str(values.get("password") or "")
    confirmation = str(values.get("password_confirmation") or "")
    errors: dict[str, str] = {}
    if not password:
        errors["password"] = "נא להזין סיסמה."
    elif not 8 <= len(password) <= 128 or password != password.strip():
        errors["password"] = "הסיסמה חייבת להכיל 8 עד 128 תווים ללא רווחים בתחילה או בסוף."
    elif any(not character.isprintable() for character in password):
        errors["password"] = "הסיסמה מכילה תווים שאינם נתמכים."
    if not confirmation:
        errors["password_confirmation"] = "נא להזין אימות סיסמה."
    elif password and password != confirmation:
        errors["password_confirmation"] = "הסיסמאות אינן תואמות."
    return errors


def customer_errors(values: Mapping[str, object], editing: bool) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not str(values.get("name") or "").strip():
        errors["name"] = "נא להזין שם."
    if not editing:
        email_error = email_errors(values.get("email"), required=True)
        if email_error:
            errors["email"] = email_error
        errors.update(password_errors(values))
        contact_name = str(values.get("contact_name") or "").strip()
        contact_phone = str(values.get("contact_phone") or "").strip()
        if bool(contact_name) != bool(contact_phone):
            missing = "contact_phone" if contact_name else "contact_name"
            errors[missing] = "יש להזין גם שם וגם טלפון לאיש הקשר, או להשאיר את שניהם ריקים."
    else:
        if not str(values.get("contact_name") or "").strip():
            errors["contact_name"] = "נא להזין שם איש קשר."
        if not str(values.get("contact_phone") or "").strip():
            errors["contact_phone"] = "נא להזין טלפון איש קשר."
    return errors


def instructor_errors(values: Mapping[str, object], editing: bool) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not str(values.get("full_name") or "").strip():
        errors["full_name"] = "נא להזין שם."
    email_error = email_errors(values.get("email"), required=not editing)
    if email_error:
        errors["email"] = email_error
    if not editing:
        errors.update(password_errors(values))
    return errors


def manager_errors(values: Mapping[str, object], editing: bool) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not str(values.get("manager_name") or "").strip():
        errors["manager_name"] = "נא להזין שם."
    if not editing:
        email_error = email_errors(values.get("email"), required=True)
        if email_error:
            errors["email"] = email_error
        errors.update(password_errors(values))
    return errors


def safe_backend_conflict(exc: Exception, default: str) -> str:
    """Translate known API conflicts without exposing raw server payloads."""
    message = str(exc).lower()
    if "last active manager" in message:
        return "לא ניתן להשבית את המנהל הפעיל האחרון."
    if "email" in message or "דוא" in message:
        return "כתובת הדוא״ל כבר קיימת במערכת."
    if any(token in message for token in ("linked", "dependenc", "מקושר", "תלו")):
        return "לא ניתן לבצע את הפעולה בגלל נתונים מקושרים."
    return default
