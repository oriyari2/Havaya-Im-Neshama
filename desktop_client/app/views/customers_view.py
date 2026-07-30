from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.views.common import StatefulWidget
from desktop_client.app.views.customer_dialogs import ContactDialog, CustomerDialog
from desktop_client.app.views.management_common import ActiveBadge, PaginationFooter, RetryState, SearchToolbar, confirm_action
from desktop_client.app.views.design_tokens import DETAIL_MIN_WIDTH, TABLE_MIN_WIDTH
from desktop_client.app.views.ui_foundations import ColumnKind, ColumnPolicy, PageScaffold, configure_data_table, configure_mixed_direction, set_disabled_explanation, set_item_text


class CustomersView(StatefulWidget):
    filters_requested = Signal(dict); page_requested = Signal(int, int); customer_selected = Signal(str); retry_requested = Signal()
    create_requested = Signal(); edit_requested = Signal(); delete_requested = Signal()
    contact_create_requested = Signal(); contact_edit_requested = Signal(dict); contact_deactivate_requested = Signal(dict); contact_reactivate_requested = Signal(dict)
    def __init__(self) -> None:
        super().__init__(); root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); self.scaffold = PageScaffold("לקוחות", "ניהול לקוחות ואנשי קשר"); root.addWidget(self.scaffold)
        self.retry = RetryState(); self.retry.hide(); self.retry.retry_requested.connect(self.retry_requested); self.scaffold.main_content.addWidget(self.retry); self.scaffold.main_content.addWidget(self.state_label)
        self.toolbar = SearchToolbar(placeholder="חיפוש לקוחות", sort_options=(("name", "שם"), ("created_at", "תאריך יצירה"))); self.toolbar.search_requested.connect(lambda search, sort: self.filters_requested.emit({"search": search or None, "order_by": sort})); self.toolbar.refresh_requested.connect(self.retry_requested); self.scaffold.filter_panel.layout.addWidget(self.toolbar)
        self.city = QComboBox(); self.city.setEditable(True); self.city.addItem("כל הערים", ""); self.city.setAccessibleName("סינון לפי עיר")
        self.kind = QComboBox(); self.kind.setEditable(True); self.kind.addItem("כל הסוגים", ""); self.kind.setAccessibleName("סינון לפי סוג לקוח")
        self.active = QComboBox(); self.active.addItem("הכול", None); self.active.addItem("פעילים", True); self.active.addItem("לא פעילים", False); self.active.setAccessibleName("סינון לפי מצב")
        self.apply_filters_button = QPushButton("החל סינון"); self.apply_filters_button.setAccessibleName("החלת מסנני לקוחות"); self.apply_filters_button.clicked.connect(self._filters)
        filter_row = QWidget(); filter_layout = QHBoxLayout(filter_row); filter_layout.setContentsMargins(0, 0, 0, 0)
        for widget in (self.city, self.kind, self.active, self.apply_filters_button): filter_layout.addWidget(widget)
        self.scaffold.filter_panel.layout.addWidget(filter_row)
        self.scaffold.filter_panel.show()
        self.create_button = QPushButton("לקוח חדש"); self.edit_button = QPushButton("עריכה"); self.delete_button = QPushButton("מחיקה")
        for button, signal in ((self.create_button, self.create_requested), (self.edit_button, self.edit_requested), (self.delete_button, self.delete_requested)): button.clicked.connect(signal); button.setAccessibleName(button.text())
        self.scaffold.action_bar.add_action(self.delete_button, destructive=True); self.scaffold.action_bar.add_action(self.edit_button); self.scaffold.action_bar.add_action(self.create_button, primary=True); self.scaffold.action_bar.show()
        self.splitter = QSplitter(Qt.Orientation.Horizontal); self.splitter.setAccessibleName("רשימת לקוחות ופרטים"); self.splitter.setChildrenCollapsible(False)
        self.table = QTableWidget(0, 6); self.table.setMinimumWidth(TABLE_MIN_WIDTH); self.table.setHorizontalHeaderLabels(["שם", "סוג", "עיר", "טלפון", "דוא״ל", "מצב"]); configure_data_table(self.table, "רשימת לקוחות", (
            ColumnPolicy(ColumnKind.PRIMARY_TEXT), ColumnPolicy(ColumnKind.COMPACT),
            ColumnPolicy(ColumnKind.SECONDARY_TEXT), ColumnPolicy(ColumnKind.TECHNICAL),
            ColumnPolicy(ColumnKind.TECHNICAL, 130), ColumnPolicy(ColumnKind.COMPACT),
        )); self.table.itemSelectionChanged.connect(self._select); self.splitter.addWidget(self.table)
        panel = QWidget(); panel.setMinimumWidth(DETAIL_MIN_WIDTH); side = QVBoxLayout(panel); self.details_splitter = QSplitter(Qt.Orientation.Vertical); self.details_splitter.setChildrenCollapsible(False); group = QGroupBox("פרטי לקוח"); self.details = QFormLayout(group); self.details_splitter.addWidget(group)
        contacts_group = QGroupBox("אנשי קשר"); contacts_layout = QVBoxLayout(contacts_group); self.contacts = QTableWidget(0, 5); self.contacts.setHorizontalHeaderLabels(["שם", "תפקיד", "טלפון", "ראשי", "מצב"]); configure_data_table(self.contacts, "אנשי קשר של הלקוח", (
            ColumnPolicy(ColumnKind.PRIMARY_TEXT, 85), ColumnPolicy(ColumnKind.SECONDARY_TEXT, 55),
            ColumnPolicy(ColumnKind.TECHNICAL, 80), ColumnPolicy(ColumnKind.COMPACT, 55),
            ColumnPolicy(ColumnKind.COMPACT, 55),
        )); self.contacts.itemSelectionChanged.connect(self._contact_state); contacts_layout.addWidget(self.contacts)
        cactions = QGridLayout(); self.add_contact = QPushButton("חדש"); self.edit_contact = QPushButton("עריכה"); self.deactivate_contact = QPushButton("השבתה"); self.reactivate_contact = QPushButton("הפעלה מחדש")
        self.add_contact.clicked.connect(self.contact_create_requested); self.edit_contact.clicked.connect(lambda: self._contact(self.contact_edit_requested)); self.deactivate_contact.clicked.connect(lambda: self._contact(self.contact_deactivate_requested)); self.reactivate_contact.clicked.connect(lambda: self._contact(self.contact_reactivate_requested))
        for index, button in enumerate((self.add_contact, self.edit_contact, self.deactivate_contact, self.reactivate_contact)): button.setAccessibleName(button.text()); cactions.addWidget(button, index // 2, index % 2)
        contacts_layout.addLayout(cactions); self.details_splitter.addWidget(contacts_group); self.details_splitter.setStretchFactor(0, 1); self.details_splitter.setStretchFactor(1, 1); self.details_splitter.setSizes([220, 220]); side.addWidget(self.details_splitter); self.splitter.addWidget(panel); self.splitter.setStretchFactor(0, 2); self.splitter.setStretchFactor(1, 1); self.splitter.setSizes([650, 330]); self.scaffold.main_content.addWidget(self.splitter, 1)
        self.footer = PaginationFooter(); self.footer.page_requested.connect(self.page_requested); self.scaffold.add_footer(self.footer); self.clear_details()
        QWidget.setTabOrder(self.toolbar.search_input, self.toolbar.search_button); QWidget.setTabOrder(self.toolbar.search_button, self.toolbar.refresh_button); QWidget.setTabOrder(self.toolbar.refresh_button, self.city); QWidget.setTabOrder(self.city, self.kind); QWidget.setTabOrder(self.kind, self.active); QWidget.setTabOrder(self.active, self.apply_filters_button); QWidget.setTabOrder(self.apply_filters_button, self.create_button); QWidget.setTabOrder(self.create_button, self.edit_button); QWidget.setTabOrder(self.edit_button, self.delete_button); QWidget.setTabOrder(self.delete_button, self.table)
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
        set_disabled_explanation(self.edit_contact, "יש לבחור איש קשר תחילה" if value is None else "עריכת איש הקשר שנבחר"); set_disabled_explanation(self.deactivate_contact, "יש לבחור איש קשר פעיל" if not active else "השבתת איש הקשר שנבחר"); set_disabled_explanation(self.reactivate_contact, "יש לבחור איש קשר לא פעיל" if value is None or active else "הפעלת איש הקשר שנבחר מחדש")
    def set_loading(self, value): super().set_loading(value); self.create_button.setEnabled(not value); self.toolbar.search_button.setEnabled(not value); self.toolbar.refresh_button.setEnabled(not value)
    def set_detail_loading(self, value):
        if value:
            self.state_label.setText("טוען פרטי לקוח…"); self.state_label.show()
        elif self.state_label.text() == "טוען פרטי לקוח…":
            self.state_label.hide()
        for button in (self.edit_button, self.delete_button, self.add_contact, self.edit_contact, self.deactivate_contact, self.reactivate_contact):
            if value: button.setEnabled(False)
        if not value and self._selected_contact() is not None: self._contact_state()
    def render_request_state(self, state):
        if state.phase in {RequestPhase.LOADING, RequestPhase.EMPTY, RequestPhase.IDLE}: super().render_request_state(state)
        elif state.phase in {RequestPhase.SUCCESS, RequestPhase.VALIDATION_ERROR}: self.state_label.hide(); self.scaffold.feedback.render(state)
        else: self.state_label.hide()
    def show_error(self, message, *, retriable=False, permission=False):
        state = RequestState(RequestPhase.AUTHORIZATION_ERROR if permission else RequestPhase.CONNECTION_ERROR if retriable else RequestPhase.SERVER_ERROR, message, "customers", retryable=retriable)
        if self.table.rowCount(): self.retry.hide(); self.scaffold.feedback.render(state)
        else: self.scaffold.feedback.hide(); self.retry.show_message(message, retriable=retriable)
    def show_success(self, message): self.scaffold.feedback.render(RequestState(RequestPhase.SUCCESS, message, "customers"))
    def show_customers(self, rows, *, offset, count, filtered):
        self.retry.hide(); self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, key in enumerate(("name", "customer_type", "city", "phone", "email")):
                item = QTableWidgetItem(str(row[key])); direction = Qt.LayoutDirection.LeftToRight if key in {"phone", "email"} else Qt.LayoutDirection.RightToLeft; set_item_text(self.table, r, c, item, tooltip_direction=direction)
                if c == 0: item.setData(Qt.ItemDataRole.UserRole, row["id"])
                if key in {"phone", "email"}: item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            badge = ActiveBadge(); badge.set_active(row["is_active"]); self.table.setCellWidget(r, 5, badge)
        self.footer.set_page(offset=offset, count=count)
        if not rows: self.show_empty("לא נמצאו לקוחות." if filtered else "אין לקוחות להצגה.")
        elif self.state_label.text() != "טוען נתונים…": self.state_label.hide()
    def show_details(self, details, customer, contacts):
        while self.details.rowCount(): self.details.removeRow(0)
        for label, value in details:
            content = QLabel(value); content.setWordWrap(True); content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse); content.setToolTip(value)
            if any(x in label for x in ("דוא", "טלפון", "מזהה")): configure_mixed_direction(content)
            self.details.addRow(label, content)
        self.contacts.setRowCount(len(contacts))
        for r, contact in enumerate(contacts):
            values = (contact["full_name"], contact["role_title"], contact["phone"], "כן" if contact["is_primary"] else "לא", "פעיל" if contact["is_active"] else "לא פעיל")
            for c, value in enumerate(values):
                item = QTableWidgetItem(str(value)); direction = Qt.LayoutDirection.LeftToRight if c == 2 else Qt.LayoutDirection.RightToLeft; set_item_text(self.contacts, r, c, item, tooltip_direction=direction)
                if c == 0: item.setData(Qt.ItemDataRole.UserRole, contact)
                if c == 2: item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.edit_button.setEnabled(True); self.add_contact.setEnabled(True); self.delete_button.setEnabled(True); self._contact_state()
    def clear_details(self):
        for button in (getattr(self, "edit_button", None), getattr(self, "add_contact", None), getattr(self, "delete_button", None), getattr(self, "edit_contact", None), getattr(self, "deactivate_contact", None), getattr(self, "reactivate_contact", None)):
            if button: button.setEnabled(False); set_disabled_explanation(button, "יש לבחור לקוח תחילה")
    def select_customer(self, customer_id):
        for r in range(self.table.rowCount()):
            if str(self.table.item(r, 0).data(Qt.ItemDataRole.UserRole)) == customer_id: self.table.selectRow(r); break
    def open_customer_form(self, initial, submit): self._dialog = CustomerDialog(initial, self); self._dialog.submitted.connect(submit); self._dialog.open()
    def open_contact_form(self, initial, submit): self._dialog = ContactDialog(initial, self); self._dialog.submitted.connect(submit); self._dialog.open()
    def confirm_customer_deletion(self, name): return confirm_action(self, "אישור מחיקה", f"למחוק לצמיתות את הלקוח {name}? לא ניתן לבטל פעולה זו.")
    def confirm_contact_deactivation(self, name): return confirm_action(self, "אישור השבתה", f"להשבית את {name}?")
