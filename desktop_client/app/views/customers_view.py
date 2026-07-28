from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from desktop_client.app.views.common import StatefulWidget
from desktop_client.app.views.customer_dialogs import ContactDialog, CustomerDialog
from desktop_client.app.views.management_common import ActiveBadge, PaginationFooter, RetryState, SearchToolbar, confirm_action

class CustomersView(StatefulWidget):
    filters_requested = Signal(dict); page_requested = Signal(int, int); customer_selected = Signal(str); retry_requested = Signal()
    create_requested = Signal(); edit_requested = Signal(); deactivate_requested = Signal(); reactivate_requested = Signal()
    contact_create_requested = Signal(); contact_edit_requested = Signal(dict); contact_deactivate_requested = Signal(dict); contact_reactivate_requested = Signal(dict)
    def __init__(self) -> None:
        super().__init__(); root = QVBoxLayout(self); title = QLabel("לקוחות"); title.setObjectName("screenTitle"); root.addWidget(title); self.retry = RetryState(); self.retry.hide(); self.retry.retry_requested.connect(self.retry_requested); root.addWidget(self.retry); root.addWidget(self.state_label)
        self.toolbar = SearchToolbar(placeholder="חיפוש לקוחות", sort_options=(("name", "שם"), ("created_at", "תאריך יצירה"))); self.toolbar.search_requested.connect(lambda search, sort: self.filters_requested.emit({"search": search or None, "order_by": sort})); self.toolbar.refresh_requested.connect(self.retry_requested); root.addWidget(self.toolbar)
        filters = QHBoxLayout(); self.city = QComboBox(); self.city.setEditable(True); self.city.addItem("כל הערים", ""); self.kind = QComboBox(); self.kind.setEditable(True); self.kind.addItem("כל הסוגים", ""); self.active = QComboBox(); self.active.addItem("הכול", None); self.active.addItem("פעילים", True); self.active.addItem("לא פעילים", False); apply = QPushButton("החל סינון"); apply.clicked.connect(self._filters)
        for widget in (self.city, self.kind, self.active, apply): filters.addWidget(widget)
        root.addLayout(filters); actions = QHBoxLayout(); self.create_button = QPushButton("לקוח חדש"); self.edit_button = QPushButton("עריכה"); self.deactivate_button = QPushButton("השבתה"); self.reactivate_button = QPushButton("הפעלה מחדש")
        for button, signal in ((self.create_button, self.create_requested), (self.edit_button, self.edit_requested), (self.deactivate_button, self.deactivate_requested), (self.reactivate_button, self.reactivate_requested)): button.clicked.connect(signal); actions.addWidget(button)
        root.addLayout(actions); split = QSplitter(); self.table = QTableWidget(0, 6); self.table.setHorizontalHeaderLabels(["שם", "סוג", "עיר", "טלפון", "דוא״ל", "מצב"]); self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); self.table.itemSelectionChanged.connect(self._select); split.addWidget(self.table)
        panel = QWidget(); side = QVBoxLayout(panel); group = QGroupBox("פרטי לקוח"); self.details = QFormLayout(group); side.addWidget(group); contacts_group = QGroupBox("אנשי קשר"); contacts_layout = QVBoxLayout(contacts_group); self.contacts = QTableWidget(0, 5); self.contacts.setHorizontalHeaderLabels(["שם", "תפקיד", "טלפון", "ראשי", "מצב"]); self.contacts.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); self.contacts.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); self.contacts.itemSelectionChanged.connect(self._contact_state); contacts_layout.addWidget(self.contacts); cactions = QHBoxLayout(); self.add_contact = QPushButton("חדש"); self.edit_contact = QPushButton("עריכה"); self.deactivate_contact = QPushButton("השבתה"); self.reactivate_contact = QPushButton("הפעלה מחדש")
        self.add_contact.clicked.connect(self.contact_create_requested); self.edit_contact.clicked.connect(lambda: self._contact(self.contact_edit_requested)); self.deactivate_contact.clicked.connect(lambda: self._contact(self.contact_deactivate_requested)); self.reactivate_contact.clicked.connect(lambda: self._contact(self.contact_reactivate_requested))
        for button in (self.add_contact, self.edit_contact, self.deactivate_contact, self.reactivate_contact): cactions.addWidget(button)
        contacts_layout.addLayout(cactions); side.addWidget(contacts_group); split.addWidget(panel); split.setStretchFactor(0, 2); root.addWidget(split); self.footer = PaginationFooter(); self.footer.page_requested.connect(self.page_requested); root.addWidget(self.footer); self.clear_details()
    def _filters(self): self.filters_requested.emit({"city": self.city.currentText().strip() if self.city.currentIndex() else None, "customer_type": self.kind.currentText().strip() if self.kind.currentIndex() else None, "is_active": self.active.currentData()})
    def _select(self):
        rows = self.table.selectionModel().selectedRows()
        if rows: self.customer_selected.emit(str(self.table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)))
    def _selected_contact(self):
        rows = self.contacts.selectionModel().selectedRows(); return self.contacts.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole) if rows else None
    def _contact(self, signal):
        value = self._selected_contact()
        if value: signal.emit(value)
    def _contact_state(self):
        value = self._selected_contact(); active = bool(value and value["is_active"]); self.edit_contact.setEnabled(value is not None); self.deactivate_contact.setEnabled(active); self.reactivate_contact.setEnabled(value is not None and not active)
    def set_loading(self, value): super().set_loading(value); self.create_button.setEnabled(not value)
    def show_error(self, message, *, retriable=False, permission=False): self.retry.show_message(message, retriable=retriable)
    def show_success(self, message): self.state_label.setText(message); self.state_label.show()
    def show_customers(self, rows, *, offset, count, filtered):
        self.retry.hide(); self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, key in enumerate(("name", "customer_type", "city", "phone", "email")):
                item = QTableWidgetItem(str(row[key])); self.table.setItem(r, c, item)
                if c == 0: item.setData(Qt.ItemDataRole.UserRole, row["id"])
            badge = ActiveBadge(); badge.set_active(row["is_active"]); self.table.setCellWidget(r, 5, badge)
        self.footer.set_page(offset=offset, count=count)
        if not rows: self.show_empty("לא נמצאו לקוחות." if filtered else "אין לקוחות להצגה.")
    def show_details(self, details, customer, contacts):
        while self.details.rowCount(): self.details.removeRow(0)
        for label, value in details: self.details.addRow(label, QLabel(value))
        self.contacts.setRowCount(len(contacts))
        for r, contact in enumerate(contacts):
            values = (contact["full_name"], contact["role_title"], contact["phone"], "כן" if contact["is_primary"] else "לא", "פעיל" if contact["is_active"] else "לא פעיל")
            for c, value in enumerate(values):
                item = QTableWidgetItem(str(value)); self.contacts.setItem(r, c, item)
                if c == 0: item.setData(Qt.ItemDataRole.UserRole, contact)
        active = bool(customer.get("is_active")); self.edit_button.setEnabled(True); self.add_contact.setEnabled(True); self.deactivate_button.setEnabled(active); self.reactivate_button.setEnabled(not active); self._contact_state()
    def clear_details(self):
        for button in (getattr(self,"edit_button",None),getattr(self,"add_contact",None),getattr(self,"deactivate_button",None),getattr(self,"reactivate_button",None),getattr(self,"edit_contact",None),getattr(self,"deactivate_contact",None),getattr(self,"reactivate_contact",None)):
            if button: button.setEnabled(False)
    def select_customer(self, customer_id):
        for r in range(self.table.rowCount()):
            if str(self.table.item(r,0).data(Qt.ItemDataRole.UserRole)) == customer_id: self.table.selectRow(r); break
    def open_customer_form(self, initial, submit): self._dialog = CustomerDialog(initial,self); self._dialog.submitted.connect(submit); self._dialog.open()
    def open_contact_form(self, initial, submit): self._dialog = ContactDialog(initial,self); self._dialog.submitted.connect(submit); self._dialog.open()
    def confirm_customer_deactivation(self,name): return confirm_action(self,"אישור השבתה",f"להשבית את {name}?")
    def confirm_contact_deactivation(self,name): return confirm_action(self,"אישור השבתה",f"להשבית את {name}?")
