from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QWidget,
)


class SearchToolbar(QWidget):
    search_requested = Signal(str, str)
    refresh_requested = Signal()

    def __init__(self, *, placeholder: str, sort_options: tuple[tuple[str, str], ...] = ()) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(placeholder)
        self.sort_combo = QComboBox()
        for value, label in sort_options:
            self.sort_combo.addItem(label, value)
        self.search_button = QPushButton("חיפוש")
        self.refresh_button = QPushButton("רענון")
        self.search_button.clicked.connect(self._emit_search)
        self.search_input.returnPressed.connect(self._emit_search)
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        layout.addWidget(self.search_input)
        if sort_options:
            layout.addWidget(self.sort_combo)
        else:
            self.sort_combo.hide()
        layout.addWidget(self.search_button)
        layout.addWidget(self.refresh_button)

    def _emit_search(self) -> None:
        self.search_requested.emit(self.search_input.text().strip(), str(self.sort_combo.currentData() or ""))


class PaginationFooter(QWidget):
    page_requested = Signal(int, int)

    def __init__(self, *, limit: int = 25) -> None:
        super().__init__()
        self.offset = 0
        self.limit = limit
        self.count = 0
        layout = QHBoxLayout(self)
        self.previous_button = QPushButton("הקודם")
        self.next_button = QPushButton("הבא")
        self.label = QLabel()
        self.previous_button.clicked.connect(self.previous)
        self.next_button.clicked.connect(self.next)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.label)
        layout.addWidget(self.next_button)
        self.set_page(offset=0, count=0)

    def set_page(self, *, offset: int, count: int) -> None:
        self.offset = max(0, offset)
        self.count = max(0, count)
        first = self.offset + 1 if self.count else 0
        last = self.offset + self.count
        self.label.setText(f"מציג {first}–{last}")
        self.previous_button.setEnabled(self.offset > 0)
        self.next_button.setEnabled(self.count >= self.limit)

    def previous(self) -> None:
        target = max(0, self.offset - self.limit)
        if target != self.offset:
            self.page_requested.emit(target, self.limit)

    def next(self) -> None:
        if self.count >= self.limit:
            self.page_requested.emit(self.offset + self.limit, self.limit)


class ActiveBadge(QLabel):
    def set_active(self, active: bool) -> None:
        self.setText("פעיל" if active else "לא פעיל")
        self.setProperty("active", active)


class RetryState(QWidget):
    retry_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        self.message = QLabel()
        self.retry_button = QPushButton("נסו שוב")
        self.retry_button.clicked.connect(self.retry_requested.emit)
        layout.addWidget(self.message)
        layout.addWidget(self.retry_button)

    def show_message(self, message: str, *, retriable: bool) -> None:
        self.message.setText(message)
        self.retry_button.setVisible(retriable)
        self.show()


def confirm_action(parent: QWidget, title: str, message: str) -> bool:
    return QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    ) == QMessageBox.StandardButton.Yes
