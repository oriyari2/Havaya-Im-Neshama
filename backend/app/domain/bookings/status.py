from __future__ import annotations

from enum import StrEnum


class BookingStatus(StrEnum):
    NEW = "NEW"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


TERMINAL_STATUSES = {BookingStatus.COMPLETED, BookingStatus.CANCELLED}


def parse_booking_status(value: str) -> BookingStatus:
    try:
        return BookingStatus(value)
    except ValueError as exc:
        raise ValueError("Invalid booking status") from exc


def validate_status_transition(current_status: BookingStatus, new_status: BookingStatus) -> None:
    if current_status == new_status:
        return
    if current_status in TERMINAL_STATUSES:
        raise ValueError("Completed or cancelled bookings cannot move to another status")
