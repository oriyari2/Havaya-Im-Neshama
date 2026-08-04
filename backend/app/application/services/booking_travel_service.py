from __future__ import annotations

from typing import Any

from backend.app.application.gateways.route_gateway import (
    RouteAddressNotFoundError,
    RouteGateway,
    RouteGatewayConfigurationError,
    RouteProviderUnavailableError,
)
from backend.app.core.environment import get_business_base_address


class TravelEstimateValidationError(Exception):
    pass


class TravelEstimateConfigurationError(Exception):
    pass


class TravelEstimateProviderError(Exception):
    pass


def estimate_booking_travel(
    booking: dict[str, Any],
    gateway: RouteGateway,
    *,
    origin_address: str | None = None,
) -> dict[str, object]:
    origin_address = str(origin_address or get_business_base_address() or "").strip()
    if not origin_address:
        raise TravelEstimateConfigurationError("Travel origin address is missing")

    destination_address = booking_destination_address(booking)
    try:
        estimate = gateway.estimate_route(origin_address, destination_address)
    except RouteGatewayConfigurationError as exc:
        raise TravelEstimateConfigurationError from exc
    except RouteAddressNotFoundError as exc:
        raise TravelEstimateValidationError from exc
    except RouteProviderUnavailableError as exc:
        raise TravelEstimateProviderError from exc

    return {
        "booking_id": booking.get("id") or booking.get("booking_id"),
        "origin_address": estimate.origin.query,
        "origin_resolved_address": estimate.origin.label,
        "destination_address": estimate.destination.query,
        "destination_resolved_address": estimate.destination.label,
        "distance_km": round(estimate.distance_meters / 1000.0, 1),
        "duration_minutes": max(1, round(estimate.duration_seconds / 60.0)),
        "provider": estimate.provider,
        "uses_live_traffic": False,
    }


def booking_destination_address(booking: dict[str, Any]) -> str:
    venue = str(booking.get("venue") or "").strip()
    city = str(booking.get("city") or "").strip()
    if not venue and not city:
        raise TravelEstimateValidationError("Booking location is missing")

    parts: list[str] = []
    if venue:
        parts.append(venue)
    if city and city.casefold() not in venue.casefold():
        parts.append(city)
    combined = ", ".join(parts)
    if "ישראל" not in combined and "israel" not in combined.casefold():
        combined = f"{combined}, ישראל"
    return combined
