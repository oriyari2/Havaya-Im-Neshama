from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QBoxLayout, QFormLayout, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QPushButton, QSizePolicy, QTableWidget, QVBoxLayout, QWidget

from desktop_client.app.resource_paths import asset_path
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

_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute




class ReadOnlyProfileCard(QFrame):
    """RTL-safe read-only card used by customer/instructor profile pages."""

    def __init__(self, title: str, role: str) -> None:
        super().__init__()
        self.setProperty("managementDetailCard", True)
        self.setProperty("managementDetailCardRole", role)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        root = QVBoxLayout(self)
        root.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_4)
        root.setSpacing(SPACE_3)

        heading = QLabel(title)
        heading.setObjectName("sectionTitle")
        heading.setAlignment(_RIGHT)
        root.addWidget(heading)

        self.rows_host = QWidget()
        self.rows_host.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.rows = QVBoxLayout(self.rows_host)
        self.rows.setContentsMargins(0, 0, 0, 0)
        self.rows.setSpacing(SPACE_2)
        root.addWidget(self.rows_host)
        root.addStretch(1)

    def clear_rows(self) -> None:
        while self.rows.count():
            item = self.rows.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def add_row(self, label_text: str, value: str, *, mixed_direction: bool = False) -> None:
        row = QWidget()
        row.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACE_3)
        layout.setDirection(QHBoxLayout.Direction.LeftToRight)

        value_label = QLabel(value)
        value_label.setProperty("managementDetailFieldValue", True)
        value_label.setWordWrap(True)
        value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        value_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        value_label.setMinimumHeight(40)
        if mixed_direction:
            value_label.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        else:
            value_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        value_label.setAlignment(_RIGHT)

        field_label = QLabel(label_text)
        field_label.setProperty("managementDetailFieldLabel", True)
        field_label.setFixedWidth(132)
        field_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        field_label.setAlignment(_RIGHT)

        layout.addWidget(value_label, 1)
        layout.addWidget(field_label, 0)
        self.rows.addWidget(row)


