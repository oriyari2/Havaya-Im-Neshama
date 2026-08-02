from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from desktop_client.app.views.design_tokens import (
    CONTROL_HEIGHT_LARGE,
    DIALOG_PADDING,
    DIALOG_ROW_GAP,
    DIALOG_SECTION_GAP,
    SPACE_2,
    SPACE_3,
)
from desktop_client.app.views.ui_foundations import configure_mixed_direction


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
    """Single layout implementation for every management form dialog."""

    submitted = Signal(dict, object)

    def __init__(self, title: str, description: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("task20Dialog")
        self.setWindowTitle(title)
        self.setAccessibleName(title)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumWidth(760)
        self.setMaximumWidth(860)
        self._previous_focus = parent.focusWidget() if parent else None
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(DIALOG_PADDING, DIALOG_PADDING, DIALOG_PADDING, DIALOG_PADDING)
        self.root.setSpacing(SPACE_3)

        self.heading_label = QLabel(title)
        self.heading_label.setObjectName("screenTitle")
        self.heading_description = QLabel(description)
        self.required_hint = QLabel("* שדה חובה")
        for label in (self.heading_label, self.heading_description, self.required_hint):
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            self.root.addWidget(label, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute)
        self.required_hint.setAccessibleName("סימון שדות חובה")

        self.body = QWidget()
        self.body.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(DIALOG_SECTION_GAP)
        self.scroll = QScrollArea()
        self.scroll.setAccessibleName("שדות הטופס")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setWidget(self.body)
        self.root.addWidget(self.scroll)

        self.error_label = QLabel()
        self.error_label.setObjectName("errorLabel")
        self.error_label.setAccessibleName("שגיאת אימות")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        self.root.addWidget(self.error_label)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.save_button = self.buttons.button(QDialogButtonBox.StandardButton.Save)
        self.save_button.setText("שמירה")
        self.save_button.setProperty("primary", True)
        self.save_button.setDefault(True)
        self.cancel_button = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        self.cancel_button.setText("ביטול")
        for button in (self.save_button, self.cancel_button):
            button.setMinimumWidth(120)
            button.setMinimumHeight(CONTROL_HEIGHT_LARGE)
        self.buttons.accepted.connect(self._submit)
        self.buttons.rejected.connect(self.reject)
        self.root.addWidget(self.buttons)
        self.fields: dict[str, QWidget] = {}
        self.section_forms: dict[str, QFormLayout] = {}
        self.form: QFormLayout | None = None

    @staticmethod
    def _configure_form(form: QFormLayout) -> None:
        form.setContentsMargins(0, 0, 0, 0)
        form.setVerticalSpacing(DIALOG_ROW_GAP)
        form.setHorizontalSpacing(SPACE_3)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

    @staticmethod
    def _section_label(title: str) -> QLabel:
        label = QLabel(title)
        label.setObjectName("sectionTitle")
        label.setAccessibleName(title)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return label

    def _build_sections(self, sections: tuple[DialogSection, ...], initial: dict, editing: bool) -> None:
        ordered_fields: list[QWidget] = []
        for section in sections:
            visible_specs = tuple(field for field in section.fields if not (editing and field.create_only))
            if not visible_specs:
                continue
            self.body_layout.addWidget(self._section_label(section.title))
            if len(visible_specs) == 1 and visible_specs[0].kind == "plain":
                spec = visible_specs[0]
                widget = QPlainTextEdit(str(initial.get(spec.key) or ""))
                widget.setMinimumHeight(112)
                widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                widget.setAccessibleName(spec.label(editing))
                self.fields[spec.key] = widget
                ordered_fields.append(widget)
                self.body_layout.addWidget(widget)
                continue
            form = QFormLayout()
            self._configure_form(form)
            self.section_forms[section.title] = form
            if self.form is None:
                self.form = form
            for spec in visible_specs:
                if spec.kind == "plain":
                    widget = QPlainTextEdit(str(initial.get(spec.key) or ""))
                    widget.setMinimumHeight(112)
                    widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                elif spec.kind == "static":
                    widget = QLabel(spec.static_value or str(initial.get(spec.key) or ""))
                    widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    widget = QLineEdit(str(initial.get(spec.key) or ""))
                    widget.setMinimumWidth(240)
                    if spec.kind == "password":
                        widget.setEchoMode(QLineEdit.EchoMode.Password)
                    if editing and spec.read_only_on_edit:
                        widget.setReadOnly(True)
                        widget.setAccessibleDescription("שדה זה הוא מזהה כניסה קבוע ואינו ניתן לעריכה")
                widget.setAccessibleName(spec.label(editing).replace(" *", ""))
                if spec.mixed_direction:
                    configure_mixed_direction(widget)
                self.fields[spec.key] = widget
                form.addRow(spec.label(editing), widget)
                ordered_fields.append(widget)
            self.body_layout.addLayout(form)
        self._tab_order = ordered_fields

    def _finalize_layout(self) -> None:
        self.body_layout.activate()
        content_height = max(1, self.body.sizeHint().height())
        self.scroll.setFixedHeight(min(content_height, 480))
        self.adjustSize()
        self.resize(max(760, self.width()), self.sizeHint().height())
        order = [*self._tab_order, self.save_button, self.cancel_button]
        for first, second in zip(order, order[1:]):
            QWidget.setTabOrder(first, second)
        if self._tab_order:
            self._tab_order[0].setFocus()

    def _submit(self) -> None:
        if self.buttons.isEnabled():
            self.submitted.emit(self.values(), self)

    def values(self) -> dict:
        values = {}
        for key, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                values[key] = widget.text()
            elif isinstance(widget, QPlainTextEdit):
                values[key] = widget.toPlainText()
        return values

    def set_submitting(self, value: bool) -> None:
        self.buttons.setEnabled(not value)

    def show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.setAccessibleDescription(message)
        self.error_label.show()
        target = self.fields.get("email") or next(iter(self.fields.values()))
        target.setAccessibleDescription(message)
        target.setFocus()

    def close_success(self) -> None:
        self.accept()

    def done(self, result: int) -> None:
        super().done(result)
        if self._previous_focus is not None and self._previous_focus.isEnabled():
            self._previous_focus.setFocus()


class EntityFormDialog(_BaseFormDialog):
    def __init__(self, *, title: str, description: str, sections: tuple[DialogSection, ...], initial: dict | None, parent=None) -> None:
        self.editing = initial is not None
        super().__init__(title, description, parent)
        self._build_sections(sections, initial or {}, self.editing)
        self._finalize_layout()

    def show_error(self, message: str) -> None:
        for key in ("password", "password_confirmation"):
            widget = self.fields.get(key)
            if isinstance(widget, QLineEdit):
                widget.clear()
        super().show_error(message)


CUSTOMER_SECTIONS = (
    DialogSection("פרטי לקוח", (
        DialogField("name", "שם *"),
        DialogField("customer_type", "סוג"),
        DialogField("city", "עיר"),
        DialogField("address", "כתובת"),
        DialogField("phone", "טלפון", mixed_direction=True),
        DialogField("email", "דוא״ל להתחברות *", "דוא״ל", mixed_direction=True, read_only_on_edit=True),
        DialogField("password", "סיסמה *", kind="password", mixed_direction=True, create_only=True),
        DialogField("password_confirmation", "אימות סיסמה *", kind="password", mixed_direction=True, create_only=True),
    )),
    DialogSection("פרטי איש קשר", (
        DialogField("contact_name", "איש קשר"),
        DialogField("contact_phone", "טלפון איש קשר", mixed_direction=True),
    )),
    DialogSection("הערות", (DialogField("notes", "הערות", kind="plain"),)),
)


class CustomerDialog(EntityFormDialog):
    def __init__(self, initial=None, parent=None) -> None:
        editing = initial is not None
        super().__init__(
            title="עריכת לקוח" if editing else "לקוח חדש",
            description="פרטי הלקוח ופרטי איש הקשר",
            sections=CUSTOMER_SECTIONS,
            initial=initial,
            parent=parent,
        )
        self.password = self.fields.get("password")
        self.password_confirmation = self.fields.get("password_confirmation")
        self.notes = self.fields["notes"]
        self.contact_form = self.section_forms["פרטי איש קשר"]
        self.save_button.setText("שמירת שינויים" if editing else "יצירת לקוח")
        self.save_button.setObjectName("customerDialogPrimary")
