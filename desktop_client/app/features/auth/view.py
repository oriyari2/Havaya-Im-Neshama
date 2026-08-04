from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from desktop_client.app.resource_paths import asset_path
from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.shared.ui.design_tokens import (
    COLOR_BORDER,
    COLOR_BRAND,
    COLOR_BRAND_HOVER,
    COLOR_BRAND_PRESSED,
    COLOR_DISABLED_BACKGROUND,
    COLOR_DISABLED_TEXT,
    COLOR_SURFACE,
    COLOR_TEXT,
    COLOR_TEXT_MUTED,
    CONTROL_HEIGHT_LARGE,
    SPACE_2,
    SPACE_3,
    SPACE_4,
    SPACE_6,
)
from desktop_client.app.shared.ui.foundations import FeedbackBanner, configure_mixed_direction

_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute


class LoginView(QWidget):
    """Approved branded login layout; authentication behavior remains unchanged."""

    login_requested = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("applicationRoot")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setAutoFillBackground(False)

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.addStretch(1)

        self.panel = QFrame()
        self.panel.setObjectName("loginPanel")
        self.panel.setMinimumWidth(520)
        self.panel.setMaximumWidth(570)
        self.panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(44, 34, 44, 34)
        panel_layout.setSpacing(0)

        logo_label = QLabel()
        logo_label.setObjectName("loginLogo")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setAccessibleName("לוגו חוויה עם נשמה")
        logo_path = asset_path("branding", "logo.png")
        logo = QPixmap(str(logo_path))
        if not logo.isNull():
            logo_label.setPixmap(
                logo.scaled(
                    300,
                    190,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        panel_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        panel_layout.addSpacing(SPACE_2)

        self.welcome_label = QLabel("ברוכים הבאים")
        self.welcome_label.setObjectName("loginWelcomeTitle")
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setAccessibleName("ברוכים הבאים")
        panel_layout.addWidget(self.welcome_label)

        self.application_name_label = QLabel("חוויה עם נשמה")
        self.application_name_label.setObjectName("loginBrandSubtitle")
        self.application_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_layout.addWidget(self.application_name_label)
        panel_layout.addSpacing(SPACE_3)

        self.description_label = QLabel("מערכת לניהול לקוחות, פעילויות והזמנות")
        self.description_label.setObjectName("loginDescription")
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description_label.setWordWrap(True)
        panel_layout.addWidget(self.description_label)
        panel_layout.addSpacing(SPACE_6)

        self.instruction_label = QLabel("התחברו כדי להמשיך למערכת הניהול")
        self.instruction_label.hide()

        self.email_label = QLabel("דוא״ל")
        self.email_label.setObjectName("loginFieldLabel")
        self.email_label.setAlignment(_RIGHT)
        self.email_input = QLineEdit()
        self.email_input.setObjectName("loginEmailInput")
        self.email_input.setAccessibleName("דוא״ל")
        self.email_input.setAccessibleDescription("כתובת הדוא״ל להתחברות")
        configure_mixed_direction(self.email_input)
        self.email_input.setAlignment(_RIGHT)
        self.email_input.setMinimumHeight(CONTROL_HEIGHT_LARGE)
        self.email_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.password_label = QLabel("סיסמה")
        self.password_label.setObjectName("loginFieldLabel")
        self.password_label.setAlignment(_RIGHT)
        self.password_input = QLineEdit()
        self.password_input.setObjectName("loginPasswordInput")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setAccessibleName("סיסמה")
        self.password_input.setAccessibleDescription("סיסמת החשבון")
        self.password_input.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.password_input.setAlignment(_RIGHT)
        self.password_input.setMinimumHeight(CONTROL_HEIGHT_LARGE)
        self.password_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        panel_layout.addWidget(self.email_label)
        panel_layout.addSpacing(SPACE_2)
        panel_layout.addWidget(self.email_input)
        panel_layout.addSpacing(SPACE_4)
        panel_layout.addWidget(self.password_label)
        panel_layout.addSpacing(SPACE_2)
        panel_layout.addWidget(self.password_input)
        panel_layout.addSpacing(SPACE_3)

        self.feedback = FeedbackBanner()
        self.error_label = self.feedback
        panel_layout.addWidget(self.feedback)
        panel_layout.addSpacing(SPACE_3)

        self.login_button = QPushButton("כניסה")
        self.login_button.setObjectName("loginPrimaryButton")
        self.login_button.setProperty("primary", True)
        self.login_button.setMinimumHeight(48)
        self.login_button.setAccessibleName("כניסה למערכת")
        self.login_button.setDefault(True)
        self.login_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.login_button.clicked.connect(self._emit_login)
        self.password_input.returnPressed.connect(self._emit_login)
        self._apply_primary_style()
        panel_layout.addWidget(self.login_button)

        root.addWidget(self.panel, alignment=Qt.AlignmentFlag.AlignHCenter)
        root.addStretch(1)

        QWidget.setTabOrder(self.email_input, self.password_input)
        QWidget.setTabOrder(self.password_input, self.login_button)
        self.email_input.setFocus()

    def _apply_primary_style(self) -> None:
        self.login_button.setStyleSheet(
            f"""
            QPushButton {{
                color: #FFFFFF;
                background: {COLOR_BRAND};
                border: 1px solid {COLOR_BRAND};
                border-radius: 8px;
                font-size: 16px;
                font-weight: 700;
            }}
            QPushButton:hover {{ color: #FFFFFF; background: {COLOR_BRAND_HOVER}; border-color: {COLOR_BRAND_HOVER}; }}
            QPushButton:pressed {{ color: #FFFFFF; background: {COLOR_BRAND_PRESSED}; border-color: {COLOR_BRAND_PRESSED}; }}
            QPushButton:disabled {{ color: {COLOR_DISABLED_TEXT}; background: {COLOR_DISABLED_BACKGROUND}; border-color: {COLOR_BORDER}; }}
            """
        )

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # The approved login uses large, visible pastel organic shapes around the
        # central card. Draw them locally so the background scales with the window
        # and does not depend on another image asset.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(231, 242, 207, 205))
        painter.drawEllipse(QRectF(-w * 0.13, h * 0.17, w * 0.31, h * 0.58))
        painter.setBrush(QColor(216, 239, 246, 205))
        painter.drawEllipse(QRectF(-w * 0.09, h * 0.72, w * 0.37, h * 0.40))
        painter.setBrush(QColor(251, 229, 219, 205))
        painter.drawEllipse(QRectF(w * 0.72, h * 0.70, w * 0.36, h * 0.42))
        painter.setBrush(QColor(255, 241, 211, 190))
        painter.drawEllipse(QRectF(w * 0.78, -h * 0.13, w * 0.31, h * 0.41))

        # Soft decorative leaves, echoing the approved mock without introducing
        # any text or interaction into the background.
        def leaf(cx: float, cy: float, rw: float, rh: float, angle: float, color: QColor) -> None:
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(angle)
            painter.setBrush(color)
            painter.drawEllipse(QRectF(-rw / 2, -rh / 2, rw, rh))
            painter.restore()

        leaf(w * 0.17, h * 0.20, w * 0.030, h * 0.074, -32, QColor(215, 232, 236, 175))
        leaf(w * 0.145, h * 0.185, w * 0.027, h * 0.068, 30, QColor(215, 232, 236, 155))
        leaf(w * 0.82, h * 0.59, w * 0.027, h * 0.070, -28, QColor(215, 232, 236, 165))
        leaf(w * 0.845, h * 0.57, w * 0.024, h * 0.062, 28, QColor(215, 232, 236, 145))
        leaf(w * 0.10, h * 0.69, w * 0.029, h * 0.070, -25, QColor(204, 233, 231, 170))
        leaf(w * 0.125, h * 0.67, w * 0.025, h * 0.060, 28, QColor(204, 233, 231, 145))

    def _emit_login(self) -> None:
        if self.login_button.isEnabled():
            self.login_requested.emit(self.email_input.text(), self.password_input.text())

    def set_loading(self, loading: bool) -> None:
        self.login_button.setDisabled(loading)
        self.email_input.setDisabled(loading)
        self.password_input.setDisabled(loading)
        self.login_button.setText("מתחבר…" if loading else "כניסה")

    def render_request_state(self, state: RequestState) -> None:
        if state.phase in {
            RequestPhase.VALIDATION_ERROR,
            RequestPhase.CONNECTION_ERROR,
            RequestPhase.SERVER_ERROR,
            RequestPhase.AUTHORIZATION_ERROR,
        }:
            self.feedback.render(state)
        elif state.phase in {RequestPhase.IDLE, RequestPhase.LOADING, RequestPhase.SUCCESS}:
            self.feedback.hide()

    def show_error(self, message: str) -> None:
        self.feedback.render(RequestState(RequestPhase.VALIDATION_ERROR, message, "login"))
        if not self.email_input.text().strip():
            self.email_input.setFocus()
        elif not self.password_input.text():
            self.password_input.setFocus()
