from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GeocodedAddress:
    query: str
    label: str
    longitude: float
    latitude: float


@dataclass(frozen=True)
class RouteEstimate:
    origin: GeocodedAddress
    destination: GeocodedAddress
    distance_meters: float
    duration_seconds: float
    provider: str


class RouteGatewayError(Exception):
    """Base error raised by an external routing provider adapter."""


class RouteGatewayConfigurationError(RouteGatewayError):
    """Raised when the server-side provider configuration is incomplete."""


class RouteAddressNotFoundError(RouteGatewayError):
    """Raised when the provider cannot resolve a supplied address."""


class RouteProviderUnavailableError(RouteGatewayError):
    """Raised when the external provider is unavailable or returns invalid data."""


class RouteGateway(Protocol):
    def estimate_route(
        self,
        origin_address: str,
        destination_address: str,
    ) -> RouteEstimate:
        ...
