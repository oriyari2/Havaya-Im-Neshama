from __future__ import annotations

from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.app.application.gateways.image_gateway import ImageGateway
from backend.app.application.services import activity_image_service
from backend.app.application.services import activity_service
from backend.app.core.auth import get_current_user, require_roles
from backend.app.infrastructure.gateways.providers import get_image_gateway
from backend.app.schemas.activity_image import ActivityImageListResponse, ActivityImageResponse


router = APIRouter(tags=["activity images"])
RequireManager = Depends(require_roles("manager"))


def _raise_activity_error(exc: Exception) -> NoReturn:
    if isinstance(exc, activity_service.ActivityNotFoundError):
        raise HTTPException(status_code=404, detail="Activity not found") from exc
    if isinstance(exc, activity_service.ActivityAccessDeniedError):
        raise HTTPException(status_code=403, detail="Not authorized") from exc
    raise exc


@router.get("/activities/{activity_id}/images", response_model=ActivityImageListResponse)
def list_activity_images(
    activity_id: UUID,
    current_user: dict = Depends(get_current_user),
) -> ActivityImageListResponse:
    try:
        images = activity_image_service.list_images_for_user(activity_id, current_user)
    except (activity_service.ActivityNotFoundError, activity_service.ActivityAccessDeniedError) as exc:
        _raise_activity_error(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not list activity images") from exc

    return ActivityImageListResponse(
        items=[ActivityImageResponse(**image) for image in images],
        count=len(images),
    )


@router.post("/activities/{activity_id}/images", response_model=ActivityImageResponse, status_code=201)
def upload_activity_image(
    activity_id: UUID,
    file: Annotated[UploadFile, File()],
    _current_user: dict = RequireManager,
    gateway: ImageGateway = Depends(get_image_gateway),
) -> ActivityImageResponse:
    try:
        file_bytes = file.file.read()
        image = activity_image_service.upload_activity_image(
            activity_id=activity_id,
            file_bytes=file_bytes,
            filename=file.filename,
            content_type=file.content_type,
            gateway=gateway,
        )
    except activity_service.ActivityNotFoundError as exc:
        _raise_activity_error(exc)
    except activity_image_service.UnsupportedActivityImageTypeError as exc:
        raise HTTPException(status_code=422, detail="Unsupported image content type") from exc
    except activity_image_service.ActivityImageGatewayError as exc:
        raise HTTPException(status_code=502, detail="Image service is unavailable") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not upload activity image") from exc

    return ActivityImageResponse(**image)


@router.delete("/activities/{activity_id}/images/{image_id}", response_model=ActivityImageResponse)
def delete_activity_image(
    activity_id: UUID,
    image_id: UUID,
    _current_user: dict = RequireManager,
    gateway: ImageGateway = Depends(get_image_gateway),
) -> ActivityImageResponse:
    try:
        image = activity_image_service.delete_activity_image(activity_id, image_id, gateway)
    except activity_service.ActivityNotFoundError as exc:
        _raise_activity_error(exc)
    except activity_image_service.ActivityImageNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Activity image not found") from exc
    except activity_image_service.ActivityImageGatewayError as exc:
        raise HTTPException(status_code=502, detail="Image service is unavailable") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not delete activity image") from exc

    return ActivityImageResponse(**image)

