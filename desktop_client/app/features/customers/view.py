from __future__ import annotations

from PySide6.QtCore import QEvent, QItemSelectionModel, QRect, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPixmap, QPainterPath, QPen
from PySide6.QtWidgets import QBoxLayout, QComboBox, QFormLayout, QGridLayout, QLabel, QPushButton, QSizePolicy, QTableWidgetItem, QVBoxLayout, QWidget

from desktop_client.app.resource_paths import asset_path
from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.shared.ui.account_dialogs import ChangePasswordDialog
from desktop_client.app.shared.ui.common import StatefulWidget
from desktop_client.app.features.customers.dialogs import CustomerDialog
from desktop_client.app.shared.ui.design_tokens import (
    COLOR_BACKGROUND,
    COLOR_BORDER,
    COLOR_BORDER_STRONG,
    COLOR_BRAND,
    COLOR_BRAND_HOVER,
    COLOR_BRAND_PRESSED,
    COLOR_BRAND_SOFT,
    COLOR_DISABLED_BACKGROUND,
    COLOR_DISABLED_TEXT,
    COLOR_ERROR,
    COLOR_ERROR_BACKGROUND,
    COLOR_SUCCESS,
    COLOR_SUCCESS_BACKGROUND,
    COLOR_SURFACE,
    COLOR_SURFACE_ALT,
    COLOR_TEXT,
    SPACE_1,
    SPACE_2,
    SPACE_3,
    SPACE_4,
    SPACE_6,
)
from desktop_client.app.shared.ui.management_common import ActiveBadge, RetryState, confirm_action
from desktop_client.app.shared.ui.management_workspace import ManagementWorkspace
from desktop_client.app.shared.ui.foundations import (
    ColumnKind,
    ColumnPolicy,
    set_disabled_explanation,
    set_item_text,
)

_RIGHT_LABEL_ALIGNMENT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute
_RIGHT_TEXT_ALIGNMENT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute
_LTR_TEXT_ALIGNMENT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute


