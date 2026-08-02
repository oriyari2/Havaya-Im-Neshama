from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from html import escape

from PySide6.QtCore import QAbstractAnimation, QEasingCurve, QEvent, QObject, QPropertyAnimation, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QFrame, QGraphicsOpacityEffect, QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QTableWidget, QVBoxLayout, QWidget,
)
from shiboken6 import isValid

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.views.design_tokens import (
    SPACE_2, SPACE_3, SPACE_4, SPACE_6, TABLE_COLUMN_ACTION_MIN,
    TABLE_COLUMN_COMPACT_MIN, TABLE_COLUMN_PRIMARY_MIN,
    TABLE_COLUMN_SECONDARY_MIN, TABLE_COLUMN_TECHNICAL_MIN,
    TABLE_HEADER_HEIGHT, TABLE_ROW_HEIGHT,
)


class ColumnKind(str, Enum):
    PRIMARY_TEXT = "primary_text"
    SECONDARY_TEXT = "secondary_text"
    TECHNICAL = "technical"
    COMPACT = "compact"
    ACTION = "action"


_COLUMN_DEFAULTS = {
    ColumnKind.PRIMARY_TEXT: (TABLE_COLUMN_PRIMARY_MIN, 4),
    ColumnKind.SECONDARY_TEXT: (TABLE_COLUMN_SECONDARY_MIN, 2),
    ColumnKind.TECHNICAL: (TABLE_COLUMN_TECHNICAL_MIN, 2),
    ColumnKind.COMPACT: (TABLE_COLUMN_COMPACT_MIN, 0),
    ColumnKind.ACTION: (TABLE_COLUMN_ACTION_MIN, 0),
}


@dataclass(frozen=True, slots=True)
class ColumnPolicy:
    kind: ColumnKind
    minimum: int | None = None
    maximum: int | None = None

    def __post_init__(self) -> None:
        if self.maximum is not None and self.maximum < self.minimum_width:
            raise ValueError("Column maximum width cannot be smaller than its minimum width")

    @property
    def minimum_width(self) -> int:
        return self.minimum if self.minimum is not None else _COLUMN_DEFAULTS[self.kind][0]

    @property
    def stretch_weight(self) -> int:
        return _COLUMN_DEFAULTS[self.kind][1]


class _SemanticColumnSizer(QObject):
    def __init__(self, table: QTableWidget, policies: tuple[ColumnPolicy, ...]) -> None:
        super().__init__(table); self.table = table; self.viewport = table.viewport(); self.policies = policies; self.viewport.installEventFilter(self); QTimer.singleShot(0, self.apply)

    def eventFilter(self, watched, event) -> bool:
        if watched is getattr(self, "viewport", None) and event.type() == QEvent.Type.Resize:
            self.apply()
        return False

    def apply(self) -> None:
        if not isValid(self.table) or self.table.columnCount() != len(self.policies):
            return
        available = max(0, self.table.viewport().width() - 1)
        widths = [policy.minimum_width for policy in self.policies]
        remaining = max(0, available - sum(widths))
        active = [index for index, policy in enumerate(self.policies) if policy.stretch_weight]
        while remaining and active:
            total_weight = sum(self.policies[index].stretch_weight for index in active)
            distributed = 0
            for index in tuple(active):
                policy = self.policies[index]
                share = max(1, remaining * policy.stretch_weight // total_weight)
                capacity = remaining if policy.maximum is None else max(0, policy.maximum - widths[index])
                addition = min(share, capacity, remaining - distributed)
                widths[index] += addition
                distributed += addition
                if policy.maximum is not None and widths[index] >= policy.maximum:
                    active.remove(index)
                if distributed >= remaining:
                    break
            if not distributed:
                break
            remaining -= distributed
        for index, width in enumerate(widths):
            self.table.setColumnWidth(index, width)


def set_disabled_explanation(widget: QWidget, explanation: str) -> None:
    widget.setToolTip(explanation)
    widget.setAccessibleDescription(explanation)


def configure_mixed_direction(widget: QWidget) -> None:
    widget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)


