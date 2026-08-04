from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from backend.app.application.gateways.route_gateway import (
    GeocodedAddress,
    RouteAddressNotFoundError,
    RouteEstimate,
    RouteGatewayConfigurationError,
    RouteProviderUnavailableError,
)
from backend.app.core.environment import (
    get_openrouteservice_api_key,
    get_openrouteservice_base_url,
    get_openrouteservice_country_code,
    get_openrouteservice_timeout_seconds,
)


class OpenRouteServiceGateway:
    """OpenRouteService adapter behind the application-owned RouteGateway port."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        country_code: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.api_key = (get_openrouteservice_api_key() if api_key is None else api_key).strip()
        self.base_url = (get_openrouteservice_base_url() if base_url is None else base_url).rstrip("/")
        self.timeout_seconds = timeout_seconds or get_openrouteservice_timeout_seconds()
        self.country_code = (
            get_openrouteservice_country_code() if country_code is None else country_code
        ).strip().upper()
        self._transport = transport

    def estimate_route(self, origin_address: str, destination_address: str) -> RouteEstimate:
        if not self.api_key:
            raise RouteGatewayConfigurationError("OpenRouteService API key is missing")
        if not origin_address.strip() or not destination_address.strip():
            raise RouteAddressNotFoundError("Origin and destination addresses are required")

        headers = {
            "Authorization": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "havaya-im-neshama-course-project/1.0",
        }
        try:
            with httpx.Client(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout_seconds,
                transport=self._transport,
            ) as client:
                origin = self._geocode(client, origin_address)
                destination = self._geocode(client, destination_address)
                return self._directions(client, origin, destination)
        except RouteAddressNotFoundError:
            raise
        except RouteGatewayConfigurationError:
            raise
        except httpx.TimeoutException as exc:
            raise RouteProviderUnavailableError("Route provider timed out") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in {401, 403}:
                raise RouteGatewayConfigurationError("OpenRouteService rejected the API key") from exc
            raise RouteProviderUnavailableError("Route provider rejected the request") from exc
        except (httpx.HTTPError, ValueError, TypeError, KeyError, IndexError) as exc:
            raise RouteProviderUnavailableError("Route provider returned an invalid response") from exc

    def _geocode(self, client: httpx.Client, query: str) -> GeocodedAddress:
        params: dict[str, object] = {"text": query.strip(), "size": 1}
        if self.country_code:
            params["boundary.country"] = self.country_code
        response = client.get("/geocode/search", params=params)
        response.raise_for_status()
        payload = _json_object(response)
        features = payload.get("features")
        if not isinstance(features, list) or not features:
            raise RouteAddressNotFoundError(f"Address was not found: {query}")

        first = features[0]
        if not isinstance(first, Mapping):
            raise RouteProviderUnavailableError("Invalid geocoding result")
        geometry = first.get("geometry")
        properties = first.get("properties")
        if not isinstance(geometry, Mapping) or not isinstance(properties, Mapping):
            raise RouteProviderUnavailableError("Invalid geocoding result")
        coordinates = geometry.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            raise RouteProviderUnavailableError("Invalid geocoding coordinates")

        longitude = float(coordinates[0])
        latitude = float(coordinates[1])
        label = str(properties.get("label") or query).strip()
        return GeocodedAddress(
            query=query.strip(),
            label=label,
            longitude=longitude,
            latitude=latitude,
        )

    def _directions(
        self,
        client: httpx.Client,
        origin: GeocodedAddress,
        destination: GeocodedAddress,
    ) -> RouteEstimate:
        response = client.post(
            "/v2/directions/driving-car/json",
            json={
                "coordinates": [
                    [origin.longitude, origin.latitude],
                    [destination.longitude, destination.latitude],
                ],
                "instructions": False,
            },
        )
        response.raise_for_status()
        payload = _json_object(response)
        routes = payload.get("routes")
        if not isinstance(routes, list) or not routes:
            raise RouteProviderUnavailableError("No route was returned")
        route = routes[0]
        if not isinstance(route, Mapping):
            raise RouteProviderUnavailableError("Invalid directions result")
        summary = route.get("summary")
        if not isinstance(summary, Mapping):
            raise RouteProviderUnavailableError("Directions summary is missing")

        distance = float(summary["distance"])
        duration = float(summary["duration"])
        if distance < 0 or duration < 0:
            raise RouteProviderUnavailableError("Directions summary is invalid")
        return RouteEstimate(
            origin=origin,
            destination=destination,
            distance_meters=distance,
            duration_seconds=duration,
            provider="openrouteservice",
        )



def _json_object(response: httpx.Response) -> dict[str, Any]:
    payload = response.json()
    if not isinstance(payload, dict):
        raise RouteProviderUnavailableError("Route provider returned a non-object response")
    return payload
