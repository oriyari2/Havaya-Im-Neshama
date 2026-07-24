from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.application.services import auth_service


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return auth_service.get_user_from_token(credentials.credentials)
    except auth_service.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Not authenticated") from exc


def require_roles(*roles: str) -> Callable:
    def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        return current_user

    return dependency
