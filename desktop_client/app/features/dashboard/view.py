from __future__ import annotations

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QFrame, QGridLayout, QHeaderView, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from desktop_client.app.resource_paths import asset_path
from desktop_client.app.shared.ui.common import BOOKING_COLUMNS, StatefulWidget, create_booking_table, populate_booking_table
from desktop_client.app.shared.ui.design_tokens import SPACE_1, SPACE_2, SPACE_3, SPACE_4, SPACE_6


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
    # Dashboard tables are compact summaries: stretch every column to the
    # available viewport so short values such as status are never clipped.
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.horizontalHeader().setStretchLastSection(True)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
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
        self._pixmap = QPixmap(str(asset_path("heroes", "dashboard-hero.png")))
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.setFixedHeight(166)
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
        # Match the approved management/customer hero treatment: image with a
        # light RTL text wash and the soft blue wave along the lower edge.
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width, height = self.width(), self.height()

        clip = QPainterPath()
        clip.moveTo(0, 0)
        clip.lineTo(width, 0)
        clip.lineTo(width, height - 30)
        clip.cubicTo(width * 0.65, height, width * 0.35, height - 25, 0, height - 15)
        clip.closeSubpath()
        painter.setClipPath(clip)

        if not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            source = QRect(
                max(0, (scaled.width() - width) // 2),
                max(0, (scaled.height() - height) // 2),
                width,
                height,
            )
            painter.drawPixmap(self.rect(), scaled, source)

            wash = QLinearGradient(0, 0, width, 0)
            wash.setColorAt(0.0, QColor(255, 255, 255, 10))
            wash.setColorAt(0.44, QColor(255, 255, 255, 82))
            wash.setColorAt(0.72, QColor(255, 255, 255, 224))
            wash.setColorAt(1.0, QColor(255, 255, 255, 255))
            painter.fillRect(self.rect(), wash)

        painter.setClipping(False)
        curve = QPainterPath()
        curve.moveTo(width, height - 30)
        curve.cubicTo(width * 0.65, height, width * 0.35, height - 25, 0, height - 15)
        painter.setPen(QPen(QColor(140, 190, 210), 2.5))
        painter.drawPath(curve)

        # QLabel children are painted by Qt after the parent paint event, so no
        # extra overlay widget is required here.


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
    assignment_request_requested = Signal(dict)

    def __init__(self, role: str = "manager") -> None:
        super().__init__()
        self.role = role
        self._registration_buttons: dict[str, QPushButton] = {}
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
        layout.setContentsMargins(SPACE_6, SPACE_4, SPACE_6, SPACE_6)
        layout.setSpacing(SPACE_3)
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

        # Dashboard navigation is available in the persistent sidebar for every
        # role, so duplicate in-page navigation buttons are intentionally hidden.
        # Keep the signal/API surface unchanged; only the redundant visual row is removed.
        self.shortcuts_region.hide()

        self.first_group = SectionPanel()
        self.first_table = create_booking_table()
        _configure_dashboard_table(self.first_table)
        self.first_table.setMinimumHeight(188)
        self.first_table.setMaximumHeight(260)
        self.first_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.first_group.content.addWidget(self.first_table)
        self.second_group = SectionPanel()
        self.second_table = create_booking_table()
        if self.role == "instructor":
            action_column = len(BOOKING_COLUMNS)
            self.second_table.insertColumn(action_column)
            action_header = QTableWidgetItem("הרשמה")
            action_header.setTextAlignment(_RIGHT_TABLE_ALIGNMENT)
            self.second_table.setHorizontalHeaderItem(action_column, action_header)
        _configure_dashboard_table(self.second_table)
        if self.role == "instructor":
            # Leave more horizontal room for the registration action while
            # keeping the low-information participant count compact.  The
            # remaining booking columns continue to share the available space.
            header = self.second_table.horizontalHeader()
            header.setStretchLastSection(False)
            for column in range(len(BOOKING_COLUMNS) - 1):
                header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
            participants_column = len(BOOKING_COLUMNS) - 1
            action_column = len(BOOKING_COLUMNS)
            header.setSectionResizeMode(participants_column, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(action_column, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(participants_column, 78)
            header.resizeSection(action_column, 145)
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
        if self.role == "instructor":
            self._populate_open_event_registration_actions(second_rows)
        if not first_rows and not second_rows:
            self.show_empty("אין נתונים קרובים להצגה.")

    def _populate_open_event_registration_actions(self, rows: list[dict[str, str]]) -> None:
        self._registration_buttons.clear()
        action_column = len(BOOKING_COLUMNS)
        for row_index, row in enumerate(rows):
            booking_activity_id = str(row.get("booking_activity_id") or "")
            request_status = str(row.get("my_request_status") or "").upper()
            button = QPushButton()
            button.setObjectName("dashboardOpenEventRegisterButton")
            button.setProperty("buttonRole", "managementPrimary")
            # Keep the action visually compact while guaranteeing the full
            # Hebrew label is visible.  The global primary-button QSS adds
            # generous padding, so this dashboard-only override uses tighter
            # padding and a slightly taller control that still fits inside the
            # standard dashboard table row.
            button.setStyleSheet(
                "font-size: 12px; font-weight: 600; "
                "padding: 0 4px;"
            )
            # Apply the fixed geometry after the local stylesheet. Qt can
            # otherwise recalculate the minimum height from QSS and report a
            # 2px minimum before layout, even though the rendered control is
            # taller. Keeping the explicit 34px contract here makes the
            # dashboard action readable and deterministic in tests.
            button.setFixedHeight(34)
            button.setCursor(Qt.CursorShape.PointingHandCursor)

            if not booking_activity_id:
                text, enabled = "לא זמין", False
            elif request_status == "PENDING":
                text, enabled = "בקשה ממתינה", False
            elif request_status == "APPROVED":
                text, enabled = "אושר", False
            elif request_status == "REJECTED":
                text, enabled = "הירשם שוב", True
            else:
                text, enabled = "הירשם לאירוע", True

            button.setText(text)
            # Size from the actual rendered text instead of a hard-coded width.
            # This prevents "הירשם לאירוע" / "בקשה ממתינה" from being clipped
            # while keeping the button clearly inside the registration column.
            text_width = button.fontMetrics().horizontalAdvance(text)
            button.setFixedWidth(max(94, min(128, text_width + 14)))
            button.setEnabled(enabled)
            button.setProperty("idleText", text)
            button.setProperty("idleEnabled", enabled)
            if enabled:
                payload = dict(row)
                button.clicked.connect(
                    lambda _checked=False, value=payload: self.assignment_request_requested.emit(value)
                )
            action_host = QWidget()
            action_host.setObjectName("dashboardOpenEventRegisterActionHost")
            action_host.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            action_layout = QHBoxLayout(action_host)
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setSpacing(0)
            action_layout.addStretch(1)
            action_layout.addWidget(button, 0, Qt.AlignmentFlag.AlignCenter)
            action_layout.addStretch(1)
            self.second_table.setCellWidget(row_index, action_column, action_host)
            if booking_activity_id:
                self._registration_buttons[booking_activity_id] = button

    def set_registration_pending(self, booking_activity_id: str) -> None:
        button = self._registration_buttons.get(str(booking_activity_id))
        if button is None:
            return
        button.setProperty("idleText", "בקשה ממתינה")
        button.setProperty("idleEnabled", False)
        button.setText("בקשה ממתינה")
        button.setEnabled(False)

    def set_registration_loading(self, booking_activity_id: str, loading: bool) -> None:
        button = self._registration_buttons.get(str(booking_activity_id))
        if button is None:
            return
        if loading:
            button.setText("שולח...")
            button.setEnabled(False)
            return
        button.setText(str(button.property("idleText") or "הירשם לאירוע"))
        button.setEnabled(bool(button.property("idleEnabled")))
