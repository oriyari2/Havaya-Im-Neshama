from __future__ import annotations

from desktop_client.app.views.customer_dialogs import DialogField, DialogSection, EntityFormDialog
from desktop_client.app.presenters.dialog_validation import password_errors


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
