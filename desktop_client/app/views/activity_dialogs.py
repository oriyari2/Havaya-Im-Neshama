from __future__ import annotations

from desktop_client.app.views.customer_dialogs import DialogField, DialogSection, EntityFormDialog


ACTIVITY_SECTIONS = (
    DialogSection("פרטי פעילות", (
        DialogField("name", "שם *"),
        DialogField("description", "תיאור", kind="plain"),
        DialogField("target_audience", "קהל יעד"),
        DialogField("season", "עונה"),
        DialogField("tags", "תגיות"),
    )),
    DialogSection("תפעול ותמחור", (
        DialogField("duration_minutes", "משך בדקות", mixed_direction=True),
        DialogField("recommended_capacity", "קיבולת מומלצת", mixed_direction=True),
        DialogField("pricing_rule", "כלל תמחור", kind="plain"),
        DialogField("required_equipment", "ציוד נדרש", kind="plain"),
        DialogField("preparation_notes", "הערות הכנה", kind="plain"),
    )),
)


def activity_errors(values: dict, _editing: bool) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not str(values.get("name") or "").strip(): errors["name"] = "נא להזין שם פעילות."
    for key, label in (("duration_minutes", "משך"), ("recommended_capacity", "קיבולת")):
        raw = str(values.get(key) or "").strip()
        if not raw: continue
        try: number = int(raw)
        except ValueError: errors[key] = f"{label} חייב להיות מספר שלם."; continue
        if number <= 0: errors[key] = f"{label} חייב להיות גדול מאפס."
    return errors


class ActivityDialog(EntityFormDialog):
    def __init__(self, initial: dict | None = None, parent=None) -> None:
        editing = initial is not None; self._active_value = bool((initial or {}).get("is_active", True))
        super().__init__(
            title="עריכת פעילות" if editing else "פעילות חדשה",
            description="פרטי הפעילות, קהל היעד והגדרות התפעול",
            sections=ACTIVITY_SECTIONS, initial=initial, validator=activity_errors, parent=parent,
        )
        self.lines = {key: widget for key, widget in self.fields.items() if hasattr(widget, "text")}
        self.texts = {key: widget for key, widget in self.fields.items() if hasattr(widget, "toPlainText")}
        self.save_button.setText("שמירת שינויים" if editing else "יצירת פעילות")

    def values(self) -> dict:
        return {**super().values(), "is_active": self._active_value}
