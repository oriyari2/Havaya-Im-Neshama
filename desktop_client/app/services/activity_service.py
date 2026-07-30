from __future__ import annotations

from pathlib import Path
from stat import S_ISREG

from desktop_client.app.api.client import ApiClient
from desktop_client.app.media_config import MAX_PREVIEW_DOWNLOAD_BYTES, MAX_UPLOAD_SIZE_BYTES


IMAGE_CONTENT_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


class ActivityService:
    def __init__(self, api_client: ApiClient) -> None:
        self.api_client = api_client

    def list_activities(self, filters: dict[str, object]) -> dict:
        return self.api_client.get("/activities", filters)

    def invalidate_list(self, filters: dict[str, object]) -> None:
        self.api_client.invalidate_cached_get("/activities", filters)

    def activity(self, activity_id: str) -> dict:
        return self.api_client.get(f"/activities/{activity_id}")

    def create_activity(self, payload: dict[str, object]) -> dict:
        return self.api_client.post("/activities", payload)

    def update_activity(self, activity_id: str, payload: dict[str, object]) -> dict:
        return self.api_client.put(f"/activities/{activity_id}", payload)

    def deactivate_activity(self, activity_id: str) -> dict:
        return self.api_client.delete(f"/activities/{activity_id}")

    def reactivate_activity(self, activity_id: str) -> dict:
        return self.update_activity(activity_id, {"is_active": True})

    def upload_image(self, activity_id: str, file_path: str) -> dict:
        path = Path(file_path)
        try:
            file_stat = path.stat()
        except OSError:
            raise ValueError("לא ניתן לגשת לקובץ התמונה.") from None
        if not S_ISREG(file_stat.st_mode):
            raise ValueError("קובץ התמונה לא נמצא.")
        content_type = IMAGE_CONTENT_TYPES.get(path.suffix.lower())
        if content_type is None:
            raise ValueError("ניתן להעלות קובצי JPEG, PNG או WebP בלבד.")
        size = file_stat.st_size
        if size <= 0:
            raise ValueError("קובץ התמונה ריק.")
        if size > MAX_UPLOAD_SIZE_BYTES:
            raise ValueError(f"קובץ התמונה חורג מהמגבלה של {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MiB.")
        try:
            file_bytes = path.read_bytes()
        except OSError:
            raise ValueError("לא ניתן לקרוא את קובץ התמונה.") from None
        if not file_bytes:
            raise ValueError("קובץ התמונה ריק.")
        if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
            raise ValueError(f"קובץ התמונה חורג מהמגבלה של {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MiB.")
        return self.api_client.post_multipart(
            f"/activities/{activity_id}/images",
            field_name="file",
            filename=path.name,
            content_type=content_type,
            file_bytes=file_bytes,
        )

    def delete_image(self, activity_id: str, image_id: str) -> dict:
        return self.api_client.delete(f"/activities/{activity_id}/images/{image_id}")

    def preview_bytes(self, secure_url: str) -> bytes:
        return self.api_client.get_public_bytes(secure_url, max_bytes=MAX_PREVIEW_DOWNLOAD_BYTES)
