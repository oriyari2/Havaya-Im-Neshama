from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.app.application.services import auth_service
from backend.app.core.auth import get_current_user
from backend.app.schemas.auth import LoginRequest, LoginResponse, UserResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    try:
        token, user = auth_service.login(payload.email, payload.password)
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail="Invalid credentials") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not login") from exc

    return LoginResponse(access_token=token, user=UserResponse(**user))


@router.get("/me", response_model=UserResponse)
def me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    return UserResponse(**current_user)
