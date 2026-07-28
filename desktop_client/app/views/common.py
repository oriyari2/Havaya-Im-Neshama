from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QTableWidget, QTableWidgetItem, QWidget


BOOKING_COLUMNS = (
    ("activity", "פעילות"),
    ("event_at", "מועד"),
    ("status", "סטטוס"),
    ("city", "עיר"),
    ("venue", "מקום"),
    ("participants", "משתתפים"),
)


class StatefulWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.state_label = QLabel()
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_label.hide()

    def set_loading(self, loading: bool) -> None:
        if loading:
            self.state_label.setText("טוען נתונים…")
            self.state_label.show()
            QApplication.processEvents()
        elif self.state_label.text() == "טוען נתונים…":
            self.state_label.hide()

    def show_error(self, message: str) -> None:
        self.state_label.setText(f"שגיאה: {message}")
        self.state_label.show()

    def show_empty(self, message: str) -> None:
        self.state_label.setText(message)
        self.state_label.show()


def create_booking_table() -> QTableWidget:
    table = QTableWidget(0, len(BOOKING_COLUMNS))
    table.setHorizontalHeaderLabels([label for _, label in BOOKING_COLUMNS])
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setAlternatingRowColors(True)
    table.horizontalHeader().setStretchLastSection(True)
    return table


def populate_booking_table(table: QTableWidget, rows: list[dict[str, str]]) -> None:
    table.setRowCount(len(rows))
    for row_index, row in enumerate(rows):
        for column_index, (key, _) in enumerate(BOOKING_COLUMNS):
            item = QTableWidgetItem(row.get(key, "—"))
            if column_index == 0:
                item.setData(Qt.ItemDataRole.UserRole, row["id"])
            table.setItem(row_index, column_index, item)
    table.resizeColumnsToContents()
