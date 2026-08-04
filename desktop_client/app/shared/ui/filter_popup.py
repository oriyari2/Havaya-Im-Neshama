from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QColor, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from desktop_client.app.shared.ui.design_tokens import SPACE_2, SPACE_3, SPACE_4
from desktop_client.app.shared.ui.management_common import apply_management_primary


class CollapsibleFilterSection(QFrame):
    """RTL filter section with a separate arrow and title hit target."""

    toggled = Signal(bool)

    def __init__(self, title: str, content: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("filterPopupSection")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACE_2)

        self.header = QFrame()
        self.header.setObjectName("filterPopupSectionHeader")
        self.header.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.header.setAccessibleName(title)
        header_layout = QHBoxLayout(self.header)
        header_layout.setDirection(QHBoxLayout.Direction.LeftToRight)
        header_layout.setContentsMargins(0, SPACE_2, 0, SPACE_2)
        header_layout.setSpacing(SPACE_2)
        self.arrow = QLabel("◀")
        self.arrow.setObjectName("filterPopupArrow")
        self.arrow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.arrow.setFixedWidth(18)
        self.arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title = QLabel(title)
        self.title.setObjectName("filterPopupSectionTitle")
        self.title.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.title.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.title, 1)
        header_layout.addWidget(self.arrow)
        layout.addWidget(self.header)

        self.content_host = QWidget()
        self.content_host.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        content_layout = QVBoxLayout(self.content_host)
        content_layout.setContentsMargins(0, 0, SPACE_4, SPACE_2)
        content_layout.addWidget(content)
        layout.addWidget(self.content_host)
        self.content_host.hide()
        self.header.installEventFilter(self)

    def is_expanded(self) -> bool:
        return self.content_host.isVisible()

    def set_expanded(self, expanded: bool) -> None:
        self.content_host.setVisible(expanded)
        self.arrow.setText("▼" if expanded else "◀")
        self.toggled.emit(expanded)

    def eventFilter(self, watched, event) -> bool:  # noqa: N802 - Qt API
        if watched is self.header:
            if event.type() == QEvent.Type.MouseButtonRelease:
                self.set_expanded(not self.is_expanded())
                return True
            if event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
                self.set_expanded(not self.is_expanded())
                return True
        return super().eventFilter(watched, event)


class FloatingFilterPopup(QFrame):
    """Shared anchored filter card. It remains a child widget, never a window."""

    apply_requested = Signal()
    clear_requested = Signal()

    def __init__(self, anchor: QWidget, parent: QWidget) -> None:
        super().__init__(parent)
        self.anchor = anchor
        self.setObjectName("sharedFilterPopup")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setFixedWidth(360)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(15, 23, 42, 45))
        self.setGraphicsEffect(shadow)

        root = QVBoxLayout(self)
        root.setContentsMargins(SPACE_4, SPACE_4, SPACE_4, SPACE_3)
        root.setSpacing(SPACE_3)
        self.scroll = QScrollArea()
        self.scroll.setObjectName("filterPopupScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.content = QWidget()
        self.content.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(SPACE_3)
        self.content_layout.addStretch()
        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)

        footer = QFrame()
        footer.setObjectName("filterPopupFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setDirection(QHBoxLayout.Direction.RightToLeft)
        footer_layout.setContentsMargins(0, SPACE_2, 0, 0)
        footer_layout.setSpacing(SPACE_2)
        self.apply_button = QPushButton("החלת סינון")
        apply_management_primary(self.apply_button)
        self.clear_button = QPushButton("ניקוי הכול")
        footer_layout.addWidget(self.apply_button)
        footer_layout.addWidget(self.clear_button)
        footer_layout.addStretch()
        root.addWidget(footer)
        self.apply_button.clicked.connect(self.apply_requested)
        self.clear_button.clicked.connect(self.clear_requested)
        self.sections: list[CollapsibleFilterSection] = []
        self.hide()
        QApplication.instance().installEventFilter(self)

    def add_section(self, title: str, content: QWidget) -> CollapsibleFilterSection:
        section = CollapsibleFilterSection(title, content)
        self.content_layout.insertWidget(self.content_layout.count() - 1, section)
        self.sections.append(section)
        return section

    def toggle(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.open()

    def open(self) -> None:
        self.reanchor()
        self.raise_()
        self.show()
        self.setFocus(Qt.FocusReason.PopupFocusReason)

    def reanchor(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return
        available_height = max(220, parent.height() - SPACE_3 * 2)
        desired_height = min(420, max(280, self.sizeHint().height()))
        self.resize(self.width(), min(desired_height, available_height))
        point = self.anchor.mapTo(parent, self.anchor.rect().bottomRight())
        x = max(SPACE_2, min(point.x() - self.width(), parent.width() - self.width() - SPACE_2))
        y = max(SPACE_2, min(point.y() + SPACE_2, parent.height() - self.height() - SPACE_2))
        self.move(x, y)

    @staticmethod
    def _is_descendant(widget: object, ancestor: QWidget) -> bool:
        current = widget if isinstance(widget, QWidget) else None
        while current is not None:
            if current is ancestor:
                return True
            current = current.parentWidget()
        return False

    def eventFilter(self, watched, event) -> bool:  # noqa: N802 - Qt API
        if self.isVisible():
            if event.type() == QEvent.Type.KeyPress and isinstance(event, QKeyEvent) and event.key() == Qt.Key.Key_Escape:
                self.hide()
                return True
            if event.type() == QEvent.Type.MouseButtonPress and isinstance(event, QMouseEvent):
                point = event.globalPosition().toPoint()
                inside_popup = self._is_descendant(watched, self) or self.rect().contains(self.mapFromGlobal(point))
                inside_anchor = self._is_descendant(watched, self.anchor) or self.anchor.rect().contains(self.anchor.mapFromGlobal(point))
                if not inside_popup and not inside_anchor:
                    self.hide()
        return super().eventFilter(watched, event)
