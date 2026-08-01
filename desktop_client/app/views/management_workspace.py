from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QBoxLayout, QFrame, QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QTableWidget, QVBoxLayout, QWidget,
)

from desktop_client.app.views.design_tokens import CONTROL_HEIGHT, SPACE_2, SPACE_3, SPACE_4
from desktop_client.app.views.management_common import ActiveBadge, PaginationFooter, SearchToolbar
from desktop_client.app.views.ui_foundations import ColumnPolicy, PageScaffold, configure_data_table


class ManagementWorkspace(QWidget):
    """Shared list-to-details composition for role-specific management modules."""

    def __init__(self, *, title: str, subtitle: str, create_text: str, plural: str,
                 search_placeholder: str, sort_options: tuple[tuple[str, str], ...],
                 headers: tuple[str, ...], policies: tuple[ColumnPolicy, ...]) -> None:
        super().__init__()
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0)
        self.scaffold = PageScaffold(title, subtitle); self.scaffold.root.setSpacing(SPACE_3); root.addWidget(self.scaffold)
        self.scaffold.header.description.setWordWrap(False)
        self.scaffold.header.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        title_row = self.scaffold.header.layout().itemAt(0).layout(); title_row.setDirection(QBoxLayout.Direction.RightToLeft)
        title_row.removeWidget(self.scaffold.header.title); self.scaffold.header.layout().removeWidget(self.scaffold.header.description)
        identity = QWidget(); identity_layout = QVBoxLayout(identity); identity_layout.setContentsMargins(0, 0, 0, 0); identity_layout.setSpacing(SPACE_2)
        for label in (self.scaffold.header.title, self.scaffold.header.description):
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); identity_layout.addWidget(label)
        title_row.insertWidget(0, identity); self.header_identity = identity
        self.create_button = QPushButton(create_text); self.create_button.setProperty("primary", True); self.scaffold.header.add_action(self.create_button)
        self.pages = QStackedWidget(); self.list_page = QWidget(); self.details_page = QWidget(); self.pages.addWidget(self.list_page); self.pages.addWidget(self.details_page); self.scaffold.main_content.addWidget(self.pages, 1)

        listing = QVBoxLayout(self.list_page); listing.setContentsMargins(0, 0, 0, 0); listing.setSpacing(SPACE_2)
        toolbar_panel = QFrame(); toolbar_panel.setObjectName("filterPanel"); toolbar_layout = QVBoxLayout(toolbar_panel); toolbar_layout.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_3)
        self.toolbar = SearchToolbar(placeholder=search_placeholder, sort_options=sort_options); self.toolbar.setLayoutDirection(Qt.LayoutDirection.RightToLeft); self.toolbar.refresh_button.setText("איפוס"); toolbar_layout.addWidget(self.toolbar); listing.addWidget(toolbar_panel)
        heading = QHBoxLayout(); heading.setDirection(QBoxLayout.Direction.RightToLeft); self.results_label = QLabel(f"רשימת {plural}"); self.results_label.setObjectName("sectionTitle"); heading.addWidget(self.results_label); heading.addStretch(); self.view_details_button = QPushButton("הצגת פרטים"); heading.addWidget(self.view_details_button); listing.addLayout(heading)
        self.table = QTableWidget(0, len(headers)); self.table.setHorizontalHeaderLabels(list(headers)); self.table.setLayoutDirection(Qt.LayoutDirection.RightToLeft); configure_data_table(self.table, f"רשימת {plural}", policies); self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); listing.addWidget(self.table, 1)
        self.footer = PaginationFooter(); self.footer.setMaximumWidth(440); listing.addWidget(self.footer, alignment=Qt.AlignmentFlag.AlignHCenter)

        detail = QVBoxLayout(self.details_page); detail.setContentsMargins(0, 0, 0, 0); detail.setSpacing(SPACE_4)
        back_row = QHBoxLayout(); self.back_button = QPushButton(f"חזרה לרשימת {plural}"); back_row.addWidget(self.back_button); back_row.addStretch(); detail.addLayout(back_row)
        self.detail_header = QFrame(); self.detail_header.setObjectName("pageHeader"); header = QHBoxLayout(self.detail_header); header.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_3)
        self.actions = QHBoxLayout(); self.actions.setDirection(QBoxLayout.Direction.RightToLeft); self.actions.setSpacing(SPACE_2); header.addLayout(self.actions); header.addStretch()
        identity = QVBoxLayout(); self.detail_title = QLabel(); self.detail_title.setObjectName("screenTitle"); self.detail_status = ActiveBadge(); identity.addWidget(self.detail_title); identity.addWidget(self.detail_status, alignment=Qt.AlignmentFlag.AlignRight); header.addLayout(identity); detail.addWidget(self.detail_header)
        self.cards = QHBoxLayout(); self.cards.setDirection(QBoxLayout.Direction.RightToLeft); self.cards.setSpacing(SPACE_4); detail.addLayout(self.cards, 1)
        self.back_button.clicked.connect(lambda: self.pages.setCurrentWidget(self.list_page)); self.pages.setCurrentWidget(self.list_page)

    def add_action(self, text: str, *, destructive: bool = False) -> QPushButton:
        button = QPushButton(text); button.setMinimumSize(148, CONTROL_HEIGHT); button.setMaximumWidth(148); button.setProperty("destructive", destructive); self.actions.addWidget(button); return button

    def set_actions_enabled(self, enabled: bool) -> None:
        for index in range(self.actions.count()):
            widget = self.actions.itemAt(index).widget()
            if widget is not None: widget.setEnabled(enabled)

    def show_detail_identity(self, name: str, active: bool) -> None:
        self.detail_title.setText(name); self.detail_status.set_active(active)

    def add_card(self, title: str):
        frame = QFrame(); frame.setObjectName("detailPanel"); layout = QVBoxLayout(frame); layout.setContentsMargins(SPACE_4, SPACE_4, SPACE_4, SPACE_4); heading = QLabel(title); heading.setObjectName("sectionTitle"); layout.addWidget(heading)
        from PySide6.QtWidgets import QFormLayout
        form = QFormLayout(); form.setLabelAlignment(Qt.AlignmentFlag.AlignRight); form.setVerticalSpacing(SPACE_3); layout.addLayout(form); layout.addStretch(); self.cards.addWidget(frame, 1); return form
