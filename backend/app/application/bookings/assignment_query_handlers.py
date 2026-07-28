from datetime import UTC,datetime
from uuid import UUID
from psycopg.rows import dict_row
from backend.app.db.connection import get_connection
from backend.app.infrastructure.repositories import booking_assignment_repository as repo
from backend.app.application.bookings.query_handlers import BookingAccessDeniedError,BookingNotFoundError

def get_assignments(booking_id:UUID,current_user:dict)->dict:
    if current_user["role"]!="manager":raise BookingAccessDeniedError
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            header=repo.get_header(cur,booking_id)
            if not header:raise BookingNotFoundError
            activities=repo.list_activities(cur,booking_id);rows=repo.list_active_assignments(cur,booking_id)
    by_activity={x["booking_activity_id"]:[] for x in activities}
    for row in rows:by_activity[row["booking_activity_id"]].append({k:row[k] for k in ("instructor_id","instructor_name","instructor_city","assigned_at")})
    return {"booking_id":header["booking_id"],"version":header["version"],"activities":[{**x,"assignments":by_activity[x["booking_activity_id"]]} for x in activities]}
def get_open_event_detail(booking_id:UUID,current_user:dict)->dict:
    if current_user["role"] not in {"manager","instructor"}:raise BookingAccessDeniedError
    if current_user["role"]=="instructor" and not current_user.get("instructor_id"):raise BookingAccessDeniedError
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            header=repo.get_open_event_header(cur,booking_id,datetime.now(UTC))
            if not header:
                if repo.get_header(cur,booking_id):raise BookingAccessDeniedError
                raise BookingNotFoundError
            activities=repo.list_activities(cur,booking_id)
    return {**header,"activities":[{k:x[k] for k in ("booking_activity_id","activity_id","activity_name","assignment_required")} for x in activities]}
