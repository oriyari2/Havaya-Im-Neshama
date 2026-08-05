from __future__ import annotations

import sys

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QMessageBox

from desktop_client.app.api.client import ApiClient
from desktop_client.app.features.auth import build_auth_service, build_login_feature
from desktop_client.app.features.contracts import FeatureContext, FeatureServices
from desktop_client.app.features.registry import mount_role_features
from desktop_client.app.features.service_factory import build_feature_services
from desktop_client.app.infrastructure.qt_operations import QtOperationExecutor
from desktop_client.app.models.session import Session
from desktop_client.app.shared.navigation import default_page_for_role, navigation_for_role
from desktop_client.app.shared.ui.shell_view import ShellView
from desktop_client.app.shared.ui.design_tokens import build_neutral_stylesheet

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
        self.auth_service = build_auth_service(self.api_client)
        self.api_client.set_unauthorized_handler(self._handle_unauthorized)
        self.session_expired.connect(self._complete_session_expiry)
        performance_cache = getattr(self.api_client, "performance_cache", None)
        if performance_cache is not None:
            performance_cache.set_refresh_failure_handler(self.cache_refresh_failed.emit)
        self.cache_refresh_failed.connect(self._show_freshness_warning)
        feature_services = build_feature_services(self.api_client)
        # Keep the historical attributes as stable composition hooks for tests and
        # runtime overrides; the concrete service classes now live with their features.
        self.booking_service = feature_services.booking
        self.assignment_service = feature_services.assignment
        self.activity_service = feature_services.activity
        self.ai_chat_service = feature_services.ai_chat
        self.customer_service = feature_services.customer
        self.instructor_service = feature_services.instructor
        self.knowledge_service = feature_services.knowledge
        self.user_service = feature_services.user
        self._presenters: dict[str, object] = {}
        self._active_page: str | None = None
        self._logout_pending = False
        self._pending_workspace_session: Session | None = None
        self._show_login()

    def _show_login(self, message: str | None = None) -> None:
        self._active_page = None
        had_workspace = hasattr(self, "shell")
        if hasattr(self, "_pending_workspace_session"):
            self._pending_workspace_session = None
        feature = build_login_feature(self.auth_service, self._schedule_workspace, self.operation_executor)
        self.login_view = feature.view
        self.login_presenter = feature.presenter
        self.setCentralWidget(self.login_view)
        if had_workspace:
            # Release the previous role workspace after Qt has detached it.
            # This guarantees Dashboard widgets/chart state cannot survive a
            # logout or expired session through MainWindow's shell reference.
            self.shell = None
        if message:
            self.login_view.show_error(message)

    def _schedule_workspace(self, session: Session) -> None:
        """Defer login -> workspace replacement until the current Qt callback returns.

        Login success is delivered through the Qt operation executor. Replacing the
        login view synchronously from that callback can destroy widgets/presenters
        that are still participating in signal delivery on Windows. Queue the actual
        workspace composition for the next event-loop turn instead.
        """
        self._pending_workspace_session = session
        QTimer.singleShot(0, self._complete_workspace_transition)

    def _complete_workspace_transition(self) -> None:
        session = self._pending_workspace_session
        self._pending_workspace_session = None
        if session is None:
            return
        self._show_workspace(session)

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
        # A hidden/unshown application shell must never manufacture a visible
        # top-level dialog (notably during composition, shutdown, or tests).
        if not self.isVisible():
            return
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
        self.shell = ShellView(session.email, self)
        navigation = navigation_for_role(session.role, has_profile=bool(session.customer_id or session.instructor_id))
        self.shell.configure_navigation(navigation)
        self.shell.navigation_requested.connect(self._navigate)
        self.shell.logout_requested.connect(self._logout)

        self._presenters.clear()
        services = FeatureServices(
            booking=self.booking_service,
            assignment=self.assignment_service,
            activity=self.activity_service,
            ai_chat=self.ai_chat_service,
            customer=self.customer_service,
            instructor=self.instructor_service,
            knowledge=self.knowledge_service,
            user=self.user_service,
        )
        context = FeatureContext(
            shell=self.shell,
            session=session,
            executor=self.operation_executor,
            services=services,
            presenters=self._presenters,
            navigate_with_filters=self._navigate_with_filters,
            refresh_booking_related=self._refresh_booking_related,
        )
        mount_role_features(context)

        default_page = default_page_for_role(session.role)
        if default_page is None or default_page not in self._presenters:
            self._active_page = None
        else:
            self._active_page = default_page
            self.shell.show_page(default_page)
            self._presenters[default_page].load()
        self.setCentralWidget(self.shell)

    def _navigate(self, key: str) -> None:
        if key not in self._presenters:
            return
        self._invalidate_page(self._active_page, unless=key)
        self._active_page = key
        self.shell.show_page(key)
        presenter = self._presenters.get(key)
        if presenter is not None:
            reset = getattr(presenter, "reset_to_default", None)
            if reset is not None and key in {"customers", "instructors", "users", "activities", "bookings", "my_bookings"}:
                reset()
            presenter.load()

    def _navigate_with_filters(self, key: str, filters: dict | None = None) -> None:
        if key not in self._presenters:
            return
        self._invalidate_page(self._active_page, unless=key)
        self._active_page = key
        self.shell.show_page(key)
        presenter = self._presenters[key]
        # Dashboard drill-downs are new list intents, not continuations of the
        # previous booking selection. Reset the feature UI first so stale chips
        # or an in-flight detail response cannot reopen a specific booking.
        reset = getattr(presenter, "reset_to_default", None)
        if reset is not None and key in {"customers", "instructors", "users", "activities", "bookings", "my_bookings"}:
            reset()
        presenter.load(filters) if filters is not None else presenter.load()

    def _refresh_booking_related(self)->None:
        for key in ("dashboard", "bookings", "my_bookings"):
            presenter=self._presenters.get(key)
            if presenter is not None:presenter.load()

    def _logout(self) -> None:
        """Schedule logout after the current Qt signal finishes dispatching.

        The logout request originates from a QPushButton that lives inside the
        current ShellView. Replacing the QMainWindow central widget directly
        from that button's ``clicked`` signal can destroy the sender while Qt
        is still dispatching the native mouse event. On Windows this can abort
        the process without a Python traceback. Deferring the central-widget
        swap by one event-loop turn keeps the sender alive until signal
        dispatch has completed.
        """
        if self._logout_pending:
            return
        self._logout_pending = True
        shell = getattr(self, "shell", None)
        logout_button = getattr(shell, "logout_button", None)
        if logout_button is not None:
            logout_button.setEnabled(False)
        QTimer.singleShot(0, self._complete_logout)

    def _complete_logout(self) -> None:
        try:
            self._invalidate_presenter_requests()
            self.operation_executor.invalidate_session()
            self._clear_preview_caches()
            self.auth_service.logout()
            self._presenters.clear()
            self._show_login()
        finally:
            self._logout_pending = False

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

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API
        dialog = getattr(self, "_session_expired_dialog", None)
        if dialog is not None:
            dialog.close()
            dialog.deleteLater()
            self._session_expired_dialog = None

        self._invalidate_presenter_requests()
        self.api_client.set_unauthorized_handler(None)
        cancel_ai_requests = getattr(self.api_client, "cancel_ai_requests", None)
        if cancel_ai_requests is not None:
            cancel_ai_requests()
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
