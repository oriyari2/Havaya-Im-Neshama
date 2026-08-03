from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from desktop_client.app.views.design_tokens import SPACE_1, SPACE_2, SPACE_3, SPACE_4
from desktop_client.app.views.management_visuals import (
    install_scaffold_hero,
    style_reference_button,
    style_reference_table,
)
from desktop_client.app.views.ui_foundations import PageScaffold, configure_mixed_direction

_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute


class KnowledgeManagementView(QWidget):
    """RTL-safe knowledge-source editor with unchanged signals and payload semantics."""

    save_requested = Signal(dict)
    replace_requested = Signal(str, dict)
    delete_requested = Signal(str)
    source_selected = Signal(str)
    retry_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.scaffold = PageScaffold("ניהול ידע", "מקורות מאושרים ליועץ AI ולמערכת ה־RAG")
        self.scaffold.root.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_4)
        self.scaffold.root.setSpacing(SPACE_2)
        root.addWidget(self.scaffold)
        self.hero = install_scaffold_hero(
            self.scaffold,
            "managers-hero.png",
            "תמונת הכנת תוכן למסך ניהול ידע",
        )

        content = QWidget()
        content.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(SPACE_3)
        self.content_scroll = QScrollArea()
        self.content_scroll.setObjectName("knowledgeContentScroll")
        self.content_scroll.setWidgetResizable(True)
        self.content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.content_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.content_scroll.setWidget(content)
        self.scaffold.main_content.addWidget(self.content_scroll, 1)

        editor_card = QFrame()
        editor_card.setProperty("referenceCard", True)
        editor_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        editor_card.setMinimumHeight(470)
        editor_layout = QVBoxLayout(editor_card)
        editor_layout.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_4)
        editor_layout.setSpacing(SPACE_2)

        editor_title = QLabel("מקור ידע")
        editor_title.setObjectName("sectionTitle")
        editor_title.setAlignment(_RIGHT)
        editor_layout.addWidget(editor_title)

        self.title_input = QLineEdit()
        self.category_input = QLineEdit()
        self.activity_input = QLineEdit()
        self.content_input = QTextEdit()
        self.content_input.setMinimumHeight(104)
        self.content_input.setMaximumHeight(126)
        self.file_path_input = QLineEdit()
        self.file_path_input.setReadOnly(True)
        configure_mixed_direction(self.file_path_input)
        self.file_path_input.setAlignment(_RIGHT)
        self.content_input.textChanged.connect(self.clear_file_path)

        for input_widget in (self.title_input, self.category_input, self.activity_input):
            input_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            input_widget.setAlignment(_RIGHT)
            input_widget.setMinimumHeight(38)

        browse = QPushButton("בחירת קובץ")
        browse.setMinimumWidth(132)
        browse.setMinimumHeight(40)
        browse.clicked.connect(self._pick_file)
        style_reference_button(browse, "secondary")

        file_host = QWidget()
        file_host.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        file_row = QHBoxLayout(file_host)
        file_row.setContentsMargins(0, 0, 0, 0)
        file_row.setSpacing(SPACE_2)
        file_row.setDirection(QHBoxLayout.Direction.LeftToRight)
        file_host.setMinimumHeight(42)
        self.file_path_input.setMinimumHeight(40)
        file_row.addWidget(self.file_path_input, 1)
        file_row.addWidget(browse)

        self.instructor_checkbox = QCheckBox("מדריכים")
        self.customer_checkbox = QCheckBox("לקוחות")
        role_host = QWidget()
        role_host.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        roles = QHBoxLayout(role_host)
        roles.setContentsMargins(0, 0, 0, 0)
        roles.setSpacing(SPACE_3)
        roles.setDirection(QHBoxLayout.Direction.RightToLeft)
        roles.addWidget(self.instructor_checkbox)
        roles.addWidget(self.customer_checkbox)
        roles.addStretch(1)

        # Deterministic physical layout: value/control on the left, label on the right.
        # Each row is its own layout, so a taller content editor cannot overlap neighboring rows.
        self._add_field_row(editor_layout, "כותרת", self.title_input)
        self._add_field_row(editor_layout, "קטגוריה", self.category_input)
        self._add_field_row(editor_layout, "פעילות", self.activity_input)
        self._add_field_row(editor_layout, "תוכן", self.content_input, top_align=True)
        self._add_field_row(editor_layout, "קובץ txt/md", file_host)
        self._add_field_row(editor_layout, "נראות", role_host)

        actions_host = QWidget()
        actions_host.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        actions_host.setMinimumHeight(46)
        actions = QHBoxLayout(actions_host)
        actions.setContentsMargins(0, SPACE_1, 0, 0)
        actions.setSpacing(SPACE_2)
        actions.setDirection(QHBoxLayout.Direction.LeftToRight)

        self.save_button = QPushButton("שמירה / העלאה")
        self.replace_button = QPushButton("החלפת מקור")
        self.delete_button = QPushButton("מחיקת מקור")
        self.replace_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        for button in (self.save_button, self.replace_button, self.delete_button):
            button.setMinimumWidth(136)
            button.setMinimumHeight(40)
        style_reference_button(self.save_button, "primary")
        style_reference_button(self.replace_button, "secondary")
        style_reference_button(self.delete_button, "destructive")
        self.save_button.clicked.connect(lambda: self.save_requested.emit(self.values()))
        self.replace_button.clicked.connect(self._emit_replace)
        self.delete_button.clicked.connect(self._confirm_delete)

        actions.addWidget(self.delete_button)
        actions.addWidget(self.replace_button)
        actions.addWidget(self.save_button)
        actions.addStretch(1)
        editor_layout.addWidget(actions_host)
        content_layout.addWidget(editor_card)

        self.state_label = QLabel("")
        self.state_label.setObjectName("errorLabel")
        self.state_label.setAlignment(_RIGHT)
        self.state_label.setWordWrap(True)
        self.state_label.hide()
        content_layout.addWidget(self.state_label)

        sources_card = QFrame()
        sources_card.setProperty("referenceCard", True)
        sources_card.setMinimumHeight(310)
        sources_layout = QVBoxLayout(sources_card)
        sources_layout.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_4)
        sources_layout.setSpacing(SPACE_2)
        sources_title = QLabel("מקורות מאושרים")
        sources_title.setObjectName("sectionTitle")
        sources_title.setAlignment(_RIGHT)
        sources_layout.addWidget(sources_title)

        self.sources_table = QTableWidget(0, 5)
        self.sources_table.setHorizontalHeaderLabels(["מזהה", "כותרת", "קטגוריה", "תפקידים", "נתחים"])
        self.sources_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.sources_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.sources_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.sources_table.setAlternatingRowColors(True)
        self.sources_table.setMinimumHeight(230)
        style_reference_table(self.sources_table, stretch=True)
        self.sources_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sources_table.itemSelectionChanged.connect(self._select_current_source)
        sources_layout.addWidget(self.sources_table, 1)
        content_layout.addWidget(sources_card, 1)

        self._selected_source_id: str | None = None
        # When the viewport is short, scroll instead of squeezing/cutting controls.
        content.setMinimumHeight(820)

    @staticmethod
    def _add_field_row(parent: QVBoxLayout, label_text: str, field: QWidget, *, top_align: bool = False) -> None:
        row_host = QWidget()
        row_host.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        row_host.setMinimumHeight(42 if not top_align else 108)
        row = QHBoxLayout(row_host)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE_4)
        row.setDirection(QHBoxLayout.Direction.LeftToRight)

        field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row.addWidget(field, 1, Qt.AlignmentFlag.AlignTop if top_align else Qt.AlignmentFlag.AlignVCenter)

        label = QLabel(label_text)
        label.setProperty("referenceFieldLabel", True)
        label.setFixedWidth(132)
        label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        label.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | (Qt.AlignmentFlag.AlignTop if top_align else Qt.AlignmentFlag.AlignVCenter)
            | Qt.AlignmentFlag.AlignAbsolute
        )
        row.addWidget(label, 0, Qt.AlignmentFlag.AlignTop if top_align else Qt.AlignmentFlag.AlignVCenter)
        parent.addWidget(row_host)

    def values(self) -> dict:
        roles = []
        if self.instructor_checkbox.isChecked():
            roles.append("instructor")
        if self.customer_checkbox.isChecked():
            roles.append("customer")
        return {
            "title": self.title_input.text(),
            "category": self.category_input.text(),
            "activity_name": self.activity_input.text() or None,
            "content": self.content_input.toPlainText(),
            "file_path": self.file_path_input.text() or None,
            "allowed_roles": roles,
        }

    def show_sources(self, sources: list[dict]) -> None:
        self.sources_table.setRowCount(len(sources))
        for row, source in enumerate(sources):
            values = [
                str(source.get("source_id", "")),
                str(source.get("title", "")),
                str(source.get("category", "")),
                ", ".join(source.get("allowed_roles", [])),
                str(source.get("chunk_count", "")),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(_RIGHT)
                self.sources_table.setItem(row, column, item)

    def show_source_detail(self, source: dict) -> None:
        self._selected_source_id = str(source.get("source_id", ""))
        self.clear_file_path()
        self.title_input.setText(str(source.get("title", "")))
        self.category_input.setText(str(source.get("category", "")))
        self.activity_input.setText(str(source.get("activity_name") or ""))
        self.content_input.setPlainText(str(source.get("content", "")))
        roles = source.get("allowed_roles", [])
        self.instructor_checkbox.setChecked("instructor" in roles)
        self.customer_checkbox.setChecked("customer" in roles)
        self.replace_button.setEnabled(bool(self._selected_source_id))
        self.delete_button.setEnabled(bool(self._selected_source_id))

    def show_error(self, message: str) -> None:
        self.state_label.setText(message)
        self.state_label.setProperty("feedback", "error")
        self.state_label.style().unpolish(self.state_label)
        self.state_label.style().polish(self.state_label)
        self.state_label.show()

    def show_message(self, message: str) -> None:
        self.state_label.setText(message)
        self.state_label.setProperty("feedback", "success")
        self.state_label.style().unpolish(self.state_label)
        self.state_label.style().polish(self.state_label)
        self.state_label.setVisible(bool(message))

    def clear_file_path(self) -> None:
        self.file_path_input.clear()

    def _pick_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "בחר קובץ ידע", "", "Text files (*.txt *.md)")
        if path:
            self.file_path_input.setText(path)

    def _select_current_source(self) -> None:
        items = self.sources_table.selectedItems()
        if not items:
            return
        source_id = self.sources_table.item(items[0].row(), 0).text()
        if source_id:
            self.source_selected.emit(source_id)

    def _emit_replace(self) -> None:
        if self._selected_source_id:
            self.replace_requested.emit(self._selected_source_id, self.values())

    def _confirm_delete(self) -> None:
        if not self._selected_source_id:
            return
        answer = QMessageBox.question(self, "מחיקת מקור", "למחוק את מקור הידע שנבחר?")
        if answer == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(self._selected_source_id)
