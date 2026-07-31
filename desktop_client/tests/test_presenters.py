from __future__ import annotations

import unittest

from desktop_client.app.models.session import Session
from desktop_client.app.api.client import ApiError
from desktop_client.app.api.client import ApiErrorKind
from desktop_client.app.presenters.ai_chat_presenter import AIChatPresenter
from desktop_client.app.presenters.bookings_presenter import BookingsPresenter, FormValidationError, validate_create_booking
from desktop_client.app.presenters.dashboard_presenter import DashboardPresenter
from desktop_client.app.presenters.login_presenter import LoginPresenter
from desktop_client.app.presenters.navigation import navigation_for_role
from desktop_client.app.presenters.open_events_presenter import OpenEventsPresenter


BOOKING = {
    "id": "booking-1",
    "event_at": "2026-08-15T10:00:00+00:00",
    "status": "NEW",
    "city": "Jerusalem",
    "venue": "Hall",
    "participant_count": 24,
    "agreed_price": "1200",
    "notes": "private",
}


class _View:
    def __init__(self) -> None:
        self.loading: list[bool] = []
        self.error = ""
        self.rows = []
        self.details = []
        self.history = []
        self.summary = {}
        self.sections = None
        self.success = ""
        self.create_values = None
        self.edit_values = None
        self.messages = []
        self.input_cleared = False
        self.cancellation_confirmed = True
        self.command_status = ""
        self.request_states = []

    def set_loading(self, loading: bool) -> None:
        self.loading.append(loading)

    def render_request_state(self, state) -> None:
        self.request_states.append(state)

    def show_error(self, message: str) -> None:
        self.error = message

    def show_bookings(self, rows, **page) -> None:
        self.rows = rows
        self.page = page

    def show_filter_options(self, customers, activities, instructors) -> None:
        self.filter_options = (customers, activities, instructors)

    def show_events(self, rows) -> None:
        self.rows = rows

    def show_details(self, details, history) -> None:
        self.details = details
        self.history = history

    def show_summary(self, summary) -> None:
        self.summary = summary

    def show_sections(self, *sections) -> None:
        self.sections = sections

    def show_success(self, message):
        self.success = message

    def append_message(self, sender, message):
        self.messages.append((sender, message))

    def clear_input(self):
        self.input_cleared = True

    def collect_create_booking(self, customers, activities, instructors, **kwargs):
        return self.create_values

    def collect_booking_changes(self, booking):
        return self.edit_values

    def confirm_cancellation(self):
        return self.cancellation_confirmed

    def confirm_completion(self):
        return self.cancellation_confirmed

    def set_command_availability(self, status):
        self.command_status = status


class _Service:
    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.fail = False

    def _check(self) -> None:
        if self.fail:
            raise RuntimeError("network error")

    def dashboard(self):
        self._check()
        self.calls.append(("dashboard",))
        return {"upcoming_count": 1}

    def list_bookings(self, filters=None):
        self._check()
        self.calls.append(("list", filters))
        return {"items": [BOOKING], "count": 1}

    def my_bookings(self, *, limit=50, offset=0):
        self._check()
        self.calls.append(("mine", limit, offset))
        return {"items": [BOOKING], "count": 1}

    def open_events(self):
        self._check()
        self.calls.append(("open",))
        return [BOOKING]

    def booking(self, booking_id):
        self._check()
        self.calls.append(("booking", booking_id))
        return BOOKING

    def history(self, booking_id):
        self._check()
        self.calls.append(("history", booking_id))
        return [{"event_type": "BookingCreated", "event_data": BOOKING, "occurred_at": BOOKING["event_at"], "actor_user_id": "user-1"}]

    def booking_form_options(self, *, include_customers=True):
        self.calls.append(("options", include_customers))
        return ([{"id": "customer-1", "name": "לקוח"}], [{"id": "activity-1", "name": "פעילות"}])

    def create_booking(self, payload):
        self._check()
        self.calls.append(("create", payload))
        return {**BOOKING, **payload, "version": 1}

    def change_status(self, booking_id, status, expected_version):
        self._check()
        self.calls.append(("status", booking_id, status, expected_version))
        return {**BOOKING, "id": booking_id, "status": status, "version": expected_version + 1}

    def change_schedule(self, booking_id, event_at, expected_version):
        self.calls.append(("schedule", expected_version))
        return {**BOOKING, "id": booking_id, "event_at": event_at, "version": expected_version + 1}

    def change_price(self, booking_id, agreed_price, expected_version):
        self.calls.append(("price", expected_version))
        return {**BOOKING, "id": booking_id, "agreed_price": agreed_price, "version": expected_version + 1}

    def change_location(self, booking_id, city, venue, expected_version):
        self.calls.append(("location", expected_version))
        return {**BOOKING, "id": booking_id, "city": city, "venue": venue, "version": expected_version + 1}

    def change_participant_count(self, booking_id, participant_count, expected_version):
        self.calls.append(("participants", expected_version))
        return {**BOOKING, "id": booking_id, "participant_count": participant_count, "version": expected_version + 1}

    def update_notes(self, booking_id, notes, expected_version):
        self.calls.append(("notes", expected_version))
        return {**BOOKING, "id": booking_id, "notes": notes, "version": expected_version + 1}


