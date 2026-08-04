from datetime import UTC, datetime
from uuid import UUID

from psycopg.rows import dict_row

from backend.app.application.bookings.query_handlers import BookingAccessDeniedError, BookingNotFoundError
from backend.app.db.connection import get_connection
from backend.app.infrastructure.repositories import booking_assignment_repository as repo


def get_assignments(booking_id: UUID, current_user: dict) -> dict:
    if current_user["role"] != "manager":
        raise BookingAccessDeniedError
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            header = repo.get_header(cur, booking_id)
            if not header:
                raise BookingNotFoundError
            activities = repo.list_activities(cur, booking_id)
            rows = repo.list_active_assignments(cur, booking_id)
            requests = repo.list_pending_requests(cur, booking_id)

    by_activity = {item["booking_activity_id"]: [] for item in activities}
    for row in rows:
        by_activity[row["booking_activity_id"]].append(
            {key: row[key] for key in ("instructor_id", "instructor_name", "instructor_city", "assigned_at")}
        )
    requests_by_activity = {item["booking_activity_id"]: [] for item in activities}
    for request in requests:
        requests_by_activity.setdefault(request["booking_activity_id"], []).append(dict(request))

    return {
        "booking_id": header["booking_id"],
        "version": header["version"],
        "activities": [
            {
                **item,
                "assignments": by_activity[item["booking_activity_id"]],
                "requests": requests_by_activity.get(item["booking_activity_id"], []),
            }
            for item in activities
        ],
    }


def get_open_event_detail(booking_id: UUID, current_user: dict) -> dict:
    if current_user["role"] not in {"manager", "instructor"}:
        raise BookingAccessDeniedError
    instructor_id = None
    if current_user["role"] == "instructor":
        if not current_user.get("instructor_id"):
            raise BookingAccessDeniedError
        instructor_id = UUID(str(current_user["instructor_id"]))

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            header = repo.get_open_event_header(cur, booking_id, datetime.now(UTC))
            if not header:
                if repo.get_header(cur, booking_id):
                    raise BookingAccessDeniedError
                raise BookingNotFoundError
            activities = repo.list_activities(cur, booking_id)
            my_requests = repo.list_my_request_states(cur, booking_id, instructor_id) if instructor_id else {}

    activity_rows = []
    for item in activities:
        request = my_requests.get(item["booking_activity_id"])
        activity_rows.append(
            {
                key: item[key]
                for key in ("booking_activity_id", "activity_id", "activity_name", "assignment_required")
            }
            | {
                "my_request_id": request["request_id"] if request else None,
                "my_request_status": request["status"] if request else None,
            }
        )
    return {**header, "activities": activity_rows}
