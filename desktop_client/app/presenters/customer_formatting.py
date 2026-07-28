from __future__ import annotations

from datetime import datetime


def _date(value: str | None) -> str:
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone().strftime("%d/%m/%Y %H:%M")
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
    }


def customer_details(item: dict) -> list[tuple[str, str]]:
    fields = (
        ("שם", "name"), ("סוג לקוח", "customer_type"), ("עיר", "city"),
        ("כתובת", "address"), ("טלפון", "phone"), ("דוא״ל", "email"),
        ("הערות", "notes"),
    )
    rows = [(label, str(item.get(key) or "—")) for label, key in fields]
    rows.extend((
        ("מצב", "פעיל" if item.get("is_active") else "לא פעיל"),
        ("נוצר", _date(item.get("created_at"))),
        ("עודכן", _date(item.get("updated_at"))),
    ))
    return rows


def contact_row(item: dict) -> dict[str, str | bool]:
    return {
        "id": str(item["id"]), "full_name": item.get("full_name") or "—",
        "role_title": item.get("role_title") or "—", "phone": item.get("phone") or "—",
        "email": item.get("email") or "—", "is_primary": bool(item.get("is_primary")),
        "is_active": bool(item.get("is_active")),
    }
