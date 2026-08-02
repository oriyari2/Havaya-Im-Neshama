from __future__ import annotations

from uuid import UUID

from psycopg import IntegrityError
from psycopg.rows import dict_row

from backend.app.core.security import hash_password
from backend.app.db.connection import get_connection
from backend.app.infrastructure.repositories import customer_repository
from backend.app.infrastructure.repositories import instructor_repository
from backend.app.infrastructure.repositories import user_repository as repo
from backend.app.schemas.user_admin import ManagerUpdateRequest, PasswordResetRequest, UserCreateRequest, UserEmailUpdateRequest


class UserNotFoundError(Exception):
    pass


class UserConflictError(Exception):
    pass


def list_users(*, search: str | None, role: str | None, is_active: bool | None, order_by: str = "email", limit: int, offset: int) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            return repo.list_users(cur, search=search, role=role, is_active=is_active, order_by=order_by, limit=limit, offset=offset)


def get_user(user_id: UUID) -> dict:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            user = repo.get_safe_user(cur, user_id)
    if user is None:
        raise UserNotFoundError
    return user


def _translate_integrity_error(exc: IntegrityError) -> UserConflictError:
    constraint = str(getattr(getattr(exc, "diag", None), "constraint_name", "") or "")
    if "customer" in constraint:
        return UserConflictError("Customer profile is already linked")
    if "instructor" in constraint:
        return UserConflictError("Instructor profile is already linked")
    return UserConflictError("Email is already registered")


def create_user(payload: UserCreateRequest) -> dict:
    with get_connection() as conn:
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                customer_id = None
                instructor_id = None
                if payload.role == "customer":
                    customer = customer_repository.create_customer(cur, {
                        "name": payload.customer_name,
                        "customer_type": payload.customer_type,
                        "city": payload.customer_city,
                        "address": payload.customer_address,
                        "phone": payload.customer_phone,
                        "email": payload.email,
                        "notes": payload.customer_notes,
                        "is_active": True,
                    })
                    customer_id = customer["id"]
                    if payload.contact_name and payload.contact_phone:
                        customer_repository.create_contact(cur, customer_id, {
                            "full_name": payload.contact_name,
                            "role_title": None,
                            "phone": payload.contact_phone,
                            "email": None,
                            "is_primary": True,
                            "notes": None,
                            "is_active": True,
                        })
                elif payload.role == "instructor":
                    if instructor_repository.get_by_email(cur, payload.email):
                        raise UserConflictError("Instructor email already exists")
                    instructor = instructor_repository.create_instructor(cur, {
                        "full_name": payload.instructor_name,
                        "phone": payload.instructor_phone,
                        "email": payload.email,
                        "city": payload.instructor_city,
                        "notes": payload.instructor_notes,
                        "is_active": True,
                    })
                    instructor_id = instructor["id"]
                created = repo.create_user(
                    cur,
                    email=payload.email,
                    password_hash=hash_password(payload.password),
                    role=payload.role,
                    display_name=payload.manager_name if payload.role == "manager" else None,
                    customer_id=customer_id,
                    instructor_id=instructor_id,
                )
                result = repo.get_safe_user(cur, created["id"])
            conn.commit()
            return result
        except IntegrityError as exc:
            conn.rollback()
            raise _translate_integrity_error(exc) from exc
        except Exception:
            conn.rollback()
            raise


def update_email(user_id: UUID, payload: UserEmailUpdateRequest) -> dict:
    with get_connection() as conn:
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                existing = repo.get_user_by_id(cur, user_id)
                if existing is None:
                    raise UserNotFoundError
                if existing["role"] == "customer":
                    customer_repository.update_customer(cur, existing["customer_id"], {"email": payload.email})
                elif existing["role"] == "instructor":
                    if instructor_repository.get_by_email(cur, payload.email, existing["instructor_id"]):
                        raise UserConflictError("Instructor email already exists")
                    instructor_repository.update_instructor(cur, existing["instructor_id"], {"email": payload.email})
                repo.update_user_email(cur, user_id, payload.email)
                result = repo.get_safe_user(cur, user_id)
            conn.commit()
            return result
        except IntegrityError as exc:
            conn.rollback()
            raise _translate_integrity_error(exc) from exc
        except Exception:
            conn.rollback()
            raise


