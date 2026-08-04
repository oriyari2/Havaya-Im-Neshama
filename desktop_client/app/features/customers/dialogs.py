from __future__ import annotations

from desktop_client.app.shared.validation.dialogs import customer_errors
from desktop_client.app.shared.ui.entity_form_dialog import DialogField, DialogSection, EntityFormDialog


CUSTOMER_SECTIONS = (
    DialogSection(
        "פרטי לקוח",
        (
            DialogField("name", "שם *"),
            DialogField("customer_type", "סוג"),
            DialogField("city", "עיר"),
            DialogField("address", "כתובת"),
            DialogField("phone", "טלפון", mixed_direction=True),
            DialogField("email", "דוא״ל להתחברות *", "דוא״ל", mixed_direction=True, read_only_on_edit=True),
            DialogField("password", "סיסמה *", kind="password", mixed_direction=True, create_only=True),
            DialogField("password_confirmation", "אימות סיסמה *", kind="password", mixed_direction=True, create_only=True),
        ),
    ),
    DialogSection(
        "פרטי איש קשר",
        (
            DialogField("contact_name", "איש קשר"),
            DialogField("contact_phone", "טלפון איש קשר", mixed_direction=True),
        ),
    ),
    DialogSection("הערות", (DialogField("notes", "הערות", kind="plain"),)),
)


class CustomerDialog(EntityFormDialog):
    def __init__(self, initial=None, parent=None) -> None:
        editing = initial is not None
        super().__init__(
            title="עריכת לקוח" if editing else "לקוח חדש",
            description="פרטי הלקוח ופרטי איש הקשר",
            sections=CUSTOMER_SECTIONS,
            initial=initial,
            validator=customer_errors,
            parent=parent,
        )
        self.password = self.fields.get("password")
        self.password_confirmation = self.fields.get("password_confirmation")
        self.notes = self.fields["notes"]
        self.contact_form = self.section_forms["פרטי איש קשר"]
        self.save_button.setText("שמירת שינויים" if editing else "יצירת לקוח")