class PageHeader(QFrame):
    def __init__(self, title: str, description: str = "") -> None:
        super().__init__(); self.setObjectName("pageHeader")
        layout = QVBoxLayout(self); layout.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_3)
        title_row = QHBoxLayout(); self.title = QLabel(title); self.title.setObjectName("screenTitle"); self.title.setAccessibleName(title); title_row.addWidget(self.title); title_row.addStretch(); self.action_slot = QHBoxLayout(); title_row.addLayout(self.action_slot); layout.addLayout(title_row)
        self.description = QLabel(description); self.description.setWordWrap(True); self.description.setVisible(bool(description)); layout.addWidget(self.description)
    def add_action(self, widget: QWidget) -> None:
        self.action_slot.addWidget(widget)


class ActionBar(QFrame):
    def __init__(self) -> None:
        super().__init__(); self.layout = QHBoxLayout(self); self.layout.setContentsMargins(0, 0, 0, 0); self.layout.setSpacing(SPACE_2); self.layout.addStretch()
    def add_action(self, button: QPushButton, *, primary: bool = False, destructive: bool = False) -> None:
        button.setProperty("primary", primary); button.setProperty("destructive", destructive); self.layout.addWidget(button)


class FilterPanel(QFrame):
    def __init__(self) -> None:
        super().__init__(); self.setObjectName("filterPanel"); self.layout = QVBoxLayout(self); self.layout.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_3); self.layout.setSpacing(SPACE_3)


class FormSection(QFrame):
    def __init__(self, title: str = "") -> None:
        super().__init__(); layout = QVBoxLayout(self); layout.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_3); layout.setSpacing(SPACE_3)
        self.title = QLabel(title); self.title.setObjectName("sectionTitle"); self.title.setAccessibleName(title); self.title.setVisible(bool(title)); layout.addWidget(self.title)
        self.content = QVBoxLayout(); layout.addLayout(self.content)
        self.validation = QLabel(); self.validation.setObjectName("errorLabel"); self.validation.setAccessibleName("סיכום שגיאות בטופס"); self.validation.setWordWrap(True); self.validation.hide(); layout.addWidget(self.validation)
    def show_validation(self, message: str) -> None:
        self.validation.setText(message); self.validation.setAccessibleDescription(message); self.validation.show()
    def clear_validation(self) -> None:
        self.validation.hide(); self.validation.clear()


class DetailPanel(QFrame):
    def __init__(self, title: str = "") -> None:
        super().__init__(); self.setObjectName("detailPanel"); layout = QVBoxLayout(self); layout.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_3); layout.setSpacing(SPACE_3)
        self.title = QLabel(title); self.title.setObjectName("sectionTitle"); self.title.setAccessibleName(title); self.title.setVisible(bool(title)); layout.addWidget(self.title); self.content = QVBoxLayout(); layout.addLayout(self.content, 1)


class FeedbackBanner(QLabel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent); self.setWordWrap(True); self.setAccessibleName("משוב פעולה"); self.setContentsMargins(SPACE_3, SPACE_2, SPACE_3, SPACE_2)
        self._dismiss_timer = QTimer(self); self._dismiss_timer.setSingleShot(True); self._dismiss_timer.setInterval(2250); self._dismiss_timer.timeout.connect(self._fade_success)
        self._opacity = QGraphicsOpacityEffect(self); self.setGraphicsEffect(self._opacity)
        self._fade = QPropertyAnimation(self._opacity, b"opacity", self); self._fade.setDuration(250); self._fade.setEasingCurve(QEasingCurve.Type.InOutQuad); self._fade.finished.connect(self.hide)
        self.hide()
    def render(self, state: RequestState) -> None:
        mapping = {RequestPhase.SUCCESS: "success", RequestPhase.AUTHORIZATION_ERROR: "error", RequestPhase.CONNECTION_ERROR: "warning", RequestPhase.SERVER_ERROR: "error", RequestPhase.VALIDATION_ERROR: "error"}
        feedback = mapping.get(state.phase)
        self._dismiss_timer.stop(); self._fade.stop(); self._opacity.setOpacity(1.0)
        if not feedback or not state.message: self.hide(); return
        self.setProperty("feedback", feedback); self.setText(state.message); self.setAccessibleDescription(state.message); self.style().unpolish(self); self.style().polish(self); self.show()
        if state.phase == RequestPhase.SUCCESS: self._dismiss_timer.start()

    def render_temporary(self, state: RequestState, *, visible_ms: int = 2750) -> None:
        self.render(state)
        if not self.isHidden():
            self._dismiss_timer.setInterval(visible_ms)
            self._dismiss_timer.start()

    def _fade_success(self) -> None:
        if self.isHidden(): return
        self._fade.setStartValue(1.0); self._fade.setEndValue(0.0); self._fade.start(QAbstractAnimation.DeletionPolicy.KeepWhenStopped)


