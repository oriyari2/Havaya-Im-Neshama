from __future__ import annotations

from datetime import datetime

from PySide6.QtCharts import QBarCategoryAxis, QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import QMargins, QRect, Qt, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from desktop_client.app.resource_paths import asset_path
from desktop_client.app.shared.ui.common import StatefulWidget
from desktop_client.app.shared.ui.design_tokens import COLOR_BORDER, COLOR_BRAND, COLOR_TEXT, COLOR_TEXT_MUTED, SPACE_1, SPACE_2, SPACE_3, SPACE_4, SPACE_6


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
MONTH_LABELS = ["ינו׳", "פבר׳", "מרץ", "אפר׳", "מאי", "יוני", "יולי", "אוג׳", "ספט׳", "אוק׳", "נוב׳", "דצמ׳"]
SELECTABLE_YEARS = tuple(range(2015, 2051))


def _align_hebrew_label(label: QLabel) -> None:
    label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    label.setAlignment(_RIGHT_LABEL_ALIGNMENT)
    label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)


def _align_dashboard_button(button: QPushButton) -> None:
    button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    button.setStyleSheet("text-align: right; padding-right: 14px; padding-left: 14px;")


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


class MonthlyTrendCard(QFrame):
    year_changed = Signal(int)
    retry_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dashboardChartCard")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumHeight(390)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE_4, SPACE_4, SPACE_4, SPACE_4)
        layout.setSpacing(SPACE_2)

        header = QHBoxLayout()
        header.setSpacing(SPACE_2)
        text = QVBoxLayout()
        self.title = QLabel("מגמת אירועים שנתית")
        self.title.setObjectName("dashboardChartTitle")
        self.subtitle = QLabel("מספר האירועים המתוכננים בכל חודש לפי מועד האירוע")
        self.subtitle.setObjectName("dashboardChartSubtitle")
        for label in (self.title, self.subtitle):
            _align_hebrew_label(label)
        text.addWidget(self.title)
        text.addWidget(self.subtitle)
        header.addLayout(text, 1)
        self.year_combo = QComboBox()
        self.year_combo.setObjectName("dashboardYearSelector")
        self.year_combo.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.year_combo.setMinimumWidth(92)
        self.year_combo.setMaximumWidth(112)
        self.year_combo.addItems([str(year) for year in SELECTABLE_YEARS])
        self.year_combo.setCurrentText(str(datetime.now().year))
        self.year_combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.year_combo.setMaxVisibleItems(12)
        year_label = QLabel("שנה:")
        year_label.setObjectName("dashboardYearLabel")
        year_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        header.addWidget(self.year_combo, 0, Qt.AlignmentFlag.AlignTop)
        header.addWidget(year_label, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        self.series = QLineSeries()
        self.series.setName("אירועים")
        self.series.setPointsVisible(True)
        pen = QPen(QColor(COLOR_BRAND), 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self.series.setPen(pen)
        self.series.setColor(QColor(COLOR_BRAND))
        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.legend().hide()
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.chart.setBackgroundVisible(False)
        self.chart.setMargins(QMargins(4, 8, 4, 4))
        self.x_axis = QBarCategoryAxis()
        self.x_axis.append(MONTH_LABELS)
        self.y_axis = QValueAxis()
        self.y_axis.setLabelFormat("%d")
        self.y_axis.setRange(0, 1)
        self.y_axis.setTickCount(2)
        self.chart.addAxis(self.x_axis, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.y_axis, Qt.AlignmentFlag.AlignLeft)
        self.series.attachAxis(self.x_axis)
        self.series.attachAxis(self.y_axis)
        for axis in (self.x_axis, self.y_axis):
            axis.setLabelsColor(QColor(COLOR_TEXT_MUTED))
            axis.setGridLineColor(QColor(COLOR_BORDER))
            axis.setLinePenColor(QColor(COLOR_BORDER))

        self.chart_view = QChartView(self.chart)
        self.chart_view.setObjectName("dashboardYearlyChart")
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setMinimumHeight(270)
        self.chart_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.chart_view, 1)
        self.status_label = QLabel()
        self.status_label.setObjectName("dashboardChartState")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.hide()
        layout.addWidget(self.status_label)
        self.retry_button = QPushButton("נסו שוב")
        self.retry_button.setObjectName("dashboardChartRetry")
        self.retry_button.setProperty("buttonRole", "managementSecondary")
        self.retry_button.clicked.connect(self.retry_requested)
        self.retry_button.hide()
        layout.addWidget(self.retry_button, 0, Qt.AlignmentFlag.AlignHCenter)
        self.year_combo.currentTextChanged.connect(self._emit_year)

    def _emit_year(self, value: str) -> None:
        if value.isdigit() and not self.year_combo.signalsBlocked():
            self.year_changed.emit(int(value))

    def set_loading(self, loading: bool) -> None:
        self.year_combo.setEnabled(not loading)
        if loading:
            self.retry_button.hide()
            self.status_label.setText("טוען נתוני מגמה...")
            self.status_label.show()

    def show_data(self, year: int, years: list[int], months: list[dict[str, int]]) -> None:
        del years
        if year in SELECTABLE_YEARS and self.year_combo.currentText() != str(year):
            self.year_combo.blockSignals(True)
            self.year_combo.setCurrentText(str(year))
            self.year_combo.blockSignals(False)
        counts = {int(item.get("month", 0)): int(item.get("count", 0)) for item in months}
        values = [max(0, counts.get(month, 0)) for month in range(1, 13)]
        self.series.clear()
        for index, count in enumerate(values):
            self.series.append(index, count)
        maximum = max(values, default=0)
        upper = max(1, maximum)
        self.y_axis.setRange(0, upper)
        self.y_axis.setTickCount(min(6, upper + 1))
        self.retry_button.hide()
        if maximum == 0:
            self.status_label.setText("אין אירועים מתוכננים בשנה זו.")
            self.status_label.show()
        else:
            self.status_label.hide()

    def show_error(self, message: str) -> None:
        self.status_label.setText(message)
        self.status_label.show()
        self.retry_button.show()


class DashboardView(StatefulWidget):
    drill_down_requested = Signal(str)
    shortcut_requested = Signal(str)
    create_booking_requested = Signal()
    year_changed = Signal(int)
    chart_retry_requested = Signal()

    def __init__(self, role: str = "manager") -> None:
        super().__init__()
        self.role = role
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

        self.trend_card = MonthlyTrendCard()
        self.trend_card.year_changed.connect(self.year_changed)
        self.trend_card.retry_requested.connect(self.chart_retry_requested)
        layout.addWidget(self.trend_card)

    def show_summary(self, summary: dict[str, int]) -> None:
        for key, label in self.card_values.items():
            label.setText(str(summary.get(key, 0)))

    def set_chart_loading(self, loading: bool) -> None:
        self.trend_card.set_loading(loading)

    def show_chart(self, year: int, years: list[int], months: list[dict[str, int]]) -> None:
        self.trend_card.show_data(year, years, months)

    def show_chart_error(self, message: str) -> None:
        self.trend_card.show_error(message)
