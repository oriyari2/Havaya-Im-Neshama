from __future__ import annotations

from uuid import UUID

from psycopg.rows import dict_row

from backend.app.application.gateways.image_gateway import ImageGateway, ImageGatewayError
from backend.app.application.services.activity_service import (
    ActivityAccessDeniedError,
    ActivityNotFoundError,
    _require_activity,
    _require_activity_visible,
)
from backend.app.db.connection import get_connection
from backend.app.infrastructure.repositories import activity_image_repository as repo


ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


class ActivityImageNotFoundError(Exception):
    pass


class UnsupportedActivityImageTypeError(Exception):
    pass


class ActivityImageGatewayError(Exception):
    pass


def list_images_for_user(activity_id: UUID, current_user: dict) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            activity = _require_activity(cur, activity_id)
            _require_activity_visible(current_user, activity)
            return repo.list_activity_images(cur, activity_id)


def upload_activity_image(
    activity_id: UUID,
    file_bytes: bytes,
    filename: str | None,
    content_type: str | None,
    gateway: ImageGateway,
) -> dict:
    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise UnsupportedActivityImageTypeError

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            _require_activity(cur, activity_id)

    try:
        uploaded = gateway.upload_activity_image(file_bytes, filename, content_type)
    except ImageGatewayError as exc:
        raise ActivityImageGatewayError from exc

    try:
        with get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                image = repo.create_activity_image(
                    cur,
                    {
                        "activity_id": activity_id,
                        "public_id": uploaded.public_id,
                        "secure_url": uploaded.secure_url,
                        "original_filename": filename,
                        "content_type": content_type,
                        "width": uploaded.width,
                        "height": uploaded.height,
                        "bytes": uploaded.bytes,
                        "is_primary": True,
                    },
                )
                conn.commit()
                return image
    except Exception:
        try:
            gateway.delete_image(uploaded.public_id)
        except ImageGatewayError:
            pass
        raise


def delete_activity_image(activity_id: UUID, image_id: UUID, gateway: ImageGateway) -> dict:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            _require_activity(cur, activity_id)
            image = repo.get_activity_image(cur, activity_id, image_id)
            if image is None:
                raise ActivityImageNotFoundError

    try:
        gateway.delete_image(image["public_id"])
    except ImageGatewayError as exc:
        raise ActivityImageGatewayError from exc

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            deleted = repo.delete_activity_image(cur, activity_id, image_id)
            if deleted is None:
                raise ActivityImageNotFoundError
            conn.commit()
            return deleted

