from __future__ import annotations

from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import QCheckBox, QDateTimeEdit, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLabel, QLineEdit, QScrollArea, QSpinBox, QTextEdit, QVBoxLayout, QWidget

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.views.entity_selector import SearchableEntitySelector
from desktop_client.app.views.ui_foundations import FeedbackBanner


class BookingFormDialog(QDialog):
    def __init__(self, *, customers=None, activities=None, instructors=None, booking=None, role="manager", preselected_activity_id=None, parent=None) -> None:
        super().__init__(parent); self.booking = booking; self.role = role; editing = booking is not None
        title = "עריכת הזמנה" if editing else "יצירת הזמנה"; self.setWindowTitle(title); self.setObjectName("task20Dialog"); self.setLayoutDirection(Qt.LayoutDirection.RightToLeft); self.setMinimumWidth(760); self.setMaximumWidth(860)
        root = QVBoxLayout(self); self.heading_label = QLabel(title); self.heading_label.setObjectName("screenTitle"); self.heading_label.setAlignment(Qt.AlignmentFlag.AlignRight); root.addWidget(self.heading_label)
        subtitle = QLabel("פרטי ההזמנה והקשרים העסקיים"); subtitle.setAlignment(Qt.AlignmentFlag.AlignRight); root.addWidget(subtitle)
        body = QWidget(); form = QFormLayout(body); form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute); form.setFormAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight); form.setHorizontalSpacing(16); form.setVerticalSpacing(10); self.form = form
        self.customer_selector = SearchableEntitySelector("בחירת לקוח"); self.customer_selector.set_items(customers or [], label_key="name", context_keys=("email", "phone", "city"), active_only=True)
        self.activity_selector = SearchableEntitySelector("בחירת פעילות"); self.activity_selector.set_items(activities or [], label_key="name", context_keys=("target_audience", "season"), active_only=True)
        self.instructor_selector = SearchableEntitySelector("בחירת מדריך"); self.instructor_selector.set_items(instructors or [], label_key="full_name", context_keys=("city", "email"), active_only=True)
        self.customer, self.activity, self.instructor = self.customer_selector.combo, self.activity_selector.combo, self.instructor_selector.combo
        self.activity_selector.selection_changed.connect(lambda _id: self.instructor_selector.clear_selection())
        self.event_at = QDateTimeEdit(QDateTime.currentDateTime().addDays(1)); self.event_at.setCalendarPopup(True); self.event_at.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.city = QLineEdit(); self.venue = QLineEdit(); self.participants = QSpinBox(); self.participants.setRange(1, 100000); self.price = QDoubleSpinBox(); self.price.setRange(0, 100000000); self.price.setDecimals(2); self.requires_instructor = QCheckBox("נדרש מדריך"); self.notes = QTextEdit(); self.notes.setMaximumHeight(100)
        self.field_errors = {}
        def add(label, widget, key):
            form.addRow(label, widget); label_widget = form.labelForField(widget); label_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute); error = QLabel(); error.setObjectName("fieldError"); error.setAlignment(Qt.AlignmentFlag.AlignRight); error.hide(); form.addRow(error); self.field_errors[key] = error
        if not editing:
            if role == "manager": add("לקוח *", self.customer_selector, "customer_id")
            add("פעילות *", self.activity_selector, "activity_id")
        add("מועד *", self.event_at, "event_at"); add("עיר", self.city, "city"); add("מקום", self.venue, "venue"); add("מספר משתתפים *", self.participants, "participant_count")
        if role == "manager": add("מחיר מוסכם", self.price, "agreed_price")
        if not editing and role == "manager": form.addRow("", self.requires_instructor); add("מדריך (אופציונלי)", self.instructor_selector, "instructor_id")
        add("הערות", self.notes, "notes")
        if editing:
            parsed = QDateTime.fromString(str(booking.get("event_at", "")), Qt.DateFormat.ISODate)
            if parsed.isValid(): self.event_at.setDateTime(parsed.toLocalTime())
            self.city.setText(booking.get("city") or ""); self.venue.setText(booking.get("venue") or ""); self.participants.setValue(int(booking.get("participant_count") or 1)); self.price.setValue(float(booking.get("agreed_price") or 0)); self.notes.setPlainText(booking.get("notes") or "")
        if preselected_activity_id: self.activity_selector.select_id(str(preselected_activity_id)); self.activity.setEnabled(False)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QScrollArea.Shape.NoFrame); scroll.setWidget(body); scroll.setFixedHeight(min(500, body.sizeHint().height())); root.addWidget(scroll)
        self.feedback = FeedbackBanner(); root.addWidget(self.feedback); self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel); self.save_button = self.buttons.button(QDialogButtonBox.StandardButton.Save); self.save_button.setText("שליחת בקשה" if role == "customer" else "שמירה"); self.save_button.setProperty("buttonRole", "managementPrimary"); self.cancel_button = self.buttons.button(QDialogButtonBox.StandardButton.Cancel); self.cancel_button.setText("ביטול"); self.buttons.accepted.connect(self.accept); self.buttons.rejected.connect(self.reject); root.addWidget(self.buttons)

    def accept(self) -> None:
        errors = {}
        if self.booking is None and self.role == "manager" and not self.customer_selector.selected_id(): errors["customer_id"] = "יש לבחור לקוח."
        if self.booking is None and not self.activity_selector.selected_id(): errors["activity_id"] = "יש לבחור פעילות."
        for key, label in self.field_errors.items(): label.setText(errors.get(key, "")); label.setVisible(key in errors)
        if errors:
            self.feedback.render_temporary(RequestState(RequestPhase.VALIDATION_ERROR, "לא ניתן לשמור. יש לתקן את השדות המסומנים.", "booking-dialog")); (self.customer_selector if "customer_id" in errors else self.activity_selector).setFocus(); return
        super().accept()

    def values(self) -> dict[str, object]:
        values = {"event_at": self.event_at.dateTime().toUTC().toString(Qt.DateFormat.ISODate), "city": self.city.text(), "venue": self.venue.text(), "participant_count": self.participants.value(), "agreed_price": f"{self.price.value():.2f}", "notes": self.notes.toPlainText()}
        activity_id = self.activity_selector.selected_id()
        if activity_id: values.update(activity_id=activity_id, status="NEW", requires_instructor=self.requires_instructor.isChecked())
        if self.customer_selector.selected_id(): values["customer_id"] = self.customer_selector.selected_id()
        if self.instructor_selector.selected_id(): values["instructor_id"] = self.instructor_selector.selected_id()
        return values
