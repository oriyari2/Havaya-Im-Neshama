from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.views.common import StatefulWidget
from desktop_client.app.views.customer_dialogs import CustomerDialog
from desktop_client.app.views.design_tokens import DETAIL_MIN_WIDTH, TABLE_MIN_WIDTH
from desktop_client.app.views.management_common import ActiveBadge, PaginationFooter, RetryState, SearchToolbar, confirm_action
from desktop_client.app.views.ui_foundations import (
    ColumnKind,
    ColumnPolicy,
    PageScaffold,
    configure_data_table,
    configure_mixed_direction,
    set_disabled_explanation,
    set_item_text,
)


class CustomersView(StatefulWidget):
    filters_requested = Signal(dict)
    page_requested = Signal(int, int)
    customer_selected = Signal(str)
    retry_requested = Signal()
    create_requested = Signal()
    edit_requested = Signal()
    delete_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.scaffold = PageScaffold("לקוחות", "ניהול לקוחות ופרטי איש קשר")
        root.addWidget(self.scaffold)

        self.retry = RetryState()
        self.retry.hide()
        self.retry.retry_requested.connect(self.retry_requested)
        self.scaffold.main_content.addWidget(self.retry)
        self.scaffold.main_content.addWidget(self.state_label)

        self.toolbar = SearchToolbar(
            placeholder="חיפוש לקוחות",
            sort_options=(("name", "שם"), ("created_at", "תאריך יצירה")),
        )
        self.toolbar.search_requested.connect(
            lambda search, sort: self.filters_requested.emit({"search": search or None, "order_by": sort})
        )
        self.toolbar.refresh_requested.connect(self.retry_requested)
        self.scaffold.filter_panel.layout.addWidget(self.toolbar)

        self.city = QComboBox()
        self.city.setEditable(True)
        self.city.addItem("כל הערים", "")
        self.city.setAccessibleName("סינון לפי עיר")
        self.kind = QComboBox()
        self.kind.setEditable(True)
        self.kind.addItem("כל הסוגים", "")
        self.kind.setAccessibleName("סינון לפי סוג לקוח")
        self.active = QComboBox()
        self.active.addItem("הכול", None)
        self.active.addItem("פעילים", True)
        self.active.addItem("לא פעילים", False)
        self.active.setAccessibleName("סינון לפי מצב לקוח")
        self.apply_filters_button = QPushButton("החל סינון")
        self.apply_filters_button.setAccessibleName("החלת מסנני לקוחות")
        self.apply_filters_button.clicked.connect(self._filters)
        filter_row = QWidget()
        filter_layout = QHBoxLayout(filter_row)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        for widget in (self.city, self.kind, self.active, self.apply_filters_button):
            filter_layout.addWidget(widget)
        self.scaffold.filter_panel.layout.addWidget(filter_row)
        self.scaffold.filter_panel.show()

        self.create_button = QPushButton("לקוח חדש")
        self.edit_button = QPushButton("עריכה")
        self.delete_button = QPushButton("מחיקה")
        for button, signal in (
            (self.create_button, self.create_requested),
            (self.edit_button, self.edit_requested),
            (self.delete_button, self.delete_requested),
        ):
            button.clicked.connect(signal)
            button.setAccessibleName(button.text())
        self.scaffold.action_bar.add_action(self.delete_button, destructive=True)
        self.scaffold.action_bar.add_action(self.edit_button)
        self.scaffold.action_bar.add_action(self.create_button, primary=True)
        self.scaffold.action_bar.show()

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setAccessibleName("רשימת לקוחות ופרטים")
        self.splitter.setChildrenCollapsible(False)
        self.table = QTableWidget(0, 6)
        self.table.setMinimumWidth(TABLE_MIN_WIDTH)
        self.table.setHorizontalHeaderLabels(["שם", "סוג", "עיר", "טלפון", "דוא״ל", "מצב לקוח"])
        configure_data_table(
            self.table,
            "רשימת לקוחות",
            (
                ColumnPolicy(ColumnKind.PRIMARY_TEXT),
                ColumnPolicy(ColumnKind.COMPACT),
                ColumnPolicy(ColumnKind.SECONDARY_TEXT),
                ColumnPolicy(ColumnKind.TECHNICAL),
                ColumnPolicy(ColumnKind.TECHNICAL, 130),
                ColumnPolicy(ColumnKind.COMPACT),
            ),
        )
        self.table.itemSelectionChanged.connect(self._select)
        self.splitter.addWidget(self.table)

        panel = QWidget()
        panel.setMinimumWidth(DETAIL_MIN_WIDTH)
        side = QVBoxLayout(panel)
        group = QGroupBox("פרטי לקוח")
        group_layout = QVBoxLayout(group)
        self.details_widget = QWidget()
        self.details = QFormLayout(self.details_widget)
        self.details.setVerticalSpacing(10)
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.details_scroll.setWidget(self.details_widget)
        group_layout.addWidget(self.details_scroll)
        side.addWidget(group)
        self.splitter.addWidget(panel)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setSizes([600, 400])
        self.scaffold.main_content.addWidget(self.splitter, 1)

        self.footer = PaginationFooter()
        self.footer.page_requested.connect(self.page_requested)
        self.scaffold.add_footer(self.footer)
        self.clear_details()

        order = (
            self.toolbar.search_input,
            self.toolbar.search_button,
            self.toolbar.refresh_button,
            self.city,
            self.kind,
            self.active,
            self.apply_filters_button,
            self.create_button,
            self.edit_button,
            self.delete_button,
            self.table,
        )
        for first, second in zip(order, order[1:]):
            QWidget.setTabOrder(first, second)

    def _filters(self) -> None:
        self.filters_requested.emit({
            "city": self.city.currentText().strip() if self.city.currentIndex() else None,
            "customer_type": self.kind.currentText().strip() if self.kind.currentIndex() else None,
            "is_active": self.active.currentData(),
        })

    def _select(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if rows:
            self.customer_selected.emit(str(self.table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)))

    def set_loading(self, value: bool) -> None:
        super().set_loading(value)
        self.create_button.setEnabled(not value)
        self.toolbar.search_button.setEnabled(not value)
        self.toolbar.refresh_button.setEnabled(not value)

    def set_detail_loading(self, value: bool) -> None:
        if value:
            self.state_label.setText("טוען פרטי לקוח…")
            self.state_label.show()
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        elif self.state_label.text() == "טוען פרטי לקוח…":
            self.state_label.hide()

    def render_request_state(self, state: RequestState) -> None:
        if state.phase in {RequestPhase.LOADING, RequestPhase.EMPTY, RequestPhase.IDLE}:
            super().render_request_state(state)
        elif state.phase in {RequestPhase.SUCCESS, RequestPhase.VALIDATION_ERROR}:
            self.state_label.hide()
            self.scaffold.feedback.render(state)
        else:
            self.state_label.hide()

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
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column, key in enumerate(("name", "customer_type", "city", "phone", "email")):
                item = QTableWidgetItem(str(row[key]))
                direction = Qt.LayoutDirection.LeftToRight if key in {"phone", "email"} else Qt.LayoutDirection.RightToLeft
                set_item_text(self.table, row_index, column, item, tooltip_direction=direction)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, row["id"])
                if key in {"phone", "email"}:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            badge = ActiveBadge()
            badge.set_active(row["is_active"])
            self.table.setCellWidget(row_index, 5, badge)
        self.footer.set_page(offset=offset, count=count)
        if not rows:
            self.show_empty("לא נמצאו לקוחות." if filtered else "אין לקוחות להצגה.")
        elif self.state_label.text() != "טוען נתונים…":
            self.state_label.hide()

    def show_details(self, details, customer, contacts) -> None:
        while self.details.rowCount():
            self.details.removeRow(0)
        for label, value in details:
            content = QLabel(value)
            content.setWordWrap(True)
            content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            content.setToolTip(value)
            if any(token in label for token in ("דוא", "טלפון", "מזהה")):
                configure_mixed_direction(content)
            self.details.addRow(label, content)
        self.edit_button.setEnabled(True)
        self.delete_button.setEnabled(True)

    def clear_details(self) -> None:
        while getattr(self, "details", None) is not None and self.details.rowCount():
            self.details.removeRow(0)
        for button in (getattr(self, "edit_button", None), getattr(self, "delete_button", None)):
            if button:
                button.setEnabled(False)
                set_disabled_explanation(button, "יש לבחור לקוח תחילה")

    def select_customer(self, customer_id: str) -> None:
        for row in range(self.table.rowCount()):
            if str(self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)) == customer_id:
                self.table.selectRow(row)
                break

    def open_customer_form(self, initial, submit) -> None:
        self._dialog = CustomerDialog(initial, self)
        self._dialog.submitted.connect(submit)
        self._dialog.open()

    def confirm_customer_deletion(self, name: str) -> bool:
        return confirm_action(self, "אישור מחיקה", f"למחוק לצמיתות את הלקוח {name}? לא ניתן לבטל פעולה זו.")
