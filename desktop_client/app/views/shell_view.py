from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QStackedWidget, QVBoxLayout, QWidget

from desktop_client.app.views.design_tokens import SPACE_3, SPACE_4
from desktop_client.app.views.ui_foundations import configure_mixed_direction


class ShellView(QWidget):
    navigation_requested = Signal(str); logout_requested = Signal()
    def __init__(self, email: str) -> None:
        super().__init__(); self.setObjectName("applicationRoot"); self.setLayoutDirection(Qt.LayoutDirection.RightToLeft); root = QHBoxLayout(self); root.setContentsMargins(0, 0, 0, 0)
        sidebar = QFrame(); sidebar.setObjectName("sidebar"); sidebar.setMinimumWidth(200); sidebar.setMaximumWidth(240)
        self.sidebar_layout = QVBoxLayout(sidebar); self.sidebar_layout.setContentsMargins(SPACE_4, SPACE_4, SPACE_4, SPACE_4); self.sidebar_layout.setSpacing(SPACE_3)
        brand = QLabel("חוויה עם נשמה"); brand.setObjectName("brand"); brand.setAccessibleName("חוויה עם נשמה"); self.sidebar_layout.addWidget(brand)
        email_label = QLabel(email); email_label.setAccessibleName("החשבון המחובר"); email_label.setToolTip(email); configure_mixed_direction(email_label); self.sidebar_layout.addWidget(email_label)
        self.navigation_buttons: dict[str, QPushButton] = {}; self.sidebar_layout.addStretch()
        self.logout_button = QPushButton("יציאה"); self.logout_button.setAccessibleName("יציאה מהמערכת"); self.logout_button.clicked.connect(self.logout_requested.emit); self.sidebar_layout.addWidget(self.logout_button)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); scroll.setWidget(sidebar); scroll.setMinimumWidth(200); scroll.setMaximumWidth(240); root.addWidget(scroll)
        self.stack = QStackedWidget(); self.stack.setAccessibleName("תוכן העמוד הנוכחי"); self.pages: dict[str, QWidget] = {}; root.addWidget(self.stack, 1)
    def configure_navigation(self, items: tuple[tuple[str, str], ...]) -> None:
        insert_at = max(2, self.sidebar_layout.count() - 2)
        previous = None
        for key, label in items:
            button = QPushButton(label); button.setCheckable(True); button.setAccessibleName(f"ניווט אל {label}"); button.clicked.connect(lambda checked=False, page_key=key: self.navigation_requested.emit(page_key)); self.sidebar_layout.insertWidget(insert_at, button); insert_at += 1; self.navigation_buttons[key] = button
            if previous is not None: QWidget.setTabOrder(previous, button)
            previous = button
        if previous is not None: QWidget.setTabOrder(previous, self.logout_button)
    def add_page(self, key: str, page: QWidget) -> None: self.pages[key] = page; self.stack.addWidget(page)
    def show_page(self, key: str) -> None:
        page = self.pages.get(key)
        if page is not None:
            self.stack.setCurrentWidget(page)
            for page_key, button in self.navigation_buttons.items():
                selected = page_key == key; button.setChecked(selected); button.setAccessibleDescription("העמוד הנוכחי" if selected else "")
