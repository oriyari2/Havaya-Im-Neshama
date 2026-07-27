from __future__ import annotations

from uuid import UUID

from psycopg.rows import dict_row

from backend.app.db.connection import get_connection
from backend.app.domain.bookings.aggregate import BookingAggregate
from backend.app.infrastructure.repositories import booking_event_repository as events_repo
from backend.app.infrastructure.repositories import booking_projection_repository as projection_repo


class BookingAccessDeniedError(Exception):
    pass


class BookingNotFoundError(Exception):
    pass


def _can_read_booking(current_user: dict, booking: dict) -> bool:
    if current_user["role"] == "manager":
        return True
    if current_user["role"] == "customer":
        return current_user.get("customer_id") == booking["customer_id"]
    return False


def list_bookings(current_user: dict, status: str | None, limit: int, offset: int) -> list[dict]:
    customer_id = None
    if current_user["role"] == "customer":
        customer_id = current_user.get("customer_id")
        if customer_id is None:
            raise BookingAccessDeniedError
    elif current_user["role"] != "manager":
        raise BookingAccessDeniedError

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            return projection_repo.list_bookings(cur, customer_id, status, limit, offset)


def get_booking(booking_id: UUID, current_user: dict) -> dict:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            booking = projection_repo.get_booking(cur, booking_id)
            if booking is None:
                raise BookingNotFoundError
            if not _can_read_booking(current_user, booking):
                raise BookingAccessDeniedError
            return booking


def get_history(booking_id: UUID, current_user: dict) -> list[dict]:
    get_booking(booking_id, current_user)
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            events = events_repo.list_events(cur, booking_id)
            if not events:
                raise BookingNotFoundError
            return events


def replay_booking(booking_id: UUID, current_user: dict) -> dict:
    if current_user["role"] != "manager":
        raise BookingAccessDeniedError
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            events = events_repo.list_events(cur, booking_id)
            if not events:
                raise BookingNotFoundError
            return BookingAggregate.replay(booking_id, events).to_projection()
