from __future__ import annotations

from datetime import UTC, datetime
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


class BookingValidationError(Exception):
    pass


def _can_read_booking(current_user: dict, booking: dict) -> bool:
    if current_user["role"] == "manager":
        return True
    if current_user["role"] == "customer":
        return current_user.get("customer_id") == booking["customer_id"]
    return False


def _resolve_visibility_scope(
    current_user: dict,
    *,
    customer_id: UUID | None = None,
    instructor_id: UUID | None = None,
) -> tuple[str, UUID | None, UUID | None]:
    role = current_user["role"]

    if role == "customer":
        if customer_id is not None:
            raise BookingValidationError("customer_id filter is not allowed for customers")
        if instructor_id is not None:
            raise BookingValidationError("instructor_id filter is not allowed for customers")
        scope_customer_id = current_user.get("customer_id")
        if scope_customer_id is None:
            raise BookingAccessDeniedError
        return role, scope_customer_id, None

    if role == "instructor":
        if customer_id is not None:
            raise BookingValidationError("customer_id filter is not allowed for instructors")
        if instructor_id is not None:
            raise BookingValidationError("instructor_id filter is not allowed for instructors")
        scope_instructor_id = current_user.get("instructor_id")
        if scope_instructor_id is None:
            raise BookingAccessDeniedError
        return role, None, scope_instructor_id

    if role == "manager":
        return role, customer_id, instructor_id

    raise BookingAccessDeniedError


def list_bookings(
    current_user: dict,
    status: str | None,
    limit: int,
    offset: int,
    *,
    customer_id: UUID | None = None,
    activity_id: UUID | None = None,
    instructor_id: UUID | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> list[dict]:
    role, scope_customer_id, scope_instructor_id = _resolve_visibility_scope(
        current_user,
        customer_id=customer_id,
        instructor_id=instructor_id,
    )

    if from_date is not None and to_date is not None and from_date > to_date:
        raise BookingValidationError("from_date must be before or equal to to_date")

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            kwargs: dict = {
                "role": role,
                "customer_id": scope_customer_id,
                "instructor_id": scope_instructor_id,
                "status": status,
                "limit": limit,
                "offset": offset,
            }
            if role == "manager":
                if customer_id is not None:
                    kwargs["customer_filter_id"] = customer_id
                if instructor_id is not None:
                    kwargs["instructor_filter_id"] = instructor_id
            if activity_id is not None:
                kwargs["activity_id"] = activity_id
            if from_date is not None:
                kwargs["from_date"] = from_date
            if to_date is not None:
                kwargs["to_date"] = to_date
            return projection_repo.list_bookings(cur, **kwargs)


def get_dashboard_summary(current_user: dict) -> dict:
    role, scope_customer_id, scope_instructor_id = _resolve_visibility_scope(current_user)
    now = datetime.now(UTC)

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            return projection_repo.get_dashboard_summary(
                cur,
                role=role,
                customer_id=scope_customer_id,
                instructor_id=scope_instructor_id,
                now=now,
            )


def get_my_bookings(current_user: dict, limit: int, offset: int) -> list[dict]:
    if current_user.get("role") != "customer":
        raise BookingAccessDeniedError
    return list_bookings(current_user, None, limit, offset)


def get_open_events(current_user: dict) -> list[dict]:
    role, scope_customer_id, scope_instructor_id = _resolve_visibility_scope(current_user)
    if role == "customer":
        raise BookingAccessDeniedError
    now = datetime.now(UTC)

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            return projection_repo.get_open_events(
                cur,
                role=role,
                customer_id=scope_customer_id,
                instructor_id=scope_instructor_id,
                now=now,
            )


def get_booking(booking_id: UUID, current_user: dict) -> dict:
    customer_id = None
    instructor_id = None
    role = current_user["role"]

    if role == "customer":
        customer_id = current_user.get("customer_id")
        if customer_id is None:
            raise BookingAccessDeniedError
    elif role == "instructor":
        instructor_id = current_user.get("instructor_id")
        if instructor_id is None:
            raise BookingAccessDeniedError
    elif role != "manager":
        raise BookingAccessDeniedError

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            booking = projection_repo.get_booking(
                cur,
                booking_id,
                role=role,
                customer_id=customer_id,
                instructor_id=instructor_id,
            )
            if booking is None:
                if projection_repo.booking_exists(cur, booking_id):
                    raise BookingAccessDeniedError
                raise BookingNotFoundError
            if role == "customer" and not _can_read_booking(current_user, booking):
                raise BookingAccessDeniedError
            return booking


def get_history(booking_id: UUID, current_user: dict) -> list[dict]:
    if current_user.get("role") != "manager":
        raise BookingAccessDeniedError
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
