from __future__ import annotations

from datetime import datetime
from typing import Any


STATUS_LABELS = {
    "NEW": "חדש / ממתין",
    "CONFIRMED": "מאושר",
    "COMPLETED": "הושלם",
    "CANCELLED": "בוטל",
}

EVENT_LABELS = {
    "BookingCreated": "הזמנה נוצרה",
    "BookingStatusChanged": "סטטוס השתנה",
    "BookingDateChanged": "מועד השתנה",
    "BookingPriceChanged": "מחיר השתנה",
    "BookingLocationChanged": "מיקום השתנה",
    "BookingParticipantCountChanged": "מספר משתתפים השתנה",
    "BookingNotesUpdated": "הערות עודכנו",
    "BookingInstructorAssigned": "מדריך שובץ",
    "BookingInstructorRemoved": "שיבוץ מדריך הוסר",
}


def format_datetime(value: str | None) -> str:
    if not value:
        return "—"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone().strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return value


def booking_row(item: dict[str, Any]) -> dict[str, str]:
    return {
        "id": str(item["id"]),
        "event_at": format_datetime(item.get("event_at")),
        "status": STATUS_LABELS.get(item.get("status", ""), item.get("status", "—")),
        "status_code": str(item.get("status") or ""),
        "city": item.get("city") or "—",
        "venue": item.get("venue") or "—",
        "participants": str(item.get("participant_count", "—")),
        "activity": item.get("activity_name") or "—",
        "customer": item.get("customer_name") or "—",
    }


def booking_details(item: dict[str, Any]) -> list[tuple[str, str]]:
    labels = [
        ("מזהה", "id"),
        ("לקוח", "customer_name"),
        ("פעילות", "activity_name"),
        ("מועד", "event_at"),
        ("סטטוס", "status"),
        ("עיר", "city"),
        ("מקום", "venue"),
        ("מספר משתתפים", "participant_count"),
        ("מחיר מוסכם", "agreed_price"),
        ("הערות", "notes"),
    ]
    details: list[tuple[str, str]] = []
    for label, key in labels:
        if key not in item:
            continue
        value = item.get(key)
        if key == "event_at":
            value = format_datetime(value)
        elif key == "status":
            value = STATUS_LABELS.get(str(value), value)
        details.append((label, "—" if value in (None, "") else str(value)))
    return details


def history_rows(events: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "event_type": EVENT_LABELS.get(event.get("event_type", ""), event.get("event_type", "—")),
            "summary": _event_summary(event),
            "occurred_at": format_datetime(event.get("occurred_at")),
            "actor": str(event.get("actor_user_id", "—")),
        }
        for event in events
    ]


def _event_summary(event: dict[str, Any]) -> str:
    data = event.get("event_data") or {}
    if event.get("event_type") == "BookingCreated":
        return "נוצרה הזמנה חדשה"
    if "previous" in data or "new" in data:
        return f"{data.get('previous', '—')} ← {data.get('new', '—')}"
    if event.get("event_type") == "BookingLocationChanged":
        previous = ", ".join(filter(None, (data.get("previous_city"), data.get("previous_venue")))) or "—"
        new = ", ".join(filter(None, (data.get("new_city"), data.get("new_venue")))) or "—"
        return f"{previous} ← {new}"
    if data.get("instructor_id"):
        return f"מדריך: {data['instructor_id']}"
    return "—"
