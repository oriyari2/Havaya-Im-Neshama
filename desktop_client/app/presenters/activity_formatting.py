from __future__ import annotations

from datetime import datetime


def _display(value: object) -> str:
    return "—" if value in (None, "") else str(value)


def _date(value: str | None) -> str:
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone().strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return value


def activity_row(item: dict) -> dict[str, object]:
    return {
        "id": str(item["id"]),
        "name": _display(item.get("name")),
        "target_audience": _display(item.get("target_audience")),
        "duration_minutes": _display(item.get("duration_minutes")),
        "recommended_capacity": _display(item.get("recommended_capacity")),
        "season": _display(item.get("season")),
        "pricing_rule": _display(item.get("pricing_rule")),
        "is_active": bool(item.get("is_active")),
    }


def activity_details(item: dict) -> list[tuple[str, str]]:
    fields = (
        ("שם", "name"), ("תיאור", "description"), ("קהל יעד", "target_audience"),
        ("משך בדקות", "duration_minutes"), ("קיבולת מומלצת", "recommended_capacity"),
        ("כלל תמחור", "pricing_rule"), ("ציוד נדרש", "required_equipment"),
        ("הערות הכנה", "preparation_notes"), ("עונה", "season"), ("תגיות", "tags"),
    )
    rows = [(label, _display(item.get(key))) for label, key in fields]
    rows.extend((("מצב", "פעילה" if item.get("is_active") else "לא פעילה"), ("נוצרה", _date(item.get("created_at"))), ("עודכנה", _date(item.get("updated_at")))))
    return rows
