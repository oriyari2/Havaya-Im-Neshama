from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget


class ShellView(QWidget):
    navigation_requested = Signal(str)
    logout_requested = Signal()

    def __init__(self, email: str) -> None:
        super().__init__()
        root = QHBoxLayout(self)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)
        self.sidebar_layout = QVBoxLayout(sidebar)
        brand = QLabel("חוויה עם נשמה")
        brand.setObjectName("brand")
        self.sidebar_layout.addWidget(brand)
        self.sidebar_layout.addWidget(QLabel(email))
        self.navigation_buttons: dict[str, QPushButton] = {}
        self.sidebar_layout.addStretch()
        logout = QPushButton("יציאה")
        logout.clicked.connect(self.logout_requested.emit)
        self.sidebar_layout.addWidget(logout)
        root.addWidget(sidebar)
        self.stack = QStackedWidget()
        self.pages: dict[str, QWidget] = {}
        root.addWidget(self.stack, 1)

    def configure_navigation(self, items: tuple[tuple[str, str], ...]) -> None:
        insert_at = max(2, self.sidebar_layout.count() - 2)
        for key, label in items:
            button = QPushButton(label)
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, page_key=key: self.navigation_requested.emit(page_key))
            self.sidebar_layout.insertWidget(insert_at, button)
            insert_at += 1
            self.navigation_buttons[key] = button

    def add_page(self, key: str, page: QWidget) -> None:
        self.pages[key] = page
        self.stack.addWidget(page)

    def show_page(self, key: str) -> None:
        page = self.pages.get(key)
        if page is not None:
            self.stack.setCurrentWidget(page)
            for page_key, button in self.navigation_buttons.items():
                button.setChecked(page_key == key)
