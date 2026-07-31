from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QLineEdit, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.views.design_tokens import CONTROL_HEIGHT_LARGE, SPACE_2, SPACE_3, SPACE_4, SPACE_6, SPACE_8
from desktop_client.app.views.ui_foundations import FeedbackBanner, configure_mixed_direction


class LoginView(QWidget):
    login_requested = Signal(str, str)

    def __init__(self) -> None:
        super().__init__(); self.setObjectName("applicationRoot"); self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root = QVBoxLayout(self); root.setContentsMargins(SPACE_8, SPACE_8, SPACE_8, SPACE_8); root.addStretch()
        self.panel = QFrame(); self.panel.setObjectName("loginPanel"); self.panel.setMinimumWidth(520); self.panel.setMaximumWidth(560)
        panel_layout = QVBoxLayout(self.panel); panel_layout.setContentsMargins(SPACE_8, SPACE_8, SPACE_8, SPACE_8); panel_layout.setSpacing(0)

        self.welcome_label = QLabel("ברוכים הבאים"); self.welcome_label.setObjectName("screenTitle"); self.welcome_label.setAccessibleName("ברוכים הבאים")
        self.application_name_label = QLabel("חוויה עם נשמה"); self.application_name_label.setObjectName("sectionTitle")
        self.description_label = QLabel("מערכת לניהול חוויות, לקוחות והזמנות"); self.description_label.setWordWrap(True)
        self.instruction_label = QLabel("התחברו כדי להמשיך למערכת הניהול")
        self.instruction_label.setWordWrap(True)
        panel_layout.addWidget(self.welcome_label)
        panel_layout.addSpacing(SPACE_2)
        panel_layout.addWidget(self.application_name_label)
        panel_layout.addSpacing(SPACE_3)
        panel_layout.addWidget(self.description_label)
        panel_layout.addSpacing(SPACE_4)
        panel_layout.addWidget(self.instruction_label)
        panel_layout.addSpacing(SPACE_6)

        self.email_label = QLabel("דוא״ל")
        self.email_input = QLineEdit(); self.email_input.setAccessibleName("דוא״ל"); self.email_input.setAccessibleDescription("כתובת הדוא״ל להתחברות"); configure_mixed_direction(self.email_input)
        self.email_input.setMinimumWidth(440); self.email_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.password_label = QLabel("סיסמה")
        self.password_input = QLineEdit(); self.password_input.setEchoMode(QLineEdit.EchoMode.Password); self.password_input.setAccessibleName("סיסמה"); self.password_input.setAccessibleDescription("סיסמת החשבון")
        self.password_input.setMinimumWidth(440); self.password_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        panel_layout.addWidget(self.email_label)
        panel_layout.addSpacing(SPACE_2)
        panel_layout.addWidget(self.email_input)
        panel_layout.addSpacing(SPACE_4)
        panel_layout.addWidget(self.password_label)
        panel_layout.addSpacing(SPACE_2)
        panel_layout.addWidget(self.password_input)
        panel_layout.addSpacing(SPACE_3)

        self.feedback = FeedbackBanner(); self.error_label = self.feedback
        self.login_button = QPushButton("כניסה"); self.login_button.setProperty("primary", True); self.login_button.setMinimumHeight(CONTROL_HEIGHT_LARGE); self.login_button.setAccessibleName("כניסה למערכת"); self.login_button.setDefault(True)
        self.login_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.login_button.clicked.connect(self._emit_login); self.password_input.returnPressed.connect(self._emit_login)
        panel_layout.addWidget(self.feedback)
        panel_layout.addSpacing(SPACE_4)
        panel_layout.addWidget(self.login_button)
        root.addWidget(self.panel, alignment=Qt.AlignmentFlag.AlignHCenter); root.addStretch()
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
