from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from psycopg.rows import dict_row

from backend.app.application.bookings import command_handlers
from backend.app.application.bookings.commands import AssignInstructorCommand
from backend.app.application.bookings.query_handlers import BookingAccessDeniedError, BookingNotFoundError, BookingValidationError
from backend.app.db.connection import get_connection
from backend.app.infrastructure.repositories import booking_assignment_repository as repo


class AssignmentRequestConflictError(Exception):
    pass


def _require_instructor(current_user: dict) -> UUID:
    if current_user.get("role") != "instructor" or not current_user.get("instructor_id"):
        raise BookingAccessDeniedError
    return UUID(str(current_user["instructor_id"]))


def request_assignment(booking_id: UUID, booking_activity_id: UUID, current_user: dict) -> dict:
    instructor_id = _require_instructor(current_user)
    with get_connection() as conn:
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                if not repo.instructor_is_active(cur, instructor_id):
                    raise BookingAccessDeniedError
                if not repo.get_requestable_activity(cur, booking_id, booking_activity_id, datetime.now(UTC)):
                    if repo.get_header(cur, booking_id):
                        raise AssignmentRequestConflictError("האירוע כבר אינו פתוח לבקשות שיבוץ.")
                    raise BookingNotFoundError
                request = repo.upsert_assignment_request(cur, booking_activity_id, instructor_id)
            conn.commit()
            return request
        except Exception:
            conn.rollback()
            raise


def approve_request(booking_id: UUID, request_id: UUID, expected_version: int, current_user: dict) -> dict:
    if current_user.get("role") != "manager":
        raise BookingAccessDeniedError
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            request = repo.get_request_for_manager(cur, booking_id, request_id)
    if not request:
        raise BookingNotFoundError
    if request["status"] != "PENDING":
        raise AssignmentRequestConflictError("בקשת השיבוץ כבר טופלה.")
    if int(request["version"]) != int(expected_version):
        raise command_handlers.BookingConcurrencyError

    try:
        booking = command_handlers.assign_instructor(
            AssignInstructorCommand(
                booking_id=booking_id,
                booking_activity_id=request["booking_activity_id"],
                instructor_id=request["instructor_id"],
                expected_version=expected_version,
                actor_user_id=current_user["id"],
            )
        )
    except ValueError as exc:
        raise AssignmentRequestConflictError(str(exc)) from exc

    with get_connection() as conn:
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                repo.resolve_approved_request(
                    cur,
                    request["booking_activity_id"],
                    request["instructor_id"],
                    current_user["id"],
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return booking


def resolve_after_assignment(booking_activity_id: UUID, instructor_id: UUID, current_user: dict) -> None:
    if current_user.get("role") != "manager":
        return
    with get_connection() as conn:
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                repo.resolve_approved_request(cur, booking_activity_id, instructor_id, current_user["id"])
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def reject_request(booking_id: UUID, request_id: UUID, current_user: dict) -> dict:
    if current_user.get("role") != "manager":
        raise BookingAccessDeniedError
    with get_connection() as conn:
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                request = repo.reject_request(cur, booking_id, request_id, current_user["id"])
                if not request:
                    existing = repo.get_request_for_manager(cur, booking_id, request_id)
                    if existing:
                        raise AssignmentRequestConflictError("בקשת השיבוץ כבר טופלה.")
                    raise BookingNotFoundError
            conn.commit()
            return request
        except Exception:
            conn.rollback()
            raise
