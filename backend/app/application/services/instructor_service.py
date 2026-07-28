from __future__ import annotations
from uuid import UUID
from psycopg import IntegrityError
from psycopg.rows import dict_row
from backend.app.db.connection import get_connection
from backend.app.infrastructure.repositories import instructor_repository as repo

class InstructorNotFoundError(Exception):pass
class InstructorAccessDeniedError(Exception):pass
class InstructorConflictError(Exception):pass
class InstructorDeleteConflictError(Exception):pass

def list_instructors(*,search,city,is_active,order_by,limit,offset,current_user):
    if current_user["role"]!="manager":raise InstructorAccessDeniedError
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:return repo.list_instructors(cur,search=search,city=city,is_active=is_active,order_by=order_by,limit=limit,offset=offset)
def _require(cur,instructor_id):
    item=repo.get_instructor(cur,instructor_id)
    if not item:raise InstructorNotFoundError
    return item
def get_instructor(instructor_id,current_user):
    if current_user["role"]!="manager":raise InstructorAccessDeniedError
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:return _require(cur,instructor_id)
def get_my_profile(current_user):
    if current_user["role"]!="instructor" or not current_user.get("instructor_id"):raise InstructorAccessDeniedError
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:return _require(cur,UUID(str(current_user["instructor_id"])))
def _ensure_email(cur,email,exclude_id=None):
    if email and repo.get_by_email(cur,email,exclude_id):raise InstructorConflictError("Instructor email already exists")
def create_instructor(payload):
    with get_connection() as conn:
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                data=payload.model_dump(); _ensure_email(cur,data.get("email")); item=repo.create_instructor(cur,data)
            conn.commit(); return item
        except Exception: conn.rollback(); raise
def update_instructor(instructor_id,payload):
    with get_connection() as conn:
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                _require(cur,instructor_id); data=payload.model_dump(exclude_unset=True)
                if "email" in data:_ensure_email(cur,data["email"],instructor_id)
                item=repo.update_instructor(cur,instructor_id,data) if data else _require(cur,instructor_id)
            conn.commit(); return item
        except Exception:conn.rollback();raise
def delete_instructor(instructor_id):
    with get_connection() as conn:
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                if not repo.lock_instructor(cur,instructor_id):raise InstructorNotFoundError
                dependencies=repo.instructor_delete_dependencies(cur,instructor_id)
                if any(dependencies.values()):raise InstructorDeleteConflictError("לא ניתן למחוק את המדריך משום שקיימים עבורו שיבוצים, רשומות היסטוריות או חשבון משתמש מקושר.")
                if not repo.delete_instructor(cur,instructor_id):raise InstructorNotFoundError
            conn.commit()
        except IntegrityError as exc:
            conn.rollback();raise InstructorDeleteConflictError("לא ניתן למחוק את המדריך משום שקיימות עבורו רשומות מקושרות.") from exc
        except Exception:conn.rollback();raise
