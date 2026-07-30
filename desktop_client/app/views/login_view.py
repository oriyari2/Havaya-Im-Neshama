from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFormLayout, QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.views.design_tokens import CONTROL_HEIGHT_LARGE, SPACE_3, SPACE_4
from desktop_client.app.views.ui_foundations import FeedbackBanner, configure_mixed_direction


class LoginView(QWidget):
    login_requested = Signal(str, str)

    def __init__(self) -> None:
        super().__init__(); self.setObjectName("applicationRoot"); self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root = QVBoxLayout(self); root.addStretch()
        panel = QFrame(); panel.setObjectName("loginPanel"); panel.setMaximumWidth(440)
        panel_layout = QVBoxLayout(panel); panel_layout.setContentsMargins(SPACE_4, SPACE_4, SPACE_4, SPACE_4); panel_layout.setSpacing(SPACE_3)
        title = QLabel("חוויה עם נשמה"); title.setObjectName("screenTitle"); title.setAccessibleName("חוויה עם נשמה")
        subtitle = QLabel("כניסה למערכת הניהול"); panel_layout.addWidget(title); panel_layout.addWidget(subtitle)
        form = QFormLayout(); form.setVerticalSpacing(SPACE_3)
        self.email_input = QLineEdit(); self.email_input.setAccessibleName("דוא״ל"); self.email_input.setAccessibleDescription("כתובת הדוא״ל להתחברות"); configure_mixed_direction(self.email_input)
        self.password_input = QLineEdit(); self.password_input.setEchoMode(QLineEdit.EchoMode.Password); self.password_input.setAccessibleName("סיסמה"); self.password_input.setAccessibleDescription("סיסמת החשבון")
        form.addRow("דוא״ל", self.email_input); form.addRow("סיסמה", self.password_input); panel_layout.addLayout(form)
        self.feedback = FeedbackBanner(); self.error_label = self.feedback
        self.login_button = QPushButton("כניסה"); self.login_button.setProperty("primary", True); self.login_button.setMinimumHeight(CONTROL_HEIGHT_LARGE); self.login_button.setAccessibleName("כניסה למערכת"); self.login_button.setDefault(True)
        self.login_button.clicked.connect(self._emit_login); self.password_input.returnPressed.connect(self._emit_login)
        panel_layout.addWidget(self.feedback); panel_layout.addWidget(self.login_button); root.addWidget(panel, alignment=Qt.AlignmentFlag.AlignHCenter); root.addStretch()
        QWidget.setTabOrder(self.email_input, self.password_input); QWidget.setTabOrder(self.password_input, self.login_button); self.email_input.setFocus()

    def _emit_login(self) -> None:
        if self.login_button.isEnabled(): self.login_requested.emit(self.email_input.text(), self.password_input.text())

    def set_loading(self, loading: bool) -> None:
        self.login_button.setDisabled(loading); self.email_input.setDisabled(loading); self.password_input.setDisabled(loading); self.login_button.setText("מתחבר…" if loading else "כניסה")

    def render_request_state(self, state: RequestState) -> None:
        if state.phase in {RequestPhase.VALIDATION_ERROR, RequestPhase.CONNECTION_ERROR, RequestPhase.SERVER_ERROR, RequestPhase.AUTHORIZATION_ERROR}:
            self.feedback.render(state)
        elif state.phase in {RequestPhase.IDLE, RequestPhase.LOADING, RequestPhase.SUCCESS}:
            self.feedback.hide()

    def show_error(self, message: str) -> None:
        self.feedback.render(RequestState(RequestPhase.VALIDATION_ERROR, message, "login"))
        if not self.email_input.text().strip(): self.email_input.setFocus()
        elif not self.password_input.text(): self.password_input.setFocus()
