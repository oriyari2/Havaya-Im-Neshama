from __future__ import annotations

import os

from backend.app.application.gateways.image_gateway import ImageGatewayError, UploadedImage
from backend.app.db.connection import load_local_env


class CloudinaryImageGateway:
    def __init__(self) -> None:
        load_local_env()
        self.folder = os.getenv("CLOUDINARY_ACTIVITY_FOLDER", "havaya-im-neshama/activities")

    def _configure(self) -> None:
        try:
            import cloudinary
        except ImportError as exc:
            raise ImageGatewayError("Cloudinary SDK is not installed") from exc

        cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
        api_key = os.getenv("CLOUDINARY_API_KEY")
        api_secret = os.getenv("CLOUDINARY_API_SECRET")
        if not cloud_name or not api_key or not api_secret:
            raise ImageGatewayError("Cloudinary configuration is missing")

        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )

    def upload_activity_image(
        self,
        file_bytes: bytes,
        filename: str | None,
        content_type: str | None,
    ) -> UploadedImage:
        self._configure()
        try:
            from cloudinary import uploader

            result = uploader.upload(
                file_bytes,
                folder=self.folder,
                resource_type="image",
                filename=filename,
                use_filename=True,
                unique_filename=True,
                overwrite=False,
            )
        except Exception as exc:
            raise ImageGatewayError("Image upload failed") from exc

        public_id = result.get("public_id")
        secure_url = result.get("secure_url")
        if not public_id or not secure_url:
            raise ImageGatewayError("Image upload did not return asset metadata")

        return UploadedImage(
            public_id=public_id,
            secure_url=secure_url,
            width=result.get("width"),
            height=result.get("height"),
            bytes=result.get("bytes"),
        )

    def delete_image(self, public_id: str) -> None:
        self._configure()
        try:
            from cloudinary import uploader

            result = uploader.destroy(public_id, resource_type="image")
        except Exception as exc:
            raise ImageGatewayError("Image delete failed") from exc

        if result.get("result") not in {"ok", "not found"}:
            raise ImageGatewayError("Image delete was not accepted by Cloudinary")

