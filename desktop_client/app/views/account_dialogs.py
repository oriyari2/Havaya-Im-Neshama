from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QWidget

from desktop_client.app.views.customer_dialogs import _BaseFormDialog
from desktop_client.app.views.ui_foundations import configure_mixed_direction


class ChangePasswordDialog(_BaseFormDialog):
    """Shared write-only password dialog for every managed account type."""

    def __init__(self, parent=None) -> None:
        super().__init__("שינוי סיסמה", parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setAccessibleName("סיסמה חדשה")
        configure_mixed_direction(self.password)
        self.form.addRow("סיסמה חדשה *", self.password)
        self.confirmation = QLineEdit()
        self.confirmation.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirmation.setAccessibleName("אימות סיסמה")
        configure_mixed_direction(self.confirmation)
        self.form.addRow("אימות סיסמה *", self.confirmation)
        self.save_button.setText("שמור")
        self.cancel_button.setText("ביטול")
        for field in (self.password, self.confirmation):
            field.textChanged.connect(self._update_save_enabled)
        self._update_save_enabled()
        self.password.setFocus()
        QWidget.setTabOrder(self.password, self.confirmation)
        QWidget.setTabOrder(self.confirmation, self.save_button)
        QWidget.setTabOrder(self.save_button, self.cancel_button)

    def _update_save_enabled(self, *_args) -> None:
        password = self.password.text()
        valid = 8 <= len(password) <= 128 and password == password.strip()
        valid = valid and all(character.isprintable() for character in password)
        self.save_button.setEnabled(bool(valid and password == self.confirmation.text()))

    def values(self) -> dict:
        return {"password": self.password.text(), "password_confirmation": self.confirmation.text()}

    def show_error(self, message: str) -> None:
        self.password.clear()
        self.confirmation.clear()
        super().show_error(message)

    def set_submitting(self, value: bool) -> None:
        super().set_submitting(value)
        if not value:
            self._update_save_enabled()
