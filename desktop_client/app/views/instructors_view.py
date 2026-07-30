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
from desktop_client.app.views.design_tokens import DETAIL_MIN_WIDTH, TABLE_MIN_WIDTH
from desktop_client.app.views.instructor_dialogs import InstructorDialog
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


class InstructorsView(StatefulWidget):
    filters_requested = Signal(dict)
    page_requested = Signal(int, int)
    instructor_selected = Signal(str)
    retry_requested = Signal()
    create_requested = Signal()
    edit_requested = Signal()
    delete_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.scaffold = PageScaffold("מדריכים", "ניהול מדריכים ופרטי התקשרות")
        root.addWidget(self.scaffold)
        self.retry_state = RetryState()
        self.retry_state.hide()
        self.retry_state.retry_requested.connect(self.retry_requested)
        self.scaffold.main_content.addWidget(self.retry_state)
        self.scaffold.main_content.addWidget(self.state_label)

        self.toolbar = SearchToolbar(
            placeholder="חיפוש מדריכים",
            sort_options=(("full_name", "שם"), ("created_at", "תאריך יצירה")),
        )
        self.toolbar.search_requested.connect(
            lambda search, order: self.filters_requested.emit({"search": search or None, "order_by": order})
        )
        self.toolbar.refresh_requested.connect(self.retry_requested)
        self.scaffold.filter_panel.layout.addWidget(self.toolbar)
        filter_row = QWidget()
        filter_layout = QHBoxLayout(filter_row)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        self.city = QComboBox()
        self.city.setEditable(True)
        self.city.addItem("כל הערים", "")
        self.city.setAccessibleName("סינון לפי עיר")
        self.active = QComboBox()
        self.active.addItem("הכול", None)
        self.active.addItem("פעילים", True)
        self.active.addItem("לא פעילים", False)
        self.active.setAccessibleName("סינון לפי מצב מדריך")
        self.apply_filters_button = QPushButton("החל סינון")
        self.apply_filters_button.clicked.connect(self._filters)
        for widget in (self.city, self.active, self.apply_filters_button):
            filter_layout.addWidget(widget)
        self.scaffold.filter_panel.layout.addWidget(filter_row)
        self.scaffold.filter_panel.show()

        self.create_button = QPushButton("מדריך חדש")
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
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setAccessibleName("רשימת מדריכים ופרטים")
        self.table = QTableWidget(0, 5)
        self.table.setMinimumWidth(TABLE_MIN_WIDTH)
        self.table.setHorizontalHeaderLabels(["שם", "טלפון", "דוא״ל", "עיר", "מצב מדריך"])
        configure_data_table(
            self.table,
            "רשימת מדריכים",
            (
                ColumnPolicy(ColumnKind.PRIMARY_TEXT),
                ColumnPolicy(ColumnKind.TECHNICAL, 115),
                ColumnPolicy(ColumnKind.TECHNICAL, 150),
                ColumnPolicy(ColumnKind.SECONDARY_TEXT, 80),
                ColumnPolicy(ColumnKind.COMPACT, 64),
            ),
        )
        self.table.itemSelectionChanged.connect(self._select)
        self.table.itemDoubleClicked.connect(lambda _item: self._select())
        self.splitter.addWidget(self.table)

        group = QGroupBox("פרטי מדריך")
        group.setMinimumWidth(DETAIL_MIN_WIDTH)
        group_layout = QVBoxLayout(group)
        details_widget = QWidget()
        self.details = QFormLayout(details_widget)
        self.details.setVerticalSpacing(10)
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.details_scroll.setWidget(details_widget)
        group_layout.addWidget(self.details_scroll)
        self.splitter.addWidget(group)
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
            "is_active": self.active.currentData(),
        })

    def _select(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if rows:
            self.instructor_selected.emit(str(self.table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)))

    def show_instructors(self, rows, *, offset: int, count: int, filtered: bool) -> None:
        self.retry_state.hide()
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column, key in enumerate(("full_name", "phone", "email", "city")):
                item = QTableWidgetItem(str(row[key]))
                direction = Qt.LayoutDirection.LeftToRight if key in {"phone", "email"} else Qt.LayoutDirection.RightToLeft
                set_item_text(self.table, row_index, column, item, tooltip_direction=direction)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, row["id"])
                if key in {"phone", "email"}:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            badge = ActiveBadge()
            badge.set_active(row["is_active"])
            self.table.setCellWidget(row_index, 4, badge)
        self.footer.set_page(offset=offset, count=count)
        if not rows:
            self.show_empty("לא נמצאו מדריכים." if filtered else "אין מדריכים להצגה.")
        else:
            self.state_label.hide()

    def show_details(self, details, item) -> None:
        while self.details.rowCount():
            self.details.removeRow(0)
        for label, value in details:
            content = QLabel(value)
            content.setWordWrap(True)
            content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            content.setToolTip(value)
            if any(token in label for token in ("דוא", "טלפון")):
                configure_mixed_direction(content)
            self.details.addRow(label, content)
        self.edit_button.setEnabled(True)
        self.delete_button.setEnabled(True)

    def clear_details(self) -> None:
        while getattr(self, "details", None) is not None and self.details.rowCount():
            self.details.removeRow(0)
        for name in ("edit_button", "delete_button"):
            button = getattr(self, name, None)
            if button:
                button.setEnabled(False)
                set_disabled_explanation(button, "יש לבחור מדריך תחילה")

    def show_error(self, message, *, retriable=False, permission=False) -> None:
        self.retry_state.show_message(message, retriable=retriable)

    def show_success(self, message) -> None:
        self.scaffold.feedback.render(RequestState(RequestPhase.SUCCESS, message, "instructors"))

    def select_instructor(self, instructor_id) -> None:
        for row in range(self.table.rowCount()):
            if str(self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)) == instructor_id:
                self.table.selectRow(row)
                break

    def open_form(self, initial, submit) -> None:
        self._dialog = InstructorDialog(initial, self)
        self._dialog.submitted.connect(submit)
        self._dialog.open()

    def confirm_deletion(self, name) -> bool:
        return confirm_action(self, "אישור מחיקה", f"למחוק לצמיתות את המדריך {name}? לא ניתן לבטל פעולה זו.")


class InstructorProfileView(StatefulWidget):
    retry_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        title = QLabel("הפרופיל שלי")
        title.setObjectName("screenTitle")
        root.addWidget(title)
        self.retry_state = RetryState()
        self.retry_state.hide()
        self.retry_state.retry_requested.connect(self.retry_requested)
        root.addWidget(self.retry_state)
        root.addWidget(self.state_label)
        group = QGroupBox("פרטי מדריך")
        self.details = QFormLayout(group)
        root.addWidget(group)

    def show_profile(self, details) -> None:
        self.retry_state.hide()
        while self.details.rowCount():
            self.details.removeRow(0)
        for label, value in details:
            self.details.addRow(label, QLabel(value))

    def show_error(self, message, *, retriable=False, permission=False) -> None:
        self.retry_state.show_message(message, retriable=retriable)