class ManagementHero(QWidget):
    """Reusable hero that mirrors the approved Customers screen composition."""

    def __init__(self, image_path: Path, accessible_name: str) -> None:
        super().__init__()
        self.setObjectName("managementHero")
        self._pixmap = QPixmap(str(image_path))
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.setFixedHeight(166)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAccessibleName(accessible_name)

    def attach_header(self, title: QLabel, subtitle: QLabel, action: QPushButton | None = None) -> None:
        title.setProperty("managementHeroTitle", True)
        subtitle.setProperty("managementHeroSubtitle", True)
        for label in (title, subtitle):
            label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            label.setAlignment(_RIGHT)
            label.setWordWrap(False)
            label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            label.setStyleSheet("margin: 0; padding: 0; background: transparent; border: none;")
        subtitle.setWordWrap(True)
        subtitle.setMaximumHeight(42)

        if action is not None:
            action.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            action.setMinimumWidth(142)
            action.setMinimumHeight(42)
            action.setProperty("managementHeroAction", True)
            style_reference_button(action, "primary")

        layout = QGridLayout(self)
        layout.setOriginCorner(Qt.Corner.TopLeftCorner)
        layout.setContentsMargins(SPACE_6, 0, SPACE_6, 0)
        layout.setHorizontalSpacing(SPACE_4)
        layout.setVerticalSpacing(0)
        layout.setRowStretch(0, 1)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)

        if action is not None:
            action_box = QWidget()
            action_box.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            action_layout = QVBoxLayout(action_box)
            action_layout.setContentsMargins(0, 0, 0, 20)
            action_layout.addStretch(1)
            action_layout.addWidget(
                action,
                0,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignAbsolute,
            )
            layout.addWidget(action_box, 0, 0)

        title_box = QWidget()
        title_box.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        title_box.setMinimumWidth(380)
        title_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        title_layout = QVBoxLayout(title_box)
        # Match the approved dashboard hero exactly: title/subtitle are vertically
        # centered as one compact group on the right side of the image wash.
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(SPACE_1)
        title_layout.addStretch(1)
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        title_layout.addStretch(1)
        # Let the title box fill the hero row. Its internal top/bottom stretches
        # keep the title + subtitle vertically centered, matching the approved dashboard.
        # Using AlignTop here collapses the box to its sizeHint and pushes every title
        # to the top edge of the hero.
        layout.addWidget(title_box, 0, 2)

        _refresh(title, subtitle, action)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width, height = self.width(), self.height()

        clip = QPainterPath()
        clip.lineTo(width, 0)
        clip.lineTo(width, height - 30)
        clip.cubicTo(width * 0.65, height, width * 0.35, height - 25, 0, height - 15)
        clip.lineTo(0, 0)
        painter.setClipPath(clip)

        if not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            source_x = max(0, (scaled.width() - width) // 2)
            source_y = max(0, (scaled.height() - height) // 2)
            painter.drawPixmap(self.rect(), scaled, QRect(source_x, source_y, width, height))

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


def install_management_hero(workspace, image_filename: str, accessible_name: str) -> ManagementHero:
    """Move the existing header widgets into a role-specific hero without changing signals."""
    hero_path = asset_path("heroes", image_filename)
    hero = ManagementHero(hero_path, accessible_name)

    identity_layout = workspace.header_identity.layout()
    if identity_layout is not None:
        identity_layout.removeWidget(workspace.scaffold.header.title)
        identity_layout.removeWidget(workspace.scaffold.header.description)
    workspace.scaffold.header.action_slot.removeWidget(workspace.create_button)
    hero.attach_header(workspace.scaffold.header.title, workspace.scaffold.header.description, workspace.create_button)

    workspace.scaffold.header.hide()
    workspace.scaffold.header.setFixedHeight(0)
    listing = workspace.list_page.layout()
    if listing is None:
        raise RuntimeError("Management list page has no layout")
    listing.insertWidget(0, hero)
    return hero


def apply_reference_list_layout(workspace, *, extra_toolbar_controls: tuple[QWidget, ...] = ()) -> None:
    """Apply the approved Customers RTL/list rhythm while preserving behavior."""
    # Compact the shared management pages slightly so more data fits on screen
    # without changing any controls or behavior.
    workspace.scaffold.root.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_4)
    workspace.scaffold.root.setSpacing(SPACE_2)
    workspace.table.setProperty("managementReferenceTable", True)
    workspace.table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    workspace.footer.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    workspace.results_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

    for label in (
        workspace.scaffold.header.title,
        workspace.scaffold.header.description,
        workspace.results_label,
        workspace.empty_title,
        workspace.empty_description,
        workspace.footer.label,
    ):
        label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        label.setAlignment(_RIGHT)

    workspace.toolbar.search_input.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    workspace.toolbar.search_input.setAlignment(_RIGHT)
    workspace.toolbar.sort_combo.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    workspace.toolbar.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    # Complete local styles prevent the global QSS disabled/loading state from
    # turning button text white on a pale background in Instructors/Managers.
    style_reference_button(workspace.toolbar.search_button, "primary")
    style_reference_button(workspace.toolbar.refresh_button, "secondary")
    workspace.toolbar.search_button.setMinimumWidth(92)
    workspace.toolbar.refresh_button.setMinimumWidth(88)

    toolbar_layout = workspace.toolbar.layout()
    if toolbar_layout is not None:
        toolbar_layout.setDirection(QBoxLayout.Direction.RightToLeft)
        controls = (
            workspace.toolbar.search_input,
            workspace.toolbar.search_button,
            workspace.toolbar.sort_combo,
            *extra_toolbar_controls,
            workspace.toolbar.refresh_button,
        )
        for control in controls:
            toolbar_layout.removeWidget(control)
        toolbar_layout.addWidget(workspace.toolbar.search_input, 1)
        toolbar_layout.addWidget(workspace.toolbar.search_button)
        toolbar_layout.addWidget(workspace.toolbar.sort_combo)
        for control in extra_toolbar_controls:
            toolbar_layout.addWidget(control)
        toolbar_layout.addWidget(workspace.toolbar.refresh_button)

    header = workspace.table.horizontalHeader()
    header.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    header.setDefaultAlignment(_RIGHT)
    for column in range(workspace.table.columnCount()):
        item = workspace.table.horizontalHeaderItem(column)
        if item is not None:
            item.setTextAlignment(_RIGHT)

    _refresh(workspace.table, workspace.results_label, workspace.toolbar)


def apply_reference_detail_layout(
    workspace,
    *,
    back_text: str,
    actions: tuple[tuple[QPushButton, str], ...],
    cards: tuple[tuple[QFormLayout, str], ...],
) -> None:
    """Apply the approved Customers detail layout to another management module."""
    page = workspace.details_page
    page.setObjectName("managementDetailsPage")
    page.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    page_layout = page.layout()
    if page_layout is not None:
        page_layout.setSpacing(SPACE_3)
    workspace.details_scroll.setObjectName("managementDetailsScroll")
    workspace.details_scroll.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    workspace.details_widget.setObjectName("managementDetailsCanvas")
    workspace.details_widget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    details_body_layout = workspace.details_widget.layout()
    if details_body_layout is not None:
        details_body_layout.setSpacing(SPACE_3)
    workspace.details_scroll.viewport().setAutoFillBackground(False)

    workspace.back_button.setObjectName("managementBackButton")
    workspace.back_button.setText(back_text)
    workspace.back_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    workspace.back_button.setMinimumWidth(196)
    workspace.back_button.setMinimumHeight(42)
    _style_back_button(workspace.back_button)
    back_layout = workspace.back_button.parentWidget().layout()
    if back_layout is not None:
        while back_layout.count():
            back_layout.takeAt(0)
        back_layout.setDirection(QBoxLayout.Direction.LeftToRight)
        back_layout.addWidget(
            workspace.back_button,
            0,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignAbsolute,
        )
        back_layout.addStretch(1)

    identity_layout = workspace.identity_container.layout()
    if identity_layout is not None:
        while identity_layout.count():
            identity_layout.takeAt(0)
        identity_layout.setDirection(QBoxLayout.Direction.TopToBottom)
        identity_layout.setContentsMargins(0, 0, 0, 0)
        identity_layout.setSpacing(SPACE_1)

    workspace.identity_container.setObjectName("managementDetailIdentity")
    workspace.identity_container.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    workspace.identity_container.setMinimumWidth(0)
    workspace.identity_container.setMaximumWidth(16777215)
    workspace.identity_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    workspace.detail_title.setObjectName("managementDetailTitle")
    workspace.detail_title.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    workspace.detail_title.setAlignment(_RIGHT)
    workspace.detail_title.setWordWrap(True)
    workspace.detail_title.setMinimumHeight(max(42, workspace.detail_title.fontMetrics().lineSpacing() * 2))
    workspace.detail_title.setMaximumHeight(16777215)
    workspace.detail_title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    workspace.detail_status.setObjectName("managementDetailStatus")
    workspace.detail_status.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    workspace.detail_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
    workspace.detail_status.setMinimumWidth(78)
    workspace.detail_status.setMaximumWidth(110)
    workspace.detail_status.setMinimumHeight(26)

    workspace.detail_subtitle.setObjectName("managementDetailSubtitle")
    workspace.detail_subtitle.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    workspace.detail_subtitle.setAlignment(_RIGHT)
    workspace.detail_subtitle.setMaximumWidth(16777215)
    # Reserve at least two complete text lines. QLabel word-wrap can otherwise
    # report a one-line size hint before the final width is known, which clips
    # the second line in detail headers on Windows/Qt.
    workspace.detail_subtitle.setMinimumHeight(
        workspace.detail_subtitle.fontMetrics().lineSpacing() * 2 + SPACE_1
    )
    workspace.detail_subtitle.setMaximumHeight(16777215)
    workspace.detail_subtitle.setWordWrap(True)
    workspace.detail_subtitle.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    if identity_layout is not None:
        # Do not attach horizontal layout alignment to the text labels. An
        # aligned QLayoutItem is constrained to its size hint instead of using
        # the full header width, which made wrapped subtitles appear clipped.
        # The QLabel alignment itself still keeps all text physically right-aligned.
        identity_layout.addWidget(workspace.detail_title)
        identity_layout.addWidget(
            workspace.detail_status,
            0,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute,
        )
        identity_layout.addWidget(workspace.detail_subtitle)

    header = workspace.detail_header
    header.setObjectName("managementDetailHeader")
    header.setProperty("managementDetailHeader", True)
    header.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    header.setMinimumHeight(216)
    header.setMaximumHeight(16777215)
    header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    header_layout = header.layout()
    if header_layout is not None:
        while header_layout.count():
            header_layout.takeAt(0)
        # Two vertical regions preserve the approved right-aligned identity and
        # bottom-left actions without forcing them to compete for one horizontal
        # line. Long names, statuses and subtitles therefore remain readable.
        header_layout.setDirection(QBoxLayout.Direction.TopToBottom)
        header_layout.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_3)
        header_layout.setSpacing(SPACE_3)
        # Let the identity region consume the full available width. The labels
        # inside it perform their own right alignment, while the expanded width
        # gives wrapped title/subtitle text enough room to render completely.
        header_layout.addWidget(workspace.identity_container)
        header_layout.addStretch(1)
        header_layout.addWidget(
            workspace.actions_container,
            0,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignAbsolute,
        )

    workspace.actions_container.setObjectName("managementDetailActions")
    workspace.actions_container.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    workspace.actions_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
    action_layout = workspace.actions
    while action_layout.count():
        action_layout.takeAt(0)
    action_layout.setDirection(QBoxLayout.Direction.LeftToRight)
    action_layout.setContentsMargins(0, 0, 0, 0)
    action_layout.setSpacing(SPACE_2)
    for button, role in actions:
        action_layout.addWidget(button)
        _style_action_button(button, role)

    styled_widgets: list[QWidget] = [
        page,
        header,
        workspace.identity_container,
        workspace.detail_title,
        workspace.detail_status,
        workspace.detail_subtitle,
        workspace.actions_container,
    ]
    for form, role in cards:
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form.setHorizontalSpacing(SPACE_3)
        form.setVerticalSpacing(SPACE_2)
        form.setLabelAlignment(_RIGHT)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        host = form.parentWidget()
        if host is not None:
            host.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        frame = host.parentWidget() if host is not None else None
        if frame is not None:
            frame.setProperty("managementDetailCard", True)
            frame.setProperty("managementDetailCardRole", role)
            frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            styled_widgets.append(frame)

    workspace.cards.setDirection(QBoxLayout.Direction.RightToLeft)
    workspace.cards.setAlignment(Qt.AlignmentFlag.AlignTop)
    if workspace._secondary_layout is not None:
        workspace._secondary_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    _refresh(*styled_widgets)


