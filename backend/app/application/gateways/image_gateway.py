from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class UploadedImage:
    public_id: str
    secure_url: str
    width: int | None = None
    height: int | None = None
    bytes: int | None = None


class ImageGatewayError(Exception):
    pass


class ImageGateway(Protocol):
    def upload_activity_image(
        self,
        file_bytes: bytes,
        filename: str | None,
        content_type: str | None,
    ) -> UploadedImage:
        ...

    def delete_image(self, public_id: str) -> None:
        ...