def update_manager(user_id: UUID, payload: ManagerUpdateRequest) -> dict:
    with get_connection() as conn:
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                existing = repo.get_user_by_id(cur, user_id)
                if existing is None or existing["role"] != "manager":
                    raise UserNotFoundError
                if not repo.update_manager_name(cur, user_id, payload.manager_name):
                    raise UserNotFoundError
                result = repo.get_safe_user(cur, user_id)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise


def set_active(user_id: UUID, active: bool, current_user: dict) -> dict:
    if not active and UUID(str(current_user["id"])) == user_id:
        raise UserConflictError("A manager cannot deactivate their own account")
    with get_connection() as conn:
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                candidate = repo.get_user_by_id(cur, user_id)
                if candidate is None:
                    raise UserNotFoundError
                active_managers = repo.lock_active_managers(cur) if not active and candidate["role"] == "manager" else None
                existing = repo.lock_user(cur, user_id)
                if existing is None:
                    raise UserNotFoundError
                if bool(existing["is_active"]) == active:
                    raise UserConflictError("User already has the requested status")
                if not active and existing["role"] == "manager":
                    if len(active_managers or ()) <= 1:
                        raise UserConflictError("The last active manager cannot be deactivated")
                if existing["role"] == "customer":
                    profile = customer_repository.lock_customer(cur, existing["customer_id"])
                    if not profile or customer_repository.set_customer_active(cur, existing["customer_id"], active) is None:
                        raise UserConflictError("Linked Customer profile was not found")
                elif existing["role"] == "instructor":
                    profile = instructor_repository.lock_instructor(cur, existing["instructor_id"])
                    if not profile or instructor_repository.set_instructor_active(cur, existing["instructor_id"], active) is None:
                        raise UserConflictError("Linked Instructor profile was not found")
                if not repo.set_user_active(cur, user_id, active):
                    raise UserNotFoundError
                result = repo.get_safe_user(cur, user_id)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise


def set_profile_active(role: str, profile_id: UUID, active: bool) -> dict:
    """Atomically synchronize a Customer/Instructor profile and its login account."""
    if role not in {"customer", "instructor"}:
        raise ValueError("Unsupported account profile role")
    profile_repo = customer_repository if role == "customer" else instructor_repository
    lock_profile = profile_repo.lock_customer if role == "customer" else profile_repo.lock_instructor
    set_profile = profile_repo.set_customer_active if role == "customer" else profile_repo.set_instructor_active
    with get_connection() as conn:
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                user = repo.lock_user_for_profile(cur, role=role, profile_id=profile_id)
                if user is None:
                    raise UserConflictError("Linked login account was not found")
                profile = lock_profile(cur, profile_id)
                if profile is None:
                    raise UserNotFoundError
                if bool(profile["is_active"]) == active and bool(user["is_active"]) == active:
                    raise UserConflictError("Profile already has the requested status")
                updated = set_profile(cur, profile_id, active)
                if updated is None or not repo.set_user_active(cur, user["id"], active):
                    raise UserNotFoundError
            conn.commit()
            return updated
        except Exception:
            conn.rollback()
            raise


def reset_password(user_id: UUID, payload: PasswordResetRequest) -> None:
    with get_connection() as conn:
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                if repo.get_user_by_id(cur, user_id) is None:
                    raise UserNotFoundError
                repo.set_password_hash(cur, user_id, hash_password(payload.new_password))
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def reset_profile_password(role: str, profile_id: UUID, payload: PasswordResetRequest) -> None:
    if role not in {"customer", "instructor"}:
        raise ValueError("Unsupported account profile role")
    with get_connection() as conn:
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                user_id = repo.get_user_id_for_profile(cur, role=role, profile_id=profile_id)
                if user_id is None:
                    raise UserNotFoundError
                if not repo.set_password_hash(cur, user_id, hash_password(payload.new_password)):
                    raise UserNotFoundError
            conn.commit()
        except Exception:
            conn.rollback()
            raise