def style_reference_extra_panel(panel: QWidget, *, role: str = "neutral") -> None:
    panel.setProperty("managementExtraPanel", True)
    panel.setProperty("managementExtraPanelRole", role)
    _refresh(panel)


def install_scaffold_hero(scaffold, image_filename: str, accessible_name: str) -> ManagementHero:
    """Install the approved hero on a regular PageScaffold without changing its actions/signals."""
    hero_path = asset_path("heroes", image_filename)
    hero = ManagementHero(hero_path, accessible_name)
    hero.attach_header(scaffold.header.title, scaffold.header.description, None)
    scaffold.header.hide()
    scaffold.header.setFixedHeight(0)
    scaffold.root.insertWidget(0, hero)
    return hero


def style_reference_button(button: QPushButton, role: str = "secondary") -> None:
    """Apply a complete local button style so global QSS cannot hide its text."""
    button.setMinimumHeight(40)
    button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    if role == "primary":
        color, background, border = "#FFFFFF", COLOR_BRAND, COLOR_BRAND
        hover_background, hover_border, pressed_background = COLOR_BRAND_HOVER, COLOR_BRAND_HOVER, COLOR_BRAND_PRESSED
    elif role == "destructive":
        color, background, border = COLOR_ERROR, COLOR_SURFACE, "#E6B8B5"
        hover_background, hover_border, pressed_background = COLOR_ERROR_BACKGROUND, COLOR_ERROR, "#F8DEDC"
    elif role == "success":
        color, background, border = COLOR_SUCCESS, COLOR_SUCCESS_BACKGROUND, "#BFDDBF"
        hover_background, hover_border, pressed_background = "#DFF1E2", COLOR_SUCCESS, "#D4EBD8"
    else:
        color, background, border = COLOR_TEXT, COLOR_SURFACE, COLOR_BORDER_STRONG
        hover_background, hover_border, pressed_background = COLOR_SURFACE_ALT, COLOR_BRAND, COLOR_BACKGROUND
    button.setStyleSheet(
        f"""
        QPushButton {{ color: {color}; background: {background}; border: 1px solid {border};
            border-radius: 8px; padding: 0 16px; font-weight: 600; text-align: center; }}
        QPushButton:hover {{ color: {color}; background: {hover_background}; border-color: {hover_border}; }}
        QPushButton:pressed {{ color: {color}; background: {pressed_background}; border-color: {hover_border}; }}
        QPushButton:disabled {{ color: {COLOR_DISABLED_TEXT}; background: {COLOR_DISABLED_BACKGROUND}; border-color: {COLOR_BORDER}; }}
        """
    )


