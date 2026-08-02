from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QTableWidget, QVBoxLayout, QWidget

from desktop_client.app.views.common import BOOKING_COLUMNS, StatefulWidget, create_booking_table, populate_booking_table
from desktop_client.app.views.design_tokens import SPACE_1, SPACE_2, SPACE_3, SPACE_4, SPACE_6


SUMMARY_LABELS = {
    "upcoming_count": "סה״כ קרובים",
    "pending_count": "חדשים",
    "confirmed_count": "מאושרים",
    "cancelled_count": "מבוטלים",
    "assigned_count": "משובצים",
    "unassigned_count": "דורשים שיבוץ",
}

CARD_ACCENTS = {
    "upcoming_count": "sky",
    "pending_count": "orange",
    "confirmed_count": "green",
    "cancelled_count": "coral",
    "assigned_count": "sky",
    "unassigned_count": "orange",
}


_RIGHT_LABEL_ALIGNMENT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute
_RIGHT_TABLE_ALIGNMENT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute
_LTR_TABLE_ALIGNMENT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute


def _align_hebrew_label(label: QLabel) -> None:
    label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    label.setAlignment(_RIGHT_LABEL_ALIGNMENT)
    label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)


def _align_dashboard_button(button: QPushButton) -> None:
    button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    button.setStyleSheet("text-align: right; padding-right: 14px; padding-left: 14px;")


def _configure_dashboard_table(table: QTableWidget) -> None:
    table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    table.horizontalHeader().setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    table.horizontalHeader().setDefaultAlignment(_RIGHT_TABLE_ALIGNMENT)
    for column in range(table.columnCount()):
        header_item = table.horizontalHeaderItem(column)
        if header_item is not None:
            header_item.setTextAlignment(_RIGHT_TABLE_ALIGNMENT)


def _align_dashboard_table_items(table: QTableWidget) -> None:
    for column, (key, _) in enumerate(BOOKING_COLUMNS):
        alignment = _LTR_TABLE_ALIGNMENT if key == "event_at" else _RIGHT_TABLE_ALIGNMENT
        for row in range(table.rowCount()):
            item = table.item(row, column)
            if item is not None:
                item.setTextAlignment(alignment)


