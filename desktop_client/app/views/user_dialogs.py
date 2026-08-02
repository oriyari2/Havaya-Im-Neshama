from __future__ import annotations

import re

from desktop_client.app.views.account_dialogs import ChangePasswordDialog
from desktop_client.app.views.customer_dialogs import DialogField, DialogSection, EntityFormDialog


EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MANAGER_SECTIONS = (
    DialogSection("פרטי מנהל", (DialogField("manager_name", "שם מנהל *", "שם *"),)),
    DialogSection("חשבון התחברות", (
        DialogField("email", "דוא״ל להתחברות *", "דוא״ל *", mixed_direction=True, read_only_on_edit=True),
        DialogField("role", "תפקיד", kind="static", static_value="מנהל"),
        DialogField("password", "סיסמה *", kind="password", mixed_direction=True, create_only=True),
        DialogField("password_confirmation", "אימות סיסמה *", kind="password", mixed_direction=True, create_only=True),
    )),
)


class CreateUserDialog(EntityFormDialog):
    """Manager-account dialog; generic User creation is not a Desktop concept."""

    def __init__(self, parent=None) -> None:
        super().__init__(title="מנהל חדש", description="פרטי המנהל וחשבון ההתחברות", sections=MANAGER_SECTIONS, initial=None, parent=parent)
        self.manager_name = self.fields["manager_name"]
        self.email = self.fields["email"]
        self.password = self.fields["password"]
        self.confirmation = self.fields["password_confirmation"]
        self.save_button.setText("יצירת מנהל")
        for field in (self.manager_name, self.email, self.password, self.confirmation):
            field.textChanged.connect(self._update_save_enabled)
        self._update_save_enabled()

    def _update_save_enabled(self, *_args) -> None:
        email = self.email.text().strip().lower()
        password = self.password.text()
        valid = len(email) <= 254 and bool(EMAIL.match(email))
        valid = valid and 8 <= len(password) <= 128 and password == password.strip()
        valid = valid and all(character.isprintable() for character in password)
        valid = valid and password == self.confirmation.text()
        self.save_button.setEnabled(bool(valid and self.manager_name.text().strip()))

    def values(self) -> dict:
        return {**super().values(), "role": "manager"}

    def set_submitting(self, value: bool) -> None:
        super().set_submitting(value)
        if not value:
            self._update_save_enabled()


class EditUserDialog(EntityFormDialog):
    def __init__(self, user: dict, parent=None) -> None:
        initial = {**user, "manager_name": user.get("display_name") or "מנהל"}
        super().__init__(title="עריכת מנהל", description="פרטי המנהל וחשבון ההתחברות", sections=MANAGER_SECTIONS, initial=initial, parent=parent)
        self.email = self.fields["email"]
        self.manager_name = self.fields["manager_name"]
        self.role = self.fields["role"]
        self.save_button.setText("שמירת שינויים")

    def values(self) -> dict:
        return {"email": self.email.text(), "manager_name": self.manager_name.text()}


class ResetPasswordDialog(ChangePasswordDialog):
    def __init__(self, _user: dict | None = None, parent=None) -> None:
        super().__init__(parent)
