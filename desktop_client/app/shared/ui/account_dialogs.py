from __future__ import annotations

from desktop_client.app.shared.ui.entity_form_dialog import DialogField, DialogSection, EntityFormDialog
from desktop_client.app.shared.validation.dialogs import password_errors


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
            validator=lambda values, _editing: password_errors(values),
            parent=parent,
        )
        self.password = self.fields["password"]
        self.confirmation = self.fields["password_confirmation"]
        self.save_button.setText("שמור")
        self.setMinimumHeight(0)
        self.resize(self.width(), min(self.height(), 470))
