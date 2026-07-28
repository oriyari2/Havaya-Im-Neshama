from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout
from desktop_client.app.views.common import StatefulWidget
from desktop_client.app.views.management_common import RetryState

class CustomerProfileView(StatefulWidget):
    retry_requested = Signal()
    def __init__(self) -> None:
        super().__init__(); root = QVBoxLayout(self); title = QLabel("הפרופיל שלי"); title.setObjectName("screenTitle"); root.addWidget(title); self.retry_state = RetryState(); self.retry_state.hide(); self.retry_state.retry_requested.connect(self.retry_requested); root.addWidget(self.retry_state); root.addWidget(self.state_label); group = QGroupBox("פרטי לקוח"); self.details = QFormLayout(group); root.addWidget(group); self.contacts = QTableWidget(0, 4); self.contacts.setHorizontalHeaderLabels(["איש קשר", "תפקיד", "טלפון", "דוא״ל"]); self.contacts.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); root.addWidget(self.contacts)
    def show_profile(self, details, contacts) -> None:
        self.retry_state.hide()
        while self.details.rowCount(): self.details.removeRow(0)
        for label, value in details: self.details.addRow(label, QLabel(value))
        self.contacts.setRowCount(len(contacts))
        for r, contact in enumerate(contacts):
            for c, key in enumerate(("full_name", "role_title", "phone", "email")): self.contacts.setItem(r, c, QTableWidgetItem(str(contact[key])))
    def show_error(self, message, *, retriable=False, permission=False) -> None: self.retry_state.show_message(message, retriable=retriable)