class DashboardHero(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dashboardHero")
        self._pixmap = QPixmap(str(Path(__file__).resolve().parents[3] / "design_reference" / "activity-dashboard-hero.png"))
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.setMinimumHeight(96)
        self.setMaximumHeight(112)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACE_6, SPACE_3, SPACE_6, SPACE_3)
        layout.setSpacing(SPACE_2)
        layout.addStretch(1)
        text_panel = QVBoxLayout()
        text_panel.setContentsMargins(0, 0, 0, 0)
        text_panel.setSpacing(SPACE_1)
        self.title = QLabel("לוח בקרה")
        self.title.setObjectName("dashboardHeroTitle")
        self.title.setAccessibleName("לוח בקרה")
        self.subtitle = QLabel("סקירה מלאה של הפעילות, האירועים והמשימות")
        self.subtitle.setObjectName("dashboardHeroSubtitle")
        self.subtitle.setProperty("subtitle", True)
        _align_hebrew_label(self.title)
        _align_hebrew_label(self.subtitle)
        self.subtitle.setWordWrap(True)
        self.title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.subtitle.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        text_panel.addStretch(1)
        text_panel.addWidget(self.title)
        text_panel.addWidget(self.subtitle)
        text_panel.addStretch(1)
        layout.addLayout(text_panel, 1)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        if not self._pixmap.isNull():
            scaled = self._pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            source = QRect(
                max(0, (scaled.width() - self.width()) // 2),
                max(0, (scaled.height() - self.height()) // 2),
                self.width(),
                self.height(),
            )
            painter.drawPixmap(self.rect(), scaled, source)
            wash = QLinearGradient(0, 0, self.width(), 0)
            wash.setColorAt(0.0, QColor(255, 255, 255, 18))
            wash.setColorAt(0.48, QColor(255, 255, 255, 130))
            wash.setColorAt(0.72, QColor(255, 255, 255, 238))
            wash.setColorAt(1.0, QColor(255, 255, 255, 255))
            painter.fillRect(self.rect(), wash)
        super().paintEvent(event)


class SectionPanel(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dashboardSection")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_4)
        layout.setSpacing(SPACE_3)
        self.title_label = QLabel()
        self.title_label.setObjectName("dashboardSectionTitle")
        _align_hebrew_label(self.title_label)
        layout.addWidget(self.title_label)
        self.content = QVBoxLayout()
        self.content.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.content, 1)
        self.setMinimumHeight(232)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def setTitle(self, title: str) -> None:
        self.title_label.setText(title)
        self.title_label.setAccessibleName(title)


class DashboardView(StatefulWidget):
    drill_down_requested = Signal(str)
    shortcut_requested = Signal(str)
    create_booking_requested = Signal()

    def __init__(self, role: str = "manager") -> None:
        super().__init__()
        self.setObjectName("dashboardPage")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        _align_hebrew_label(self.state_label)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("dashboardScrollArea")
        self.scroll_area.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        root.addWidget(self.scroll_area)

        self.content = QWidget()
        self.content.setObjectName("dashboardContent")
        self.content.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.scroll_area.setWidget(self.content)

        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(SPACE_6, SPACE_6, SPACE_6, SPACE_6)
        layout.setSpacing(SPACE_4)
        layout.addWidget(DashboardHero())
        layout.addWidget(self.state_label)

        self.cards_region = QWidget()
        self.cards_region.setObjectName("dashboardCardsRegion")
        self.cards_region.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.cards_layout = QGridLayout(self.cards_region)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(SPACE_4)
        self.card_values: dict[str, QLabel] = {}
        self.card_labels: dict[str, QLabel] = {}
        self.drill_buttons: dict[str, QPushButton] = {}
        role_fields = {
            "manager": tuple(SUMMARY_LABELS),
            "instructor": ("upcoming_count", "assigned_count"),
            "customer": ("upcoming_count", "pending_count", "confirmed_count", "cancelled_count"),
        }.get(role, ())
        for index, key in enumerate(role_fields):
            label = SUMMARY_LABELS[key]
            card = QFrame()
            card.setObjectName("dashboardStatCard")
            card.setProperty("statCard", True)
            card.setProperty("accent", CARD_ACCENTS.get(key, "sky"))
            card.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            card.setMinimumHeight(128)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(SPACE_4, SPACE_4, SPACE_4, SPACE_4)
            card_layout.setSpacing(SPACE_2)
            label_widget = QLabel(label)
            label_widget.setObjectName("dashboardStatLabel")
            _align_hebrew_label(label_widget)
            label_widget.setWordWrap(True)
            card_layout.addWidget(label_widget)
            value = QLabel("0")
            value.setObjectName("summaryValue")
            _align_hebrew_label(value)
            card_layout.addWidget(value)
            card_layout.addStretch(1)
            if key in {"upcoming_count", "pending_count", "confirmed_count", "cancelled_count", "assigned_count", "unassigned_count"}:
                open_button = QPushButton("פתיחה")
                open_button.setObjectName("dashboardDrillButton")
                open_button.setProperty("accent", CARD_ACCENTS.get(key, "sky"))
                _align_dashboard_button(open_button)
                open_button.setMinimumHeight(34)
                open_button.clicked.connect(lambda _checked=False, target=key: self.drill_down_requested.emit(target))
                card_layout.addWidget(open_button)
                self.drill_buttons[key] = open_button
            self.cards_layout.addWidget(card, index // 3, index % 3)
            self.card_labels[key] = label_widget
            self.card_values[key] = value
        for column in range(3):
            self.cards_layout.setColumnStretch(column, 1)
        layout.addWidget(self.cards_region)

        self.shortcuts_region = QFrame()
        self.shortcuts_region.setObjectName("dashboardShortcuts")
        self.shortcuts_region.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        shortcuts = QHBoxLayout(self.shortcuts_region)
        shortcuts.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_3)
        shortcuts.setSpacing(SPACE_3)
        targets = {
            "manager": (("create", "יצירת הזמנה"), ("customers", "לקוחות"), ("instructors", "מדריכים"), ("activities", "פעילויות"), ("bookings", "הזמנות")),
            "instructor": (("bookings", "האירועים שלי"), ("activities", "פעילויות"), ("my_profile", "הפרופיל שלי")),
            "customer": (("my_bookings", "ההזמנות שלי"), ("activities", "פעילויות"), ("my_profile", "הפרופיל שלי")),
        }
        for key, label in targets.get(role, ()):
            button = QPushButton(label)
            button.setObjectName("dashboardShortcutButton")
            _align_dashboard_button(button)
            button.setMinimumHeight(42)
            button.setMinimumWidth(128)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            if key == "create":
                button.setProperty("buttonRole", "managementPrimary")
                button.clicked.connect(self.create_booking_requested.emit)
            else:
                button.clicked.connect(lambda _checked=False, target=key: self.shortcut_requested.emit(target))
            shortcuts.addWidget(button, 1)
        layout.addWidget(self.shortcuts_region)

        self.first_group = SectionPanel()
        self.first_table = create_booking_table()
        _configure_dashboard_table(self.first_table)
        self.first_table.setMinimumHeight(188)
        self.first_table.setMaximumHeight(260)
        self.first_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.first_group.content.addWidget(self.first_table)
        self.second_group = SectionPanel()
        self.second_table = create_booking_table()
        _configure_dashboard_table(self.second_table)
        self.second_table.setMinimumHeight(188)
        self.second_table.setMaximumHeight(260)
        self.second_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.second_group.content.addWidget(self.second_table)
        layout.addWidget(self.first_group)
        layout.addWidget(self.second_group)

    def show_summary(self, summary: dict[str, int]) -> None:
        for key, label in self.card_values.items():
            label.setText(str(summary.get(key, 0)))

    def show_sections(self, first_title: str, first_rows: list[dict[str, str]], second_title: str, second_rows: list[dict[str, str]]) -> None:
        self.state_label.hide()
        self.first_group.setTitle(first_title)
        populate_booking_table(self.first_table, first_rows)
        _align_dashboard_table_items(self.first_table)
        self.second_group.setTitle(second_title)
        self.second_group.setVisible(bool(second_title))
        populate_booking_table(self.second_table, second_rows)
        _align_dashboard_table_items(self.second_table)
        if not first_rows and not second_rows:
            self.show_empty("אין נתונים קרובים להצגה.")
