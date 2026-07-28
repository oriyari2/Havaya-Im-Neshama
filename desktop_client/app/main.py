from __future__ import annotations

import sys

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QApplication, QMainWindow

from desktop_client.app.api.client import ApiClient
from desktop_client.app.models.session import Session
from desktop_client.app.presenters.bookings_presenter import BookingsPresenter
from desktop_client.app.presenters.booking_assignments_presenter import BookingAssignmentsPresenter
from desktop_client.app.presenters.activities_presenter import ActivitiesPresenter
from desktop_client.app.presenters.dashboard_presenter import DashboardPresenter
from desktop_client.app.presenters.login_presenter import LoginPresenter
from desktop_client.app.presenters.instructors_presenter import InstructorProfilePresenter, InstructorsPresenter
from desktop_client.app.presenters.customers_presenter import CustomerProfilePresenter, CustomersPresenter
from desktop_client.app.presenters.navigation import navigation_for_role
from desktop_client.app.presenters.open_events_presenter import OpenEventsPresenter
from desktop_client.app.services.auth_service import AuthService
from desktop_client.app.services.booking_service import BookingService
from desktop_client.app.services.assignment_service import AssignmentService
from desktop_client.app.services.activity_service import ActivityService
from desktop_client.app.services.customer_service import CustomerService
from desktop_client.app.services.instructor_service import InstructorService
from desktop_client.app.views.bookings_view import BookingsView
from desktop_client.app.views.activities_view import ActivitiesView
from desktop_client.app.views.dashboard_view import DashboardView
from desktop_client.app.views.customer_profile_view import CustomerProfileView
from desktop_client.app.views.customers_view import CustomersView
from desktop_client.app.views.instructors_view import InstructorProfileView, InstructorsView
from desktop_client.app.views.login_view import LoginView
from desktop_client.app.views.open_events_view import OpenEventsView
from desktop_client.app.views.shell_view import ShellView


APP_STYLE = """
QWidget { font-size: 14px; }
QMainWindow { background: #f5f2eb; }
#screenTitle { font-size: 25px; font-weight: 700; color: #45372c; }
#summaryValue { font-size: 28px; font-weight: 700; color: #8b5e3c; }
#sidebar { background: #49392f; color: white; }
#sidebar QLabel { color: white; }
#brand { font-size: 20px; font-weight: 700; }
#errorLabel { color: #a12622; }
QPushButton { padding: 8px 12px; }
QGroupBox { font-weight: 600; margin-top: 10px; }
QTableWidget { background: white; alternate-background-color: #faf7f2; }
"""