def style_reference_table(table: QTableWidget, *, stretch: bool = True) -> None:
    """Bring an auxiliary table into the same visual/RTL system as the approved list tables."""
    table.setProperty("managementReferenceTable", True)
    table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    table.verticalHeader().hide()
    header = table.horizontalHeader()
    header.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    header.setDefaultAlignment(_RIGHT)
    if stretch:
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    for column in range(table.columnCount()):
        item = table.horizontalHeaderItem(column)
        if item is not None:
            item.setTextAlignment(_RIGHT)
    _refresh(table)


def style_reference_form(form: QFormLayout, *, label_width: int = 136) -> None:
    """Right-align a read-only/property form while keeping values spacious and consistent."""
    form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
    form.setHorizontalSpacing(SPACE_3)
    form.setVerticalSpacing(SPACE_2)
    form.setLabelAlignment(_RIGHT)
    form.setFormAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
    for row in range(form.rowCount()):
        label_item = form.itemAt(row, QFormLayout.ItemRole.LabelRole)
        field_item = form.itemAt(row, QFormLayout.ItemRole.FieldRole)
        label = label_item.widget() if label_item is not None else None
        field = field_item.widget() if field_item is not None else None
        if isinstance(label, QLabel):
            label.setFixedWidth(label_width)
            label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            label.setAlignment(_RIGHT)
            label.setProperty("managementDetailFieldLabel", True)
        if isinstance(field, QLabel):
            field.setAlignment(_RIGHT)
            field.setProperty("managementDetailFieldValue", True)
            field.setMinimumHeight(40)
            field.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    host = form.parentWidget()
    if host is not None:
        host.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    _refresh(host)


