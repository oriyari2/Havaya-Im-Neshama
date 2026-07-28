from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import secrets

import jwt
from jwt import InvalidTokenError as JwtInvalidTokenError

from backend.app.core.environment import load_backend_env

HASH_ALGORITHM = "pbkdf2_sha256"
HASH_ITERATIONS = 260_000
TOKEN_ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 120
LOCAL_DEVELOPMENT_SECRET = "local-dev-auth-secret-change-me"


def get_app_env() -> str:
    load_backend_env()
    return os.getenv("APP_ENV", "development").strip().lower()


def hash_password(password: str, salt: str | None = None) -> str:
    password_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        password_salt.encode("utf-8"),
        HASH_ITERATIONS,
    )
    return (
        f"{HASH_ALGORITHM}${HASH_ITERATIONS}${password_salt}$"
        f"{base64.urlsafe_b64encode(digest).decode('ascii')}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt, expected_digest = password_hash.split("$", 3)
        if algorithm != HASH_ALGORITHM:
            return False
        iterations = int(iterations_text)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        actual_digest = base64.urlsafe_b64encode(digest).decode("ascii")
        return hmac.compare_digest(actual_digest, expected_digest)
    except (ValueError, TypeError):
        return False


def get_auth_secret() -> str:
    load_backend_env()
    secret = os.getenv("AUTH_SECRET_KEY")
    if secret and secret != "change-me-in-local-env":
        return secret
    if get_app_env() in {"development", "local", "test"}:
        return LOCAL_DEVELOPMENT_SECRET
    raise RuntimeError("AUTH_SECRET_KEY must be set outside local development")


def create_access_token(subject: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, get_auth_secret(), algorithm=TOKEN_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, get_auth_secret(), algorithms=[TOKEN_ALGORITHM])
    except JwtInvalidTokenError as exc:
        raise ValueError("Invalid token") from exc
