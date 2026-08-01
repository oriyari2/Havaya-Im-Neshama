from __future__ import annotations

import re

from PySide6.QtWidgets import QLabel, QLineEdit, QWidget

from desktop_client.app.views.customer_dialogs import _BaseFormDialog
from desktop_client.app.views.account_dialogs import ChangePasswordDialog
from desktop_client.app.views.ui_foundations import configure_mixed_direction


ROLE_LABELS = {"manager": "מנהל", "customer": "לקוח", "instructor": "מדריך"}
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class CreateUserDialog(_BaseFormDialog):
    """Manager-account dialog; generic User creation is not a Desktop concept."""

    def __init__(self, parent=None) -> None:
        super().__init__("מנהל חדש", parent)
        self.fields = {}
        self.email = QLineEdit()
        self.email.setAccessibleName("אימייל להתחברות")
        configure_mixed_direction(self.email)
        self.form.addRow("אימייל להתחברות *", self.email)
        self.fields["email"] = self.email
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setAccessibleName("סיסמה")
        configure_mixed_direction(self.password)
        self.form.addRow("סיסמה *", self.password)
        self.fields["password"] = self.password
        self.confirmation = QLineEdit()
        self.confirmation.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirmation.setAccessibleName("אימות סיסמה")
        configure_mixed_direction(self.confirmation)
        self.form.addRow("אימות סיסמה *", self.confirmation)
        self.fields["password_confirmation"] = self.confirmation
        self.manager_name = QLineEdit()
        self.manager_name.setAccessibleName("שם מנהל")
        self.form.addRow("שם מנהל *", self.manager_name)
        self.fields["manager_name"] = self.manager_name
        for field in self.fields.values():
            field.textChanged.connect(self._update_save_enabled)
        self._update_save_enabled()
        self.email.setFocus()
        order = [self.email, self.password, self.confirmation, self.manager_name, self.save_button, self.cancel_button]
        for first, second in zip(order, order[1:]):
            QWidget.setTabOrder(first, second)

    def _update_save_enabled(self, *_args) -> None:
        email = self.email.text().strip().lower()
        password = self.password.text()
        valid = len(email) <= 254 and bool(EMAIL.match(email))
        valid = valid and 8 <= len(password) <= 128 and password == password.strip()
        valid = valid and all(character.isprintable() for character in password)
        valid = valid and password == self.confirmation.text()
        self.save_button.setEnabled(bool(valid and self.manager_name.text().strip()))

    def values(self) -> dict:
        return {
            "email": self.email.text(),
            "password": self.password.text(),
            "password_confirmation": self.confirmation.text(),
            "role": "manager",
            "manager_name": self.manager_name.text(),
        }

    def show_error(self, message: str) -> None:
        self.password.clear()
        self.confirmation.clear()
        super().show_error(message)

    def set_submitting(self, value: bool) -> None:
        super().set_submitting(value)
        if not value:
            self._update_save_enabled()


class EditUserDialog(_BaseFormDialog):
    def __init__(self, user: dict, parent=None) -> None:
        super().__init__("עריכת מנהל", parent)
        self.fields = {}
        self.email = QLineEdit(str(user["email"]))
        self.email.setAccessibleName("דוא״ל")
        self.email.setReadOnly(True)
        self.email.setAccessibleDescription("דוא״ל ההתחברות קבוע ואינו ניתן לעריכה")
        configure_mixed_direction(self.email)
        self.form.addRow("דוא״ל *", self.email)
        self.fields["email"] = self.email
        self.role = QLabel(ROLE_LABELS["manager"])
        self.form.addRow("תפקיד", self.role)
        self.manager_name = QLineEdit(str(user.get("display_name") or "מנהל"))
        self.manager_name.setAccessibleName("שם מנהל")
        self.form.addRow("שם *", self.manager_name)
        self.fields["manager_name"] = self.manager_name
        self.manager_name.setFocus()

    def values(self) -> dict:
        return {"email": self.email.text(), "manager_name": self.manager_name.text()}


class ResetPasswordDialog(ChangePasswordDialog):
    def __init__(self, _user: dict | None = None, parent=None) -> None:
        super().__init__(parent)
