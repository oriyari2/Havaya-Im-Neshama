from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QApplication, QFormLayout, QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget


class LoginView(QWidget):
    login_requested = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root = QVBoxLayout(self)
        root.addStretch()

        panel = QFrame()
        panel.setMaximumWidth(440)
        panel_layout = QVBoxLayout(panel)
        title = QLabel("חוויה עם נשמה")
        title.setObjectName("screenTitle")
        subtitle = QLabel("כניסה למערכת הניהול")
        panel_layout.addWidget(title)
        panel_layout.addWidget(subtitle)

        form = QFormLayout()
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("דוא״ל", self.email_input)
        form.addRow("סיסמה", self.password_input)
        panel_layout.addLayout(form)

        self.error_label = QLabel()
        self.error_label.setObjectName("errorLabel")
        self.error_label.hide()
        self.login_button = QPushButton("כניסה")
        self.login_button.clicked.connect(self._emit_login)
        self.password_input.returnPressed.connect(self._emit_login)
        panel_layout.addWidget(self.error_label)
        panel_layout.addWidget(self.login_button)
        root.addWidget(panel, alignment=Qt.AlignmentFlag.AlignHCenter)
        root.addStretch()

    def _emit_login(self) -> None:
        self.login_requested.emit(self.email_input.text(), self.password_input.text())

    def set_loading(self, loading: bool) -> None:
        self.login_button.setDisabled(loading)
        self.login_button.setText("מתחבר…" if loading else "כניסה")
        if loading:
            QApplication.processEvents()

    def show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.show()