class PresenterTests(unittest.TestCase):
    def test_role_navigation_contains_only_permitted_booking_modules(self) -> None:
        self.assertEqual([key for key, _ in navigation_for_role("manager")], ["dashboard", "customers", "instructors", "activities", "bookings", "open_events", "knowledge", "users", "ai_chat"])
        self.assertEqual([key for key, _ in navigation_for_role("instructor")], ["dashboard", "activities", "bookings", "open_events", "my_profile", "ai_chat"])
        self.assertEqual([key for key, _ in navigation_for_role("customer")], ["dashboard", "activities", "my_bookings", "my_profile", "ai_chat"])
        self.assertEqual([key for key, _ in navigation_for_role("customer", has_profile=False)], ["dashboard", "activities", "my_bookings", "ai_chat"])
        self.assertEqual(navigation_for_role("unknown"), ())

    def test_ai_chat_presenter_appends_conversation_and_loading(self) -> None:
        view = _View()

        class AIService:
            def consult(self, prompt):
                return f"תשובה עבור {prompt}"

        presenter = AIChatPresenter(view, AIService())
        presenter.send_message(" שלום ")

        self.assertEqual(view.loading, [True, False])
        self.assertEqual(view.messages, [("את/ה", "שלום"), ("היועץ", "תשובה עבור שלום")])
        self.assertTrue(view.input_cleared)

    def test_ai_chat_presenter_displays_rag_sources(self) -> None:
        view = _View()

        class AIService:
            def consult(self, prompt):
                return {
                    "answer": "Grounded answer [1].",
                    "answer_basis": "rag",
                    "sources": [{"source_title": "Task17 Equipment", "source_uri": "demo://equipment"}],
                }

        presenter = AIChatPresenter(view, AIService())
        presenter.send_message("hello")

        self.assertIn("Grounded answer [1].", view.messages[-1][1])
        self.assertIn("מקורות:", view.messages[-1][1])
        self.assertIn("Task17 Equipment", view.messages[-1][1])
        self.assertIn("demo://equipment", view.messages[-1][1])

    def test_ai_chat_presenter_handles_empty_prompt_and_errors(self) -> None:
        view = _View()

        class FailingAIService:
            def consult(self, prompt):
                raise RuntimeError("offline")

        presenter = AIChatPresenter(view, FailingAIService())
        presenter.send_message(" ")
        self.assertIn("שאלה", view.error)
        presenter.send_message("שלום")
        self.assertEqual(view.error, "offline")
        self.assertEqual(view.loading, [True, False])

    def test_login_presenter_validates_and_reports_loading(self) -> None:
        view = _View()
        authenticated = []
        expected = Session("token", "id", "customer@example.com", "customer")

        class Auth:
            def login(self, email, password):
                return expected

        presenter = LoginPresenter(view, Auth(), authenticated.append)
        presenter.login("", "")
        self.assertIn("דוא״ל", view.error)
        presenter.login("customer@example.com", "secret")
        self.assertEqual(authenticated, [expected])
        self.assertEqual(view.loading, [True, False])
        self.assertEqual(view.request_states[0].phase.value, "loading")

    def test_login_presenter_sanitizes_failures_and_releases_guard(self) -> None:
        for error, expected in (
            (ApiError("secret transport", kind=ApiErrorKind.CONNECTION), "לא ניתן להתחבר לשרת"),
            (ApiError("secret backend", kind=ApiErrorKind.SERVER), "השרת לא הצליח"),
            (ApiError("raw auth", kind=ApiErrorKind.AUTHENTICATION), "פרטי ההתחברות"),
            (RuntimeError("internal secret"), "לא ניתן להשלים"),
        ):
            view = _View()
            class Auth:
                def login(self, email, password): raise error
            LoginPresenter(view, Auth(), lambda _session: None).login("user@example.com", "secret")
            self.assertIn(expected, view.error)
            self.assertNotIn("secret", view.error)
            self.assertEqual(view.loading, [True, False])
            self.assertEqual(view.request_states[-1].operation_key, "login")

    def test_login_presenter_rejects_reentrant_duplicate(self) -> None:
        view = _View(); calls = []
        class Auth:
            def login(inner_self, email, password):
                calls.append((email, password)); presenter.login(email, password)
                return Session("token", "id", email, "customer")
        presenter = LoginPresenter(view, Auth(), lambda _session: None); presenter.login("user@example.com", "secret")
        self.assertEqual(calls, [("user@example.com", "secret")]); self.assertFalse(presenter._loading)

    def test_dashboard_loads_role_specific_sections(self) -> None:
        for role, expected_call in (("manager", "list"), ("instructor", "list"), ("customer", "mine")):
            view = _View()
            service = _Service()
            DashboardPresenter(view, service, role).load()
            self.assertEqual(view.summary, {"upcoming_count": 1})
            self.assertIn(expected_call, [entry[0] for entry in service.calls])
            self.assertIsNotNone(view.sections)

    def test_dashboard_drilldown_maps_status_and_unassigned_without_cross_role_scope(self) -> None:
        calls = []
        presenter = DashboardPresenter(_View(), _Service(), "manager", lambda key, filters=None: calls.append((key, filters)))
        presenter.drill_down("confirmed_count")
        presenter.drill_down("unassigned_count")
        self.assertEqual(calls[0], ("bookings", {"status": "CONFIRMED"}))
        self.assertEqual(calls[1], ("open_events", None))
        customer_calls = []
        DashboardPresenter(_View(), _Service(), "customer", lambda key, filters=None: customer_calls.append((key, filters))).drill_down("pending_count")
        self.assertEqual(customer_calls, [("my_bookings", {"status": "NEW"})])

    def test_customer_booking_presenter_uses_my_bookings(self) -> None:
        view = _View()
        service = _Service()
        BookingsPresenter(view, service, "customer").load()
        self.assertEqual(service.calls, [("mine", 25, 0)])
        self.assertEqual(view.rows[0]["id"], "booking-1")

    def test_manager_details_include_history_but_instructor_details_do_not(self) -> None:
        manager_view, manager_service = _View(), _Service()
        BookingsPresenter(manager_view, manager_service, "manager").select_booking("booking-1")
        self.assertIn(("history", "booking-1"), manager_service.calls)
        self.assertEqual(manager_view.history[0]["event_type"], "הזמנה נוצרה")
        self.assertEqual(manager_view.history[0]["summary"], "נוצרה הזמנה חדשה")

        instructor_view, instructor_service = _View(), _Service()
        BookingsPresenter(instructor_view, instructor_service, "instructor").select_booking("booking-1")
        self.assertNotIn(("history", "booking-1"), instructor_service.calls)
        self.assertEqual(instructor_view.history, [])

    def test_presenters_surface_service_errors_and_finish_loading(self) -> None:
        view, service = _View(), _Service()
        service.fail = True
        OpenEventsPresenter(view, service).load()
        self.assertEqual(view.error, "network error")
        self.assertEqual(view.loading, [True, False])

    def test_create_validation_and_success_refresh(self) -> None:
        with self.assertRaises(FormValidationError):
            validate_create_booking({})
        with self.assertRaises(FormValidationError):
            validate_create_booking({"event_at": "bad", "participant_count": 0, "agreed_price": -1})

        view, service = _View(), _Service()
        refreshed = []
        presenter = BookingsPresenter(view, service, "manager", lambda: refreshed.append(True))
        presenter.create({
            "customer_id": "customer-1", "activity_id": "activity-1",
            "event_at": "2026-09-01T10:00:00+00:00", "participant_count": "20",
            "agreed_price": "1000", "requires_instructor": True,
        })
        self.assertEqual([call[0] for call in service.calls].count("create"), 1)
        self.assertTrue(view.success)
        self.assertEqual(refreshed, [True])
        self.assertEqual(view.loading[0], True)
        self.assertEqual(view.loading[-1], False)

    def test_customer_creation_infers_identity_and_forces_request_fields(self) -> None:
        view, service = _View(), _Service()
        presenter = BookingsPresenter(view, service, "customer")
        presenter.create({
            "activity_id": "activity-1", "event_at": "2027-01-02T10:00:00+00:00",
            "participant_count": 8, "agreed_price": "999", "status": "CONFIRMED",
            "requires_instructor": True,
        })
        payload = next(call[1] for call in service.calls if call[0] == "create")
        self.assertNotIn("customer_id", payload)
        self.assertEqual(payload["agreed_price"], "0")
        self.assertEqual(payload["status"], "NEW")
        self.assertFalse(payload["requires_instructor"])

    def test_manager_creation_routes_optional_instructor_to_existing_assignment_workflow(self) -> None:
        view, service = _View(), _Service()
        assigned = []
        presenter = BookingsPresenter(view, service, "manager")
        presenter.assign_after_creation = lambda booking, instructor_id: assigned.append((booking["id"], instructor_id))
        presenter.create({
            "customer_id": "customer-1", "activity_id": "activity-1",
            "instructor_id": "instructor-1", "event_at": "2027-01-02T10:00:00+00:00",
            "participant_count": 8, "agreed_price": "100",
        })
        payload = next(call[1] for call in service.calls if call[0] == "create")
        self.assertNotIn("instructor_id", payload)
        self.assertTrue(payload["requires_instructor"])
        self.assertEqual(assigned, [("booking-1", "instructor-1")])

    def test_customer_form_loads_activities_without_customer_options(self) -> None:
        view, service = _View(), _Service()
        view.create_values = None
        BookingsPresenter(view, service, "customer").begin_create("activity-1")
        self.assertIn(("options", False), service.calls)

    def test_manager_confirm_and_cancel_use_current_version(self) -> None:
        view, service = _View(), _Service()
        presenter = BookingsPresenter(view, service, "manager")
        presenter.current_booking = {**BOOKING, "version": 3}
        presenter.confirm()
        self.assertIn(("status", "booking-1", "CONFIRMED", 3), service.calls)
        presenter.current_booking = {**BOOKING, "version": 4}
        presenter.cancel()
        self.assertIn(("status", "booking-1", "CANCELLED", 4), service.calls)

    def test_manager_complete_uses_expected_version_and_terminal_states_reject(self) -> None:
        view, service = _View(), _Service()
        presenter = BookingsPresenter(view, service, "manager")
        presenter.current_booking = {**BOOKING, "status": "CONFIRMED", "version": 5}
        presenter.complete()
        self.assertIn(("status", "booking-1", "COMPLETED", 5), service.calls)
        presenter.current_booking = {**BOOKING, "status": "CANCELLED", "version": 6}
        presenter.complete()
        self.assertIn("להשלים", view.error)

    def test_booking_pagination_preserves_filters_and_prevents_negative_offset(self) -> None:
        view, service = _View(), _Service()
        presenter = BookingsPresenter(view, service, "manager")
        presenter.load({"status": "CONFIRMED", "limit": 25, "offset": 0})
        presenter.page(-25, 25)
        self.assertEqual(service.calls[-1][1]["status"], "CONFIRMED")
        self.assertEqual(service.calls[-1][1]["offset"], 0)
        self.assertEqual(view.page["count"], 1)

    def test_customer_status_drilldown_uses_role_scoped_list(self) -> None:
        view, service = _View(), _Service()
        BookingsPresenter(view, service, "customer").load({"status": "CONFIRMED", "offset": 0})
        self.assertEqual(service.calls[0][0], "list")

    def test_cancel_requires_confirmation_and_non_managers_cannot_mutate(self) -> None:
        view, service = _View(), _Service()
        view.cancellation_confirmed = False
        manager = BookingsPresenter(view, service, "manager")
        manager.current_booking = {**BOOKING, "version": 1}
        manager.cancel()
        self.assertNotIn("status", [call[0] for call in service.calls])
        instructor = BookingsPresenter(view, service, "instructor")
        instructor.current_booking = {**BOOKING, "version": 1}
        instructor.confirm()
        instructor.create({})
        self.assertNotIn("status", [call[0] for call in service.calls])
        self.assertNotIn("create", [call[0] for call in service.calls])

    def test_edit_carries_versions_across_granular_commands(self) -> None:
        view, service = _View(), _Service()
        presenter = BookingsPresenter(view, service, "manager")
        presenter.current_booking = {**BOOKING, "version": 7, "customer_id": "c", "activity_id": "a"}
        presenter.update({"participant_count": 25, "notes": "חדש"})
        self.assertIn(("participants", 7), service.calls)
        self.assertIn(("notes", 8), service.calls)

    def test_failure_allows_retry_and_maps_authorization_error(self) -> None:
        view, service = _View(), _Service()
        presenter = BookingsPresenter(view, service, "manager")
        presenter.current_booking = {**BOOKING, "version": 1}
        service.fail = True
        presenter.confirm()
        self.assertEqual(view.error, "network error")
        service.fail = False
        presenter.confirm()
        self.assertEqual([c[0] for c in service.calls].count("status"), 1)
        self.assertEqual(presenter._command_error(ApiError("denied", status_code=403)), "אין הרשאה לבצע פעולה זו.")

    def test_duplicate_submission_is_ignored(self) -> None:
        view, service = _View(), _Service()
        presenter = BookingsPresenter(view, service, "manager")
        presenter.current_booking = {**BOOKING, "version": 1}
        presenter._submitting = True
        presenter.confirm()
        presenter.update({"notes": "חדש"})
        self.assertNotIn("status", [call[0] for call in service.calls])
        self.assertNotIn("notes", [call[0] for call in service.calls])


if __name__ == "__main__":
    unittest.main()
