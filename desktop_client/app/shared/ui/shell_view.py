from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from desktop_client.app.resource_paths import asset_path
from desktop_client.app.shared.ui.design_tokens import SPACE_2, SPACE_3
from desktop_client.app.shared.ui.foundations import configure_mixed_direction


class _SidebarFrame(QFrame):
    """Sidebar surface with a soft decorative image near the lower-right corner."""

    def __init__(self, leaf_path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._leaf_path = leaf_path
        self._leaf_pixmap = QPixmap(str(leaf_path))

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().paintEvent(event)
        if self._leaf_pixmap.isNull():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setOpacity(0.24)

        target_width = max(88, min(132, self.width() - 28))
        target_height = int(target_width * self._leaf_pixmap.height() / self._leaf_pixmap.width())
        leaf = self._leaf_pixmap.scaled(
            target_width,
            target_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        x = self.width() - leaf.width() - 10
        y = self.height() - leaf.height() - 62
        painter.drawPixmap(x, y, leaf)


class ShellView(QWidget):
    navigation_requested = Signal(str)
    logout_requested = Signal()

    def __init__(self, email: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("applicationRoot")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.logo_path = self._logo_path()
        self.leaf_path = self._leaf_path()

        sidebar = _SidebarFrame(self.leaf_path)
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(200)
        sidebar.setMaximumWidth(240)
        self.sidebar_layout = QVBoxLayout(sidebar)
        self.sidebar_layout.setContentsMargins(SPACE_3, SPACE_3, SPACE_3, SPACE_3)
        self.sidebar_layout.setSpacing(SPACE_2)

        identity = QWidget()
        identity_layout = QVBoxLayout(identity)
        identity_layout.setContentsMargins(0, 0, 0, 0)
        identity_layout.setSpacing(SPACE_2)

        self.logo_label = QLabel()
        self.logo_label.setObjectName("brandLogo")
        self.logo_label.setAccessibleName("לוגו חוויה עם נשמה")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        logo = QPixmap(str(self.logo_path))
        if not logo.isNull():
            sidebar_logo = logo.scaled(
                QSize(144, 102),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.logo_label.setPixmap(sidebar_logo)
            self.logo_label.setMinimumSize(sidebar_logo.size())
            self.logo_label.setMaximumSize(sidebar_logo.size())
        identity_layout.addWidget(self.logo_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        email_label = QLabel(email)
        email_label.setObjectName("sidebarEmail")
        email_label.setAccessibleName("החשבון המחובר")
        email_label.setToolTip(email)
        email_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        configure_mixed_direction(email_label)
        identity_layout.addWidget(email_label)

        self.sidebar_layout.addWidget(identity)
        self.sidebar_layout.addSpacing(SPACE_3)

        self.navigation_buttons: dict[str, QPushButton] = {}
        self.sidebar_layout.addStretch()
        self.logout_button = QPushButton("יציאה")
        self.logout_button.setAccessibleName("יציאה מהמערכת")
        self.logout_button.clicked.connect(self.logout_requested.emit)
        self.sidebar_layout.addWidget(self.logout_button)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(sidebar)
        scroll.setMinimumWidth(200)
        scroll.setMaximumWidth(240)
        root.addWidget(scroll)

        self.stack = QStackedWidget()
        self.stack.setAccessibleName("תוכן העמוד הנוכחי")
        self.pages: dict[str, QWidget] = {}
        root.addWidget(self.stack, 1)

    def configure_navigation(self, items: tuple[tuple[str, str], ...]) -> None:
        insert_at = self.sidebar_layout.count() - 2
        previous = None
        for key, label in items:
            button = QPushButton(label)
            button.setCheckable(True)
            button.setAccessibleName(f"ניווט אל {label}")
            button.clicked.connect(
                lambda checked=False, page_key=key: self.navigation_requested.emit(page_key)
            )
            self.sidebar_layout.insertWidget(insert_at, button)
            insert_at += 1
            self.navigation_buttons[key] = button
            if previous is not None:
                QWidget.setTabOrder(previous, button)
            previous = button
        if previous is not None:
            QWidget.setTabOrder(previous, self.logout_button)

    def add_page(self, key: str, page: QWidget) -> None:
        self.pages[key] = page
        self.stack.addWidget(page)

    def show_page(self, key: str) -> None:
        page = self.pages.get(key)
        if page is not None:
            self.stack.setCurrentWidget(page)
            for page_key, button in self.navigation_buttons.items():
                selected = page_key == key
                button.setChecked(selected)
                button.setAccessibleDescription("העמוד הנוכחי" if selected else "")

    @staticmethod
    def _logo_path() -> Path:
        return asset_path("branding", "logo-sidebar.png")

    @staticmethod
    def _leaf_path() -> Path:
        return asset_path("branding", "sidebar-leaf.png")
