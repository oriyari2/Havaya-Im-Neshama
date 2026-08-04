from __future__ import annotations

import os
import unittest
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QWidget

from desktop_client.app.main import MainWindow
from desktop_client.app.models.session import Session
from desktop_client.app.features.bookings.view import BookingsView
from desktop_client.app.features.bookings.dialogs import BookingFormDialog
from desktop_client.app.features.dashboard.view import DashboardView
from desktop_client.app.shared.ui.shell_view import ShellView


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

    def test_booking_filters_open_as_anchored_popover(self) -> None:
        customer = BookingsView("customer")
        customer.show()
        self.assertFalse(customer.filter_popup.isVisible())
        self.assertFalse(customer.customer_filter.isVisible())
        manager = BookingsView("manager")
        manager.show()
        manager.filter_button.click(); self.assertTrue(manager.filter_popup.isVisible())
        self.assertIs(manager.filter_popup.parentWidget(), manager.list_page)
        self.assertNotIn(manager.filter_popup, QApplication.topLevelWidgets())
        manager.close()

    def test_booking_command_controls_are_manager_only(self) -> None:
        manager = BookingsView("manager")
        manager.show()
        self.assertFalse(manager.command_panel.isHidden())
        self.assertTrue(manager.create_button.isEnabled())
        self.assertFalse(manager.cancel_button.isEnabled())
        manager.set_command_availability("NEW")
        self.assertTrue(manager.edit_button.isEnabled())
        self.assertTrue(manager.confirm_button.isEnabled())
        self.assertFalse(manager.confirm_button.isHidden())
        self.assertTrue(manager.cancel_button.isEnabled())
        manager.set_command_availability("CANCELLED")
        self.assertFalse(manager.edit_button.isEnabled())
        self.assertFalse(manager.confirm_button.isEnabled())
        self.assertFalse(manager.cancel_button.isEnabled())
        customer = BookingsView("customer")
        customer.show()
        self.assertTrue(customer.command_panel.isHidden())
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
        self.assertEqual(manager.assignment_group.objectName(), "detailPanel")
        self.assertIn("מצב השיבוץ", manager.assignment_hint.text())
        unassigned = {"activity_name": "פעילות", "assignment_required": True, "assignments": []}
        manager.show_assignments([unassigned])
        labels = [label.text() for label in manager.assignment_cards.findChildren(QLabel)]
        self.assertIn("ממתין לשיבוץ", labels); self.assertIn("לא שובץ מדריך", labels)
        self.assertIn("שיבוץ מדריך", [button.text() for button in manager.assignment_cards.findChildren(QPushButton)])
        assigned = {**unassigned, "assignments": [{"instructor_name": "מדריך", "instructor_city": None}]}
        manager.show_assignments([assigned])
        self.app.processEvents()
        labels = [label.text() for label in manager.assignment_cards.findChildren(QLabel)]
        buttons = [button.text() for button in manager.assignment_cards.findChildren(QPushButton)]
        self.assertIn("משובץ", labels); self.assertIn("מדריך", labels)
        self.assertIn("החלפת מדריך", buttons); self.assertIn("הסרת שיבוץ", buttons)
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
        self.assertIs(bookings.workspace.table_region.currentWidget(), bookings.workspace.empty_state)
        dashboard = DashboardView()
        dashboard.show_sections("קרובים", [], "", [])
        self.assertIn("אין נתונים", dashboard.state_label.text())

    def test_shell_renders_only_configured_navigation(self) -> None:
        shell = ShellView("user@example.com")
        shell.configure_navigation((("dashboard", "לוח בקרה"), ("my_bookings", "ההזמנות שלי")))
        self.assertEqual(set(shell.navigation_buttons), {"dashboard", "my_bookings"})
        first = shell.stack.currentWidget()
        shell.show_page("forbidden")
        self.assertIs(shell.stack.currentWidget(), first)

    def test_management_navigation_is_module_home_and_shell_never_becomes_top_level(self) -> None:
        class Api:
            def set_unauthorized_handler(self, handler): self.handler = handler
        window = MainWindow(Api()); window.shell = ShellView("manager@example.com", window); page = QWidget(); window.shell.add_page("customers", page)
        presenter = Mock(); window._presenters = {"customers": presenter}; window._active_page = "customers"; window._navigate("customers")
        presenter.reset_to_default.assert_called_once_with(); presenter.load.assert_called_once_with(); self.assertFalse(window.shell.isWindow())

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
            "manager": {"dashboard", "customers", "instructors", "users", "bookings", "activities", "knowledge", "ai_chat"},
            "instructor": {"dashboard", "activities", "bookings", "my_profile", "ai_chat"},
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
            if operation == "logout":
                self.app.processEvents()
            presenter.invalidate_requests.assert_called_once_with(); window.close()

    def test_login_success_defers_workspace_transition_until_callback_returns(self) -> None:
        class Api:
            def set_unauthorized_handler(self, handler): self.handler = handler

        window = MainWindow(Api())
        session = Session("token", "id", "manager@example.com", "manager")
        show_workspace = Mock()
        window._show_workspace = show_workspace

        window.login_presenter.on_authenticated(session)

        # Authentication success must not replace/destroy the login feature
        # while the executor callback is still being dispatched.
        show_workspace.assert_not_called()
        self.assertIs(window._pending_workspace_session, session)

        self.app.processEvents()

        show_workspace.assert_called_once_with(session)
        self.assertIsNone(window._pending_workspace_session)
        window.close()

    def test_logout_button_defers_shell_replacement_until_signal_returns(self) -> None:
        class Api:
            def set_unauthorized_handler(self, handler): self.handler = handler
            def set_access_token(self, token): self.token = token

        api = Api()
        window = MainWindow(api)
        window._show_workspace(Session("token", "id", "manager@example.com", "manager"))
        window.show()
        self.app.processEvents()

        shell = window.shell
        shell.logout_button.click()

        # The ShellView must still exist while QPushButton.clicked is being
        # dispatched; replacing it synchronously is the native-crash hazard.
        self.assertIs(window.centralWidget(), shell)
        self.assertTrue(window._logout_pending)
        self.assertFalse(shell.logout_button.isEnabled())

        self.app.processEvents()

        self.assertIs(window.centralWidget(), window.login_view)
        self.assertFalse(window._logout_pending)
        self.assertIsNone(api.token)
        window.close()


if __name__ == "__main__":
    unittest.main()
