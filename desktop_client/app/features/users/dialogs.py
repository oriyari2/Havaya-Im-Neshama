from __future__ import annotations

from desktop_client.app.shared.ui.account_dialogs import ChangePasswordDialog
from desktop_client.app.shared.ui.entity_form_dialog import DialogField, DialogSection, EntityFormDialog
from desktop_client.app.shared.validation.dialogs import manager_errors


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
        super().__init__(title="מנהל חדש", description="פרטי המנהל וחשבון ההתחברות", sections=MANAGER_SECTIONS, initial=None, validator=manager_errors, parent=parent)
        self.manager_name = self.fields["manager_name"]
        self.email = self.fields["email"]
        self.password = self.fields["password"]
        self.confirmation = self.fields["password_confirmation"]
        self.save_button.setText("יצירת מנהל")

    def values(self) -> dict:
        return {**super().values(), "role": "manager"}

class EditUserDialog(EntityFormDialog):
    def __init__(self, user: dict, parent=None) -> None:
        initial = {**user, "manager_name": user.get("display_name") or "מנהל"}
        super().__init__(title="עריכת מנהל", description="פרטי המנהל וחשבון ההתחברות", sections=MANAGER_SECTIONS, initial=initial, validator=manager_errors, parent=parent)
        self.email = self.fields["email"]
        self.manager_name = self.fields["manager_name"]
        self.role = self.fields["role"]
        self.save_button.setText("שמירת שינויים")

    def values(self) -> dict:
        return {"email": self.email.text(), "manager_name": self.manager_name.text()}


class ResetPasswordDialog(ChangePasswordDialog):
    def __init__(self, _user: dict | None = None, parent=None) -> None:
        super().__init__(parent)
