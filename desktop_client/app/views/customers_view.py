from __future__ import annotations

from PySide6.QtCore import QEvent, QItemSelectionModel, Qt, Signal
from PySide6.QtWidgets import QLabel, QTableWidgetItem, QVBoxLayout

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.views.account_dialogs import ChangePasswordDialog
from desktop_client.app.views.common import StatefulWidget
from desktop_client.app.views.customer_dialogs import CustomerDialog
from desktop_client.app.views.management_common import ActiveBadge, RetryState, confirm_action
from desktop_client.app.views.management_workspace import ManagementWorkspace
from desktop_client.app.views.ui_foundations import (
    ColumnKind,
    ColumnPolicy,
    configure_mixed_direction,
    set_disabled_explanation,
    set_item_text,
)


class CustomersView(StatefulWidget):
    """Customer configuration of the shared management UI foundation."""

    filters_requested = Signal(dict)
    page_requested = Signal(int, int)
    customer_selected = Signal(str)
    retry_requested = Signal()
    create_requested = Signal()
    edit_requested = Signal()
    delete_requested = Signal()
    change_password_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._selected_customer_id: str | None = None
        self._empty_filtered = False
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.workspace = ManagementWorkspace(
            title="לקוחות",
            subtitle="ניהול לקוחות ופרטי קשר",
            create_text="לקוח חדש",
            plural="לקוחות",
            detail_subtitle="מידע מלא ופעולות עבור הלקוח שנבחר",
            search_placeholder="חיפוש לפי שם, דוא״ל או טלפון",
            sort_options=(("name", "מיון לפי: שם"), ("created_at", "מיון לפי: תאריך יצירה")),
            headers=("שם לקוח", "סוג", "עיר", "מצב"),
            policies=(
                ColumnPolicy(ColumnKind.PRIMARY_TEXT, 180),
                ColumnPolicy(ColumnKind.SECONDARY_TEXT, 140, 220),
                ColumnPolicy(ColumnKind.SECONDARY_TEXT, 150, 240),
                ColumnPolicy(ColumnKind.COMPACT, 110),
            ),
        )
        root.addWidget(self.workspace)
        for name in (
            "scaffold", "toolbar", "table", "footer", "create_button", "pages",
            "list_page", "details_page", "back_button", "view_details_button",
            "header_identity", "identity_container", "actions_container",
            "table_region", "empty_state", "empty_title", "empty_description",
            "empty_action_button", "details_scroll", "details_widget",
        ):
            setattr(self, name, getattr(self.workspace, name))
        self.sort_by = self.toolbar.sort_combo
        self.create_button.setObjectName("customerCreateButton")
        self.toolbar.search_button.setObjectName("customerSearchButton")
        self.empty_action_button.setObjectName("customerEmptyActionButton")

        self.retry = RetryState()
        self.retry.retry_requested.connect(self.retry_requested)
        self.scaffold.main_content.insertWidget(0, self.retry)
        self.scaffold.main_content.insertWidget(1, self.state_label)

        self.edit_button = self.workspace.add_action("עריכת לקוח")
        self.change_password_button = self.workspace.add_action("שינוי סיסמה")
        self.delete_button = self.workspace.add_action("מחיקת לקוח", destructive=True)
        self.customer_details = self.workspace.add_card("פרטי לקוח")
        self.contact_details = self.workspace.add_card("פרטי קשר")
        self.system_details = self.workspace.add_card("מידע מערכת")
        self.detail_forms = {
            "customer": self.customer_details,
            "contact": self.contact_details,
            "system": self.system_details,
        }

        self.create_button.clicked.connect(self.create_requested)
        self.edit_button.clicked.connect(self.edit_requested)
        self.change_password_button.clicked.connect(self.change_password_requested)
        self.delete_button.clicked.connect(self.delete_requested)
        self.toolbar.search_requested.connect(self._search)
        self.toolbar.sort_combo.currentIndexChanged.connect(self._sort_changed)
        self.toolbar.refresh_requested.connect(self._reset_filters)
        self.footer.page_requested.connect(self.page_requested)
        self.table.itemSelectionChanged.connect(self._select)
        self.table.cellDoubleClicked.connect(lambda _row, _column: self._open_selected_customer())
        self.table.installEventFilter(self)
        self.view_details_button.clicked.connect(self._open_selected_customer)
        self.empty_action_button.clicked.connect(self._empty_action)
        self.clear_details()

    def eventFilter(self, watched, event) -> bool:
        if watched is self.table and event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._open_selected_customer()
            return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape and self.pages.currentWidget() is self.details_page:
            self.workspace.show_list()
            return
        super().keyPressEvent(event)

    def _search(self, search: str, _sort: str) -> None:
        self.filters_requested.emit({"search": search or None, "order_by": self.sort_by.currentData()})

    def _sort_changed(self, _index: int) -> None:
        self.filters_requested.emit({"order_by": self.sort_by.currentData()})

    def _reset_filters(self) -> None:
        self.toolbar.search_input.clear()
        blocked = self.sort_by.blockSignals(True)
        self.sort_by.setCurrentIndex(0)
        self.sort_by.blockSignals(blocked)
        self.clear_details()
        self.filters_requested.emit({"search": None, "order_by": "name", "_clear_selection": True})

    def _empty_action(self) -> None:
        self._reset_filters() if self._empty_filtered else self.create_requested.emit()

    def _select(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self._selected_customer_id = None
            self.view_details_button.setEnabled(False)
            set_disabled_explanation(self.view_details_button, "יש לבחור לקוח תחילה")
            return
        customer_id = str(self.table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole))
        changed = customer_id != self._selected_customer_id
        self._selected_customer_id = customer_id
        self.view_details_button.setEnabled(True)
        set_disabled_explanation(self.view_details_button, "")
        if changed:
            self._clear_forms()
            self.workspace.detail_title.clear()
            self.workspace.set_actions_enabled(False)
            self.customer_selected.emit(customer_id)

    def _open_selected_customer(self) -> None:
        if self._selected_customer_id:
            self.workspace.show_details()

    def set_loading(self, value: bool) -> None:
        self.create_button.setEnabled(not value)
        for control in (self.toolbar.search_button, self.toolbar.refresh_button, self.sort_by):
            control.setEnabled(not value)
        if value and not self.table.rowCount():
            self.workspace.show_loading("טוען לקוחות…")

    def set_detail_loading(self, value: bool) -> None:
        if value:
            self.workspace.set_actions_enabled(False)

    def render_request_state(self, state: RequestState) -> None:
        if state.phase in {RequestPhase.SUCCESS, RequestPhase.VALIDATION_ERROR}:
            self.scaffold.feedback.render(state)
        elif state.phase not in {RequestPhase.LOADING, RequestPhase.IDLE, RequestPhase.EMPTY}:
            self.show_error(state.message, retriable=state.retryable, permission=state.phase == RequestPhase.AUTHORIZATION_ERROR)

    def show_error(self, message: str, *, retriable: bool = False, permission: bool = False) -> None:
        state = RequestState(
            RequestPhase.AUTHORIZATION_ERROR if permission else RequestPhase.CONNECTION_ERROR if retriable else RequestPhase.SERVER_ERROR,
            message,
            "customers",
            retryable=retriable,
        )
        if self.table.rowCount():
            self.retry.hide()
            self.scaffold.feedback.render(state)
        else:
            self.scaffold.feedback.hide()
            self.retry.show_message(message, retriable=retriable)

    def show_success(self, message: str) -> None:
        self.scaffold.feedback.render(RequestState(RequestPhase.SUCCESS, message, "customers"))

    def show_customers(self, rows, *, offset: int, count: int, filtered: bool) -> None:
        self.retry.hide()
        if not rows and offset > 0:
            self.page_requested.emit(max(0, offset - 25), 25)
            return
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column, key in enumerate(("name", "customer_type", "city")):
                item = QTableWidgetItem(str(row.get(key) or "—"))
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute)
                set_item_text(self.table, row_index, column, item, tooltip_direction=Qt.LayoutDirection.RightToLeft)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, str(row["id"]))
            badge = ActiveBadge()
            badge.set_active(bool(row.get("is_active")))
            self.workspace.configure_status_badge(badge)
            self.table.setCellWidget(row_index, 3, badge)
        self.footer.set_page(offset=offset, count=count)
        self.workspace.results_label.setText(f"לקוחות • {len(rows)}")
        self._empty_filtered = filtered
        self.workspace.show_empty_state(empty=not rows, filtered=filtered, plural="לקוחות")
        if not rows:
            self.empty_title.setText("לא נמצאו לקוחות" if filtered else "אין עדיין לקוחות")
            self.empty_description.setText("אפשר לאפס את החיפוש ולנסות שוב." if filtered else "צרו את הלקוח הראשון כדי להתחיל.")
            self.empty_action_button.setText("איפוס חיפוש ומסננים" if filtered else "לקוח חדש")
        self.footer.setVisible(bool(rows))
        self.view_details_button.setVisible(bool(rows))

    def show_details(self, details, customer) -> None:
        self._selected_customer_id = str(customer.get("id")) if customer.get("id") is not None else self._selected_customer_id
        self._clear_forms()
        customer_labels = {"שם", "סוג לקוח", "עיר", "כתובת", "הערות"}
        contact_labels = {"טלפון", "דוא״ל", "איש קשר", "טלפון איש קשר"}
        for label, value in details:
            content = QLabel(value)
            content.setWordWrap(True)
            content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            content.setToolTip(value)
            if label in {"טלפון", "דוא״ל", "טלפון איש קשר", "נוצר", "עודכן"}:
                configure_mixed_direction(content)
            form = self.customer_details if label in customer_labels else self.contact_details if label in contact_labels else self.system_details
            self.workspace.add_property_row(form, label, content)
        self.workspace.show_detail_identity(str(customer.get("name") or "פרטי לקוח"), bool(customer.get("is_active")))
        self.workspace.set_actions_enabled(True)
        for button in (self.edit_button, self.change_password_button, self.delete_button):
            set_disabled_explanation(button, "")

    def _clear_forms(self) -> None:
        for form in self.detail_forms.values():
            while form.rowCount():
                form.removeRow(0)

    def clear_details(self) -> None:
        if hasattr(self, "detail_forms"):
            self._clear_forms()
        self._selected_customer_id = None
        self.workspace.detail_title.clear()
        self.workspace.set_actions_enabled(False)
        self.workspace.show_list()
        self.table.clearSelection()
        self.view_details_button.setEnabled(False)
        set_disabled_explanation(self.view_details_button, "יש לבחור לקוח תחילה")
        for button in (self.edit_button, self.change_password_button, self.delete_button):
            set_disabled_explanation(button, "יש לבחור לקוח תחילה")

    def reset_to_default(self) -> None:
        dialog = getattr(self, "_dialog", None)
        if dialog is not None and dialog.isVisible():
            dialog.reject()
        self.scaffold.feedback.hide()
        self.toolbar.search_input.clear()
        blocked = self.sort_by.blockSignals(True)
        self.sort_by.setCurrentIndex(0)
        self.sort_by.blockSignals(blocked)
        self.clear_details()

    def select_customer(self, customer_id: str) -> None:
        for row in range(self.table.rowCount()):
            if str(self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)) == customer_id:
                blocked = self.table.blockSignals(True)
                index = self.table.model().index(row, 0)
                self.table.selectionModel().setCurrentIndex(
                    index,
                    QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows,
                )
                self.table.blockSignals(blocked)
                changed = self._selected_customer_id != customer_id
                self._selected_customer_id = customer_id
                self.view_details_button.setEnabled(True)
                if changed:
                    self.customer_selected.emit(customer_id)
                break

    def open_customer_form(self, initial, submit) -> None:
        self._dialog = CustomerDialog(initial, self)
        self._dialog.submitted.connect(submit)
        self._dialog.open()

    def open_change_password(self, submit) -> None:
        self._dialog = ChangePasswordDialog(self)
        self._dialog.submitted.connect(submit)
        self._dialog.open()

    def confirm_customer_deletion(self, name: str) -> bool:
        return confirm_action(self, "אישור מחיקה", f"למחוק לצמיתות את הלקוח {name}? לא ניתן לבטל פעולה זו.")
