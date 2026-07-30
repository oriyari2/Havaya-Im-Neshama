from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QWidget

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.views.ui_foundations import ColumnKind, ColumnPolicy, FeedbackBanner, StatePanel, configure_data_table, set_item_text


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
        self.state_panel = StatePanel(self)
        self.feedback_banner = FeedbackBanner(self)
        self.state_label = QLabel()
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_label.setAccessibleName("מצב תוכן")
        self.state_label.hide()

    def render_request_state(self, state: RequestState) -> None:
        if state.phase in {RequestPhase.SUCCESS, RequestPhase.VALIDATION_ERROR}:
            self.state_panel.hide()
            self.feedback_banner.render(state)
        else:
            self.feedback_banner.hide()
            self.state_panel.render(state)
        if state.phase in {RequestPhase.LOADING, RequestPhase.EMPTY, RequestPhase.CONNECTION_ERROR, RequestPhase.SERVER_ERROR, RequestPhase.AUTHORIZATION_ERROR} and state.message:
            self.state_label.setText(state.message)
            self.state_label.show()
        else:
            self.state_label.hide()

    def set_loading(self, loading: bool) -> None:
        if loading:
            self.render_request_state(RequestState(RequestPhase.LOADING, "טוען נתונים…", "load", blocks_primary_action=True))
        elif self.state_label.text() == "טוען נתונים…":
            self.state_panel.hide()
            self.state_label.hide()

    def show_error(self, message: str) -> None:
        self.render_request_state(RequestState(RequestPhase.SERVER_ERROR, f"שגיאה: {message}", "load"))

    def show_empty(self, message: str) -> None:
        self.render_request_state(RequestState(RequestPhase.EMPTY, message, "load"))


def create_booking_table() -> QTableWidget:
    table = QTableWidget(0, len(BOOKING_COLUMNS))
    table.setHorizontalHeaderLabels([label for _, label in BOOKING_COLUMNS])
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setAlternatingRowColors(True)
    configure_data_table(table, "רשימת הזמנות", (
        ColumnPolicy(ColumnKind.PRIMARY_TEXT),
        ColumnPolicy(ColumnKind.TECHNICAL, 130),
        ColumnPolicy(ColumnKind.COMPACT),
        ColumnPolicy(ColumnKind.SECONDARY_TEXT),
        ColumnPolicy(ColumnKind.SECONDARY_TEXT),
        ColumnPolicy(ColumnKind.COMPACT),
    ))
    return table


def populate_booking_table(table: QTableWidget, rows: list[dict[str, str]]) -> None:
    table.setRowCount(len(rows))
    for row_index, row in enumerate(rows):
        for column_index, (key, _) in enumerate(BOOKING_COLUMNS):
            item = QTableWidgetItem(row.get(key, "—"))
            if column_index == 0:
                item.setData(Qt.ItemDataRole.UserRole, row["id"])
            direction = Qt.LayoutDirection.LeftToRight if key == "event_at" else Qt.LayoutDirection.RightToLeft
            set_item_text(table, row_index, column_index, item, tooltip_direction=direction)
