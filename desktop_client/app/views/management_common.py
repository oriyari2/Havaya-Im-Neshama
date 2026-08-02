from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QBoxLayout,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QWidget,
)

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.views.ui_foundations import StatePanel


MANAGEMENT_PRIMARY_ROLE = "managementPrimary"


def apply_management_primary(button: QPushButton) -> None:
    """Apply the single primary-action role used by management modules."""
    button.setProperty("buttonRole", MANAGEMENT_PRIMARY_ROLE)
    button.style().unpolish(button)
    button.style().polish(button)


class SearchToolbar(QWidget):
    search_requested = Signal(str, str)
    refresh_requested = Signal()

    def __init__(self, *, placeholder: str, sort_options: tuple[tuple[str, str], ...] = ()) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(placeholder)
        self.search_input.setAccessibleName(placeholder)
        self.search_input.setAccessibleDescription("שדה חיפוש; Enter מפעיל חיפוש")
        self.sort_combo = QComboBox()
        for value, label in sort_options:
            self.sort_combo.addItem(label, value)
        self.search_button = QPushButton("חיפוש")
        self.refresh_button = QPushButton("רענון")
        self.search_button.setAccessibleName("הפעלת חיפוש")
        self.refresh_button.setAccessibleName("רענון הרשימה")
        self.search_button.clicked.connect(self._emit_search)
        self.search_input.returnPressed.connect(self._emit_search)
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        layout.addWidget(self.search_input, 1)
        if sort_options:
            layout.addWidget(self.sort_combo)
        else:
            self.sort_combo.hide()
        layout.addWidget(self.search_button)
        layout.addWidget(self.refresh_button)

    def _emit_search(self) -> None:
        self.search_requested.emit(self.search_input.text().strip(), str(self.sort_combo.currentData() or ""))


def configure_reference_toolbar(toolbar: SearchToolbar) -> None:
    """Apply the approved Customer RTL control order to every management toolbar."""
    layout = toolbar.layout()
    toolbar.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    layout.setDirection(QBoxLayout.Direction.RightToLeft)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    toolbar.search_input.setMinimumWidth(300)
    toolbar.sort_combo.setMinimumWidth(190)
    apply_management_primary(toolbar.search_button)
    for control in (toolbar.search_input, toolbar.sort_combo, toolbar.search_button, toolbar.refresh_button):
        layout.removeWidget(control)
    layout.addWidget(toolbar.search_input, 1)
    layout.addWidget(toolbar.search_button)
    if toolbar.sort_combo.count():
        toolbar.sort_combo.show()
        layout.addWidget(toolbar.sort_combo)
    layout.addWidget(toolbar.refresh_button)


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
        self.previous_button.setAccessibleDescription("מעבר לעמוד התוצאות הקודם")
        self.next_button.setAccessibleDescription("מעבר לעמוד התוצאות הבא")
        self.label.setAccessibleName("טווח התוצאות המוצג")
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
        self.setAccessibleName("מצב: פעיל" if active else "מצב: לא פעיל")
        self.setAccessibleDescription(self.text())


class RetryState(QWidget):
    retry_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        self.panel = StatePanel()
        self.panel.retry_requested.connect(self.retry_requested.emit)
        self.message = self.panel.message
        self.retry_button = self.panel.retry_button
        layout.addWidget(self.panel)

    def show_message(self, message: str, *, retriable: bool) -> None:
        self.panel.render(RequestState(RequestPhase.CONNECTION_ERROR if retriable else RequestPhase.AUTHORIZATION_ERROR, message, "load", retryable=retriable))
        self.show()


def confirm_action(parent: QWidget, title: str, message: str) -> bool:
    dialog = QMessageBox(QMessageBox.Icon.Warning, title, message, QMessageBox.StandardButton.NoButton, parent)
    dialog.setLayoutDirection(parent.layoutDirection())
    dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    dialog.setDefaultButton(QMessageBox.StandardButton.No)
    dialog.button(QMessageBox.StandardButton.Yes).setText("מחיקה")
    dialog.button(QMessageBox.StandardButton.No).setText("ביטול")
    for label in dialog.findChildren(QLabel):
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label.setWordWrap(True)
    return dialog.exec() == QMessageBox.StandardButton.Yes
