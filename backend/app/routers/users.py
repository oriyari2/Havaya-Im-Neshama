from __future__ import annotations

from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from backend.app.application.services import user_admin_service as service
from backend.app.core.auth import require_roles
from backend.app.schemas.user_admin import (
    PasswordResetRequest,
    ManagerUpdateRequest,
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserRole,
)


router = APIRouter(tags=["users"])
RequireManager = Depends(require_roles("manager"))


def _error(exc: Exception) -> NoReturn:
    if isinstance(exc, service.UserNotFoundError):
        raise HTTPException(404, "User not found") from exc
    if isinstance(exc, service.UserConflictError):
        raise HTTPException(409, str(exc)) from exc
    raise HTTPException(500, "Could not manage user") from exc


@router.get("/users", response_model=UserListResponse)
def list_users(
    search: str | None = None,
    role: UserRole | None = None,
    is_active: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    _current_user: dict = RequireManager,
) -> UserListResponse:
    try:
        items = service.list_users(search=search, role=role, is_active=is_active, limit=limit, offset=offset)
        return UserListResponse(items=items, count=len(items))
    except Exception as exc:
        _error(exc)


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(payload: UserCreateRequest, _current_user: dict = RequireManager) -> UserResponse:
    try:
        return UserResponse(**service.create_user(payload))
    except Exception as exc:
        _error(exc)


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, _current_user: dict = RequireManager) -> UserResponse:
    try:
        return UserResponse(**service.get_user(user_id))
    except Exception as exc:
        _error(exc)


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: UUID, payload: ManagerUpdateRequest, _current_user: dict = RequireManager) -> UserResponse:
    try:
        return UserResponse(**service.update_manager(user_id, payload))
    except Exception as exc:
        _error(exc)


@router.post("/users/{user_id}/activate", response_model=UserResponse)
def activate_user(user_id: UUID, current_user: dict = RequireManager) -> UserResponse:
    try:
        return UserResponse(**service.set_active(user_id, True, current_user))
    except Exception as exc:
        _error(exc)


@router.post("/users/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(user_id: UUID, current_user: dict = RequireManager) -> UserResponse:
    try:
        return UserResponse(**service.set_active(user_id, False, current_user))
    except Exception as exc:
        _error(exc)


@router.post("/users/{user_id}/reset-password", status_code=204)
def reset_password(user_id: UUID, payload: PasswordResetRequest, _current_user: dict = RequireManager) -> Response:
    try:
        service.reset_password(user_id, payload)
        return Response(status_code=204)
    except Exception as exc:
        _error(exc)
