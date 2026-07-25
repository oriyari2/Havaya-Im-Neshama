from __future__ import annotations

from uuid import UUID

from psycopg.rows import dict_row

from backend.app.db.connection import get_connection
from backend.app.infrastructure.repositories import activity_repository as repo
from backend.app.infrastructure.repositories import activity_image_repository
from backend.app.schemas.activity import ActivityCreate, ActivityUpdate


class ActivityNotFoundError(Exception):
    pass


class ActivityAccessDeniedError(Exception):
    pass


def _require_activity(cur, activity_id: UUID) -> dict:
    activity = repo.get_activity(cur, activity_id)
    if activity is None:
        raise ActivityNotFoundError
    return activity


def _visible_is_active(current_user: dict, requested_is_active: bool | None) -> bool | None:
    if current_user["role"] == "manager":
        return requested_is_active
    return True


def _require_activity_visible(current_user: dict, activity: dict) -> None:
    if current_user["role"] == "manager":
        return
    if activity["is_active"]:
        return
    raise ActivityAccessDeniedError


def list_activities(
    search: str | None,
    target_audience: str | None,
    season: str | None,
    tag: str | None,
    is_active: bool | None,
    limit: int,
    offset: int,
    current_user: dict,
) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            return repo.list_activities(
                cur=cur,
                search=search,
                target_audience=target_audience,
                season=season,
                tag=tag,
                is_active=_visible_is_active(current_user, is_active),
                limit=limit,
                offset=offset,
            )


def get_activity_for_user(activity_id: UUID, current_user: dict) -> dict:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            activity = _require_activity(cur, activity_id)
            _require_activity_visible(current_user, activity)
            activity["images"] = activity_image_repository.list_activity_images(cur, activity_id)
            return activity


def create_activity(payload: ActivityCreate) -> dict:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            activity = repo.create_activity(cur, payload.model_dump())
            conn.commit()
    return activity


def update_activity(activity_id: UUID, payload: ActivityUpdate) -> dict:
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        with get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                return _require_activity(cur, activity_id)

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            _require_activity(cur, activity_id)
            activity = repo.update_activity(cur, activity_id, update_data)
            conn.commit()
    return activity


def soft_delete_activity(activity_id: UUID) -> dict:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            _require_activity(cur, activity_id)
            activity = repo.soft_delete_activity(cur, activity_id)
            conn.commit()
    return activity
