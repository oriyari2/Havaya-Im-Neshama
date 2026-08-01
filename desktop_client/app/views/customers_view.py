from PySide6.QtCore import QEvent, QItemSelectionModel, Qt, Signal
from PySide6.QtWidgets import (
    QBoxLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.views.common import StatefulWidget
from desktop_client.app.views.customer_dialogs import CustomerDialog
from desktop_client.app.views.account_dialogs import ChangePasswordDialog
from desktop_client.app.views.design_tokens import SPACE_2, SPACE_3, SPACE_4, SPACE_6
from desktop_client.app.views.management_common import ActiveBadge, PaginationFooter, RetryState, SearchToolbar, configure_reference_toolbar, confirm_action
from desktop_client.app.views.ui_foundations import (
    ColumnKind,
    ColumnPolicy,
    PageScaffold,
    configure_data_table,
    configure_mixed_direction,
    set_disabled_explanation,
    set_item_text,
)

DETAIL_LABEL_WIDTH = 140
DETAILS_WIDE_BREAKPOINT = 880


class CustomersView(StatefulWidget):
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
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.scaffold = PageScaffold("לקוחות", "ניהול לקוחות ופרטי קשר")
        self.scaffold.root.setSpacing(SPACE_3)
        self.scaffold.header.layout().setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_3)
        self.scaffold.header.layout().setSpacing(SPACE_2)
        self.scaffold.header.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.scaffold.header.title.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.scaffold.header.description.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.scaffold.header.description.setWordWrap(False)
        root.addWidget(self.scaffold)

        self.create_button = QPushButton("לקוח חדש")
        self.create_button.setObjectName("customerCreateButton")
        self.create_button.setAccessibleName("יצירת לקוח חדש")
        self.create_button.setProperty("primary", True)
        self.create_button.clicked.connect(self.create_requested)
        self.scaffold.header.add_action(self.create_button)
        self.scaffold.header.layout().itemAt(0).layout().setDirection(QBoxLayout.Direction.RightToLeft)
        title_row = self.scaffold.header.layout().itemAt(0).layout()
        title_row.removeWidget(self.scaffold.header.title)
        self.scaffold.header.layout().removeWidget(self.scaffold.header.description)
        self.header_identity = QWidget()
        header_identity_layout = QVBoxLayout(self.header_identity)
        header_identity_layout.setContentsMargins(0, 0, 0, 0)
        header_identity_layout.setSpacing(SPACE_2)
        header_identity_layout.addWidget(self.scaffold.header.title)
        header_identity_layout.addWidget(self.scaffold.header.description)
        title_row.insertWidget(0, self.header_identity)

        self.retry = RetryState()
        self.retry.hide()
        self.retry.retry_requested.connect(self.retry_requested)
        self.scaffold.main_content.addWidget(self.retry)
        self.scaffold.main_content.addWidget(self.state_label)

        self.pages = QStackedWidget()
        self.pages.setAccessibleName("לקוחות: רשימה ופרטי לקוח")
        self.list_page = self._build_list_page()
        self.details_page = self._build_details_page()
        self.pages.addWidget(self.list_page)
        self.pages.addWidget(self.details_page)
        self.scaffold.main_content.addWidget(self.pages, 1)

        self.footer = PaginationFooter()
        self.footer.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.footer.page_requested.connect(self.page_requested)
        self.footer.previous_button.setMaximumWidth(120)
        self.footer.next_button.setMaximumWidth(120)
        self.footer.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer.setMaximumWidth(440)
        self.list_layout.addWidget(self.footer, alignment=Qt.AlignmentFlag.AlignHCenter)
        self._set_list_page()
        self.clear_details()

        order = (
            self.toolbar.search_input,
            self.toolbar.search_button,
            self.sort_by,
            self.toolbar.refresh_button,
            self.create_button,
            self.table,
            self.view_details_button,
            self.back_button,
            self.edit_button,
            self.change_password_button,
            self.delete_button,
        )
        for first, second in zip(order, order[1:]):
            QWidget.setTabOrder(first, second)

    def _build_list_page(self) -> QWidget:
        page = QWidget()
        self.list_layout = QVBoxLayout(page)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(SPACE_2)

        search_panel = QWidget()
        search_panel.setObjectName("filterPanel")
        search_layout = QVBoxLayout(search_panel)
        search_layout.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_3)
        search_layout.setSpacing(SPACE_3)
        self.toolbar = SearchToolbar(
            placeholder="חיפוש לפי שם, דוא״ל או טלפון",
            sort_options=(("name", "מיון לפי: שם"), ("created_at", "מיון לפי: תאריך יצירה")),
        )
        configure_reference_toolbar(self.toolbar)
        self.toolbar.search_input.setMinimumWidth(300)
        self.toolbar.search_button.setObjectName("customerSearchButton")
        self.toolbar.search_button.setProperty("primary", True)
        self.toolbar.search_requested.connect(self._search)
        self.toolbar.refresh_button.setText("איפוס")
        self.toolbar.refresh_button.setAccessibleName("איפוס חיפוש ומיון")
        self.toolbar.refresh_button.setAccessibleDescription("ניקוי החיפוש, איפוס המיון וחזרה לעמוד הראשון")
        self.toolbar.refresh_requested.connect(self._reset_filters)
        self.sort_by = self.toolbar.sort_combo
        self.sort_by.setMinimumWidth(190)
        self.sort_by.setAccessibleName("מיון לפי")
        self.sort_by.currentIndexChanged.connect(self._sort_changed)
        search_layout.addWidget(self.toolbar)
        self.list_layout.addWidget(search_panel)

        table_heading = QHBoxLayout()
        table_heading.setDirection(QBoxLayout.Direction.RightToLeft)
        self.results_label = QLabel("רשימת הלקוחות")
        self.results_label.setObjectName("sectionTitle")
        self.results_label.setAccessibleName("תוצאות לקוחות")
        table_heading.addWidget(self.results_label)
        table_heading.addStretch()
        self.view_details_button = QPushButton("הצגת פרטים")
        self.view_details_button.setAccessibleName("פתיחת פרטי הלקוח שנבחר")
        self.view_details_button.clicked.connect(self._open_selected_customer)
        table_heading.addWidget(self.view_details_button)
        self.list_layout.addLayout(table_heading)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["שם לקוח", "סוג", "עיר", "מצב"])
        self.table.verticalHeader().hide()
        configure_data_table(
            self.table,
            "רשימת לקוחות",
            (
                ColumnPolicy(ColumnKind.PRIMARY_TEXT, 180),
                ColumnPolicy(ColumnKind.SECONDARY_TEXT, 140, 220),
                ColumnPolicy(ColumnKind.SECONDARY_TEXT, 150, 240),
                ColumnPolicy(ColumnKind.COMPACT, 110),
            ),
        )
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.table.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
            | Qt.AlignmentFlag.AlignAbsolute
        )
        self.table.setAccessibleDescription("חץ למעלה ולמטה לבחירה; Enter או לחיצה כפולה לפתיחת פרטים")
        self.table.itemSelectionChanged.connect(self._select)
        self.table.cellDoubleClicked.connect(lambda _row, _column: self._open_selected_customer())
        self.table.installEventFilter(self)
        self.table_region = QStackedWidget()
        self.table_region.setAccessibleName("תוצאות לקוחות")
        self.empty_state = QWidget()
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setContentsMargins(SPACE_6, SPACE_6, SPACE_6, SPACE_6)
        empty_layout.setSpacing(SPACE_3)
        empty_layout.addStretch()
        self.empty_title = QLabel()
        self.empty_title.setObjectName("sectionTitle")
        self.empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_description = QLabel()
        self.empty_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_description.setWordWrap(True)
        self.empty_action_button = QPushButton()
        self.empty_action_button.setObjectName("customerEmptyActionButton")
        self.empty_action_button.setProperty("primary", True)
        self.empty_action_button.setMinimumWidth(160)
        self.empty_action_button.clicked.connect(self._empty_action)
        empty_layout.addWidget(self.empty_title)
        empty_layout.addWidget(self.empty_description)
        empty_layout.addWidget(self.empty_action_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        empty_layout.addStretch()
        self.table_region.addWidget(self.table)
        self.table_region.addWidget(self.empty_state)
        self.list_layout.addWidget(self.table_region, 1)
        return page

    def _build_details_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACE_4)

        navigation_widget = QWidget()
        navigation_widget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        navigation = QHBoxLayout(navigation_widget)
        navigation.setContentsMargins(0, 0, 0, 0)
        navigation.setDirection(QBoxLayout.Direction.LeftToRight)
        self.back_button = QPushButton("חזרה לרשימת הלקוחות")
        self.back_button.setAccessibleName("חזרה לרשימת הלקוחות")
        self.back_button.clicked.connect(self._set_list_page)
        navigation.addWidget(self.back_button)
        navigation.addStretch()
        layout.addWidget(navigation_widget)

        header = QFrame()
        header.setObjectName("pageHeader")
        header.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        header_layout = QHBoxLayout(header)
        header_layout.setDirection(QBoxLayout.Direction.LeftToRight)
        header_layout.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_3)
        self.identity_container = QWidget()
        self.identity_container.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        identity = QVBoxLayout(self.identity_container)
        identity.setContentsMargins(0, 0, 0, 0)
        identity.setSpacing(SPACE_2)
        identity_top = QHBoxLayout()
        identity_top.setContentsMargins(0, 0, 0, 0)
        identity_top.setDirection(QBoxLayout.Direction.RightToLeft)
        self.detail_title = QLabel("פרטי לקוח")
        self.detail_title.setObjectName("screenTitle")
        self.detail_title.setAccessibleName("פרטי לקוח")
        self.detail_title.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.detail_subtitle = QLabel("מידע מלא ופעולות עבור הלקוח שנבחר")
        self.detail_subtitle.setWordWrap(True)
        self.detail_subtitle.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.detail_status = ActiveBadge()
        identity_top.addWidget(self.detail_title)
        identity_top.addStretch()
        identity.addLayout(identity_top)
        identity.addWidget(self.detail_status, alignment=Qt.AlignmentFlag.AlignRight)
        identity.addWidget(self.detail_subtitle)
        self.actions_container = QWidget()
        actions = QHBoxLayout(self.actions_container)
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(SPACE_2)
        self.edit_button = QPushButton("עריכת לקוח")
        self.change_password_button = QPushButton("שינוי סיסמה")
        self.delete_button = QPushButton("מחיקת לקוח")
        self.edit_button.clicked.connect(self.edit_requested)
        self.change_password_button.clicked.connect(self.change_password_requested)
        self.delete_button.clicked.connect(self.delete_requested)
        self.edit_button.setAccessibleName("עריכת הלקוח")
        self.change_password_button.setAccessibleName("שינוי סיסמת הלקוח")
        self.delete_button.setAccessibleName("מחיקת הלקוח")
        self.delete_button.setProperty("destructive", True)
        actions.addWidget(self.delete_button)
        actions.addWidget(self.change_password_button)
        actions.addWidget(self.edit_button)
        for button in (self.edit_button, self.change_password_button, self.delete_button):
            button.setMinimumSize(148, 40)
            button.setMaximumWidth(148)
        header_layout.addWidget(self.actions_container)
        header_layout.addStretch()
        header_layout.addWidget(self.identity_container)
        layout.addWidget(header)

        self.detail_loading_label = QLabel("טוען פרטי לקוח…")
        self.detail_loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_loading_label.setAccessibleName("מצב טעינת פרטי לקוח")
        layout.addWidget(self.detail_loading_label, 1)

        self.details_widget = QWidget()
        self.details_widget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        detail_layout = QVBoxLayout(self.details_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_sections = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        self.detail_sections.setContentsMargins(0, 0, 0, 0)
        self.detail_sections.setSpacing(SPACE_4)
        self.detail_forms: dict[str, QGridLayout] = {}
        customer_group, self.customer_details = self._detail_group("פרטי לקוח")
        contact_group, self.contact_details = self._detail_group("פרטי קשר")
        system_group, self.system_details = self._detail_group("מידע מערכת")
        self.detail_forms = {
            "customer": self.customer_details,
            "contact": self.contact_details,
            "system": self.system_details,
        }
        self.detail_groups = {
            "customer": customer_group,
            "contact": contact_group,
            "system": system_group,
        }
        self._detail_rows = {key: 0 for key in self.detail_forms}
        self.secondary_details = QWidget()
        self.secondary_details.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        secondary = QVBoxLayout(self.secondary_details)
        secondary.setContentsMargins(0, 0, 0, 0)
        secondary.setSpacing(SPACE_4)
        secondary.addWidget(contact_group)
        secondary.addWidget(system_group)
        secondary.addStretch()
        self.detail_sections.addWidget(customer_group)
        self.detail_sections.addWidget(self.secondary_details)
        detail_layout.addLayout(self.detail_sections)
        detail_layout.addStretch()
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.details_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.details_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.details_scroll.setWidget(self.details_widget)
        self.details_scroll.viewport().installEventFilter(self)
        self._update_details_composition(self.details_scroll.viewport().width())
        layout.addWidget(self.details_scroll, 1)
        return page

    @staticmethod
    def _detail_group(title: str) -> tuple[QFrame, QGridLayout]:
        group = QFrame()
        group.setObjectName("detailPanel")
        group.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        group.setAccessibleName(title)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(SPACE_4, SPACE_4, SPACE_4, SPACE_4)
        layout.setSpacing(SPACE_3)
        heading_row = QWidget()
        heading_row.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        heading_layout = QHBoxLayout(heading_row)
        heading_layout.setContentsMargins(0, 0, 0, 0)
        heading_layout.addStretch()
        heading = QLabel(title)
        heading.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        heading.setObjectName("sectionTitle")
        heading.setAccessibleName(title)
        heading.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        heading_layout.addWidget(heading)
        group.section_heading = heading
        layout.addWidget(heading_row)
        fields = QGridLayout()
        fields.setContentsMargins(0, 0, 0, 0)
        fields.setVerticalSpacing(SPACE_3)
        fields.setHorizontalSpacing(SPACE_4)
        fields.setColumnStretch(0, 1)
        fields.setColumnStretch(1, 0)
        fields.setColumnMinimumWidth(1, DETAIL_LABEL_WIDTH)
        layout.addLayout(fields)
        layout.addStretch()
        return group, fields

    def _clear_detail_forms(self) -> None:
        for key, fields in self.detail_forms.items():
            while fields.count():
                item = fields.takeAt(0)
                if item.widget() is not None:
                    item.widget().deleteLater()
            self._detail_rows[key] = 0

    def _detail_row_count(self) -> int:
        return sum(self._detail_rows.values())

    def eventFilter(self, watched, event) -> bool:
        if watched is self.table and event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._open_selected_customer()
            return True
        details_scroll = getattr(self, "details_scroll", None)
        if details_scroll is not None and watched is details_scroll.viewport() and event.type() == QEvent.Type.Resize:
            self._update_details_composition(event.size().width())
        return super().eventFilter(watched, event)

    def _update_details_composition(self, width: int) -> None:
        wide = width >= DETAILS_WIDE_BREAKPOINT
        self.detail_sections.setDirection(
            QBoxLayout.Direction.RightToLeft if wide else QBoxLayout.Direction.TopToBottom
        )
        self.detail_sections.setStretch(0, 3 if wide else 0)
        self.detail_sections.setStretch(1, 2 if wide else 0)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape and self.pages.currentWidget() is self.details_page:
            self._set_list_page()
            return
        super().keyPressEvent(event)

    def _search(self, search: str, _unused_sort: str) -> None:
        self.filters_requested.emit({"search": search or None, "order_by": self.sort_by.currentData()})

    def _sort_changed(self) -> None:
        self.filters_requested.emit({"order_by": self.sort_by.currentData()})

    def _reset_filters(self) -> None:
        self.toolbar.search_input.clear()
        was_blocked = self.sort_by.blockSignals(True)
        self.sort_by.setCurrentIndex(0)
        self.sort_by.blockSignals(was_blocked)
        self.clear_details()
        self.filters_requested.emit({
            "search": None,
            "order_by": "name",
            "_clear_selection": True,
        })

    def _empty_action(self) -> None:
        if getattr(self, "_empty_filtered", False):
            self._reset_filters()
        else:
            self.create_requested.emit()

    def _select(self) -> None:
        selected_indexes = self.table.selectionModel().selectedIndexes()
        if not selected_indexes:
            self._selected_customer_id = None
            self.view_details_button.setEnabled(False)
            set_disabled_explanation(self.view_details_button, "יש לבחור לקוח תחילה")
            return
        customer_id = str(self.table.item(selected_indexes[0].row(), 0).data(Qt.ItemDataRole.UserRole))
        selection_changed = customer_id != self._selected_customer_id
        if selection_changed:
            self._clear_detail_forms()
            self.detail_title.setText("פרטי לקוח")
            self.details_scroll.hide()
            self.edit_button.setEnabled(False)
            self.change_password_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        self._selected_customer_id = customer_id
        self.view_details_button.setEnabled(True)
        self.view_details_button.setAccessibleDescription("פותח את כרטיס הלקוח שנבחר")
        if selection_changed:
            self.customer_selected.emit(self._selected_customer_id)

    def _open_selected_customer(self) -> None:
        if not self._selected_customer_id and self.table.currentRow() >= 0:
            self._selected_customer_id = str(self.table.item(self.table.currentRow(), 0).data(Qt.ItemDataRole.UserRole))
        if self._selected_customer_id:
            self.scaffold.header.hide()
            self.pages.setCurrentWidget(self.details_page)
            self.back_button.setFocus()

    def _set_list_page(self) -> None:
        self.scaffold.header.show()
        self.pages.setCurrentWidget(self.list_page)
        if hasattr(self, "table"):
            self.table.setFocus()

    def set_loading(self, value: bool) -> None:
        super().set_loading(value)
        self.create_button.setEnabled(not value)
        self.toolbar.search_button.setEnabled(not value)
        self.toolbar.refresh_button.setEnabled(not value)
        self.sort_by.setEnabled(not value)
        self.empty_action_button.setEnabled(not value)
        self.view_details_button.setEnabled(not value and self._selected_customer_id is not None)
        has_details = self._detail_row_count() > 0
        self.edit_button.setEnabled(not value and has_details)
        self.change_password_button.setEnabled(not value and has_details)
        self.delete_button.setEnabled(not value and has_details)

    def set_detail_loading(self, value: bool) -> None:
        self.detail_loading_label.setVisible(value)
        self.details_scroll.setVisible(not value and self._detail_row_count() > 0)
        if value:
            self.edit_button.setEnabled(False)
            self.change_password_button.setEnabled(False)
            self.delete_button.setEnabled(False)

    def render_request_state(self, state: RequestState) -> None:
        if state.operation_key == "detail":
            if state.phase == RequestPhase.LOADING:
                self.set_detail_loading(True)
            return
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
        previous_scroll = self.table.verticalScrollBar().value()
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column, key in enumerate(("name", "customer_type", "city")):
                item = QTableWidgetItem(str(row[key]))
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight
                    | Qt.AlignmentFlag.AlignVCenter
                    | Qt.AlignmentFlag.AlignAbsolute
                )
                set_item_text(self.table, row_index, column, item, tooltip_direction=Qt.LayoutDirection.RightToLeft)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, row["id"])
            badge = ActiveBadge()
            badge.set_active(row["is_active"])
            badge.setAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
                | Qt.AlignmentFlag.AlignAbsolute
            )
            badge.setContentsMargins(SPACE_3, 0, SPACE_3, 0)
            self.table.setCellWidget(row_index, 3, badge)
        self.results_label.setText(f"לקוחות • {len(rows)}")
        self.footer.set_page(offset=offset, count=count)
        first = offset + 1 if count else 0
        self.footer.label.setText(f"מציג לקוחות {first}–{offset + count}")
        if rows:
            self.table.verticalScrollBar().setValue(min(previous_scroll, self.table.verticalScrollBar().maximum()))
        if not rows and offset > 0:
            # A deletion can empty the final page.  Stay in the list and ask
            # for the preceding valid page without changing any filter state.
            self.page_requested.emit(max(0, offset - self.footer.limit), self.footer.limit)
            return
        if not rows:
            self._empty_filtered = filtered
            self.empty_title.setText("לא נמצאו לקוחות" if filtered else "אין עדיין לקוחות")
            self.empty_description.setText(
                "נסו לשנות את החיפוש או לאפס את המסננים."
                if filtered else "צרו את הלקוח הראשון כדי להתחיל."
            )
            self.empty_action_button.setText("איפוס חיפוש ומסננים" if filtered else "לקוח חדש")
            self.empty_action_button.setAccessibleName(self.empty_action_button.text())
            self.table_region.setCurrentWidget(self.empty_state)
            self.view_details_button.hide()
            self.footer.hide()
            self.state_label.hide()
        else:
            self.table_region.setCurrentWidget(self.table)
            self.view_details_button.show()
            self.footer.show()
            if self.state_label.text() != "טוען נתונים…":
                self.state_label.hide()

    def show_details(self, details, customer) -> None:
        self._clear_detail_forms()
        for label, value in details:
            content = QLabel(value)
            content.setWordWrap(True)
            content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            content.setAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
                | Qt.AlignmentFlag.AlignAbsolute
            )
            content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            content.setToolTip(value)
            if any(token in label for token in ("דוא", "טלפון", "מזהה")):
                configure_mixed_direction(content)
                content.setAlignment(
                    Qt.AlignmentFlag.AlignRight
                    | Qt.AlignmentFlag.AlignVCenter
                    | Qt.AlignmentFlag.AlignAbsolute
                )
            if label in {"איש קשר", "טלפון איש קשר"}:
                section = "contact"
            elif label in {"מצב", "נוצר", "עודכן"}:
                section = "system"
            else:
                section = "customer"
            label_widget = QLabel(label)
            label_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            label_widget.setFixedWidth(DETAIL_LABEL_WIDTH)
            label_widget.setAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
                | Qt.AlignmentFlag.AlignAbsolute
            )
            target = self.detail_forms[section]
            row = self._detail_rows[section]
            target.addWidget(content, row, 0)
            target.addWidget(label_widget, row, 1)
            self._detail_rows[section] += 1
        self.detail_title.setText(str(customer.get("name") or "פרטי לקוח"))
        self.detail_title.setAccessibleName(f"פרטי לקוח: {self.detail_title.text()}")
        self.detail_status.set_active(bool(customer.get("is_active")))
        self.detail_loading_label.hide()
        self.details_scroll.show()
        self.edit_button.setEnabled(True)
        self.change_password_button.setEnabled(True)
        self.delete_button.setEnabled(True)

    def clear_details(self) -> None:
        if hasattr(self, "detail_forms"):
            self._clear_detail_forms()
        if hasattr(self, "detail_title"):
            self.detail_title.setText("פרטי לקוח")
            self.details_scroll.hide()
            self.detail_loading_label.hide()
        self._selected_customer_id = None
        for button in (getattr(self, "view_details_button", None), getattr(self, "edit_button", None), getattr(self, "change_password_button", None), getattr(self, "delete_button", None)):
            if button:
                button.setEnabled(False)
                set_disabled_explanation(button, "יש לבחור לקוח תחילה")
        if hasattr(self, "pages"):
            self._set_list_page()

    def reset_to_default(self) -> None:
        dialog = getattr(self, "_dialog", None)
        if dialog is not None and dialog.isVisible():
            dialog.reject()
        self.scaffold.feedback.hide()
        self.toolbar.search_input.clear()
        blocked = self.sort_by.blockSignals(True)
        self.sort_by.setCurrentIndex(0)
        self.sort_by.blockSignals(blocked)
        self.table.clearSelection()
        self.clear_details()

    def select_customer(self, customer_id: str) -> None:
        for row in range(self.table.rowCount()):
            if str(self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)) == customer_id:
                signals_were_blocked = self.table.blockSignals(True)
                index = self.table.model().index(row, 0)
                self.table.selectionModel().setCurrentIndex(
                    index,
                    QItemSelectionModel.SelectionFlag.ClearAndSelect
                    | QItemSelectionModel.SelectionFlag.Rows,
                )
                self.table.blockSignals(signals_were_blocked)
                selection_changed = self._selected_customer_id != customer_id
                self._selected_customer_id = customer_id
                self.view_details_button.setEnabled(True)
                if selection_changed:
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
