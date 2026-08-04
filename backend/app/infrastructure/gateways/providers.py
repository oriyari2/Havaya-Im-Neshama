from __future__ import annotations

from backend.app.application.gateways.image_gateway import ImageGateway
from backend.app.application.gateways.route_gateway import RouteGateway
from backend.app.infrastructure.gateways.cloudinary_image_gateway import CloudinaryImageGateway
from backend.app.infrastructure.gateways.openrouteservice_gateway import OpenRouteServiceGateway


def get_image_gateway() -> ImageGateway:
    return CloudinaryImageGateway()



def get_route_gateway() -> RouteGateway:
    return OpenRouteServiceGateway()
