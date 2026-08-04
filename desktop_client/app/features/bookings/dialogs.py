from __future__ import annotations

from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.shared.ui.design_tokens import (
    COLOR_BACKGROUND,
    COLOR_BORDER,
    COLOR_BRAND,
    COLOR_BRAND_HOVER,
    COLOR_BRAND_PRESSED,
    COLOR_DISABLED_BACKGROUND,
    COLOR_DISABLED_TEXT,
    COLOR_SURFACE,
    COLOR_SURFACE_ALT,
    COLOR_TEXT,
    CONTROL_HEIGHT_LARGE,
    SPACE_1,
    SPACE_2,
    SPACE_3,
)
from desktop_client.app.shared.ui.entity_selector import SearchableEntitySelector
from desktop_client.app.shared.ui.foundations import FeedbackBanner

_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute


class BookingFormDialog(QDialog):
    """Booking form with the same deterministic RTL field geometry as customer forms."""

    def __init__(
        self,
        *,
        customers=None,
        activities=None,
        instructors=None,
        booking=None,
        role="manager",
        preselected_activity_id=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.booking = booking
        self.role = role
        editing = booking is not None
        title = "עריכת הזמנה" if editing else "יצירת הזמנה"
        self.setWindowTitle(title)
        self.setObjectName("task20Dialog")
        self.setProperty("bookingFormDialog", True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumWidth(700)
        self.setMaximumWidth(840)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(SPACE_2)

        self.heading_label = QLabel(title)
        self.heading_label.setObjectName("screenTitle")
        self.heading_label.setProperty("dialogHeading", True)
        self.heading_label.setAlignment(_RIGHT)
        root.addWidget(self.heading_label)

        subtitle = QLabel("פרטי ההזמנה והקשרים העסקיים")
        subtitle.setProperty("dialogLead", True)
        subtitle.setAlignment(_RIGHT)
        root.addWidget(subtitle)

        hint = QLabel("* שדה חובה")
        hint.setProperty("dialogHint", True)
        hint.setAlignment(_RIGHT)
        root.addWidget(hint)

        body = QWidget()
        body.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, SPACE_1, 0, SPACE_1)
        body_layout.setSpacing(SPACE_3)

        section = QFrame()
        section.setProperty("dialogSection", True)
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(18, 14, 18, 16)
        section_layout.setSpacing(SPACE_2)
        section_title = QLabel("פרטי הזמנה")
        section_title.setProperty("dialogSectionTitle", True)
        section_title.setAlignment(_RIGHT)
        section_layout.addWidget(section_title)

        grid_host = QWidget()
        grid_host.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(12)
        grid.setColumnStretch(0, 1)
        grid.setColumnMinimumWidth(1, 156)
        self.form = grid
        section_layout.addWidget(grid_host)
        body_layout.addWidget(section)

        self.customer_selector = SearchableEntitySelector("בחירת לקוח")
        self.customer_selector.set_items(customers or [], label_key="name", context_keys=("email", "phone", "city"), active_only=True)
        self.activity_selector = SearchableEntitySelector("בחירת פעילות")
        self.activity_selector.set_items(activities or [], label_key="name", context_keys=("target_audience", "season"), active_only=True)
        self.instructor_selector = SearchableEntitySelector("בחירת מדריך")
        self.instructor_selector.set_items(instructors or [], label_key="full_name", context_keys=("city", "email"), active_only=True)
        self.customer, self.activity, self.instructor = self.customer_selector.combo, self.activity_selector.combo, self.instructor_selector.combo
        self.activity_selector.selection_changed.connect(lambda _id: self.instructor_selector.clear_selection())

        self.event_at = QDateTimeEdit(QDateTime.currentDateTime().addDays(1))
        self.event_at.setCalendarPopup(True)
        self.event_at.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.city = QLineEdit()
        self.venue = QLineEdit()
        self.participants = QSpinBox()
        self.participants.setRange(1, 100000)
        self.price = QDoubleSpinBox()
        self.price.setRange(0, 100000000)
        self.price.setDecimals(2)
        self.requires_instructor = QCheckBox("כן")
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(120)

        for field in (self.city, self.venue, self.participants, self.price, self.event_at):
            field.setAlignment(_RIGHT)
        self.notes.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.requires_instructor.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        for selector in (self.customer_selector, self.activity_selector, self.instructor_selector):
            selector.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            selector.combo.setMinimumHeight(CONTROL_HEIGHT_LARGE)
            selector.combo.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            selector.combo.lineEdit().setAlignment(_RIGHT)

        self.field_errors: dict[str, QLabel] = {}
        row_index = 0

        def add(label: str, widget: QWidget, key: str) -> None:
            nonlocal row_index
            label_widget = QLabel(label)
            label_widget.setProperty("dialogFieldLabel", True)
            label_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            label_widget.setAlignment(_RIGHT)
            label_widget.setFixedWidth(156)

            field_host = QWidget()
            field_host.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            field_layout = QVBoxLayout(field_host)
            field_layout.setContentsMargins(0, 0, 0, 0)
            field_layout.setSpacing(4)
            field_layout.addWidget(widget)

            error = QLabel()
            error.setObjectName("fieldError")
            error.setAlignment(_RIGHT)
            error.setWordWrap(True)
            error.hide()
            field_layout.addWidget(error)
            self.field_errors[key] = error

            grid.addWidget(field_host, row_index, 0)
            grid.addWidget(label_widget, row_index, 1, alignment=_RIGHT)
            row_index += 1

        if not editing:
            if role == "manager":
                add("לקוח *", self.customer_selector, "customer_id")
            add("פעילות *", self.activity_selector, "activity_id")
        add("מועד *", self.event_at, "event_at")
        add("עיר", self.city, "city")
        add("מקום", self.venue, "venue")
        add("מספר משתתפים *", self.participants, "participant_count")
        if role == "manager":
            add("מחיר מוסכם", self.price, "agreed_price")
        if not editing and role == "manager":
            add("נדרש מדריך", self.requires_instructor, "requires_instructor")
            add("מדריך (אופציונלי)", self.instructor_selector, "instructor_id")
        add("הערות", self.notes, "notes")

        if editing:
            parsed = QDateTime.fromString(str(booking.get("event_at", "")), Qt.DateFormat.ISODate)
            if parsed.isValid():
                self.event_at.setDateTime(parsed.toLocalTime())
            self.city.setText(booking.get("city") or "")
            self.venue.setText(booking.get("venue") or "")
            self.participants.setValue(int(booking.get("participant_count") or 1))
            self.price.setValue(float(booking.get("agreed_price") or 0))
            self.notes.setPlainText(booking.get("notes") or "")

        self.notes.selectAll()
        self.notes.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.notes.moveCursor(self.notes.textCursor().MoveOperation.End)
        if preselected_activity_id:
            self.activity_selector.select_id(str(preselected_activity_id))
            self.activity.setEnabled(False)

        scroll = QScrollArea()
        scroll.setObjectName("dialogScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        self.feedback = FeedbackBanner()
        root.addWidget(self.feedback)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.setObjectName("dialogButtonBox")
        self.buttons.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.save_button = self.buttons.button(QDialogButtonBox.StandardButton.Save)
        self.save_button.setText("שליחת בקשה" if role == "customer" else "שמירה")
        self.save_button.setObjectName("customerDialogPrimary")
        self.cancel_button = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        self.cancel_button.setText("ביטול")
        for button in (self.save_button, self.cancel_button):
            button.setMinimumWidth(140)
            button.setMinimumHeight(CONTROL_HEIGHT_LARGE)
        self._apply_button_styles()
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons, alignment=Qt.AlignmentFlag.AlignLeft)

        screen = self.screen()
        available_height = screen.availableGeometry().height() if screen is not None else 800
        self.resize(760, min(730, max(580, available_height - 140)))

    def _apply_button_styles(self) -> None:
        self.save_button.setStyleSheet(
            f"""
            QPushButton {{ color: #FFFFFF; background: {COLOR_BRAND}; border: 1px solid {COLOR_BRAND}; border-radius: 8px; padding: 0 18px; font-weight: 600; }}
            QPushButton:hover {{ color: #FFFFFF; background: {COLOR_BRAND_HOVER}; border-color: {COLOR_BRAND_HOVER}; }}
            QPushButton:pressed {{ color: #FFFFFF; background: {COLOR_BRAND_PRESSED}; border-color: {COLOR_BRAND_PRESSED}; }}
            QPushButton:disabled {{ color: {COLOR_DISABLED_TEXT}; background: {COLOR_DISABLED_BACKGROUND}; border-color: {COLOR_BORDER}; }}
            """
        )
        self.cancel_button.setStyleSheet(
            f"""
            QPushButton {{ color: {COLOR_TEXT}; background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: 8px; padding: 0 18px; font-weight: 600; }}
            QPushButton:hover {{ color: {COLOR_TEXT}; background: {COLOR_SURFACE_ALT}; border-color: {COLOR_BRAND}; }}
            QPushButton:pressed {{ color: {COLOR_TEXT}; background: {COLOR_BACKGROUND}; }}
            """
        )

    def accept(self) -> None:
        errors = {}
        if self.booking is None and self.role == "manager" and not self.customer_selector.selected_id():
            errors["customer_id"] = "יש לבחור לקוח."
        if self.booking is None and not self.activity_selector.selected_id():
            errors["activity_id"] = "יש לבחור פעילות."
        for key, label in self.field_errors.items():
            label.setText(errors.get(key, ""))
            label.setVisible(key in errors)
        if errors:
            self.feedback.render_temporary(
                RequestState(
                    RequestPhase.VALIDATION_ERROR,
                    "לא ניתן לשמור. יש לתקן את השדות המסומנים.",
                    "booking-dialog",
                )
            )
            (self.customer_selector if "customer_id" in errors else self.activity_selector).setFocus()
            return
        super().accept()

    def values(self) -> dict[str, object]:
        values = {
            "event_at": self.event_at.dateTime().toUTC().toString(Qt.DateFormat.ISODate),
            "city": self.city.text(),
            "venue": self.venue.text(),
            "participant_count": self.participants.value(),
            "agreed_price": f"{self.price.value():.2f}",
            "notes": self.notes.toPlainText(),
        }
        activity_id = self.activity_selector.selected_id()
        if activity_id:
            values.update(activity_id=activity_id, status="NEW", requires_instructor=self.requires_instructor.isChecked())
        if self.customer_selector.selected_id():
            values["customer_id"] = self.customer_selector.selected_id()
        if self.instructor_selector.selected_id():
            values["instructor_id"] = self.instructor_selector.selected_id()
        return values
