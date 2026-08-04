from __future__ import annotations

import json
import unittest
from unittest.mock import patch
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient

from backend.app.application.gateways.route_gateway import (
    GeocodedAddress,
    RouteAddressNotFoundError,
    RouteEstimate,
    RouteGatewayConfigurationError,
)
from backend.app.application.bookings import query_handlers
from backend.app.application.services import booking_travel_service
from backend.app.core.auth import get_current_user
from backend.app.infrastructure.gateways.openrouteservice_gateway import OpenRouteServiceGateway
from backend.app.infrastructure.gateways.providers import get_route_gateway
from backend.app.main import app


class _FakeRouteGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def estimate_route(self, origin_address: str, destination_address: str) -> RouteEstimate:
        self.calls.append((origin_address, destination_address))
        return RouteEstimate(
            origin=GeocodedAddress(origin_address, "לנדרס 16, רמת גן, ישראל", 34.81, 32.08),
            destination=GeocodedAddress(destination_address, "בנייני האומה, ירושלים, ישראל", 35.20, 31.78),
            distance_meters=61234.0,
            duration_seconds=4320.0,
            provider="openrouteservice",
        )


class OpenRouteServiceGatewayTests(unittest.TestCase):
    def test_geocodes_both_addresses_and_returns_distance_and_duration(self) -> None:
        seen_queries: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.headers.get("Authorization"), "test-key")
            if request.url.path == "/geocode/search":
                query = request.url.params["text"]
                seen_queries.append(query)
                coordinates = [34.81, 32.08] if len(seen_queries) == 1 else [35.20, 31.78]
                return httpx.Response(
                    200,
                    json={
                        "features": [
                            {
                                "geometry": {"coordinates": coordinates},
                                "properties": {"label": f"resolved:{query}"},
                            }
                        ]
                    },
                )
            if request.url.path == "/v2/directions/driving-car/json":
                payload = json.loads(request.content.decode("utf-8"))
                self.assertEqual(payload["coordinates"], [[34.81, 32.08], [35.20, 31.78]])
                self.assertFalse(payload["instructions"])
                return httpx.Response(200, json={"routes": [{"summary": {"distance": 61234.0, "duration": 4320.0}}]})
            return httpx.Response(404)

        gateway = OpenRouteServiceGateway(
            api_key="test-key",
            transport=httpx.MockTransport(handler),
        )

        estimate = gateway.estimate_route(
            "לנדרס 16, רמת גן, ישראל",
            "בנייני האומה, ירושלים, ישראל",
        )

        self.assertEqual(seen_queries, ["לנדרס 16, רמת גן, ישראל", "בנייני האומה, ירושלים, ישראל"])
        self.assertEqual(estimate.distance_meters, 61234.0)
        self.assertEqual(estimate.duration_seconds, 4320.0)
        self.assertEqual(estimate.provider, "openrouteservice")

    def test_missing_api_key_and_unknown_address_fail_closed(self) -> None:
        with self.assertRaises(RouteGatewayConfigurationError):
            OpenRouteServiceGateway(api_key="").estimate_route("מוצא", "יעד")

        transport = httpx.MockTransport(lambda _request: httpx.Response(200, json={"features": []}))
        with self.assertRaises(RouteAddressNotFoundError):
            OpenRouteServiceGateway(api_key="test-key", transport=transport).estimate_route("מוצא", "יעד")


class BookingTravelServiceTests(unittest.TestCase):
    def test_builds_israeli_destination_and_normalizes_provider_result(self) -> None:
        gateway = _FakeRouteGateway()
        booking_id = uuid4()

        with patch(
            "backend.app.application.services.booking_travel_service.get_business_base_address",
            return_value="לנדרס 16, רמת גן, ישראל",
        ):
            result = booking_travel_service.estimate_booking_travel(
                {"id": booking_id, "venue": "בנייני האומה", "city": "ירושלים"},
                gateway,
            )

        self.assertEqual(gateway.calls, [("לנדרס 16, רמת גן, ישראל", "בנייני האומה, ירושלים, ישראל")])
        self.assertEqual(result["booking_id"], booking_id)
        self.assertEqual(result["distance_km"], 61.2)
        self.assertEqual(result["duration_minutes"], 72)
        self.assertFalse(result["uses_live_traffic"])

    def test_missing_booking_location_is_rejected_before_provider_call(self) -> None:
        with self.assertRaises(booking_travel_service.TravelEstimateValidationError):
            booking_travel_service.booking_destination_address({"city": None, "venue": None})


