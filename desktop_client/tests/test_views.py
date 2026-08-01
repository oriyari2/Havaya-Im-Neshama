from __future__ import annotations

import os
import unittest
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication

from desktop_client.app.main import MainWindow
from desktop_client.app.models.session import Session
from desktop_client.app.views.bookings_view import BookingsView
from desktop_client.app.views.booking_dialogs import BookingFormDialog
from desktop_client.app.views.dashboard_view import DashboardView
from desktop_client.app.views.open_events_view import OpenEventsView
from desktop_client.app.views.shell_view import ShellView


class ViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def tearDown(self) -> None:
        for widget in list(QApplication.topLevelWidgets()):
            widget.close()
            widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def test_manager_has_related_filters_and_customer_has_status_only(self) -> None:
        customer = BookingsView("customer")
        customer.show()
        self.assertTrue(customer.filter_panel.isVisible())
        self.assertFalse(customer.customer_filter.isVisible())
        manager = BookingsView("manager")
        manager.show()
        self.assertTrue(manager.filter_panel.isVisible())
        manager.close()

    def test_booking_command_controls_are_manager_only(self) -> None:
        manager = BookingsView("manager")
        manager.show()
        self.assertTrue(manager.command_panel.isVisible())
        self.assertTrue(manager.create_button.isEnabled())
        self.assertFalse(manager.cancel_button.isEnabled())
        manager.set_command_availability("NEW")
        self.assertTrue(manager.edit_button.isEnabled())
        self.assertTrue(manager.confirm_button.isEnabled())
        self.assertTrue(manager.confirm_button.isHidden())
        self.assertTrue(manager.cancel_button.isEnabled())
        manager.set_command_availability("CANCELLED")
        self.assertFalse(manager.edit_button.isEnabled())
        self.assertFalse(manager.confirm_button.isEnabled())
        self.assertFalse(manager.cancel_button.isEnabled())
        customer = BookingsView("customer")
        customer.show()
        self.assertTrue(customer.command_panel.isVisible())
        self.assertTrue(customer.create_button.isVisible())
        self.assertFalse(customer.edit_button.isVisible())
        instructor = BookingsView("instructor")
        instructor.show()
        self.assertFalse(instructor.command_panel.isVisible())
        manager.close()
        customer.close()
        instructor.close()

    def test_manager_assignment_action_is_clear_and_only_in_booking_details(self) -> None:
        manager = BookingsView("manager")
        customer = BookingsView("customer")
        instructor = BookingsView("instructor")
        self.assertEqual(manager.assignment_group.title(), "שיבוץ מדריך להזמנה")
        self.assertEqual(manager.assign_button.text(), "שיבוץ מדריך לפעילות שנבחרה")
        self.assertIn("בחרו פעילות", manager.assignment_hint.text())
        self.assertFalse(manager.assign_button.isEnabled())
        manager.set_command_availability("NEW")
        self.assertFalse(manager.assign_and_confirm_button.isHidden())
        unassigned = {"activity_name": "פעילות", "assignment_required": True, "assignments": []}
        manager.show_assignments([unassigned])
        manager.assignment_tree.setCurrentItem(manager.assignment_tree.topLevelItem(0))
        self.assertEqual(manager.assign_and_confirm_button.text(), "שיבוץ מדריך ואישור הזמנה")
        assigned = {**unassigned, "assignments": [{"instructor_name": "מדריך", "instructor_city": None}]}
        manager.show_assignments([assigned])
        manager.assignment_tree.setCurrentItem(manager.assignment_tree.topLevelItem(0))
        self.assertEqual(manager.assign_and_confirm_button.text(), "אישור הזמנה")
        manager.set_command_availability("CONFIRMED")
        self.assertTrue(manager.assign_and_confirm_button.isHidden())
        self.assertFalse(manager.assignment_group.isHidden())
        self.assertTrue(customer.assignment_group.isHidden())
        self.assertTrue(instructor.assignment_group.isHidden())

    def test_customer_booking_dialog_hides_identity_and_admin_fields(self) -> None:
        dialog = BookingFormDialog(
            activities=[{"id": "activity-1", "name": "פעילות"}],
            role="customer",
            preselected_activity_id="activity-1",
        )
        dialog.show()
        self.assertFalse(dialog.customer.isVisible())
        self.assertFalse(dialog.price.isVisible())
        self.assertFalse(dialog.requires_instructor.isVisible())
        self.assertEqual(dialog.activity.currentData(), "activity-1")
        self.assertFalse(dialog.activity.isEnabled())
        self.assertNotIn("customer_id", dialog.values())
        dialog.close()

    def test_booking_dialog_returns_backend_shaped_values(self) -> None:
        dialog = BookingFormDialog(
            customers=[{"id": "customer-1", "name": "לקוח"}],
            activities=[{"id": "activity-1", "name": "פעילות"}],
            instructors=[{"id": "instructor-1", "full_name": "מדריך"}],
        )
        dialog.customer.setCurrentIndex(1)
        dialog.activity.setCurrentIndex(1)
        dialog.participants.setValue(12)
        dialog.price.setValue(450.5)
        dialog.instructor.setCurrentIndex(1)
        values = dialog.values()
        self.assertEqual(values["customer_id"], "customer-1")
        self.assertEqual(values["activity_id"], "activity-1")
        self.assertEqual(values["participant_count"], 12)
        self.assertEqual(values["agreed_price"], "450.50")
        self.assertEqual(values["status"], "NEW")
        self.assertEqual(values["instructor_id"], "instructor-1")

    def test_empty_states_are_visible(self) -> None:
        bookings = BookingsView("customer")
        bookings.show_bookings([])
        self.assertTrue(bookings.state_label.isVisibleTo(bookings))
        dashboard = DashboardView()
        dashboard.show_sections("קרובים", [], "", [])
        self.assertIn("אין נתונים", dashboard.state_label.text())
        events = OpenEventsView()
        events.show_events([])
        self.assertIn("אין כרגע", events.state_label.text())

    def test_shell_renders_only_configured_navigation(self) -> None:
        shell = ShellView("user@example.com")
        shell.configure_navigation((("dashboard", "לוח בקרה"), ("my_bookings", "ההזמנות שלי")))
        self.assertEqual(set(shell.navigation_buttons), {"dashboard", "my_bookings"})
        first = shell.stack.currentWidget()
        shell.show_page("forbidden")
        self.assertIs(shell.stack.currentWidget(), first)

    def test_main_window_builds_expected_pages_for_every_role(self) -> None:
        class Api:
            def set_unauthorized_handler(self, handler):
                self.handler = handler

            def set_access_token(self, token):
                pass

        class Service:
            def dashboard(self):
                return {}

            def list_bookings(self, filters=None):
                return {"items": [], "count": 0}

            def my_bookings(self, *, limit=50, offset=0):
                return {"items": [], "count": 0}

            def open_events(self):
                return []

            def list_customers(self, filters=None):
                return {"items": [], "count": 0}

            def customer(self, customer_id):
                return {"id": customer_id, "name": "Customer", "is_active": True, "created_at": "", "updated_at": "", "contacts": []}

            def list_activities(self, filters=None):
                return {"items": [], "count": 0}

            def list_instructors(self, filters=None):
                return {"items": [], "count": 0}

            def list_sources(self):
                return []

            def list_users(self, filters=None):
                return {"items": [], "count": 0}

            def my_profile(self):
                return {"id": "instructor-id", "full_name": "Instructor", "is_active": True, "created_at": "", "updated_at": ""}

        expected_pages = {
            "manager": {"dashboard", "customers", "instructors", "users", "bookings", "activities", "open_events", "knowledge", "ai_chat"},
            "instructor": {"dashboard", "activities", "bookings", "open_events", "my_profile", "ai_chat"},
            "customer": {"dashboard", "activities", "my_bookings", "my_profile", "ai_chat"},
        }
        for role, pages in expected_pages.items():
            window = MainWindow(Api())
            window.booking_service = Service()
            window.customer_service = Service()
            window.activity_service = Service()
            window.instructor_service = Service()
            window.knowledge_service = Service()
            window.user_service = Service()
            customer_id = "customer-id" if role == "customer" else None
            instructor_id = "instructor-id" if role == "instructor" else None
            window._show_workspace(Session("token", "id", f"{role}@example.com", role, customer_id=customer_id, instructor_id=instructor_id))
            self.assertEqual(set(window.shell.pages), pages)
            self.assertEqual(set(window.shell.navigation_buttons), pages)
            for page in pages:
                window._navigate(page)
                self.assertIs(window.shell.stack.currentWidget(), window.shell.pages[page])
            window.close()

    def test_session_expiry_returns_workspace_to_login(self) -> None:
        class Api:
            def set_unauthorized_handler(self, handler):
                self.handler = handler

            def set_access_token(self, token):
                self.token = token

        api = Api()
        window = MainWindow(api)
        window._show_workspace(Session("token", "id", "manager@example.com", "manager"))
        api.handler()
        self.app.processEvents()
        self.assertIs(window.centralWidget(), window.login_view)
        self.assertTrue(window.login_view.error_label.isVisibleTo(window.login_view))
        self.assertIsNone(api.token)
        window.close()

    def test_logout_and_session_expiry_invalidate_presenter_requests(self) -> None:
        class Api:
            def set_unauthorized_handler(self, handler): self.handler = handler
            def set_access_token(self, token): self.token = token
        for operation in ("logout", "expiry"):
            window = MainWindow(Api()); presenter = Mock(spec=["invalidate_requests"]); window._presenters = {"customers": presenter}
            window._logout() if operation == "logout" else window._complete_session_expiry()
            presenter.invalidate_requests.assert_called_once_with(); window.close()


if __name__ == "__main__":
    unittest.main()