class StatePanel(QFrame):
    retry_requested = Signal()
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent); self.setObjectName("task20StatePanel"); layout = QVBoxLayout(self); self.message = QLabel(); self.message.setAlignment(Qt.AlignmentFlag.AlignCenter); self.message.setWordWrap(True); self.message.setAccessibleName("מצב תוכן"); self.retry_button = QPushButton("נסו שוב"); self.retry_button.setAccessibleName("ניסיון טעינה מחדש"); self.retry_button.clicked.connect(self.retry_requested); layout.addWidget(self.message); layout.addWidget(self.retry_button, alignment=Qt.AlignmentFlag.AlignCenter); self.hide()
    def render(self, state: RequestState) -> None:
        visible = state.phase in {RequestPhase.LOADING, RequestPhase.EMPTY, RequestPhase.CONNECTION_ERROR, RequestPhase.SERVER_ERROR, RequestPhase.AUTHORIZATION_ERROR}
        if not visible or not state.message: self.hide(); return
        self.message.setText(state.message); self.message.setAccessibleDescription(state.message); self.retry_button.setVisible(state.retryable); self.show()


class PageScaffold(QWidget):
    def __init__(self, title: str, description: str = "") -> None:
        super().__init__(); self.setObjectName("pageScaffold"); self.root = QVBoxLayout(self); self.root.setContentsMargins(SPACE_6, SPACE_6, SPACE_6, SPACE_6); self.root.setSpacing(SPACE_6); self.header = PageHeader(title, description); self.feedback = FeedbackBanner(); self.action_bar = ActionBar(); self.filter_panel = FilterPanel(); self.main_content = QVBoxLayout(); self.main_content.setSpacing(SPACE_3); self.footer_region = QWidget(); self.footer_slot = QVBoxLayout(self.footer_region); self.footer_slot.setContentsMargins(0, 0, 0, 0); self.root.addWidget(self.header); self.root.addWidget(self.feedback); self.root.addWidget(self.action_bar); self.root.addWidget(self.filter_panel); self.root.addLayout(self.main_content, 1); self.root.addWidget(self.footer_region); self.action_bar.hide(); self.filter_panel.hide(); self.footer_region.hide()
    def add_footer(self, widget: QWidget) -> None:
        self.footer_slot.addWidget(widget); self.footer_region.show()


def configure_data_table(table: QTableWidget, accessible_name: str, policies: tuple[ColumnPolicy, ...] | None = None) -> None:
    table.setProperty("task20Table", True); table.setAccessibleName(accessible_name); table.setAccessibleDescription("טבלה לקריאה ובחירת שורה באמצעות המקלדת")
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection); table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); table.setAlternatingRowColors(True); table.setTextElideMode(Qt.TextElideMode.ElideRight); table.verticalHeader().setDefaultSectionSize(TABLE_ROW_HEIGHT); table.horizontalHeader().setMinimumHeight(TABLE_HEADER_HEIGHT); table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed); table.horizontalHeader().setStretchLastSection(False)
    resolved = policies or tuple(ColumnPolicy(ColumnKind.PRIMARY_TEXT if index == 0 else ColumnKind.COMPACT if index == table.columnCount() - 1 else ColumnKind.SECONDARY_TEXT) for index in range(table.columnCount()))
    if len(resolved) != table.columnCount():
        raise ValueError("A semantic column policy is required for every table column")
    table._task20_column_sizer = _SemanticColumnSizer(table, resolved)


def set_item_text(table: QTableWidget, row: int, column: int, item, *, tooltip_direction: Qt.LayoutDirection | None = None) -> None:
    direction = "ltr" if tooltip_direction == Qt.LayoutDirection.LeftToRight else "rtl" if tooltip_direction == Qt.LayoutDirection.RightToLeft else "auto"
    item.setToolTip(f'<div dir="{direction}">{escape(item.text())}</div>'); item.setData(int(Qt.ItemDataRole.UserRole) + 1, item.text()); table.setItem(row, column, item)
