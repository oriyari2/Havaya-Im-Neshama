from __future__ import annotations

from PySide6.QtCore import Qt,Signal
from PySide6.QtWidgets import QFormLayout,QGroupBox,QHBoxLayout,QLabel,QLineEdit,QPushButton,QVBoxLayout

from desktop_client.app.views.common import StatefulWidget, create_booking_table, populate_booking_table


class OpenEventsView(StatefulWidget):
    event_selected=Signal(str)
    filter_requested=Signal(str)
    retry_requested=Signal()
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("אירועים פתוחים לשיבוץ")
        title.setObjectName("screenTitle")
        layout.addWidget(title)
        layout.addWidget(self.state_label)
        bar=QHBoxLayout();self.search=QLineEdit();self.search.setPlaceholderText("חיפוש בפעילות, עיר או מקום");search_button=QPushButton("חיפוש");retry_button=QPushButton("רענון");search_button.clicked.connect(lambda:self.filter_requested.emit(self.search.text()));retry_button.clicked.connect(self.retry_requested.emit);bar.addWidget(self.search);bar.addWidget(search_button);bar.addWidget(retry_button);layout.addLayout(bar)
        self.table = create_booking_table()
        self.table.itemSelectionChanged.connect(self._select)
        layout.addWidget(self.table)
        group=QGroupBox("פרטי אירוע פתוח");self.details=QFormLayout(group);layout.addWidget(group)

    def show_events(self, rows: list[dict[str, str]]) -> None:
        self.state_label.hide()
        populate_booking_table(self.table, rows)
        if not rows:
            self.show_empty("אין כרגע אירועים פתוחים לשיבוץ.")
    def _select(self):
        rows=self.table.selectionModel().selectedRows()
        if rows:self.event_selected.emit(str(self.table.item(rows[0].row(),0).data(Qt.ItemDataRole.UserRole)))
    def show_details(self,details):
        while self.details.rowCount():self.details.removeRow(0)
        for label,value in details:self.details.addRow(label,QLabel(value))
