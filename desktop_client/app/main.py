from __future__ import annotations

import sys

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QMessageBox

from desktop_client.app.api.client import ApiClient
from desktop_client.app.infrastructure.qt_operations import QtOperationExecutor
from desktop_client.app.models.session import Session
from desktop_client.app.presenters.bookings_presenter import BookingsPresenter
from desktop_client.app.presenters.booking_assignments_presenter import BookingAssignmentsPresenter
from desktop_client.app.presenters.activities_presenter import ActivitiesPresenter
from desktop_client.app.presenters.ai_chat_presenter import AIChatPresenter
from desktop_client.app.presenters.dashboard_presenter import DashboardPresenter
from desktop_client.app.presenters.login_presenter import LoginPresenter
from desktop_client.app.presenters.instructors_presenter import InstructorProfilePresenter, InstructorsPresenter
from desktop_client.app.presenters.knowledge_presenter import KnowledgeManagementPresenter
from desktop_client.app.presenters.customers_presenter import CustomerProfilePresenter, CustomersPresenter
from desktop_client.app.presenters.navigation import navigation_for_role
from desktop_client.app.presenters.open_events_presenter import OpenEventsPresenter
from desktop_client.app.presenters.users_presenter import UsersPresenter
from desktop_client.app.services.auth_service import AuthService
from desktop_client.app.services.booking_service import BookingService
from desktop_client.app.services.assignment_service import AssignmentService
from desktop_client.app.services.activity_service import ActivityService
from desktop_client.app.services.ai_chat_service import AIChatService
from desktop_client.app.services.customer_service import CustomerService
from desktop_client.app.services.instructor_service import InstructorService
from desktop_client.app.services.knowledge_service import KnowledgeService
from desktop_client.app.services.user_service import UserService
from desktop_client.app.views.bookings_view import BookingsView
from desktop_client.app.views.activities_view import ActivitiesView
from desktop_client.app.views.ai_chat_view import AIChatView
from desktop_client.app.views.dashboard_view import DashboardView
from desktop_client.app.views.customer_profile_view import CustomerProfileView
from desktop_client.app.views.customers_view import CustomersView
from desktop_client.app.views.instructors_view import InstructorProfileView, InstructorsView
from desktop_client.app.views.knowledge_view import KnowledgeManagementView
from desktop_client.app.views.login_view import LoginView
from desktop_client.app.views.open_events_view import OpenEventsView
from desktop_client.app.views.shell_view import ShellView
from desktop_client.app.views.users_view import UsersView
from desktop_client.app.views.design_tokens import build_neutral_stylesheet


APP_STYLE = build_neutral_stylesheet()