class MainWindow(QMainWindow):
    def __init__(self, api_client: ApiClient | None = None) -> None:
        super().__init__()
        self.setWindowTitle("חוויה עם נשמה — מערכת ניהול")
        self.resize(1200, 760)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.api_client = api_client or ApiClient()
        self.auth_service = AuthService(self.api_client)
        self.api_client.set_unauthorized_handler(self._handle_unauthorized)
        self.booking_service = BookingService(self.api_client)
        self.assignment_service = AssignmentService(self.api_client)
        self.activity_service = ActivityService(self.api_client)
        self.customer_service = CustomerService(self.api_client)
        self.instructor_service = InstructorService(self.api_client)
        self._presenters: dict[str, object] = {}
        self._show_login()

    def _show_login(self, message: str | None = None) -> None:
        self.login_view = LoginView()
        self.login_presenter = LoginPresenter(self.login_view, self.auth_service, self._show_workspace)
        self.login_view.login_requested.connect(self.login_presenter.login)
        self.setCentralWidget(self.login_view)
        if message:
            self.login_view.show_error(message)

    def _handle_unauthorized(self) -> None:
        self.auth_service.expire_session()
        QTimer.singleShot(0, self._complete_session_expiry)

    def _complete_session_expiry(self) -> None:
        self._presenters.clear()
        self._show_login("פג תוקף ההתחברות. יש להתחבר מחדש.")

    def _show_workspace(self, session: Session) -> None:
        self.session = session
        self.shell = ShellView(session.email)
        navigation = navigation_for_role(session.role, has_profile=bool(session.customer_id or session.instructor_id))
        self.shell.configure_navigation(navigation)
        self.shell.navigation_requested.connect(self._navigate)
        self.shell.logout_requested.connect(self._logout)

        dashboard_view = DashboardView(session.role)
        dashboard_presenter = DashboardPresenter(dashboard_view, self.booking_service, session.role, self._navigate_with_filters)
        dashboard_view.drill_down_requested.connect(dashboard_presenter.drill_down)
        dashboard_view.shortcut_requested.connect(dashboard_presenter.drill_down)
        self.shell.add_page("dashboard", dashboard_view)
        self._presenters["dashboard"] = dashboard_presenter

        activities_view = ActivitiesView(session.role)
        activities_presenter = ActivitiesPresenter(activities_view, self.activity_service, session.role)
        activities_view.filters_requested.connect(activities_presenter.apply_filters)
        activities_view.page_requested.connect(activities_presenter.page)
        activities_view.activity_selected.connect(activities_presenter.select)
        activities_view.retry_requested.connect(activities_presenter.retry)
        if session.role == "manager":
            activities_view.create_requested.connect(activities_presenter.begin_create)
            activities_view.edit_requested.connect(activities_presenter.begin_edit)
            activities_view.deactivate_requested.connect(activities_presenter.deactivate)
            activities_view.reactivate_requested.connect(activities_presenter.reactivate)
        self.shell.add_page("activities", activities_view)
        self._presenters["activities"] = activities_presenter

        if session.role == "manager":
            instructors_view=InstructorsView(); instructors_presenter=InstructorsPresenter(instructors_view,self.instructor_service)
            instructors_view.filters_requested.connect(instructors_presenter.apply_filters);instructors_view.page_requested.connect(instructors_presenter.page);instructors_view.instructor_selected.connect(instructors_presenter.select);instructors_view.retry_requested.connect(instructors_presenter.retry);instructors_view.create_requested.connect(instructors_presenter.begin_create);instructors_view.edit_requested.connect(instructors_presenter.begin_edit);instructors_view.delete_requested.connect(instructors_presenter.delete)
            self.shell.add_page("instructors",instructors_view);self._presenters["instructors"]=instructors_presenter
        elif session.role == "instructor" and session.instructor_id:
            instructor_profile=InstructorProfileView();instructor_profile_presenter=InstructorProfilePresenter(instructor_profile,self.instructor_service);instructor_profile.retry_requested.connect(instructor_profile_presenter.retry);self.shell.add_page("my_profile",instructor_profile);self._presenters["my_profile"]=instructor_profile_presenter

        if session.role == "manager":
            customers_view = CustomersView()
            customers_presenter = CustomersPresenter(customers_view, self.customer_service)
            customers_view.filters_requested.connect(customers_presenter.apply_filters)
            customers_view.page_requested.connect(customers_presenter.page)
            customers_view.customer_selected.connect(customers_presenter.select)
            customers_view.retry_requested.connect(customers_presenter.retry)
            customers_view.create_requested.connect(customers_presenter.begin_create)
            customers_view.edit_requested.connect(customers_presenter.begin_edit)
            customers_view.delete_requested.connect(customers_presenter.delete)
            customers_view.contact_create_requested.connect(customers_presenter.begin_contact_create)
            customers_view.contact_edit_requested.connect(customers_presenter.begin_contact_edit)
            customers_view.contact_deactivate_requested.connect(customers_presenter.deactivate_contact)
            customers_view.contact_reactivate_requested.connect(customers_presenter.reactivate_contact)
            self.shell.add_page("customers", customers_view)
            self._presenters["customers"] = customers_presenter
        elif session.role == "customer" and session.customer_id:
            profile_view = CustomerProfileView()
            profile_presenter = CustomerProfilePresenter(profile_view, self.customer_service, session.customer_id)
            profile_view.retry_requested.connect(profile_presenter.retry)
            self.shell.add_page("my_profile", profile_view)
            self._presenters["my_profile"] = profile_presenter

        bookings_key = "my_bookings" if session.role == "customer" else "bookings"
        bookings_view = BookingsView(session.role)
        bookings_presenter = BookingsPresenter(
            bookings_view,
            self.booking_service,
            session.role,
            on_changed=self._refresh_booking_related,
            customer_service=self.customer_service,
            activity_service=self.activity_service,
            instructor_service=self.instructor_service,
        )
        bookings_view.filters_requested.connect(bookings_presenter.load)
        bookings_view.booking_selected.connect(bookings_presenter.select_booking)
        bookings_view.page_requested.connect(bookings_presenter.page)
        if session.role == "manager":
            bookings_view.create_requested.connect(bookings_presenter.begin_create)
            bookings_view.edit_requested.connect(bookings_presenter.begin_edit)
            bookings_view.confirm_requested.connect(bookings_presenter.confirm)
            bookings_view.cancel_requested.connect(bookings_presenter.cancel)
            bookings_view.complete_requested.connect(bookings_presenter.complete)
            dashboard_presenter.create_booking = bookings_presenter.begin_create
            dashboard_view.create_booking_requested.connect(dashboard_presenter.create_booking)
        self.shell.add_page(bookings_key, bookings_view)
        self._presenters[bookings_key] = bookings_presenter
        if session.role=="manager":
            assignments_presenter=BookingAssignmentsPresenter(bookings_view,self.assignment_service,self.instructor_service,refresh_booking=bookings_presenter.select_booking,refresh_related=self._refresh_booking_related)
            bookings_view.booking_selected.connect(assignments_presenter.select_booking);bookings_view.assignment_add_requested.connect(assignments_presenter.begin_assign);bookings_view.assignment_remove_requested.connect(assignments_presenter.remove);self._presenters["booking_assignments"]=assignments_presenter

        if session.role in {"manager", "instructor"}:
            open_view = OpenEventsView()
            open_presenter = OpenEventsPresenter(open_view, self.booking_service)
            open_view.event_selected.connect(open_presenter.select)
            open_view.filter_requested.connect(open_presenter.apply_filter)
            open_view.retry_requested.connect(open_presenter.load)
            self.shell.add_page("open_events", open_view)
            self._presenters["open_events"] = open_presenter

        self.setCentralWidget(self.shell)
        self._navigate("dashboard")

    def _navigate(self, key: str) -> None:
        self.shell.show_page(key)
        presenter = self._presenters.get(key)
        if presenter is not None:
            presenter.load()

    def _navigate_with_filters(self, key: str, filters: dict | None = None) -> None:
        if key not in self._presenters:
            return
        self.shell.show_page(key)
        presenter = self._presenters[key]
        presenter.load(filters) if filters is not None else presenter.load()

    def _refresh_booking_related(self)->None:
        for key in ("dashboard","open_events"):
            presenter=self._presenters.get(key)
            if presenter is not None:presenter.load()

    def _logout(self) -> None:
        self.auth_service.logout()
        self._presenters.clear()
        self._show_login()


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