class BookingTravelApiTests(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_manager_can_calculate_booking_travel_estimate(self) -> None:
        booking_id = uuid4()
        gateway = _FakeRouteGateway()
        app.dependency_overrides[get_current_user] = lambda: {"id": uuid4(), "role": "manager"}
        app.dependency_overrides[get_route_gateway] = lambda: gateway

        with patch(
            "backend.app.routers.travel.query_handlers.get_booking",
            return_value={"id": booking_id, "venue": "בנייני האומה", "city": "ירושלים"},
        ), patch(
            "backend.app.application.services.booking_travel_service.get_business_base_address",
            return_value="לנדרס 16, רמת גן, ישראל",
        ):
            response = TestClient(app).get(f"/bookings/{booking_id}/travel-estimate")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["booking_id"], str(booking_id))
        self.assertEqual(payload["distance_km"], 61.2)
        self.assertEqual(payload["duration_minutes"], 72)
        self.assertEqual(payload["provider"], "openrouteservice")


    def test_instructor_can_calculate_from_profile_city_for_assigned_booking(self) -> None:
        booking_id = uuid4()
        instructor_id = uuid4()
        gateway = _FakeRouteGateway()
        app.dependency_overrides[get_current_user] = lambda: {
            "id": uuid4(),
            "role": "instructor",
            "instructor_id": instructor_id,
        }
        app.dependency_overrides[get_route_gateway] = lambda: gateway

        with patch(
            "backend.app.routers.travel.instructor_service.get_my_profile",
            return_value={"id": instructor_id, "city": "פתח תקווה"},
        ), patch(
            "backend.app.routers.travel.query_handlers.get_booking",
            return_value={"id": booking_id, "venue": "אולם תלמוד תורה", "city": "ירושלים"},
        ):
            response = TestClient(app).get(f"/bookings/{booking_id}/travel-estimate")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(gateway.calls[0][0], "פתח תקווה, ישראל")
        self.assertEqual(response.json()["distance_km"], 61.2)

    def test_instructor_can_calculate_for_visible_open_event(self) -> None:
        booking_id = uuid4()
        instructor_id = uuid4()
        gateway = _FakeRouteGateway()
        app.dependency_overrides[get_current_user] = lambda: {
            "id": uuid4(),
            "role": "instructor",
            "instructor_id": instructor_id,
        }
        app.dependency_overrides[get_route_gateway] = lambda: gateway

        with patch(
            "backend.app.routers.travel.instructor_service.get_my_profile",
            return_value={"id": instructor_id, "city": "רמת גן"},
        ), patch(
            "backend.app.routers.travel.query_handlers.get_booking",
            side_effect=query_handlers.BookingAccessDeniedError(),
        ), patch(
            "backend.app.routers.travel.assignment_query_handlers.get_open_event_detail",
            return_value={"booking_id": booking_id, "venue": "מרכז קהילתי", "city": "רחובות"},
        ):
            response = TestClient(app).get(f"/bookings/{booking_id}/travel-estimate")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(gateway.calls[0], ("רמת גן, ישראל", "מרכז קהילתי, רחובות, ישראל"))

    def test_instructor_without_city_gets_validation_error_before_provider_call(self) -> None:
        instructor_id = uuid4()
        gateway = _FakeRouteGateway()
        app.dependency_overrides[get_current_user] = lambda: {
            "id": uuid4(),
            "role": "instructor",
            "instructor_id": instructor_id,
        }
        app.dependency_overrides[get_route_gateway] = lambda: gateway

        with patch(
            "backend.app.routers.travel.instructor_service.get_my_profile",
            return_value={"id": instructor_id, "city": None},
        ):
            response = TestClient(app).get(f"/bookings/{uuid4()}/travel-estimate")

        self.assertEqual(response.status_code, 422)
        self.assertEqual(gateway.calls, [])

    def test_customer_is_denied_before_external_call(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: {"id": uuid4(), "role": "customer", "customer_id": uuid4()}
        app.dependency_overrides[get_route_gateway] = _FakeRouteGateway

        response = TestClient(app).get(f"/bookings/{uuid4()}/travel-estimate")

        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
