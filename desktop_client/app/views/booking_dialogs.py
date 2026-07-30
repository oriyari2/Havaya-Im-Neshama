from __future__ import annotations

from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)


class BookingFormDialog(QDialog):
    def __init__(
        self,
        *,
        customers: list[dict] | None = None,
        activities: list[dict] | None = None,
        booking: dict | None = None,
        role: str = "manager",
        preselected_activity_id: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle("יצירת הזמנה" if booking is None else "עריכת הזמנה")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.customer = QComboBox()
        self.activity = QComboBox()

        if booking is None:
            self.customer.addItem("— בחר לקוח —", None)
            self.activity.addItem("— בחר פעילות —", None)

        for item in customers or []:
            self.customer.addItem(
                item.get("name") or str(item["id"]),
                str(item["id"]),
            )

        for item in activities or []:
            self.activity.addItem(
                item.get("name") or str(item["id"]),
                str(item["id"]),
            )

        if preselected_activity_id:
            index = self.activity.findData(str(preselected_activity_id))
            if index >= 0:
                self.activity.setCurrentIndex(index)
                self.activity.setEnabled(False)

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

        self.requires_instructor = QCheckBox("נדרש מדריך")
        self.notes = QTextEdit()

        if booking is None:
            if role == "manager":
                form.addRow("לקוח", self.customer)
            form.addRow("פעילות", self.activity)
            form.addRow("מועד", self.event_at)
            form.addRow("עיר", self.city)
            form.addRow("מקום", self.venue)
            form.addRow("מספר משתתפים", self.participants)
            if role == "manager":
                form.addRow("מחיר מוסכם", self.price)
                form.addRow("", self.requires_instructor)
            form.addRow("הערות", self.notes)
        else:
            form.addRow("מועד", self.event_at)
            form.addRow("עיר", self.city)
            form.addRow("מקום", self.venue)
            form.addRow("מספר משתתפים", self.participants)
            form.addRow("מחיר מוסכם", self.price)
            form.addRow("הערות", self.notes)

            parsed = QDateTime.fromString(
                str(booking.get("event_at", "")),
                Qt.DateFormat.ISODate,
            )

            if parsed.isValid():
                self.event_at.setDateTime(parsed.toLocalTime())

            self.city.setText(booking.get("city") or "")
            self.venue.setText(booking.get("venue") or "")
            self.participants.setValue(int(booking.get("participant_count") or 1))
            self.price.setValue(float(booking.get("agreed_price") or 0))
            self.notes.setPlainText(booking.get("notes") or "")

        layout.addLayout(form)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        self.buttons.button(
            QDialogButtonBox.StandardButton.Save
        ).setText("שליחת בקשה" if role == "customer" else "שמירה")

        self.buttons.button(
            QDialogButtonBox.StandardButton.Cancel
        ).setText("ביטול")

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(self.buttons)

    def accept(self) -> None:
        if self.customer.isVisible():
            if self.customer.currentData() is None:
                QMessageBox.warning(
                    self,
                    "שגיאה",
                    "יש לבחור לקוח.",
                )
                return

        if self.activity.currentData() is None:
            QMessageBox.warning(self, "שגיאה", "יש לבחור פעילות.")
            return

        super().accept()

    def values(self) -> dict[str, object]:
        values: dict[str, object] = {
            "event_at": self.event_at.dateTime().toUTC().toString(
                Qt.DateFormat.ISODate
            ),
            "city": self.city.text(),
            "venue": self.venue.text(),
            "participant_count": self.participants.value(),
            "agreed_price": f"{self.price.value():.2f}",
            "notes": self.notes.toPlainText(),
        }

        if self.activity.currentData() is not None:
            values.update(
                activity_id=self.activity.currentData(),
                status="NEW",
                requires_instructor=self.requires_instructor.isChecked(),
            )
            if self.customer.currentData() is not None:
                values["customer_id"] = self.customer.currentData()

        return values
