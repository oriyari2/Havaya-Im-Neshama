from __future__ import annotations

import unittest

from PySide6.QtWidgets import QApplication

from desktop_client.app.features.bookings.presenter import BookingsPresenter
from desktop_client.app.features.bookings.service import BookingService
from desktop_client.app.features.bookings.view import BookingsView


class _ApiClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def get(self, path, params=None):
        self.calls.append((path, params))
        return {"distance_km": 61.2, "duration_minutes": 72}


class _PresenterView:
    def __init__(self) -> None:
        self.loading: list[bool] = []
        self.estimate = None
        self.error = ""

    def set_travel_loading(self, loading):
        self.loading.append(bool(loading))

    def show_travel_estimate(self, estimate):
        self.estimate = estimate

    def show_travel_error(self, message):
        self.error = message


class _PresenterService:
    def travel_estimate(self, booking_id):
        return {
            "booking_id": booking_id,
            "distance_km": 61.2,
            "duration_minutes": 72,
            "origin_resolved_address": "רמת גן",
            "destination_resolved_address": "ירושלים",
        }


class TravelGatewayDesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_booking_service_calls_travel_estimate_endpoint(self) -> None:
        client = _ApiClient()
        result = BookingService(client).travel_estimate("booking-1")

        self.assertEqual(result["distance_km"], 61.2)
        self.assertEqual(client.calls, [("/bookings/booking-1/travel-estimate", None)])

    def test_manager_presenter_loads_travel_estimate_for_current_booking(self) -> None:
        view = _PresenterView()
        presenter = BookingsPresenter(view, _PresenterService(), "manager")
        presenter.current_booking = {"id": "booking-1"}

        presenter.estimate_travel()

        self.assertEqual(view.loading, [True, False])
        self.assertEqual(view.estimate["duration_minutes"], 72)
        self.assertEqual(view.error, "")

    def test_manager_view_exposes_external_route_panel_and_readable_result(self) -> None:
        view = BookingsView("manager")
        try:
            self.assertFalse(view.travel_group.isHidden())
            self.assertIn("חשב מרחק", view.travel_button.text())

            view.show_travel_estimate(
                {
                    "distance_km": 61.2,
                    "duration_minutes": 72,
                    "origin_resolved_address": "לנדרס 16, רמת גן, ישראל",
                    "destination_resolved_address": "בנייני האומה, ירושלים, ישראל",
                }
            )

            self.assertIn("61.2", view.travel_summary.text())
            self.assertIn("72", view.travel_summary.text())
            self.assertIn("רמת גן", view.travel_addresses.text())
            self.assertIn("ירושלים", view.travel_addresses.text())
        finally:
            view.close()
            view.deleteLater()
            self.app.processEvents()

    def test_instructor_view_exposes_route_panel_from_profile_city(self) -> None:
        view = BookingsView("instructor")
        try:
            self.assertFalse(view.travel_group.isHidden())
            self.assertIn("עיר", view.travel_hint.text())
            self.assertIn("חשב מרחק", view.travel_button.text())
        finally:
            view.close()
            view.deleteLater()
            self.app.processEvents()

    def test_instructor_presenter_can_load_travel_estimate_for_open_event(self) -> None:
        view = _PresenterView()
        presenter = BookingsPresenter(view, _PresenterService(), "instructor")
        presenter.current_booking = {"booking_id": "booking-open-1"}

        presenter.estimate_travel()

        self.assertEqual(view.loading, [True, False])
        self.assertEqual(view.estimate["distance_km"], 61.2)
        self.assertEqual(view.error, "")

    def test_customer_view_hides_route_calculation_panel(self) -> None:
        view = BookingsView("customer")
        try:
            self.assertTrue(view.travel_group.isHidden())
        finally:
            view.close()
            view.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
