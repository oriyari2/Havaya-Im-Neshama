from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from desktop_client.app.views.common import StatefulWidget, create_booking_table, populate_booking_table


SUMMARY_LABELS = {
    "upcoming_count": "סה״כ קרובים",
    "pending_count": "חדשים",
    "confirmed_count": "מאושרים",
    "cancelled_count": "מבוטלים",
    "assigned_count": "משובצים",
    "unassigned_count": "דורשים שיבוץ",
}


class DashboardView(StatefulWidget):
    drill_down_requested = Signal(str)
    shortcut_requested = Signal(str)
    create_booking_requested = Signal()

    def __init__(self, role: str = "manager") -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("לוח בקרה")
        title.setObjectName("screenTitle")
        layout.addWidget(title)
        layout.addWidget(self.state_label)

        self.cards_layout = QGridLayout()
        self.card_values: dict[str, QLabel] = {}
        role_fields = {
            "manager": tuple(SUMMARY_LABELS),
            "instructor": ("upcoming_count", "assigned_count"),
            "customer": ("upcoming_count", "pending_count", "confirmed_count", "cancelled_count"),
        }.get(role, ())
        for index, key in enumerate(role_fields):
            label = SUMMARY_LABELS[key]
            card = QGroupBox(label)
            card_layout = QVBoxLayout(card)
            value = QLabel("0")
            value.setObjectName("summaryValue")
            card_layout.addWidget(value)
            if key in {"upcoming_count", "pending_count", "confirmed_count", "cancelled_count", "unassigned_count"}:
                open_button = QPushButton("פתיחה")
                open_button.clicked.connect(lambda _checked=False, target=key: self.drill_down_requested.emit(target))
                card_layout.addWidget(open_button)
            self.cards_layout.addWidget(card, index // 3, index % 3)
            self.card_values[key] = value
        layout.addLayout(self.cards_layout)

        shortcuts = QHBoxLayout()
        targets = {
            "manager": (("create", "יצירת הזמנה"), ("customers", "לקוחות"), ("instructors", "מדריכים"), ("activities", "פעילויות"), ("bookings", "הזמנות"), ("open_events", "אירועים פתוחים")),
            "instructor": (("bookings", "האירועים שלי"), ("open_events", "אירועים פתוחים"), ("activities", "פעילויות"), ("my_profile", "הפרופיל שלי")),
            "customer": (("my_bookings", "ההזמנות שלי"), ("activities", "פעילויות"), ("my_profile", "הפרופיל שלי")),
        }
        for key, label in targets.get(role, ()):
            button = QPushButton(label)
            if key == "create":
                button.clicked.connect(self.create_booking_requested.emit)
            else:
                button.clicked.connect(lambda _checked=False, target=key: self.shortcut_requested.emit(target))
            shortcuts.addWidget(button)
        layout.addLayout(shortcuts)

        self.first_group = QGroupBox()
        first_layout = QVBoxLayout(self.first_group)
        self.first_table = create_booking_table()
        first_layout.addWidget(self.first_table)
        self.second_group = QGroupBox()
        second_layout = QVBoxLayout(self.second_group)
        self.second_table = create_booking_table()
        second_layout.addWidget(self.second_table)
        layout.addWidget(self.first_group)
        layout.addWidget(self.second_group)

    def show_summary(self, summary: dict[str, int]) -> None:
        for key, label in self.card_values.items():
            label.setText(str(summary.get(key, 0)))

    def show_sections(self, first_title: str, first_rows: list[dict[str, str]], second_title: str, second_rows: list[dict[str, str]]) -> None:
        self.state_label.hide()
        self.first_group.setTitle(first_title)
        populate_booking_table(self.first_table, first_rows)
        self.second_group.setTitle(second_title)
        self.second_group.setVisible(bool(second_title))
        populate_booking_table(self.second_table, second_rows)
        if not first_rows and not second_rows:
            self.show_empty("אין נתונים קרובים להצגה.")
