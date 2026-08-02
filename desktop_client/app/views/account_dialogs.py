from __future__ import annotations

from desktop_client.app.views.customer_dialogs import DialogField, DialogSection, EntityFormDialog


PASSWORD_SECTIONS = (
    DialogSection("סיסמה חדשה", (
        DialogField("password", "סיסמה חדשה *", kind="password", mixed_direction=True),
        DialogField("password_confirmation", "אימות סיסמה *", kind="password", mixed_direction=True),
    )),
)


class ChangePasswordDialog(EntityFormDialog):
    """Shared write-only password dialog for every managed account type."""

    def __init__(self, parent=None) -> None:
        super().__init__(
            title="שינוי סיסמה",
            description="הסיסמה נשמרת באופן מאובטח ואינה מוצגת במערכת",
            sections=PASSWORD_SECTIONS,
            initial={},
            parent=parent,
        )
        self.password = self.fields["password"]
        self.confirmation = self.fields["password_confirmation"]
        self.save_button.setText("שמור")
        for field in (self.password, self.confirmation):
            field.textChanged.connect(self._update_save_enabled)
        self._update_save_enabled()

    def _update_save_enabled(self, *_args) -> None:
        password = self.password.text()
        valid = 8 <= len(password) <= 128 and password == password.strip()
        valid = valid and all(character.isprintable() for character in password)
        self.save_button.setEnabled(bool(valid and password == self.confirmation.text()))

    def set_submitting(self, value: bool) -> None:
        super().set_submitting(value)
        if not value:
            self._update_save_enabled()
