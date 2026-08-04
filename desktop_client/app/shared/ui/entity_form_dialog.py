from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.shared.ui.design_tokens import (
    COLOR_BACKGROUND,
    COLOR_BORDER,
    COLOR_BRAND,
    COLOR_BRAND_HOVER,
    COLOR_BRAND_PRESSED,
    COLOR_DISABLED_BACKGROUND,
    COLOR_DISABLED_TEXT,
    COLOR_SURFACE,
    COLOR_SURFACE_ALT,
    COLOR_TEXT,
    CONTROL_HEIGHT_LARGE,
    SPACE_1,
    SPACE_2,
    SPACE_3,
)
from desktop_client.app.shared.ui.foundations import FeedbackBanner, configure_mixed_direction

_ALIGN_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute


@dataclass(frozen=True)
class DialogField:
    key: str
    create_label: str
    edit_label: str | None = None
    kind: str = "line"
    mixed_direction: bool = False
    create_only: bool = False
    read_only_on_edit: bool = False
    static_value: str | None = None

    def label(self, editing: bool) -> str:
        return self.edit_label if editing and self.edit_label is not None else self.create_label


@dataclass(frozen=True)
class DialogSection:
    title: str
    fields: tuple[DialogField, ...]


class _BaseFormDialog(QDialog):
    """Compact RTL customer form dialog with deterministic layout."""

    submitted = Signal(dict, object)

    def __init__(self, title: str, description: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("task20Dialog")
        self.setWindowTitle(title)
        self.setAccessibleName(title)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumWidth(700)
        self.setMaximumWidth(840)
        self._previous_focus = parent.focusWidget() if parent else None

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(20, 18, 20, 18)
        self.root.setSpacing(SPACE_2)

        self.heading_label = QLabel(title)
        self.heading_label.setObjectName("screenTitle")
        self.heading_label.setProperty("dialogHeading", True)
        self.heading_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.heading_label.setAlignment(_ALIGN_RIGHT)
        self.root.addWidget(self.heading_label)

        self.heading_description = QLabel(description)
        self.heading_description.setProperty("dialogLead", True)
        self.heading_description.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.heading_description.setAlignment(_ALIGN_RIGHT)
        self.heading_description.setWordWrap(True)
        self.root.addWidget(self.heading_description)

        self.required_hint = QLabel("* שדה חובה")
        self.required_hint.setProperty("dialogHint", True)
        self.required_hint.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.required_hint.setAlignment(_ALIGN_RIGHT)
        self.root.addWidget(self.required_hint)

        self.body = QWidget()
        self.body.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, SPACE_1, 0, SPACE_1)
        self.body_layout.setSpacing(SPACE_3)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("dialogScrollArea")
        self.scroll.setAccessibleName("שדות הטופס")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.scroll.setWidget(self.body)
        self.root.addWidget(self.scroll, 1)

        self.error_label = FeedbackBanner()
        self.error_label.setObjectName("errorLabel")
        self.error_label.hide()
        self.root.addWidget(self.error_label)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.setObjectName("dialogButtonBox")
        self.buttons.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.save_button = self.buttons.button(QDialogButtonBox.StandardButton.Save)
        self.save_button.setObjectName("customerDialogPrimary")
        self.save_button.setText("שמירה")
        self.save_button.setDefault(True)
        self.cancel_button = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        self.cancel_button.setObjectName("customerDialogCancel")
        self.cancel_button.setText("ביטול")
        for button in (self.save_button, self.cancel_button):
            button.setMinimumWidth(140)
            button.setMinimumHeight(CONTROL_HEIGHT_LARGE)
        self._apply_button_styles()
        self.buttons.accepted.connect(self._submit)
        self.buttons.rejected.connect(self.reject)
        self.root.addWidget(self.buttons, alignment=Qt.AlignmentFlag.AlignLeft)

        self.fields: dict[str, QWidget] = {}
        self.field_errors: dict[str, QLabel] = {}
        self.section_forms: dict[str, QGridLayout] = {}
        self._validator: Callable[[dict], dict[str, str]] | None = None
        self._validation_attempted = False
        self._tab_order: list[QWidget] = []

    def _apply_button_styles(self) -> None:
        self.save_button.setStyleSheet(
            f"""
            QPushButton {{
                color: #FFFFFF;
                background: {COLOR_BRAND};
                border: 1px solid {COLOR_BRAND};
                border-radius: 8px;
                padding: 0 18px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                color: #FFFFFF;
                background: {COLOR_BRAND_HOVER};
                border-color: {COLOR_BRAND_HOVER};
            }}
            QPushButton:pressed {{
                color: #FFFFFF;
                background: {COLOR_BRAND_PRESSED};
                border-color: {COLOR_BRAND_PRESSED};
            }}
            QPushButton:disabled {{
                color: {COLOR_DISABLED_TEXT};
                background: {COLOR_DISABLED_BACKGROUND};
                border-color: {COLOR_BORDER};
            }}
            """
        )
        self.cancel_button.setStyleSheet(
            f"""
            QPushButton {{
                color: {COLOR_TEXT};
                background: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                padding: 0 18px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                color: {COLOR_TEXT};
                background: {COLOR_SURFACE_ALT};
                border-color: {COLOR_BRAND};
            }}
            QPushButton:pressed {{
                color: {COLOR_TEXT};
                background: {COLOR_BACKGROUND};
            }}
            """
        )

    @staticmethod
    def _section_label(title: str) -> QLabel:
        label = QLabel(title)
        label.setObjectName("sectionTitle")
        label.setProperty("dialogSectionTitle", True)
        label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        label.setAlignment(_ALIGN_RIGHT)
        return label

    def _create_field_widget(self, spec: DialogField, initial: dict, editing: bool) -> QWidget:
        value = str(initial.get(spec.key) or "")
        if spec.kind == "plain":
            widget = QPlainTextEdit(value)
            widget.setMinimumHeight(120)
            widget.setMaximumHeight(140)
            widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        elif spec.kind == "static":
            widget = QLabel(spec.static_value or value)
            widget.setProperty("dialogStaticValue", True)
            widget.setAlignment(_ALIGN_RIGHT)
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        else:
            widget = QLineEdit(value)
            widget.setMinimumHeight(CONTROL_HEIGHT_LARGE)
            widget.setMinimumWidth(320)
            widget.setMaximumWidth(9999)
            if spec.kind == "password":
                widget.setEchoMode(QLineEdit.EchoMode.Password)
            if editing and spec.read_only_on_edit:
                widget.setReadOnly(True)
                widget.setAccessibleDescription("שדה זה הוא מזהה כניסה קבוע ואינו ניתן לעריכה")

        widget.setAccessibleName(spec.label(editing).replace(" *", ""))
        if spec.mixed_direction:
            configure_mixed_direction(widget)
            if isinstance(widget, QLineEdit):
                widget.setAlignment(_ALIGN_RIGHT)
        else:
            widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            if isinstance(widget, QLineEdit):
                widget.setAlignment(_ALIGN_RIGHT)
        return widget

    def _build_sections(self, sections: tuple[DialogSection, ...], initial: dict, editing: bool) -> None:
        ordered_fields: list[QWidget] = []
        for section in sections:
            visible_specs = tuple(field for field in section.fields if not (editing and field.create_only))
            if not visible_specs:
                continue

            section_frame = QFrame()
            section_frame.setProperty("dialogSection", True)
            section_layout = QVBoxLayout(section_frame)
            section_layout.setContentsMargins(18, 14, 18, 16)
            section_layout.setSpacing(SPACE_2)
            section_layout.addWidget(self._section_label(section.title))

            # Keep this host physically LTR: column 0 is always the field on
            # the left, and column 1 is always the Hebrew label on the right.
            # The widgets themselves keep their own RTL/LTR text direction.
            grid_host = QWidget()
            grid_host.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            grid = QGridLayout(grid_host)
            grid.setOriginCorner(Qt.Corner.TopLeftCorner)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setHorizontalSpacing(18)
            grid.setVerticalSpacing(12)
            grid.setColumnStretch(0, 1)
            grid.setColumnStretch(1, 0)
            grid.setColumnMinimumWidth(1, 150)
            self.section_forms[section.title] = grid

            row = 0
            for spec in visible_specs:
                widget = self._create_field_widget(spec, initial, editing)
                self.fields[spec.key] = widget

                label_widget = QLabel(spec.label(editing))
                label_widget.setProperty("dialogFieldLabel", True)
                label_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                label_widget.setAlignment(_ALIGN_RIGHT)
                label_widget.setFixedWidth(150)

                field_column = QWidget()
                field_column.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
                field_layout = QVBoxLayout(field_column)
                field_layout.setContentsMargins(0, 0, 0, 0)
                field_layout.setSpacing(4)
                field_layout.addWidget(widget)

                error = QLabel()
                error.setObjectName("fieldError")
                error.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                error.setAlignment(_ALIGN_RIGHT)
                error.setWordWrap(True)
                error.hide()
                field_layout.addWidget(error)
                self.field_errors[spec.key] = error

                grid.addWidget(field_column, row, 0)
                grid.addWidget(label_widget, row, 1, alignment=_ALIGN_RIGHT)

                if isinstance(widget, QLineEdit):
                    widget.textChanged.connect(lambda _text, key=spec.key: self._field_changed(key))
                elif isinstance(widget, QPlainTextEdit):
                    widget.textChanged.connect(lambda key=spec.key: self._field_changed(key))
                ordered_fields.append(widget)
                row += 1

            section_layout.addWidget(grid_host)
            self.body_layout.addWidget(section_frame)

        self._tab_order = ordered_fields

    def _finalize_layout(self) -> None:
        screen = self.screen() or QApplication.primaryScreen()
        available = screen.availableGeometry() if screen is not None else None
        available_width = available.width() if available is not None else 1280
        available_height = available.height() if available is not None else 800
        target_width = min(780, max(700, available_width - 160))
        target_height = min(760, max(580, available_height - 140))
        self.resize(target_width, target_height)

        order = [*self._tab_order, self.save_button, self.cancel_button]
        for first, second in zip(order, order[1:]):
            QWidget.setTabOrder(first, second)
        if self._tab_order:
            self._tab_order[0].setFocus()

    def _submit(self) -> None:
        if not self.save_button.isEnabled():
            return
        errors = self.validation_errors()
        if errors:
            self._validation_attempted = True
            self._apply_validation_errors(errors)
            self.error_label.render_temporary(
                RequestState(RequestPhase.VALIDATION_ERROR, "לא ניתן לשמור. יש לתקן את השדות המסומנים.", "dialog-validation")
            )
            first = next((self.fields[key] for key in self.fields if key in errors), None)
            if first is not None:
                first.setFocus()
            return
        self.clear_validation_errors()
        self.submitted.emit(self.values(), self)

    def validation_errors(self) -> dict[str, str]:
        return self._validator(self.values()) if self._validator is not None else {}

    def _field_changed(self, _key: str) -> None:
        if self._validation_attempted:
            self._apply_validation_errors(self.validation_errors())

    def _apply_validation_errors(self, errors: dict[str, str]) -> None:
        for key, widget in self.fields.items():
            message = errors.get(key, "")
            widget.setProperty("invalid", bool(message))
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            label = self.field_errors.get(key)
            if label is not None:
                label.setText(message)
                label.setVisible(bool(message))

    def clear_validation_errors(self) -> None:
        self._validation_attempted = False
        self._apply_validation_errors({})

    def values(self) -> dict:
        values = {}
        for key, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                values[key] = widget.text()
            elif isinstance(widget, QPlainTextEdit):
                values[key] = widget.toPlainText()
        return values

    def set_submitting(self, value: bool) -> None:
        self.save_button.setEnabled(not value)

    def show_error(self, message: str) -> None:
        self.error_label.render_temporary(RequestState(RequestPhase.VALIDATION_ERROR, message, "dialog-backend"))
        target = self.fields.get("email") or next(iter(self.fields.values()), None)
        if target is not None:
            target.setFocus()

    def close_success(self) -> None:
        self.clear_validation_errors()
        self.accept()

    def done(self, result: int) -> None:
        super().done(result)
        if self._previous_focus is not None and self._previous_focus.isEnabled():
            self._previous_focus.setFocus()


class EntityFormDialog(_BaseFormDialog):
    def __init__(self, *, title: str, description: str, sections: tuple[DialogSection, ...], initial: dict | None, validator: Callable[[dict, bool], dict[str, str]] | None = None, parent=None) -> None:
        self.editing = initial is not None
        super().__init__(title, description, parent)
        self._build_sections(sections, initial or {}, self.editing)
        self._validator = (lambda values: validator(values, self.editing)) if validator is not None else None
        self._finalize_layout()

    def show_error(self, message: str) -> None:
        for key in ("password", "password_confirmation"):
            widget = self.fields.get(key)
            if isinstance(widget, QLineEdit):
                widget.clear()
        super().show_error(message)
