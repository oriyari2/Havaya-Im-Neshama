from __future__ import annotations

from uuid import UUID

from psycopg import IntegrityError
from psycopg.rows import dict_row

from backend.app.core.security import hash_password
from backend.app.db.connection import get_connection
from backend.app.infrastructure.repositories import customer_repository
from backend.app.infrastructure.repositories import instructor_repository
from backend.app.infrastructure.repositories import user_repository as repo
from backend.app.schemas.user_admin import PasswordResetRequest, UserCreateRequest, UserEmailUpdateRequest


class UserNotFoundError(Exception):
    pass


class UserConflictError(Exception):
    pass


def list_users(*, search: str | None, role: str | None, is_active: bool | None, limit: int, offset: int) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            return repo.list_users(cur, search=search, role=role, is_active=is_active, limit=limit, offset=offset)


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
                        "address": None,
                        "phone": None,
                        "email": payload.email,
                        "notes": None,
                        "is_active": True,
                    })
                    customer_id = customer["id"]
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
                        "notes": None,
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


def set_active(user_id: UUID, active: bool, current_user: dict) -> dict:
    if not active and UUID(str(current_user["id"])) == user_id:
        raise UserConflictError("A manager cannot deactivate their own account")
    with get_connection() as conn:
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                existing = repo.get_user_by_id(cur, user_id)
                if existing is None:
                    raise UserNotFoundError
                if bool(existing["is_active"]) == active:
                    raise UserConflictError("User already has the requested status")
                if active:
                    if existing["role"] == "customer":
                        profile = repo.get_customer_profile(cur, existing["customer_id"])
                        if not profile or not profile["is_active"]:
                            raise UserConflictError("Linked Customer profile is inactive")
                    elif existing["role"] == "instructor":
                        profile = repo.get_instructor_profile(cur, existing["instructor_id"])
                        if not profile or not profile["is_active"]:
                            raise UserConflictError("Linked Instructor profile is inactive")
                repo.set_user_active(cur, user_id, active)
                result = repo.get_safe_user(cur, user_id)
            conn.commit()
            return result
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
