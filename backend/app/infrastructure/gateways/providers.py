from __future__ import annotations

from backend.app.application.gateways.image_gateway import ImageGateway
from backend.app.infrastructure.gateways.cloudinary_image_gateway import CloudinaryImageGateway


def get_image_gateway() -> ImageGateway:
    return CloudinaryImageGateway()

