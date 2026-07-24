from __future__ import annotations

from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.application.services import activity_service
from backend.app.core.auth import get_current_user, require_roles
from backend.app.schemas.activity import (
    ActivityCreate,
    ActivityListResponse,
    ActivityResponse,
    ActivityUpdate,
)


router = APIRouter(tags=["activities"])
RequireManager = Depends(require_roles("manager"))


def _raise_not_found(exc: Exception) -> NoReturn:
    if isinstance(exc, activity_service.ActivityNotFoundError):
        raise HTTPException(status_code=404, detail="Activity not found") from exc
    raise exc


def _raise_access_denied(exc: Exception) -> NoReturn:
    if isinstance(exc, activity_service.ActivityAccessDeniedError):
        raise HTTPException(status_code=403, detail="Not authorized") from exc
    raise exc


@router.get("/activities", response_model=ActivityListResponse)
def list_activities(
    search: str | None = None,
    target_audience: str | None = None,
    season: str | None = None,
    tag: str | None = None,
    is_active: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    current_user: dict = Depends(get_current_user),
) -> ActivityListResponse:
    try:
        activities = activity_service.list_activities(
            search=search,
            target_audience=target_audience,
            season=season,
            tag=tag,
            is_active=is_active,
            limit=limit,
            offset=offset,
            current_user=current_user,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not list activities") from exc

    return ActivityListResponse(
        items=[ActivityResponse(**activity) for activity in activities],
        count=len(activities),
    )


@router.get("/activities/{activity_id}", response_model=ActivityResponse)
def get_activity(
    activity_id: UUID,
    current_user: dict = Depends(get_current_user),
) -> ActivityResponse:
    try:
        activity = activity_service.get_activity_for_user(activity_id, current_user)
    except activity_service.ActivityNotFoundError as exc:
        _raise_not_found(exc)
    except activity_service.ActivityAccessDeniedError as exc:
        _raise_access_denied(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not get activity") from exc

    return ActivityResponse(**activity)


@router.post("/activities", response_model=ActivityResponse, status_code=201)
def create_activity(payload: ActivityCreate, _current_user: dict = RequireManager) -> ActivityResponse:
    try:
        activity = activity_service.create_activity(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not create activity") from exc

    return ActivityResponse(**activity)


@router.put("/activities/{activity_id}", response_model=ActivityResponse)
def update_activity(
    activity_id: UUID,
    payload: ActivityUpdate,
    _current_user: dict = RequireManager,
) -> ActivityResponse:
    try:
        activity = activity_service.update_activity(activity_id, payload)
    except activity_service.ActivityNotFoundError as exc:
        _raise_not_found(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not update activity") from exc

    return ActivityResponse(**activity)


@router.delete("/activities/{activity_id}", response_model=ActivityResponse)
def delete_activity(activity_id: UUID, _current_user: dict = RequireManager) -> ActivityResponse:
    try:
        activity = activity_service.soft_delete_activity(activity_id)
    except activity_service.ActivityNotFoundError as exc:
        _raise_not_found(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not delete activity") from exc

    return ActivityResponse(**activity)
