from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QBoxLayout, QFormLayout, QFrame, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QStackedWidget, QStyle, QTableWidget, QToolButton, QVBoxLayout, QWidget,
)

from desktop_client.app.views.design_tokens import CONTROL_HEIGHT, SPACE_2, SPACE_3, SPACE_4, SPACE_6
from desktop_client.app.views.management_common import ActiveBadge, PaginationFooter, SearchToolbar, apply_management_primary, configure_reference_toolbar
from desktop_client.app.views.ui_foundations import ColumnKind, ColumnPolicy, PageScaffold, configure_data_table


class ManagementWorkspace(QWidget):
    """Shared list-to-details composition for role-specific management modules."""

    def __init__(self, *, title: str, subtitle: str, create_text: str, plural: str,
                 detail_subtitle: str,
                 search_placeholder: str, sort_options: tuple[tuple[str, str], ...],
                 headers: tuple[str, ...], policies: tuple[ColumnPolicy, ...]) -> None:
        super().__init__()
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0)
        self.scaffold = PageScaffold(title, subtitle); self.scaffold.root.setSpacing(SPACE_3); root.addWidget(self.scaffold)
        self.scaffold.header.layout().setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_3); self.scaffold.header.layout().setSpacing(SPACE_2)
        self.scaffold.header.description.setWordWrap(False)
        self.scaffold.header.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        title_row = self.scaffold.header.layout().itemAt(0).layout(); title_row.setDirection(QBoxLayout.Direction.RightToLeft)
        title_row.removeWidget(self.scaffold.header.title); self.scaffold.header.layout().removeWidget(self.scaffold.header.description)
        identity = QWidget(); identity_layout = QVBoxLayout(identity); identity_layout.setContentsMargins(0, 0, 0, 0); identity_layout.setSpacing(SPACE_2)
        for label in (self.scaffold.header.title, self.scaffold.header.description):
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); identity_layout.addWidget(label)
        title_row.insertWidget(0, identity); self.header_identity = identity
        self.create_button = QPushButton(create_text); apply_management_primary(self.create_button); self.scaffold.header.add_action(self.create_button)
        self.pages = QStackedWidget(); self.list_page = QWidget(); self.details_page = QWidget(); self.pages.addWidget(self.list_page); self.pages.addWidget(self.details_page); self.scaffold.main_content.addWidget(self.pages, 1)

        listing = QVBoxLayout(self.list_page); listing.setContentsMargins(0, 0, 0, 0); listing.setSpacing(SPACE_2)
        toolbar_panel = QFrame(); toolbar_panel.setObjectName("filterPanel"); toolbar_layout = QVBoxLayout(toolbar_panel); toolbar_layout.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_3); toolbar_layout.setSpacing(SPACE_3)
        self.toolbar = SearchToolbar(placeholder=search_placeholder, sort_options=sort_options); configure_reference_toolbar(self.toolbar); self.toolbar.refresh_button.setText("איפוס"); toolbar_layout.addWidget(self.toolbar); listing.addWidget(toolbar_panel)
        heading = QHBoxLayout(); heading.setDirection(QBoxLayout.Direction.RightToLeft); self.results_label = QLabel(f"רשימת {plural}"); self.results_label.setObjectName("sectionTitle"); heading.addWidget(self.results_label); heading.addStretch(); listing.addLayout(heading)
        table_headers = ("פתיחה", *headers)
        table_policies = (ColumnPolicy(ColumnKind.ACTION, 52, 52), *policies)
        self.table = QTableWidget(0, len(table_headers)); self.table.setHorizontalHeaderLabels(list(table_headers)); self.table.verticalHeader().hide(); self.table.setLayoutDirection(Qt.LayoutDirection.RightToLeft); configure_data_table(self.table, f"רשימת {plural}", table_policies); self.table.setColumnWidth(0, 52); self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignAbsolute); self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table_region = QStackedWidget(); self.table_region.addWidget(self.table)
        self.empty_state = QWidget(); empty = QVBoxLayout(self.empty_state); empty.setContentsMargins(SPACE_6, SPACE_6, SPACE_6, SPACE_6); empty.setSpacing(SPACE_3); empty.addStretch(); self.empty_title = QLabel(); self.empty_title.setObjectName("sectionTitle"); self.empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter); self.empty_description = QLabel(); self.empty_description.setAlignment(Qt.AlignmentFlag.AlignCenter); self.empty_description.setWordWrap(True); self.empty_action_button = QPushButton(); self.empty_action_button.setProperty("primary", True); self.empty_action_button.setMinimumWidth(160); empty.addWidget(self.empty_title); empty.addWidget(self.empty_description); empty.addWidget(self.empty_action_button, alignment=Qt.AlignmentFlag.AlignHCenter); empty.addStretch(); self.table_region.addWidget(self.empty_state); listing.addWidget(self.table_region, 1)
        self.empty_label = self.empty_description
        self.footer = PaginationFooter(); self.footer.setLayoutDirection(Qt.LayoutDirection.RightToLeft); self.footer.previous_button.setMaximumWidth(120); self.footer.next_button.setMaximumWidth(120); self.footer.label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.footer.setMaximumWidth(440); listing.addWidget(self.footer, alignment=Qt.AlignmentFlag.AlignHCenter)

        detail = QVBoxLayout(self.details_page); detail.setContentsMargins(0, 0, 0, 0); detail.setSpacing(SPACE_4)
        navigation = QWidget(); navigation.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        back_row = QHBoxLayout(navigation); back_row.setContentsMargins(0, 0, 0, 0); back_row.setDirection(QBoxLayout.Direction.LeftToRight)
        self.back_button = QPushButton(f"חזרה לרשימת {plural}"); back_row.addWidget(self.back_button); back_row.addStretch(); detail.addWidget(navigation)
        self.detail_header = QFrame(); self.detail_header.setObjectName("pageHeader"); self.detail_header.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        header = QHBoxLayout(self.detail_header); header.setDirection(QBoxLayout.Direction.LeftToRight); header.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_3)
        self.actions_container = QWidget(); self.actions = QHBoxLayout(self.actions_container); self.actions.setContentsMargins(0, 0, 0, 0); self.actions.setSpacing(SPACE_2); header.addWidget(self.actions_container); header.addStretch()
        self.identity_container = QWidget(); self.identity_container.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        identity = QVBoxLayout(self.identity_container); identity.setContentsMargins(0, 0, 0, 0); identity.setSpacing(SPACE_2)
        identity_top = QHBoxLayout(); identity_top.setContentsMargins(0, 0, 0, 0); identity_top.setDirection(QBoxLayout.Direction.RightToLeft)
        self.detail_title = QLabel(); self.detail_title.setObjectName("screenTitle"); self.detail_title.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        identity_top.addWidget(self.detail_title); identity_top.addStretch(); identity.addLayout(identity_top)
        self.detail_status = ActiveBadge(); identity.addWidget(self.detail_status, alignment=Qt.AlignmentFlag.AlignRight)
        self.detail_subtitle = QLabel(detail_subtitle); self.detail_subtitle.setWordWrap(True); self.detail_subtitle.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); identity.addWidget(self.detail_subtitle)
        header.addWidget(self.identity_container); detail.addWidget(self.detail_header)
        self.details_widget = QWidget(); self.details_widget.setLayoutDirection(Qt.LayoutDirection.LeftToRight); detail_body = QVBoxLayout(self.details_widget); detail_body.setContentsMargins(0, 0, 0, 0)
        self.cards = QBoxLayout(QBoxLayout.Direction.RightToLeft); self.cards.setContentsMargins(0, 0, 0, 0); self.cards.setSpacing(SPACE_4); detail_body.addLayout(self.cards); detail_body.addStretch()
        self._primary_card = None; self._secondary_cards = None; self._secondary_layout = None
        self.details_scroll = QScrollArea(); self.details_scroll.setWidgetResizable(True); self.details_scroll.setFrameShape(QScrollArea.Shape.NoFrame); self.details_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); self.details_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); self.details_scroll.setWidget(self.details_widget); detail.addWidget(self.details_scroll, 1)
        self.back_button.clicked.connect(self.show_list); self.pages.setCurrentWidget(self.list_page)

    def set_row_open_action(self, row: int, entity_id: str, callback) -> QToolButton:
        button = QToolButton()
        button.setObjectName("managementRowOpenAction")
        button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft))
        button.setToolTip("פתיחת פרטים")
        button.setAccessibleName("פתיחת פרטים")
        button.setFixedSize(36, 32)
        button.clicked.connect(lambda _checked=False, value=entity_id: callback(value))
        host = QWidget(); layout = QHBoxLayout(host); layout.setContentsMargins(8, 4, 8, 4); layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.table.setCellWidget(row, 0, host)
        return button

    def add_action(self, text: str, *, destructive: bool = False) -> QPushButton:
        button = QPushButton(text); button.setMinimumSize(148, CONTROL_HEIGHT); button.setMaximumWidth(148); button.setProperty("destructive", destructive); self.actions.insertWidget(0, button); return button

    def add_lifecycle_actions(self, *, edit: str, password: str, deactivate: str, reactivate: str):
        edit_button = self.add_action(edit)
        password_button = self.add_action(password)
        deactivate_button = self.add_action(deactivate, destructive=True)
        reactivate_button = self.add_action(reactivate)
        deactivate_button.hide()
        reactivate_button.hide()
        return edit_button, password_button, deactivate_button, reactivate_button

    @staticmethod
    def show_lifecycle(active: bool, deactivate_button: QPushButton, reactivate_button: QPushButton) -> None:
        deactivate_button.setVisible(active)
        reactivate_button.setVisible(not active)

    def set_actions_enabled(self, enabled: bool) -> None:
        for index in range(self.actions.count()):
            widget = self.actions.itemAt(index).widget()
            if widget is not None: widget.setEnabled(enabled)

    def show_detail_identity(self, name: str, active: bool) -> None:
        self.detail_title.setText(name); self.detail_status.set_active(active)

    def show_details(self) -> None:
        self.scaffold.header.hide(); self.pages.setCurrentWidget(self.details_page); self.back_button.setFocus()

    def show_list(self) -> None:
        self.scaffold.header.show(); self.pages.setCurrentWidget(self.list_page); self.table.setFocus()

    def show_empty_state(self, *, empty: bool, filtered: bool, plural: str) -> None:
        self.table_region.setCurrentWidget(self.empty_state if empty else self.table)
        self.empty_title.show(); self.empty_description.show(); self.empty_action_button.show()
        self.empty_title.setText(f"לא נמצאו {plural}" if filtered else f"אין {plural} להצגה")
        self.empty_description.setText("אפשר לאפס את החיפוש ולנסות שוב." if filtered else f"אפשר ליצור {plural} חדשים כדי להתחיל.")
        self.empty_action_button.setText("איפוס חיפוש" if filtered else "יצירה חדשה")

    def show_loading(self, text: str) -> None:
        self.table_region.setCurrentWidget(self.empty_state); self.empty_title.hide(); self.empty_action_button.hide(); self.empty_description.setText(text); self.empty_description.show()

    def add_card(self, title: str):
        frame = QFrame(); frame.setObjectName("detailPanel"); frame.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        layout = QVBoxLayout(frame); layout.setContentsMargins(SPACE_4, SPACE_4, SPACE_4, SPACE_4); layout.setSpacing(SPACE_3)
        heading_row = QHBoxLayout(); heading_row.setContentsMargins(0, 0, 0, 0); heading_row.addStretch()
        heading = QLabel(title); heading.setObjectName("sectionTitle"); heading.setLayoutDirection(Qt.LayoutDirection.RightToLeft); heading.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); heading_row.addWidget(heading); layout.addLayout(heading_row)
        form_host = QWidget(); form_host.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        form = QFormLayout(form_host); form.setContentsMargins(0, 0, 0, 0); form.setHorizontalSpacing(SPACE_4); form.setVerticalSpacing(SPACE_3); form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); form.setFormAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight); form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        layout.addWidget(form_host); layout.addStretch()
        if self._primary_card is None:
            self._primary_card = frame; self.cards.addWidget(frame, 3)
        else:
            if self._secondary_cards is None:
                self._secondary_cards = QWidget(); self._secondary_cards.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
                self._secondary_layout = QVBoxLayout(self._secondary_cards); self._secondary_layout.setContentsMargins(0, 0, 0, 0); self._secondary_layout.setSpacing(SPACE_4)
                self.cards.addWidget(self._secondary_cards, 2)
            self._secondary_layout.addWidget(frame)
        return form

    @staticmethod
    def add_property_row(form: QFormLayout, label: str, content: QLabel) -> None:
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        content.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute)
        form.addRow(label, content)
        label_widget = form.itemAt(form.rowCount() - 1, QFormLayout.ItemRole.LabelRole).widget()
        if isinstance(label_widget, QLabel):
            label_widget.setFixedWidth(140); label_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft); label_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute)

    @staticmethod
    def configure_status_badge(badge: ActiveBadge) -> None:
        badge.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute)
        badge.setContentsMargins(SPACE_3, 0, SPACE_3, 0)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        self.cards.setDirection(QBoxLayout.Direction.RightToLeft if event.size().width() >= 880 else QBoxLayout.Direction.TopToBottom)
        super().resizeEvent(event)
