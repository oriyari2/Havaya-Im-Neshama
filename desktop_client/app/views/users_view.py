from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.views.common import StatefulWidget
from desktop_client.app.views.management_common import ActiveBadge, PaginationFooter, RetryState, SearchToolbar, confirm_action
from desktop_client.app.views.ui_foundations import ColumnKind, ColumnPolicy, PageScaffold, configure_data_table, set_disabled_explanation, set_item_text
from desktop_client.app.views.user_dialogs import CreateUserDialog, EditUserDialog, ResetPasswordDialog, ROLE_LABELS


class UsersView(StatefulWidget):
    filters_requested = Signal(dict); page_requested = Signal(int, int); user_selected = Signal(str); retry_requested = Signal()
    create_requested = Signal(); edit_requested = Signal(); activate_requested = Signal(); deactivate_requested = Signal(); reset_password_requested = Signal()

    def __init__(self) -> None:
        super().__init__(); root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); self.scaffold = PageScaffold("מנהלים", "יצירה וניהול של חשבונות מנהלים"); root.addWidget(self.scaffold)
        self.retry = RetryState(); self.retry.hide(); self.retry.retry_requested.connect(self.retry_requested); self.scaffold.main_content.addWidget(self.retry); self.scaffold.main_content.addWidget(self.state_label)
        self.toolbar = SearchToolbar(placeholder="חיפוש לפי דוא״ל או שם"); self.toolbar.search_requested.connect(lambda search, _sort: self.filters_requested.emit({"search": search or None})); self.toolbar.refresh_requested.connect(self.retry_requested); self.scaffold.filter_panel.layout.addWidget(self.toolbar)
        row = QHBoxLayout(); self.status_filter = QComboBox(); self.status_filter.setAccessibleName("סינון לפי מצב חשבון"); self.status_filter.addItem("כל מצבי החשבון", None); self.status_filter.addItem("חשבונות פעילים", True); self.status_filter.addItem("חשבונות לא פעילים", False)
        self.apply_button = QPushButton("החל סינון"); self.apply_button.clicked.connect(self._filters)
        for widget in (self.status_filter, self.apply_button): row.addWidget(widget)
        self.scaffold.filter_panel.layout.addLayout(row); self.scaffold.filter_panel.show()
        self.create_button = QPushButton("מנהל חדש"); self.edit_button = QPushButton("עריכת אימייל"); self.activate_button = QPushButton("הפעלה"); self.deactivate_button = QPushButton("מחיקת מנהל"); self.reset_button = QPushButton("איפוס סיסמה")
        for button, signal in ((self.create_button, self.create_requested), (self.edit_button, self.edit_requested), (self.activate_button, self.activate_requested), (self.deactivate_button, self.deactivate_requested), (self.reset_button, self.reset_password_requested)): button.clicked.connect(signal); button.setAccessibleName(button.text())
        self.scaffold.action_bar.add_action(self.deactivate_button, destructive=True); self.scaffold.action_bar.add_action(self.activate_button); self.scaffold.action_bar.add_action(self.reset_button); self.scaffold.action_bar.add_action(self.edit_button); self.scaffold.action_bar.add_action(self.create_button, primary=True); self.scaffold.action_bar.show()
        splitter = QSplitter(Qt.Orientation.Horizontal); splitter.setChildrenCollapsible(False)
        self.table = QTableWidget(0, 5); self.table.setHorizontalHeaderLabels(["דוא״ל", "תפקיד", "שם", "מצב חשבון", "עודכן"]); configure_data_table(self.table, "רשימת מנהלים", (ColumnPolicy(ColumnKind.PRIMARY_TEXT, 180), ColumnPolicy(ColumnKind.COMPACT), ColumnPolicy(ColumnKind.SECONDARY_TEXT), ColumnPolicy(ColumnKind.COMPACT), ColumnPolicy(ColumnKind.TECHNICAL, 120))); self.table.itemSelectionChanged.connect(self._select); self.table.itemDoubleClicked.connect(lambda _item: self._select()); splitter.addWidget(self.table)
        group = QGroupBox("פרטי מנהל"); self.details = QFormLayout(group); splitter.addWidget(group); splitter.setStretchFactor(0, 2); splitter.setStretchFactor(1, 1); self.scaffold.main_content.addWidget(splitter, 1)
        self.footer = PaginationFooter(); self.footer.page_requested.connect(self.page_requested); self.scaffold.add_footer(self.footer); self.clear_details()

    def _filters(self) -> None: self.filters_requested.emit({"is_active": self.status_filter.currentData()})
    def _select(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if rows: self.user_selected.emit(str(self.table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)))

    def show_users(self, rows: list[dict], *, offset: int, count: int, filtered: bool) -> None:
        rows = [user for user in rows if user.get("role") == "manager"]
        self.retry.hide(); self.table.setRowCount(len(rows))
        for row_index, user in enumerate(rows):
            name = user.get("display_name") or user.get("customer_name") or user.get("instructor_name") or "מנהל"
            values = (user["email"], ROLE_LABELS.get(user["role"], user["role"]), name, "פעיל" if user["is_active"] else "לא פעיל", str(user["updated_at"]))
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value)); direction = Qt.LayoutDirection.LeftToRight if column in {0, 4} else Qt.LayoutDirection.RightToLeft; set_item_text(self.table, row_index, column, item, tooltip_direction=direction)
                if column == 0: item.setData(Qt.ItemDataRole.UserRole, str(user["id"])); item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.footer.set_page(offset=offset, count=len(rows))
        if not rows: self.show_empty("לא נמצאו מנהלים." if filtered else "אין מנהלים להצגה.")
        else: self.state_label.hide()

    def show_details(self, user: dict, *, current_user_id: str) -> None:
        while self.details.rowCount(): self.details.removeRow(0)
        name = user.get("display_name") or user.get("customer_name") or user.get("instructor_name") or "מנהל"
        rows = [("אימייל התחברות", user["email"]), ("תפקיד", ROLE_LABELS.get(user["role"], user["role"])), ("שם", name)]
        if user["role"] == "customer":
            rows.extend((("אימייל לקוח", user.get("customer_email") or user["email"]), ("איש קשר", user.get("contact_name") or "—"), ("טלפון איש קשר", user.get("contact_phone") or "—")))
        elif user["role"] == "instructor":
            rows.extend((("אימייל מדריך", user.get("instructor_email") or user["email"]), ("טלפון מדריך", user.get("instructor_phone") or "—")))
        rows.extend((("מצב חשבון", "פעיל" if user["is_active"] else "לא פעיל"), ("נוצר", user["created_at"]), ("עודכן", user["updated_at"])))
        for label, value in rows:
            content = QLabel(str(value)); content.setWordWrap(True); content.setToolTip(str(value)); self.details.addRow(label, content)
        self.edit_button.setEnabled(True); self.reset_button.setEnabled(True); self.activate_button.setEnabled(not user["is_active"]); self.deactivate_button.setEnabled(bool(user["is_active"] and str(user["id"]) != current_user_id))
        set_disabled_explanation(self.deactivate_button, "לא ניתן למחוק לוגית את החשבון המחובר" if str(user["id"]) == current_user_id else "המנהל כבר לא פעיל" if not user["is_active"] else "מחיקה לוגית באמצעות השבתת המנהל שנבחר")
        set_disabled_explanation(self.activate_button, "המנהל כבר פעיל" if user["is_active"] else "הפעלת המנהל שנבחר")

    def clear_details(self) -> None:
        while getattr(self, "details", None) is not None and self.details.rowCount(): self.details.removeRow(0)
        for name in ("edit_button", "activate_button", "deactivate_button", "reset_button"):
            button = getattr(self, name, None)
            if button: button.setEnabled(False); set_disabled_explanation(button, "יש לבחור מנהל תחילה")

    def set_detail_loading(self, value: bool) -> None:
        for button in (self.edit_button, self.activate_button, self.deactivate_button, self.reset_button):
            if value: button.setEnabled(False)

    def set_loading(self, value: bool) -> None:
        super().set_loading(value); self.create_button.setEnabled(not value); self.toolbar.search_button.setEnabled(not value); self.toolbar.refresh_button.setEnabled(not value); self.apply_button.setEnabled(not value)

    def show_error(self, message: str, *, retriable: bool = False, permission: bool = False) -> None:
        state = RequestState(RequestPhase.AUTHORIZATION_ERROR if permission else RequestPhase.CONNECTION_ERROR if retriable else RequestPhase.SERVER_ERROR, message, "users", retryable=retriable)
        if self.table.rowCount(): self.retry.hide(); self.scaffold.feedback.render(state)
        else: self.scaffold.feedback.hide(); self.retry.show_message(message, retriable=retriable)
    def show_success(self, message: str) -> None: self.scaffold.feedback.render(RequestState(RequestPhase.SUCCESS, message, "users"))
    def select_user(self, user_id: str) -> None:
        for row in range(self.table.rowCount()):
            if str(self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)) == user_id: self.table.selectRow(row); break
    def open_create(self, submit) -> None: self._dialog = CreateUserDialog(self); self._dialog.submitted.connect(submit); self._dialog.open()
    def open_edit(self, user, submit) -> None: self._dialog = EditUserDialog(user, self); self._dialog.submitted.connect(submit); self._dialog.open()
    def open_reset_password(self, user, submit) -> None: self._dialog = ResetPasswordDialog(user, self); self._dialog.submitted.connect(submit); self._dialog.open()
    def confirm_deactivation(self, email: str) -> bool: return confirm_action(self, "אישור מחיקת מנהל", f"למחוק לוגית את המנהל {email}? החשבון יושבת ולא יוכל להתחבר עד להפעלה מחדש. הנתונים לא יימחקו ממסד הנתונים.")
