from __future__ import annotations

from desktop_client.app.shared.ui.entity_form_dialog import DialogField, DialogSection, EntityFormDialog
from desktop_client.app.shared.validation.dialogs import instructor_errors


INSTRUCTOR_SECTIONS = (
    DialogSection("פרטי מדריך", (
        DialogField("full_name", "שם *"),
        DialogField("city", "עיר"),
        DialogField("phone", "טלפון", mixed_direction=True),
        DialogField("email", "דוא״ל להתחברות *", "דוא״ל", mixed_direction=True, read_only_on_edit=True),
        DialogField("password", "סיסמה *", kind="password", mixed_direction=True, create_only=True),
        DialogField("password_confirmation", "אימות סיסמה *", kind="password", mixed_direction=True, create_only=True),
    )),
    DialogSection("הערות", (DialogField("notes", "הערות", kind="plain"),)),
)


class InstructorDialog(EntityFormDialog):
    def __init__(self, initial=None, parent=None):
        self.is_create = initial is None
        super().__init__(
            title="מדריך חדש" if self.is_create else "עריכת מדריך",
            description="פרטי המדריך וחשבון ההתחברות",
            sections=INSTRUCTOR_SECTIONS,
            initial=initial,
            validator=instructor_errors,
            parent=parent,
        )
        self.password = self.fields.get("password")
        self.password_confirmation = self.fields.get("password_confirmation")
        self.notes = self.fields["notes"]
        self.save_button.setText("יצירת מדריך" if self.is_create else "שמירת שינויים")