# שינוי ל-QWidget במקום QFrame כדי להימנע ממסגרות או רקעים לבנים מה-Stylesheet של המערכת
class CustomersHero(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("customersHero")
        self.hero_path = asset_path("heroes", "customers-hero.png")
        self._pixmap = QPixmap(str(self.hero_path))
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.setFixedHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAccessibleName("תמונת פעילות לקוחות")

    def attach_header(self, title: QLabel, subtitle: QLabel, action: QPushButton) -> None:
        title.setProperty("customersHeroTitle", True)
        subtitle.setProperty("customersHeroSubtitle", True)

        # הטקסט עצמו הוא RTL, אבל המעטפת נשארת LTR כדי ש-Qt לא יהפוך
        # את AlignRight לצד שמאל. AlignAbsolute מונע תלות בכיוון של ההורה.
        for label in (title, subtitle):
            label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            label.setAlignment(_RIGHT_LABEL_ALIGNMENT)
            label.setWordWrap(False)
            label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            label.setStyleSheet("margin: 0px; padding: 0px; background: transparent; border: none;")

        action.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        action.setMinimumWidth(132)
        action.setMinimumHeight(40)

        layout = QGridLayout(self)
        layout.setOriginCorner(Qt.Corner.TopLeftCorner)
        layout.setContentsMargins(SPACE_6, 0, SPACE_6, 0)
        layout.setHorizontalSpacing(SPACE_4)
        layout.setVerticalSpacing(0)
        layout.setRowStretch(0, 1)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)

        # הכפתור נשאר בפינה השמאלית-תחתונה של ההירו.
        action_box = QWidget()
        action_box.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        action_layout = QVBoxLayout(action_box)
        action_layout.setContentsMargins(0, 0, 0, 30)
        action_layout.addStretch(1)
        action_layout.addWidget(
            action,
            0,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignAbsolute,
        )
        layout.addWidget(action_box, 0, 0)

        # המעטפת תופסת את כל החצי הימני; לכן שתי התוויות מקבלות רוחב
        # אמיתי והיישור שלהן הוא לקצה הימני של התמונה, לא רק לגודל הטקסט.
        title_box = QWidget()
        title_box.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        title_box.setMinimumWidth(360)
        title_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        title_layout = QVBoxLayout(title_box)
        title_layout.setContentsMargins(0, 0, 0, 30)
        title_layout.setSpacing(SPACE_1)
        title_layout.addStretch(1)
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        layout.addWidget(title_box, 0, 2)

        # המאפיינים הדינמיים נקבעו אחרי יצירת התוויות, ולכן מרעננים את
        # ה-QSS רק לאחר שהן כבר נמצאות בתוך customersHero.
        for widget in (title, subtitle, action):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        path = QPainterPath()
        path.lineTo(w, 0)
        path.lineTo(w, h - 30)
        path.cubicTo(w * 0.65, h, w * 0.35, h - 25, 0, h - 15)
        path.lineTo(0, 0)
        
        painter.setClipPath(path)

        if not self._pixmap.isNull():
            scaled = self._pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            source_x = max(0, (scaled.width() - self.width()) // 2)
            source_y = max(0, (scaled.height() - self.height()) // 2)
            painter.drawPixmap(self.rect(), scaled, QRect(source_x, source_y, self.width(), self.height()))
            wash = QLinearGradient(0, 0, self.width(), 0)
            wash.setColorAt(0.0, QColor(255, 255, 255, 14))
            wash.setColorAt(0.44, QColor(255, 255, 255, 92))
            wash.setColorAt(0.72, QColor(255, 255, 255, 224))
            wash.setColorAt(1.0, QColor(255, 255, 255, 255))
            painter.fillRect(self.rect(), wash)

        painter.setClipping(False)
        curve_path = QPainterPath()
        curve_path.moveTo(w, h - 30)
        curve_path.cubicTo(w * 0.65, h, w * 0.35, h - 25, 0, h - 15)
        
        pen = QPen(QColor(140, 190, 210), 2.5)
        painter.setPen(pen)
        painter.drawPath(curve_path)


class CustomersView(StatefulWidget):
    """Customer configuration of the shared management UI foundation."""

    filters_requested = Signal(dict)
    page_requested = Signal(int, int)
    customer_selected = Signal(str)
    retry_requested = Signal()
    create_requested = Signal()
    edit_requested = Signal()
    deactivate_requested = Signal()
    reactivate_requested = Signal()
    change_password_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._selected_customer_id: str | None = None
        self._pending_open_id: str | None = None
        self._empty_filtered = False
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        
        # החזרת המספור והעמודות המלאות כפי שביקשת
        self.workspace = ManagementWorkspace(
            title="לקוחות",
            subtitle="מערכת לניהול לקוחות ופרטי קשר",
            create_text="לקוח חדש +",
            plural="לקוחות",
            detail_subtitle="מידע מלא ופעולות עבור הלקוח שנבחר",
            search_placeholder="חיפוש לפי שם, טלפון, אימייל, מזהה לקוח...",
            sort_options=(("name", "מיון לפי: שם"), ("created_at", "מיון לפי: תאריך יצירה")),
            headers=("#", "שם לקוח", "טלפון", "אימייל", "עיר", "סטטוס", "תאריך הצטרפות"),
            policies=(
                ColumnPolicy(ColumnKind.COMPACT, 40),          # מספר סידורי
                ColumnPolicy(ColumnKind.PRIMARY_TEXT, 140),    # שם לקוח
                ColumnPolicy(ColumnKind.SECONDARY_TEXT, 120),  # טלפון
                ColumnPolicy(ColumnKind.SECONDARY_TEXT, 180),  # אימייל
                ColumnPolicy(ColumnKind.SECONDARY_TEXT, 100),  # עיר
                ColumnPolicy(ColumnKind.COMPACT, 100),         # סטטוס
                ColumnPolicy(ColumnKind.SECONDARY_TEXT, 110),  # תאריך הצטרפות
            ),
            row_action_position="end",
        )
        root.addWidget(self.workspace)
        

        self.workspace.create_button.setObjectName("customerCreateButton")
        self.hero = CustomersHero()
        self._move_header_into_hero()
        self._install_customers_hero()
        
        self.workspace.scaffold.root.setContentsMargins(SPACE_6, SPACE_4, SPACE_6, SPACE_6)
        self.workspace.scaffold.root.setSpacing(SPACE_3)
        self.workspace.table.setProperty("customerTable", True)
        self._apply_customers_rtl_alignment()
        
        for styled in (self.workspace.table,):
            styled.style().unpolish(styled)
            styled.style().polish(styled)
            
        for name in (
            "scaffold", "toolbar", "table", "footer", "create_button", "pages",
            "list_page", "details_page", "back_button",
            "header_identity", "identity_container", "actions_container",
            "table_region", "empty_state", "empty_title", "empty_description",
            "empty_action_button", "details_scroll", "details_widget",
        ):
            setattr(self, name, getattr(self.workspace, name))
            
        # הסתרת תיבת ה-"10 בשורה" הספציפית בעמוד הזה כדי שיראה נקי
        for combo in self.footer.findChildren(QComboBox):
            combo.hide()
            
        self.sort_by = self.toolbar.sort_combo
        self.toolbar.search_button.setObjectName("customerSearchButton")
        self.empty_action_button.setObjectName("customerEmptyActionButton")

        self.retry = RetryState()
        self.retry.retry_requested.connect(self.retry_requested)
        self.scaffold.main_content.insertWidget(0, self.retry)
        self.scaffold.main_content.insertWidget(1, self.state_label)

        self.edit_button, self.change_password_button, self.deactivate_button, self.reactivate_button = self.workspace.add_lifecycle_actions(
            edit="עריכת לקוח", password="שינוי סיסמה", deactivate="השבתת לקוח", reactivate="הפעלת לקוח מחדש"
        )
        self.customer_details = self.workspace.add_card("פרטי לקוח")
        self.contact_details = self.workspace.add_card("פרטי קשר")
        self.system_details = self.workspace.add_card("מידע מערכת")
        self.detail_forms = {
            "customer": self.customer_details,
            "contact": self.contact_details,
            "system": self.system_details,
        }
        self._apply_customer_detail_design()

        self.create_button.clicked.connect(self.create_requested)
        self.edit_button.clicked.connect(self.edit_requested)
        self.change_password_button.clicked.connect(self.change_password_requested)
        self.deactivate_button.clicked.connect(self.deactivate_requested)
        self.reactivate_button.clicked.connect(self.reactivate_requested)
        self.toolbar.search_requested.connect(self._search)
        self.toolbar.sort_combo.currentIndexChanged.connect(self._sort_changed)
        self.toolbar.refresh_requested.connect(self._reset_filters)
        self.footer.page_requested.connect(self.page_requested)
        self.table.itemSelectionChanged.connect(self._select)
        self.table.cellDoubleClicked.connect(lambda row, _column: self._request_open_customer(self._row_id(row)))
        self.table.installEventFilter(self)
        self.empty_action_button.clicked.connect(self._empty_action)
        self.clear_details()

    def _install_customers_hero(self) -> None:
        """Place the customers hero inside the list page without shared-API dependencies.

        The current project version has no shared helper for inserting list
        headers. Inserting directly into the existing list-page
        layout keeps this view compatible and also makes the hero disappear
        automatically when the details page is shown.
        """
        header = self.workspace.scaffold.header
        header.hide()
        header.setFixedHeight(0)

        listing = self.workspace.list_page.layout()
        if listing is None:
            raise RuntimeError("Customers list page has no layout")
        listing.insertWidget(0, self.hero)

    def _move_header_into_hero(self) -> None:
        identity_layout = self.workspace.header_identity.layout()
        if identity_layout is not None:
            identity_layout.removeWidget(self.workspace.scaffold.header.title)
            identity_layout.removeWidget(self.workspace.scaffold.header.description)
        action_slot = self.workspace.scaffold.header.action_slot
        action_slot.removeWidget(self.workspace.create_button)
        self.hero.attach_header(
            self.workspace.scaffold.header.title,
            self.workspace.scaffold.header.description,
            self.workspace.create_button,
        )

    def _apply_customers_rtl_alignment(self) -> None:
        self.workspace.header_identity.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.workspace.create_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.workspace.table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.workspace.footer.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.workspace.results_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

        for label in (
            self.workspace.scaffold.header.title,
            self.workspace.scaffold.header.description,
            self.workspace.results_label,
            self.workspace.empty_title,
            self.workspace.empty_description,
            self.workspace.footer.label,
        ):
            label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            label.setAlignment(_RIGHT_LABEL_ALIGNMENT)

        for button in (
            self.workspace.create_button,
            self.workspace.toolbar.search_button,
            self.workspace.toolbar.refresh_button,
            self.workspace.empty_action_button,
            self.workspace.footer.previous_button,
            self.workspace.footer.next_button,
        ):
            button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            button.setStyleSheet("text-align: right;")

        self.workspace.toolbar.search_input.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.workspace.toolbar.search_input.setAlignment(_RIGHT_TEXT_ALIGNMENT)
        self.workspace.toolbar.sort_combo.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.workspace.toolbar.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        toolbar_layout = self.workspace.toolbar.layout()
        toolbar_layout.setDirection(QBoxLayout.Direction.RightToLeft)
        for control in (
            self.workspace.toolbar.search_input,
            self.workspace.toolbar.search_button,
            self.workspace.toolbar.sort_combo,
            self.workspace.toolbar.refresh_button,
        ):
            toolbar_layout.removeWidget(control)
        toolbar_layout.addWidget(self.workspace.toolbar.search_input, 1)
        toolbar_layout.addWidget(self.workspace.toolbar.search_button)
        toolbar_layout.addWidget(self.workspace.toolbar.sort_combo)
        toolbar_layout.addWidget(self.workspace.toolbar.refresh_button)

        header = self.workspace.table.horizontalHeader()
        header.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        header.setDefaultAlignment(_RIGHT_TEXT_ALIGNMENT)
        for column in range(self.workspace.table.columnCount()):
            header_item = self.workspace.table.horizontalHeaderItem(column)
            if header_item is not None:
                header_item.setTextAlignment(_RIGHT_TEXT_ALIGNMENT)

    def _apply_customer_detail_design(self) -> None:
        """Apply a deterministic customer-only layout and style.

        The shared workspace uses semantic RTL layouts. For this screen we
        rebuild the two critical rows explicitly so Qt cannot mirror the
        physical right edge or hide text through stylesheet cascade order.
        """
        page = self.workspace.details_page
        page.setObjectName("customerDetailsPage")
        page.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        self.workspace.details_scroll.setObjectName("customerDetailsScroll")
        self.workspace.details_scroll.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.workspace.details_widget.setObjectName("customerDetailsCanvas")
        self.workspace.details_widget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.workspace.details_scroll.viewport().setAutoFillBackground(False)

        # Back navigation deliberately stays on the physical left.
        self.workspace.back_button.setObjectName("customerBackButton")
        self.workspace.back_button.setText("← חזרה לרשימת לקוחות")
        self.workspace.back_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.workspace.back_button.setMinimumWidth(196)
        self.workspace.back_button.setMinimumHeight(42)
        self.workspace.back_button.setStyleSheet(
            f"""
            QPushButton {{
                color: {COLOR_BRAND};
                background: {COLOR_SURFACE};
                border: 1px solid #BFDDE1;
                border-radius: 9px;
                padding: 0 16px;
                font-weight: 600;
                text-align: center;
            }}
            QPushButton:hover {{
                color: {COLOR_BRAND};
                background: {COLOR_BRAND_SOFT};
                border-color: {COLOR_BRAND};
            }}
            QPushButton:pressed {{
                color: {COLOR_BRAND};
                background: {COLOR_SURFACE_ALT};
            }}
            """
        )
        back_layout = self.workspace.back_button.parentWidget().layout()
        if back_layout is not None:
            while back_layout.count():
                back_layout.takeAt(0)
            back_layout.setDirection(QBoxLayout.Direction.LeftToRight)
            back_layout.addWidget(
                self.workspace.back_button,
                0,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignAbsolute,
            )
            back_layout.addStretch(1)

        # Rebuild the identity block without the nested semantic RTL row.
        # This guarantees that the title, badge and subtitle share one exact
        # physical right edge, including when the customer name is English.
        identity_layout = self.workspace.identity_container.layout()
        if identity_layout is not None:
            while identity_layout.count():
                identity_layout.takeAt(0)
            identity_layout.setDirection(QBoxLayout.Direction.TopToBottom)
            identity_layout.setContentsMargins(0, 0, 0, 0)
            identity_layout.setSpacing(SPACE_2)

        self.workspace.identity_container.setObjectName("customerDetailIdentity")
        self.workspace.identity_container.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.workspace.identity_container.setMinimumWidth(420)
        self.workspace.identity_container.setMaximumWidth(560)
        self.workspace.identity_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        self.workspace.detail_title.setObjectName("customerDetailTitle")
        self.workspace.detail_title.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.workspace.detail_title.setAlignment(_RIGHT_TEXT_ALIGNMENT)
        self.workspace.detail_title.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        self.workspace.detail_status.setObjectName("customerDetailStatus")
        self.workspace.detail_status.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.workspace.detail_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.workspace.detail_status.setMinimumWidth(78)
        self.workspace.detail_status.setMaximumWidth(96)

        self.workspace.detail_subtitle.setObjectName("customerDetailSubtitle")
        self.workspace.detail_subtitle.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.workspace.detail_subtitle.setAlignment(_RIGHT_TEXT_ALIGNMENT)
        self.workspace.detail_subtitle.setMaximumWidth(540)
        self.workspace.detail_subtitle.setMinimumHeight(40)
        self.workspace.detail_subtitle.setWordWrap(True)
        self.workspace.detail_subtitle.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        if identity_layout is not None:
            identity_layout.addWidget(
                self.workspace.detail_title,
                0,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute,
            )
            identity_layout.addWidget(
                self.workspace.detail_status,
                0,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute,
            )
            identity_layout.addWidget(
                self.workspace.detail_subtitle,
                0,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute,
            )

        # Put actions on the physical left and identity on the physical right.
        header = self.workspace.detail_header
        header.setObjectName("customerDetailHeader")
        header.setProperty("customerDetailHeader", True)
        header.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        header.setMinimumHeight(156)
        header_layout = header.layout()
        if header_layout is not None:
            while header_layout.count():
                header_layout.takeAt(0)
            header_layout.setDirection(QBoxLayout.Direction.LeftToRight)
            header_layout.setContentsMargins(SPACE_6, SPACE_4, SPACE_6, SPACE_4)
            header_layout.setSpacing(SPACE_4)
            header_layout.addWidget(
                self.workspace.actions_container,
                0,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignAbsolute,
            )
            header_layout.addStretch(1)
            header_layout.addWidget(
                self.workspace.identity_container,
                0,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignAbsolute,
            )

        self.workspace.actions_container.setObjectName("customerDetailActions")
        self.workspace.actions_container.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.workspace.actions_container.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Fixed,
        )
        actions_layout = self.workspace.actions
        while actions_layout.count():
            actions_layout.takeAt(0)
        actions_layout.setDirection(QBoxLayout.Direction.LeftToRight)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(SPACE_2)
        actions_layout.addWidget(self.deactivate_button)
        actions_layout.addWidget(self.reactivate_button)
        actions_layout.addWidget(self.change_password_button)
        actions_layout.addWidget(self.edit_button)

        self._style_customer_action_button(self.edit_button, "edit")
        self._style_customer_action_button(self.change_password_button, "password")
        self._style_customer_action_button(self.deactivate_button, "deactivate")
        self._style_customer_action_button(self.reactivate_button, "reactivate")

        card_roles = (
            (self.customer_details, "primary"),
            (self.contact_details, "contact"),
            (self.system_details, "system"),
        )
        styled_widgets = [
            page,
            header,
            self.workspace.identity_container,
            self.workspace.detail_title,
            self.workspace.detail_status,
            self.workspace.detail_subtitle,
            self.workspace.actions_container,
        ]
        for form, role in card_roles:
            form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
            form.setHorizontalSpacing(SPACE_3)
            form.setVerticalSpacing(SPACE_2)
            form.setLabelAlignment(_RIGHT_LABEL_ALIGNMENT)
            form.setFormAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
            form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            host = form.parentWidget()
            if host is not None:
                host.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            frame = host.parentWidget() if host is not None else None
            if frame is not None:
                frame.setProperty("customerDetailCard", True)
                frame.setProperty("customerDetailCardRole", role)
                frame.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Preferred,
                )
                styled_widgets.append(frame)

        self.workspace.cards.setDirection(QBoxLayout.Direction.RightToLeft)
        self.workspace.cards.setAlignment(Qt.AlignmentFlag.AlignTop)
        if self.workspace._secondary_layout is not None:
            self.workspace._secondary_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._refresh_styles(*styled_widgets)

    @staticmethod
    def _style_customer_action_button(button: QPushButton, role: str) -> None:
        button.setObjectName(f"customerDetailAction_{role}")
        button.setMinimumWidth(124)
        button.setMaximumWidth(148)
        button.setMinimumHeight(42)
        button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        if role == "edit":
            base_color = "#FFFFFF"
            base_background = COLOR_BRAND
            base_border = COLOR_BRAND
            hover_background = COLOR_BRAND_HOVER
            hover_border = COLOR_BRAND_HOVER
            pressed_background = COLOR_BRAND_PRESSED
        elif role == "deactivate":
            base_color = COLOR_ERROR
            base_background = COLOR_SURFACE
            base_border = "#E6B8B5"
            hover_background = COLOR_ERROR_BACKGROUND
            hover_border = COLOR_ERROR
            pressed_background = "#F8DEDC"
        elif role == "reactivate":
            base_color = COLOR_SUCCESS
            base_background = COLOR_SUCCESS_BACKGROUND
            base_border = "#BFDDBF"
            hover_background = "#DFF1E2"
            hover_border = COLOR_SUCCESS
            pressed_background = "#D4EBD8"
        else:
            base_color = COLOR_TEXT
            base_background = COLOR_SURFACE
            base_border = COLOR_BORDER_STRONG
            hover_background = COLOR_SURFACE_ALT
            hover_border = COLOR_BRAND
            pressed_background = COLOR_BACKGROUND

        button.setStyleSheet(
            f"""
            QPushButton {{
                color: {base_color};
                background: {base_background};
                border: 1px solid {base_border};
                border-radius: 8px;
                padding: 0 14px;
                font-weight: 600;
                text-align: center;
            }}
            QPushButton:hover {{
                color: {base_color};
                background: {hover_background};
                border-color: {hover_border};
            }}
            QPushButton:pressed {{
                color: {base_color};
                background: {pressed_background};
                border-color: {hover_border};
            }}
            QPushButton:disabled {{
                color: {COLOR_DISABLED_TEXT};
                background: {COLOR_DISABLED_BACKGROUND};
                border-color: {COLOR_BORDER};
            }}
            """
        )

    @staticmethod
    def _refresh_styles(*widgets: QWidget) -> None:
        for widget in widgets:
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    @staticmethod
    def _is_rtl_text(value: str) -> bool:
        return any("\u0590" <= character <= "\u05FF" for character in value)

    def _add_customer_detail_row(self, form: QFormLayout, label: str, content: QLabel) -> None:
        label_widget = QLabel(label)
        label_widget.setProperty("customerDetailFieldLabel", True)
        label_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        label_widget.setAlignment(_RIGHT_LABEL_ALIGNMENT)
        label_widget.setFixedWidth(128)

        content.setProperty("customerDetailFieldValue", True)
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        content.setMinimumHeight(40)
        content.setContentsMargins(0, 0, 0, 0)
        content.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
            if self._is_rtl_text(content.text())
            else Qt.LayoutDirection.LeftToRight
        )
        # AlignAbsolute keeps the physical edge on the right while LTR values
        # such as email addresses and phone numbers retain their character order.
        content.setAlignment(_RIGHT_TEXT_ALIGNMENT)

        form.addRow(label_widget, content)
        self._refresh_styles(label_widget, content)

    def eventFilter(self, watched, event) -> bool:
        if watched is self.table and event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._open_selected_customer()
            return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape and self.pages.currentWidget() is self.details_page:
            self.workspace.show_list()
            return
        super().keyPressEvent(event)

    def _search(self, search: str, _sort: str) -> None:
        self.filters_requested.emit({"search": search or None, "order_by": self.sort_by.currentData()})

    def _sort_changed(self, _index: int) -> None:
        self.filters_requested.emit({"order_by": self.sort_by.currentData()})

    def _reset_filters(self) -> None:
        self.toolbar.search_input.clear()
        blocked = self.sort_by.blockSignals(True)
        self.sort_by.setCurrentIndex(0)
        self.sort_by.blockSignals(blocked)
        self.clear_details()
        self.filters_requested.emit({"search": None, "order_by": "name", "_clear_selection": True})

    def _empty_action(self) -> None:
        self._reset_filters() if self._empty_filtered else self.create_requested.emit()

    def _select(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self._selected_customer_id = None
            return
        customer_id = self._row_id(rows[0].row())
        changed = customer_id != self._selected_customer_id
        self._selected_customer_id = customer_id
        if changed:
            self._clear_forms()
            self.workspace.detail_title.clear()
            self.workspace.set_actions_enabled(False)
            self.customer_selected.emit(customer_id)

    def _open_selected_customer(self) -> None:
        if self._selected_customer_id:
            self._pending_open_id = self._selected_customer_id
        if self._selected_customer_id and self.workspace.detail_title.text():
            self._pending_open_id = None
            self.workspace.show_details()

    def _row_id(self, row: int) -> str:
        # עמודת השם שומרת את מזהה הלקוח; עמודת הפעולות נמצאת בקצה השמאלי.
        return str(self.table.item(row, 1).data(Qt.ItemDataRole.UserRole))

    def _request_open_customer(self, customer_id: str) -> None:
        self._pending_open_id = customer_id
        self.select_customer(customer_id)
        if self.workspace.detail_title.text() and self._selected_customer_id == customer_id:
            self._pending_open_id = None
            self.workspace.show_details()

    def set_loading(self, value: bool) -> None:
        self.create_button.setEnabled(not value)
        for control in (self.toolbar.search_button, self.toolbar.refresh_button, self.sort_by):
            control.setEnabled(not value)
        if value and not self.table.rowCount():
            self.workspace.show_loading("טוען לקוחות…")

    def set_detail_loading(self, value: bool) -> None:
        if value:
            self.workspace.set_actions_enabled(False)

    def render_request_state(self, state: RequestState) -> None:
        if state.phase in {RequestPhase.SUCCESS, RequestPhase.VALIDATION_ERROR}:
            self.scaffold.feedback.render(state)
        elif state.phase not in {RequestPhase.LOADING, RequestPhase.IDLE, RequestPhase.EMPTY}:
            self.show_error(state.message, retriable=state.retryable, permission=state.phase == RequestPhase.AUTHORIZATION_ERROR)

    def show_error(self, message: str, *, retriable: bool = False, permission: bool = False) -> None:
        state = RequestState(
            RequestPhase.AUTHORIZATION_ERROR if permission else RequestPhase.CONNECTION_ERROR if retriable else RequestPhase.SERVER_ERROR,
            message,
            "customers",
            retryable=retriable,
        )
        if self.table.rowCount():
            self.retry.hide()
            self.scaffold.feedback.render(state)
        else:
            self.scaffold.feedback.hide()
            self.retry.show_message(message, retriable=retriable)

    def show_success(self, message: str) -> None:
        self.scaffold.feedback.render(RequestState(RequestPhase.SUCCESS, message, "customers"))

    def show_customers(self, rows, *, offset: int, count: int, filtered: bool) -> None:
        self.retry.hide()
        if not rows and offset > 0:
            self.page_requested.emit(max(0, offset - 25), 25)
            return
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            open_button = self.workspace.set_row_open_action(
                row_index, str(row["id"]), self._request_open_customer
            )
            open_button.setIcon(QIcon())
            open_button.setText("⋮")
            open_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            open_button.setProperty("customerRowAction", True)
            open_button.setToolTip("פתיחת פרטי לקוח")
            open_button.setAccessibleName("פתיחת פרטי לקוח")
            open_button.style().unpolish(open_button)
            open_button.style().polish(open_button)
            
            # עמודה 0: מספור
            val_id = str(offset + row_index + 1)
            item_id = QTableWidgetItem(val_id)
            item_id.setTextAlignment(_RIGHT_TEXT_ALIGNMENT)
            set_item_text(self.table, row_index, 0, item_id, tooltip_direction=Qt.LayoutDirection.RightToLeft)
            
            # עמודות 1 עד 4: שם, טלפון, אימייל, עיר
            keys_to_map = [
                ("name", "—"),        
                ("phone", "—"),       
                ("email", "—"),       
                ("city", "—"),        
            ]
            
            for offset_col, (key, fallback) in enumerate(keys_to_map):
                column = offset_col + 1  
                val = str(row.get(key) or fallback)
                item = QTableWidgetItem(val)
                
                alignment = _LTR_TEXT_ALIGNMENT if column in [2, 3] else _RIGHT_TEXT_ALIGNMENT
                item.setTextAlignment(alignment)
                
                tooltip_direction = (
                    Qt.LayoutDirection.LeftToRight
                    if column in [2, 3]
                    else Qt.LayoutDirection.RightToLeft
                )
                set_item_text(
                    self.table, row_index, column, item, tooltip_direction=tooltip_direction
                )
                
                if column == 1: # עמודת השם שומרת את המזהה האמיתי
                    item.setData(Qt.ItemDataRole.UserRole, str(row["id"]))
            
            # עמודה 5: סטטוס
            badge = ActiveBadge()
            badge.set_active(bool(row.get("is_active")))
            self.workspace.configure_status_badge(badge)
            self.table.setCellWidget(row_index, 5, badge)
            
            # עמודה 6: תאריך הצטרפות
            item_date = QTableWidgetItem(str(row.get("join_date") or "—"))
            item_date.setTextAlignment(_RIGHT_TEXT_ALIGNMENT)
            set_item_text(self.table, row_index, 6, item_date, tooltip_direction=Qt.LayoutDirection.RightToLeft)

        self.footer.set_page(offset=offset, count=count)
        self.workspace.results_label.setText(f"מציג {offset + 1}-{offset + len(rows)} מתוך {count}")
        self._empty_filtered = filtered
        self.workspace.show_empty_state(empty=not rows, filtered=filtered, plural="לקוחות")
        if not rows:
            self.empty_title.setText("לא נמצאו לקוחות" if filtered else "אין עדיין לקוחות")
            self.empty_description.setText("אפשר לאפס את החיפוש ולנסות שוב." if filtered else "צרו את הלקוח הראשון כדי להתחיל.")
            self.empty_action_button.setText("איפוס חיפוש ומסננים" if filtered else "לקוח חדש")
        self.footer.setVisible(bool(rows))

    def show_details(self, details, customer) -> None:
        self._selected_customer_id = str(customer.get("id")) if customer.get("id") is not None else self._selected_customer_id
        self._clear_forms()
        customer_labels = {"שם", "סוג לקוח", "עיר", "כתובת", "הערות"}
        contact_labels = {"טלפון", "דוא״ל", "איש קשר", "טלפון איש קשר"}
        for label, value in details:
            content = QLabel(value)
            content.setWordWrap(True)
            content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            content.setToolTip(value)
            form = self.customer_details if label in customer_labels else self.contact_details if label in contact_labels else self.system_details
            self._add_customer_detail_row(form, label, content)

        customer_name = str(customer.get("name") or "פרטי לקוח")
        self.workspace.show_detail_identity(customer_name, bool(customer.get("is_active")))
        self.workspace.detail_title.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
            if self._is_rtl_text(customer_name)
            else Qt.LayoutDirection.LeftToRight
        )
        self.workspace.detail_title.setAlignment(_RIGHT_TEXT_ALIGNMENT)
        self._refresh_styles(self.workspace.detail_title, self.workspace.detail_status)
        self.workspace.set_actions_enabled(True)
        self.workspace.show_lifecycle(bool(customer.get("is_active")), self.deactivate_button, self.reactivate_button)
        for button in (self.edit_button, self.change_password_button, self.deactivate_button, self.reactivate_button):
            set_disabled_explanation(button, "")
        if self._pending_open_id == str(customer.get("id")):
            self._pending_open_id = None
            self.workspace.show_details()

    def _clear_forms(self) -> None:
        for form in self.detail_forms.values():
            while form.rowCount():
                form.removeRow(0)

    def clear_details(self) -> None:
        if hasattr(self, "detail_forms"):
            self._clear_forms()
        self._selected_customer_id = None
        self._pending_open_id = None
        self.workspace.detail_title.clear()
        self.workspace.set_actions_enabled(False)
        self.workspace.show_list()
        self.table.clearSelection()
        self.deactivate_button.hide()
        self.reactivate_button.hide()
        for button in (self.edit_button, self.change_password_button, self.deactivate_button, self.reactivate_button):
            set_disabled_explanation(button, "יש לבחור לקוח תחילה")

    def reset_to_default(self) -> None:
        dialog = getattr(self, "_dialog", None)
        if dialog is not None and dialog.isVisible():
            dialog.reject()
        self.scaffold.feedback.hide()
        self.toolbar.search_input.clear()
        blocked = self.sort_by.blockSignals(True)
        self.sort_by.setCurrentIndex(0)
        self.sort_by.blockSignals(blocked)
        self.clear_details()

    def select_customer(self, customer_id: str) -> None:
        for row in range(self.table.rowCount()):
            if str(self.table.item(row, 1).data(Qt.ItemDataRole.UserRole)) == customer_id:
                blocked = self.table.blockSignals(True)
                index = self.table.model().index(row, 0)
                self.table.selectionModel().setCurrentIndex(
                    index,
                    QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows,
                )
                self.table.blockSignals(blocked)
                changed = self._selected_customer_id != customer_id
                self._selected_customer_id = customer_id
                if changed:
                    self.customer_selected.emit(customer_id)
                break

    def open_customer_form(self, initial, submit) -> None:
        self._dialog = CustomerDialog(initial, self)
        self._dialog.submitted.connect(submit)
        self._dialog.open()

    def open_change_password(self, submit) -> None:
        self._dialog = ChangePasswordDialog(self)
        self._dialog.submitted.connect(submit)
        self._dialog.open()

    def confirm_deactivation(self, name: str) -> bool:
        return confirm_action(self, "אישור השבתת לקוח", f"להשבית את הלקוח {name}? חשבון ההתחברות יושבת עד להפעלה מחדש.")