def _style_action_button(button: QPushButton, role: str) -> None:
    button.setProperty("managementDetailAction", role)
    # Use one generous width for lifecycle actions. It keeps the visual rhythm
    # consistent and fits labels such as "הפעלת מדריך מחדש" in full.
    button.setMinimumWidth(176)
    button.setMaximumWidth(176)
    button.setMinimumHeight(42)
    button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    if role == "primary":
        color, background, border = "#FFFFFF", COLOR_BRAND, COLOR_BRAND
        hover_background, hover_border, pressed_background = COLOR_BRAND_HOVER, COLOR_BRAND_HOVER, COLOR_BRAND_PRESSED
    elif role == "destructive":
        color, background, border = COLOR_ERROR, COLOR_SURFACE, "#E6B8B5"
        hover_background, hover_border, pressed_background = COLOR_ERROR_BACKGROUND, COLOR_ERROR, "#F8DEDC"
    elif role == "success":
        color, background, border = COLOR_SUCCESS, COLOR_SUCCESS_BACKGROUND, "#BFDDBF"
        hover_background, hover_border, pressed_background = "#DFF1E2", COLOR_SUCCESS, "#D4EBD8"
    else:
        color, background, border = COLOR_TEXT, COLOR_SURFACE, COLOR_BORDER_STRONG
        hover_background, hover_border, pressed_background = COLOR_SURFACE_ALT, COLOR_BRAND, COLOR_BACKGROUND

    button.setStyleSheet(
        f"""
        QPushButton {{
            color: {color};
            background: {background};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 0 14px;
            font-weight: 600;
            text-align: center;
        }}
        QPushButton:hover {{
            color: {color};
            background: {hover_background};
            border-color: {hover_border};
        }}
        QPushButton:pressed {{
            color: {color};
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


def _style_back_button(button: QPushButton) -> None:
    button.setStyleSheet(
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
        QPushButton:hover {{ color: {COLOR_BRAND}; background: {COLOR_BRAND_SOFT}; border-color: {COLOR_BRAND}; }}
        QPushButton:pressed {{ color: {COLOR_BRAND}; background: {COLOR_SURFACE_ALT}; }}
        """
    )


def _refresh(*widgets: QWidget) -> None:
    """Re-polish widgets without calling QAbstractItemView.update(index).

    QTableWidget/QAbstractItemView defines its own update(QModelIndex) overload,
    which hides QWidget.update() in PySide6. repaint() is inherited from
    QWidget and is safe for both ordinary widgets and item views.
    """
    for widget in widgets:
        if widget is None:
            continue
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.updateGeometry()
        widget.repaint()
