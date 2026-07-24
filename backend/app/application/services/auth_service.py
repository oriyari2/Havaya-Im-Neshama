from __future__ import annotations

from uuid import UUID

from psycopg.rows import dict_row

from backend.app.core.security import create_access_token, decode_access_token, verify_password
from backend.app.db.connection import get_connection
from backend.app.infrastructure.repositories import user_repository


class InvalidCredentialsError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


def _public_user(user: dict) -> dict:
    return {key: value for key, value in user.items() if key != "password_hash"}


def login(email: str, password: str) -> tuple[str, dict]:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            user = user_repository.get_user_by_email(cur, email)

    if user is None or not user["is_active"] or not verify_password(password, user["password_hash"]):
        raise InvalidCredentialsError

    token = create_access_token(str(user["id"]), user["role"])
    return token, _public_user(user)


def get_user_from_token(token: str) -> dict:
    try:
        payload = decode_access_token(token)
        user_id = UUID(str(payload["sub"]))
    except Exception as exc:
        raise InvalidTokenError from exc

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            user = user_repository.get_user_by_id(cur, user_id)

    if user is None or not user["is_active"]:
        raise InvalidTokenError
    return _public_user(user)
