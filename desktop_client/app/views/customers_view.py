from PySide6.QtCore import QDate, QEvent, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QBoxLayout,
    QDateEdit,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.views.common import StatefulWidget
from desktop_client.app.views.customer_dialogs import CustomerDialog
from desktop_client.app.views.design_tokens import SPACE_2, SPACE_3, SPACE_4, SPACE_6
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
        self._selected_customer_id: str | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.scaffold = PageScaffold("לקוחות", "ניהול לקוחות ופרטי קשר")
        self.scaffold.root.setSpacing(SPACE_3)
        self.scaffold.header.layout().setContentsMargins(SPACE_3, SPACE_2, SPACE_3, SPACE_2)
        self.scaffold.header.layout().setSpacing(SPACE_2)
        root.addWidget(self.scaffold)

        self.create_button = QPushButton("לקוח חדש")
        self.create_button.setObjectName("customerCreateButton")
        self.create_button.setAccessibleName("יצירת לקוח חדש")
        self.create_button.setProperty("primary", True)
        self.create_button.clicked.connect(self.create_requested)
        self.scaffold.header.add_action(self.create_button)
        self.scaffold.header.layout().itemAt(0).layout().setDirection(QBoxLayout.Direction.RightToLeft)

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
            self.filter_by_button,
            self.toolbar.refresh_button,
            self.create_button,
            self.table,
            self.view_details_button,
            self.back_button,
            self.edit_button,
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
        search_layout = QVBoxLayout(search_panel)
        search_layout.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_3)
        search_layout.setSpacing(SPACE_3)
        self.toolbar = SearchToolbar(placeholder="חיפוש לפי שם, דוא״ל או טלפון")
        self.toolbar.layout().setDirection(QBoxLayout.Direction.RightToLeft)
        self.toolbar.search_input.setMinimumWidth(420)
        self.toolbar.search_button.setObjectName("customerSearchButton")
        self.toolbar.search_button.setProperty("primary", True)
        self.toolbar.search_requested.connect(self._search)
        self.toolbar.refresh_button.setText("איפוס")
        self.toolbar.refresh_button.setAccessibleName("איפוס חיפוש ומסננים")
        self.toolbar.refresh_button.setAccessibleDescription("ניקוי החיפוש והמסננים, איפוס המיון וחזרה לעמוד הראשון")
        self.toolbar.refresh_requested.connect(self._reset_filters)
        self.filter_by_button = QPushButton("סינון לפי")
        self.filter_by_button.setAccessibleName("הוספת מסנן לרשימת הלקוחות")
        self.filter_by_button.clicked.connect(self._show_filter_menu)
        toolbar_layout = self.toolbar.layout()
        toolbar_layout.insertWidget(toolbar_layout.count() - 1, self.filter_by_button)
        search_layout.addWidget(self.toolbar)

        self.filter_panel = QWidget()
        self.filter_panel.setAccessibleName("מסננים פעילים")
        filter_layout = QHBoxLayout(self.filter_panel)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(SPACE_2)
        filter_layout.setDirection(QBoxLayout.Direction.RightToLeft)
        self.active_filter_layout = QHBoxLayout()
        self.active_filter_layout.setSpacing(SPACE_2)
        filter_layout.addLayout(self.active_filter_layout, 1)
        self.apply_filters_button = QPushButton("החל")
        self.apply_filters_button.setAccessibleName("החלת מסנני לקוחות")
        self.apply_filters_button.clicked.connect(self._filters)
        filter_layout.addWidget(self.apply_filters_button)
        self.filter_panel.hide()
        self.active_filters: dict[str, QWidget] = {}
        self.filter_menu = QMenu(self)
        self.filter_menu.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        for key, label in (
            ("name", "שם"), ("city", "עיר"), ("customer_type", "סוג לקוח"),
            ("is_active", "מצב"), ("email", "דוא״ל"), ("phone", "טלפון"),
            ("created_at", "תאריך יצירה"), ("updated_at", "תאריך עדכון"),
        ):
            action = self.filter_menu.addAction(label)
            action.triggered.connect(lambda _checked=False, field=key: self._add_filter(field))
        search_layout.addWidget(self.filter_panel)
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
                ColumnPolicy(ColumnKind.PRIMARY_TEXT),
                ColumnPolicy(ColumnKind.COMPACT, 110),
                ColumnPolicy(ColumnKind.SECONDARY_TEXT),
                ColumnPolicy(ColumnKind.COMPACT),
            ),
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

    def _show_filter_menu(self) -> None:
        self.filter_menu.exec(self.filter_by_button.mapToGlobal(self.filter_by_button.rect().bottomRight()))

    def _add_filter(self, field: str) -> None:
        if field in self.active_filters:
            editor = self.active_filters[field].findChild(QWidget, "filterEditor")
            if editor:
                editor.setFocus()
            return
        labels = {"name": "שם", "city": "עיר", "customer_type": "סוג לקוח", "is_active": "מצב", "email": "דוא״ל", "phone": "טלפון", "created_at": "תאריך יצירה", "updated_at": "תאריך עדכון"}
        container = QWidget()
        container.setAccessibleName(f"מסנן {labels[field]}")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACE_2)
        layout.addWidget(QLabel(labels[field]))
        if field == "is_active":
            editor = QComboBox()
            editor.addItem("הכול", None); editor.addItem("פעילים", True); editor.addItem("לא פעילים", False)
        elif field in {"created_at", "updated_at"}:
            editor = QDateEdit(QDate.currentDate())
            editor.setCalendarPopup(True)
            editor.setDisplayFormat("dd/MM/yyyy")
        else:
            editor = QLineEdit()
            editor.setPlaceholderText(f"הזנת {labels[field]}")
            if field in {"email", "phone"}:
                configure_mixed_direction(editor)
        editor.setObjectName("filterEditor")
        editor.setAccessibleName(f"סינון לפי {labels[field]}")
        editor.setMinimumWidth(150)
        layout.addWidget(editor)
        self.active_filter_layout.addWidget(container)
        self.active_filters[field] = container
        self.filter_panel.show()
        editor.setFocus()

    def _build_details_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACE_4)

        navigation = QHBoxLayout()
        navigation.setDirection(QBoxLayout.Direction.RightToLeft)
        self.back_button = QPushButton("חזרה לרשימת הלקוחות")
        self.back_button.setAccessibleName("חזרה לרשימת הלקוחות")
        self.back_button.clicked.connect(self._set_list_page)
        navigation.addWidget(self.back_button)
        navigation.addStretch()
        layout.addLayout(navigation)

        header = QFrame()
        header.setObjectName("pageHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setDirection(QBoxLayout.Direction.RightToLeft)
        header_layout.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_3)
        identity = QVBoxLayout()
        identity.setSpacing(SPACE_2)
        self.detail_title = QLabel("פרטי לקוח")
        self.detail_title.setObjectName("screenTitle")
        self.detail_title.setAccessibleName("פרטי לקוח")
        self.detail_subtitle = QLabel("מידע מלא ופעולות עבור הלקוח שנבחר")
        identity.addWidget(self.detail_title)
        identity.addWidget(self.detail_subtitle)
        header_layout.addLayout(identity, 1)
        self.detail_status = ActiveBadge()
        header_layout.addWidget(self.detail_status)
        self.edit_button = QPushButton("עריכת לקוח")
        self.delete_button = QPushButton("מחיקת לקוח")
        self.edit_button.clicked.connect(self.edit_requested)
        self.delete_button.clicked.connect(self.delete_requested)
        self.edit_button.setAccessibleName("עריכת הלקוח")
        self.delete_button.setAccessibleName("מחיקת הלקוח")
        self.delete_button.setProperty("destructive", True)
        header_layout.addWidget(self.edit_button)
        header_layout.addWidget(self.delete_button)
        layout.addWidget(header)

        self.detail_loading_label = QLabel("טוען פרטי לקוח…")
        self.detail_loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_loading_label.setAccessibleName("מצב טעינת פרטי לקוח")
        layout.addWidget(self.detail_loading_label, 1)

        self.details_widget = QWidget()
        detail_layout = QVBoxLayout(self.details_widget)
        detail_layout.setContentsMargins(SPACE_6, SPACE_6, SPACE_6, SPACE_6)
        sections = QHBoxLayout()
        sections.setDirection(QBoxLayout.Direction.RightToLeft)
        sections.setSpacing(SPACE_4)
        self.detail_forms: dict[str, QFormLayout] = {}
        customer_group, self.customer_details = self._detail_group("פרטי לקוח")
        contact_group, self.contact_details = self._detail_group("פרטי קשר")
        system_group, self.system_details = self._detail_group("מידע מערכת")
        self.detail_forms = {
            "customer": self.customer_details,
            "contact": self.contact_details,
            "system": self.system_details,
        }
        secondary = QVBoxLayout()
        secondary.setSpacing(SPACE_4)
        secondary.addWidget(contact_group)
        secondary.addWidget(system_group)
        secondary.addStretch()
        sections.addWidget(customer_group, 3)
        sections.addLayout(secondary, 2)
        detail_layout.addLayout(sections)
        detail_layout.addStretch()
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.details_scroll.setWidget(self.details_widget)
        layout.addWidget(self.details_scroll, 1)
        return page

    @staticmethod
    def _detail_group(title: str) -> tuple[QWidget, QFormLayout]:
        group = QWidget()
        group.setAccessibleName(title)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(SPACE_4, SPACE_2, SPACE_4, SPACE_2)
        layout.setSpacing(SPACE_3)
        heading = QLabel(title)
        heading.setObjectName("sectionTitle")
        heading.setAccessibleName(title)
        layout.addWidget(heading)
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setVerticalSpacing(SPACE_3)
        form.setHorizontalSpacing(SPACE_4)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        layout.addLayout(form)
        layout.addStretch()
        return group, form

    def _clear_detail_forms(self) -> None:
        for form in self.detail_forms.values():
            while form.rowCount():
                form.removeRow(0)

    def _detail_row_count(self) -> int:
        return sum(form.rowCount() for form in self.detail_forms.values())

    def eventFilter(self, watched, event) -> bool:
        if watched is self.table and event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._open_selected_customer()
            return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape and self.pages.currentWidget() is self.details_page:
            self._set_list_page()
            return
        super().keyPressEvent(event)

    def _search(self, search: str, _unused_sort: str) -> None:
        self.filters_requested.emit({"search": search or None, **self._filter_values()})

    def _reset_filters(self) -> None:
        self.toolbar.search_input.clear()
        while self.active_filter_layout.count():
            item = self.active_filter_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.active_filters.clear()
        self.filter_panel.hide()
        self.filters_requested.emit({
            "search": None,
            "city": None,
            "customer_type": None,
            "is_active": None,
            "order_by": "name",
        })

    def _empty_action(self) -> None:
        if getattr(self, "_empty_filtered", False):
            self._reset_filters()
        else:
            self.create_requested.emit()

    def _filters(self) -> None:
        self.filters_requested.emit(self._filter_values())

    def _filter_values(self) -> dict[str, object]:
        values: dict[str, object] = {"city": None, "customer_type": None, "is_active": None, "order_by": "name"}
        search_terms: list[str] = []
        for field, container in self.active_filters.items():
            editor = container.findChild(QWidget, "filterEditor")
            if isinstance(editor, QLineEdit):
                value = editor.text().strip()
                if field in {"name", "email", "phone"} and value:
                    search_terms.append(value)
                elif field in {"city", "customer_type"}:
                    values[field] = value or None
            elif isinstance(editor, QComboBox):
                values[field] = editor.currentData()
            elif isinstance(editor, QDateEdit):
                # The existing Customer API exposes creation-date ordering only;
                # retain the selected date locally until date-range querying is
                # introduced as a separately scoped backend task.
                if field == "created_at":
                    values["order_by"] = "created_at"
        if search_terms:
            values["search"] = " ".join(search_terms)
        return values

    def _select(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self._selected_customer_id = None
            self.view_details_button.setEnabled(False)
            set_disabled_explanation(self.view_details_button, "יש לבחור לקוח תחילה")
            return
        customer_id = str(self.table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole))
        if customer_id != self._selected_customer_id:
            self._clear_detail_forms()
            self.detail_title.setText("פרטי לקוח")
            self.details_scroll.hide()
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        self._selected_customer_id = customer_id
        self.view_details_button.setEnabled(True)
        self.view_details_button.setAccessibleDescription("פותח את כרטיס הלקוח שנבחר")
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
        self.filter_by_button.setEnabled(not value)
        self.apply_filters_button.setEnabled(not value)
        self.empty_action_button.setEnabled(not value)
        self.view_details_button.setEnabled(not value and self._selected_customer_id is not None)
        has_details = self._detail_row_count() > 0
        self.edit_button.setEnabled(not value and has_details)
        self.delete_button.setEnabled(not value and has_details)

    def set_detail_loading(self, value: bool) -> None:
        self.detail_loading_label.setVisible(value)
        self.details_scroll.setVisible(not value and self._detail_row_count() > 0)
        if value:
            self.edit_button.setEnabled(False)
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
                set_item_text(self.table, row_index, column, item, tooltip_direction=Qt.LayoutDirection.RightToLeft)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, row["id"])
            badge = ActiveBadge()
            badge.set_active(row["is_active"])
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
            content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            content.setToolTip(value)
            if any(token in label for token in ("דוא", "טלפון", "מזהה")):
                configure_mixed_direction(content)
            if label in {"איש קשר", "טלפון איש קשר"}:
                target = self.contact_details
            elif label in {"מצב", "נוצר", "עודכן"}:
                target = self.system_details
            else:
                target = self.customer_details
            target.addRow(label, content)
        self.detail_title.setText(str(customer.get("name") or "פרטי לקוח"))
        self.detail_title.setAccessibleName(f"פרטי לקוח: {self.detail_title.text()}")
        self.detail_status.set_active(bool(customer.get("is_active")))
        self.detail_loading_label.hide()
        self.details_scroll.show()
        self.edit_button.setEnabled(True)
        self.delete_button.setEnabled(True)

    def clear_details(self) -> None:
        if hasattr(self, "detail_forms"):
            self._clear_detail_forms()
        if hasattr(self, "detail_title"):
            self.detail_title.setText("פרטי לקוח")
            self.details_scroll.hide()
            self.detail_loading_label.hide()
        self._selected_customer_id = None
        for button in (getattr(self, "view_details_button", None), getattr(self, "edit_button", None), getattr(self, "delete_button", None)):
            if button:
                button.setEnabled(False)
                set_disabled_explanation(button, "יש לבחור לקוח תחילה")
        if hasattr(self, "pages"):
            self._set_list_page()

    def select_customer(self, customer_id: str) -> None:
        for row in range(self.table.rowCount()):
            if str(self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)) == customer_id:
                self._selected_customer_id = customer_id
                self.view_details_button.setEnabled(True)
                self.table.selectRow(row)
                break

    def open_customer_form(self, initial, submit) -> None:
        self._dialog = CustomerDialog(initial, self)
        self._dialog.submitted.connect(submit)
        self._dialog.open()

    def confirm_customer_deletion(self, name: str) -> bool:
        return confirm_action(self, "אישור מחיקה", f"למחוק לצמיתות את הלקוח {name}? לא ניתן לבטל פעולה זו.")
