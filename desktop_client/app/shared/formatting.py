from __future__ import annotations

from datetime import datetime


def display_value(value: object) -> str:
    return "—" if value in (None, "") else str(value)


def format_local_datetime(value: str | None) -> str:
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone().strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return value
