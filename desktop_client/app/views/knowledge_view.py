from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class KnowledgeManagementView(QWidget):
    save_requested = Signal(dict)
    replace_requested = Signal(str, dict)
    delete_requested = Signal(str)
    source_selected = Signal(str)
    retry_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        title = QLabel("ניהול ידע RAG")
        title.setObjectName("screenTitle")
        root.addWidget(title)

        form = QFormLayout()
        self.title_input = QLineEdit()
        self.category_input = QLineEdit()
        self.activity_input = QLineEdit()
        self.content_input = QTextEdit()
        self.file_path_input = QLineEdit()
        self.file_path_input.setReadOnly(True)
        self.content_input.textChanged.connect(self.clear_file_path)
        browse = QPushButton("בחר קובץ")
        browse.clicked.connect(self._pick_file)
        file_row = QHBoxLayout()
        file_row.addWidget(self.file_path_input, 1)
        file_row.addWidget(browse)
        self.instructor_checkbox = QCheckBox("מדריכים")
        self.customer_checkbox = QCheckBox("לקוחות")
        roles = QHBoxLayout()
        roles.addWidget(self.instructor_checkbox)
        roles.addWidget(self.customer_checkbox)
        roles.addStretch()
        form.addRow("כותרת", self.title_input)
        form.addRow("קטגוריה", self.category_input)
        form.addRow("פעילות", self.activity_input)
        form.addRow("טקסט", self.content_input)
        form.addRow("קובץ txt/md", file_row)
        form.addRow("נראות", roles)
        root.addLayout(form)

        actions = QHBoxLayout()
        self.save_button = QPushButton("שמור/העלה")
        self.replace_button = QPushButton("החלף מקור")
        self.delete_button = QPushButton("מחק מקור")
        self.replace_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.save_button.clicked.connect(lambda: self.save_requested.emit(self.values()))
        self.replace_button.clicked.connect(self._emit_replace)
        self.delete_button.clicked.connect(self._confirm_delete)
        actions.addWidget(self.save_button)
        actions.addWidget(self.replace_button)
        actions.addWidget(self.delete_button)
        actions.addStretch()
        root.addLayout(actions)

        self.state_label = QLabel("")
        self.state_label.setObjectName("errorLabel")
        root.addWidget(self.state_label)

        self.sources_table = QTableWidget(0, 5)
        self.sources_table.setHorizontalHeaderLabels(["מזהה", "כותרת", "קטגוריה", "תפקידים", "נתחים"])
        self.sources_table.itemSelectionChanged.connect(self._select_current_source)
        root.addWidget(self.sources_table, 1)
        self._selected_source_id: str | None = None

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
                self.sources_table.setItem(row, column, QTableWidgetItem(value))

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

    def show_message(self, message: str) -> None:
        self.state_label.setText(message)

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