class MainWindow(QMainWindow):
    session_expired = Signal()
    cache_refresh_failed = Signal(str)

    def __init__(self, api_client: ApiClient | None = None) -> None:
        super().__init__()
        self.setWindowTitle("חוויה עם נשמה — מערכת ניהול")
        self.resize(1200, 760)
        self.setMinimumSize(1024, 640)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.api_client = api_client or ApiClient()
        self.operation_executor = QtOperationExecutor(parent=self)
        self.auth_service = AuthService(self.api_client)
        self.api_client.set_unauthorized_handler(self._handle_unauthorized)
        self.session_expired.connect(self._complete_session_expiry)
        performance_cache = getattr(self.api_client, "performance_cache", None)
        if performance_cache is not None:
            performance_cache.set_refresh_failure_handler(self.cache_refresh_failed.emit)
        self.cache_refresh_failed.connect(self._show_freshness_warning)
        self.booking_service = BookingService(self.api_client)
        self.assignment_service = AssignmentService(self.api_client)
        self.activity_service = ActivityService(self.api_client)
        self.ai_chat_service = AIChatService(self.api_client)
        self.customer_service = CustomerService(self.api_client)
        self.instructor_service = InstructorService(self.api_client)
        self.knowledge_service = KnowledgeService(self.api_client)
        self.user_service = UserService(self.api_client)
        self._presenters: dict[str, object] = {}
        self._active_page: str | None = None
        self._show_login()

    def _show_login(self, message: str | None = None) -> None:
        self._active_page = None
        self.login_view = LoginView()
        self.login_presenter = LoginPresenter(self.login_view, self.auth_service, self._show_workspace, self.operation_executor)
        self.login_view.login_requested.connect(self.login_presenter.login)
        self.setCentralWidget(self.login_view)
        if message:
            self.login_view.show_error(message)

    def _handle_unauthorized(self) -> None:
        self.auth_service.expire_session()
        self.session_expired.emit()

    def _complete_session_expiry(self) -> None:
        self._invalidate_presenter_requests()
        self.operation_executor.invalidate_session()
        self._clear_preview_caches()
        self._presenters.clear()
        self._show_login("פג תוקף ההתחברות. יש להתחבר מחדש.")
        self._show_session_expired_dialog()

    def _show_session_expired_dialog(self) -> None:
        dialog = QMessageBox(QMessageBox.Icon.Information, "פג תוקף ההתחברות", "לשמירה על אבטחת החשבון, יש להתחבר מחדש כדי להמשיך.", QMessageBox.StandardButton.NoButton, self)
        dialog.setObjectName("sessionExpiredDialog")
        dialog.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.button(QMessageBox.StandardButton.Ok).setText("להתחברות")
        for label in dialog.findChildren(QLabel):
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            label.setWordWrap(True)
        self._session_expired_dialog = dialog
        dialog.open()

    def _show_freshness_warning(self, _resource: str) -> None:
        presenter = self._presenters.get(self._active_page or "")
        view = getattr(presenter, "view", None)
        show_error = getattr(view, "show_error", None)
        if show_error is not None:
            show_error("המידע המוצג זמין, אך לא ניתן היה לוודא שהוא מעודכן. אפשר לנסות לרענן שוב.")

    def _show_workspace(self, session: Session) -> None:
        self.session = session
        self.shell = ShellView(session.email)
        navigation = navigation_for_role(session.role, has_profile=bool(session.customer_id or session.instructor_id))
        self.shell.configure_navigation(navigation)
        self.shell.navigation_requested.connect(self._navigate)
        self.shell.logout_requested.connect(self._logout)

        dashboard_view = DashboardView(session.role)
        dashboard_presenter = DashboardPresenter(dashboard_view, self.booking_service, session.role, self._navigate_with_filters, executor=self.operation_executor)
        dashboard_view.drill_down_requested.connect(dashboard_presenter.drill_down)
        dashboard_view.shortcut_requested.connect(dashboard_presenter.drill_down)
        self.shell.add_page("dashboard", dashboard_view)
        self._presenters["dashboard"] = dashboard_presenter

        activities_view = ActivitiesView(session.role)
        activities_presenter = ActivitiesPresenter(activities_view, self.activity_service, session.role, executor=self.operation_executor)
        activities_view.filters_requested.connect(activities_presenter.apply_filters)
        activities_view.page_requested.connect(activities_presenter.page)
        activities_view.activity_selected.connect(activities_presenter.select)
        activities_view.retry_requested.connect(activities_presenter.retry)
        activities_view.image_selected.connect(activities_presenter.select_image)
        activities_view.preview_retry_requested.connect(activities_presenter.retry_preview)
        if session.role == "manager":
            activities_view.create_requested.connect(activities_presenter.begin_create)
            activities_view.edit_requested.connect(activities_presenter.begin_edit)
            activities_view.deactivate_requested.connect(activities_presenter.deactivate)
            activities_view.reactivate_requested.connect(activities_presenter.reactivate)
            activities_view.upload_image_requested.connect(activities_presenter.upload_image)
            activities_view.delete_image_requested.connect(activities_presenter.delete_image)
        self.shell.add_page("activities", activities_view)
        self._presenters["activities"] = activities_presenter

        if session.role == "manager":
            instructors_view=InstructorsView(); instructors_presenter=InstructorsPresenter(instructors_view,self.instructor_service,self.user_service,executor=self.operation_executor)
            instructors_view.filters_requested.connect(instructors_presenter.apply_filters);instructors_view.page_requested.connect(instructors_presenter.page);instructors_view.instructor_selected.connect(instructors_presenter.select);instructors_view.retry_requested.connect(instructors_presenter.retry);instructors_view.create_requested.connect(instructors_presenter.begin_create);instructors_view.edit_requested.connect(instructors_presenter.begin_edit);instructors_view.delete_requested.connect(instructors_presenter.delete)
            self.shell.add_page("instructors",instructors_view);self._presenters["instructors"]=instructors_presenter
        elif session.role == "instructor" and session.instructor_id:
            instructor_profile=InstructorProfileView();instructor_profile_presenter=InstructorProfilePresenter(instructor_profile,self.instructor_service,executor=self.operation_executor);instructor_profile.retry_requested.connect(instructor_profile_presenter.retry);self.shell.add_page("my_profile",instructor_profile);self._presenters["my_profile"]=instructor_profile_presenter

        if session.role == "manager":
            users_view = UsersView()
            users_presenter = UsersPresenter(users_view, self.user_service, current_user_id=session.user_id, session_role=session.role, executor=self.operation_executor)
            users_view.filters_requested.connect(users_presenter.apply_filters)
            users_view.page_requested.connect(users_presenter.page)
            users_view.user_selected.connect(users_presenter.select)
            users_view.retry_requested.connect(users_presenter.retry)
            users_view.create_requested.connect(users_presenter.begin_create)
            users_view.edit_requested.connect(users_presenter.begin_edit)
            users_view.activate_requested.connect(users_presenter.activate)
            users_view.deactivate_requested.connect(users_presenter.deactivate)
            users_view.reset_password_requested.connect(users_presenter.begin_reset_password)
            self.shell.add_page("users", users_view)
            self._presenters["users"] = users_presenter

            customers_view = CustomersView()
            customers_presenter = CustomersPresenter(customers_view, self.customer_service, self.user_service, executor=self.operation_executor)
            customers_view.filters_requested.connect(customers_presenter.apply_filters)
            customers_view.page_requested.connect(customers_presenter.page)
            customers_view.customer_selected.connect(customers_presenter.select)
            customers_view.retry_requested.connect(customers_presenter.retry)
            customers_view.create_requested.connect(customers_presenter.begin_create)
            customers_view.edit_requested.connect(customers_presenter.begin_edit)
            customers_view.delete_requested.connect(customers_presenter.delete)
            self.shell.add_page("customers", customers_view)
            self._presenters["customers"] = customers_presenter

            knowledge_view = KnowledgeManagementView()
            knowledge_presenter = KnowledgeManagementPresenter(knowledge_view, self.knowledge_service, self.operation_executor)
            knowledge_view.save_requested.connect(knowledge_presenter.save)
            knowledge_view.replace_requested.connect(knowledge_presenter.replace)
            knowledge_view.delete_requested.connect(knowledge_presenter.delete)
            knowledge_view.source_selected.connect(knowledge_presenter.select_source)
            knowledge_view.retry_requested.connect(knowledge_presenter.retry)
            self.shell.add_page("knowledge", knowledge_view)
            self._presenters["knowledge"] = knowledge_presenter
        elif session.role == "customer" and session.customer_id:
            profile_view = CustomerProfileView()
            profile_presenter = CustomerProfilePresenter(profile_view, self.customer_service, session.customer_id, self.operation_executor)
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
            executor=self.operation_executor,
        )
        bookings_view.filters_requested.connect(bookings_presenter.load)
        bookings_view.booking_selected.connect(bookings_presenter.select_booking)
        bookings_view.page_requested.connect(bookings_presenter.page)
        if session.role in {"manager", "customer"}:
            bookings_view.create_requested.connect(bookings_presenter.begin_create)
            activities_view.booking_requested.connect(bookings_presenter.begin_create)
        if session.role == "manager":
            bookings_view.edit_requested.connect(bookings_presenter.begin_edit)
            bookings_view.confirm_requested.connect(bookings_presenter.confirm)
            bookings_view.cancel_requested.connect(bookings_presenter.cancel)
            bookings_view.complete_requested.connect(bookings_presenter.complete)
            dashboard_presenter.create_booking = bookings_presenter.begin_create
            dashboard_view.create_booking_requested.connect(dashboard_presenter.create_booking)
        self.shell.add_page(bookings_key, bookings_view)
        self._presenters[bookings_key] = bookings_presenter
        if session.role=="manager":
            assignments_presenter=BookingAssignmentsPresenter(bookings_view,self.assignment_service,self.instructor_service,refresh_booking=bookings_presenter.select_booking,refresh_related=self._refresh_booking_related,confirm_after_assignment=bookings_presenter.confirm_after_assignment,executor=self.operation_executor)
            bookings_presenter.assign_after_creation=assignments_presenter.assign_after_creation
            bookings_view.booking_selected.connect(assignments_presenter.select_booking);bookings_view.assignment_add_requested.connect(assignments_presenter.begin_assign);bookings_view.assignment_add_and_confirm_requested.connect(assignments_presenter.begin_assign_and_confirm);bookings_view.assignment_remove_requested.connect(assignments_presenter.remove);self._presenters["booking_assignments"]=assignments_presenter

        if session.role in {"manager", "instructor"}:
            open_view = OpenEventsView()
            open_presenter = OpenEventsPresenter(open_view, self.booking_service, self.operation_executor)
            open_view.event_selected.connect(open_presenter.select)
            open_view.filter_requested.connect(open_presenter.apply_filter)
            open_view.retry_requested.connect(open_presenter.retry)
            self.shell.add_page("open_events", open_view)
            self._presenters["open_events"] = open_presenter

        ai_chat_view = AIChatView()
        ai_chat_presenter = AIChatPresenter(ai_chat_view, self.ai_chat_service, self.operation_executor)
        ai_chat_view.message_submitted.connect(ai_chat_presenter.send_message)
        self.shell.add_page("ai_chat", ai_chat_view)
        self._presenters["ai_chat"] = ai_chat_presenter

        self.setCentralWidget(self.shell)
        self._navigate("dashboard")

    def _navigate(self, key: str) -> None:
        self._invalidate_page(self._active_page, unless=key)
        self._active_page = key
        self.shell.show_page(key)
        presenter = self._presenters.get(key)
        if presenter is not None:
            presenter.load()

    def _navigate_with_filters(self, key: str, filters: dict | None = None) -> None:
        if key not in self._presenters:
            return
        self._invalidate_page(self._active_page, unless=key)
        self._active_page = key
        self.shell.show_page(key)
        presenter = self._presenters[key]
        presenter.load(filters) if filters is not None else presenter.load()

    def _refresh_booking_related(self)->None:
        for key in ("dashboard","open_events"):
            presenter=self._presenters.get(key)
            if presenter is not None:presenter.load()

    def _logout(self) -> None:
        self._invalidate_presenter_requests()
        self.operation_executor.invalidate_session()
        self._clear_preview_caches()
        self.auth_service.logout()
        self._presenters.clear()
        self._show_login()

    def _invalidate_page(self, key: str | None, *, unless: str) -> None:
        if key is None or key == unless:
            return
        presenter = self._presenters.get(key)
        invalidate = getattr(presenter, "invalidate_requests", None)
        if invalidate is not None:
            invalidate()

    def _clear_preview_caches(self) -> None:
        for presenter in self._presenters.values():
            clear_cache = getattr(presenter, "clear_preview_cache", None)
            if clear_cache is not None:
                clear_cache()

    def _invalidate_presenter_requests(self) -> None:
        for presenter in self._presenters.values():
            invalidate = getattr(presenter, "invalidate_requests", None)
            if invalidate is not None:
                invalidate()

    def closeEvent(self, event) -> None:
        self._invalidate_presenter_requests()
        self.api_client.set_unauthorized_handler(None)
        performance_cache = getattr(self.api_client, "performance_cache", None)
        if performance_cache is not None:
            performance_cache.set_refresh_failure_handler(None)
            performance_cache.shutdown()
        self.operation_executor.shutdown()
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
