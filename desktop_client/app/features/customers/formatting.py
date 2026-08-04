from __future__ import annotations

from datetime import datetime


def _date(value: str | None) -> str:
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone().strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return value


def _date_only(value: str | None) -> str:
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone().strftime("%d/%m/%Y")
    except ValueError:
        return value


def customer_row(item: dict) -> dict[str, str | bool]:
    return {
        "id": str(item["id"]),
        "name": item.get("name") or "—",
        "customer_type": item.get("customer_type") or "—",
        "city": item.get("city") or "—",
        "phone": item.get("phone") or "—",
        "email": item.get("email") or "—",
        "is_active": bool(item.get("is_active")),
        # The list API already returns created_at. Preserve it in the row
        # model so the Customers table can render the join date instead of a
        # permanent em dash.
        "join_date": _date_only(item.get("created_at")),
    }


def customer_details(item: dict) -> list[tuple[str, str]]:
    fields = (
        ("שם", "name"), ("סוג לקוח", "customer_type"), ("עיר", "city"),
        ("כתובת", "address"), ("טלפון", "phone"), ("דוא״ל", "email"),
        ("הערות", "notes"),
    )
    rows = [(label, str(item.get(key) or "—")) for label, key in fields]
    contacts = list(item.get("contacts", []))
    contact = next(
        (entry for entry in contacts if entry.get("is_primary") and entry.get("is_active")),
        next((entry for entry in contacts if entry.get("is_active")), None),
    )
    rows.insert(6, ("איש קשר", str(contact.get("full_name") or "—") if contact else "—"))
    rows.insert(7, ("טלפון איש קשר", str(contact.get("phone") or "—") if contact else "—"))
    rows.extend((
        ("מצב", "פעיל" if item.get("is_active") else "לא פעיל"),
        ("נוצר", _date(item.get("created_at"))),
        ("עודכן", _date(item.get("updated_at"))),
    ))
    return rows
