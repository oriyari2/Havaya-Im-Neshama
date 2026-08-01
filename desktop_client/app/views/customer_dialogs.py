from __future__ import annotations

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
    DIALOG_WIDTH_DEFAULT,
    DIALOG_WIDTH_MAX,
    SPACE_2,
    SPACE_3,
)
from desktop_client.app.views.ui_foundations import configure_mixed_direction


class _BaseFormDialog(QDialog):
    submitted = Signal(dict, object)

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("task20Dialog")
        self.setWindowTitle(title)
        self.setAccessibleName(title)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumWidth(DIALOG_WIDTH_DEFAULT)
        self.setMaximumWidth(DIALOG_WIDTH_MAX)
        self._previous_focus = parent.focusWidget() if parent else None
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(DIALOG_PADDING, DIALOG_PADDING, DIALOG_PADDING, DIALOG_PADDING)
        self.root.setSpacing(DIALOG_SECTION_GAP)
        body = QWidget()
        body.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.body_layout = QVBoxLayout(body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.form = QFormLayout()
        self.form.setVerticalSpacing(DIALOG_ROW_GAP)
        self.body_layout.addLayout(self.form)
        self.scroll = QScrollArea()
        self.scroll.setAccessibleName("שדות הטופס")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setWidget(body)
        self.root.addWidget(self.scroll, 1)
        self.error_label = QLabel()
        self.error_label.setObjectName("errorLabel")
        self.error_label.setAccessibleName("שגיאת אימות")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        self.root.addWidget(self.error_label)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.buttons.setAccessibleName("פעולות הטופס")
        self.save_button = self.buttons.button(QDialogButtonBox.StandardButton.Save)
        self.save_button.setText("שמירה")
        self.save_button.setProperty("primary", True)
        self.save_button.setDefault(True)
        self.cancel_button = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        self.cancel_button.setText("ביטול")
        self.buttons.accepted.connect(self._submit)
        self.buttons.rejected.connect(self.reject)
        self.root.addWidget(self.buttons)

    def _submit(self) -> None:
        if self.buttons.isEnabled():
            self.submitted.emit(self.values(), self)

    def values(self) -> dict:
        raise NotImplementedError

    def set_submitting(self, value: bool) -> None:
        self.buttons.setEnabled(not value)

    def show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.setAccessibleDescription(message)
        self.error_label.show()
        target = self.fields.get("email") if "דוא״ל" in message else next(iter(self.fields.values()))
        target.setAccessibleDescription(message)
        target.setFocus()

    def close_success(self) -> None:
        self.accept()

    def done(self, result: int) -> None:
        super().done(result)
        if self._previous_focus is not None and self._previous_focus.isEnabled():
            self._previous_focus.setFocus()


class CustomerDialog(_BaseFormDialog):
    def __init__(self, initial=None, parent=None) -> None:
        super().__init__("עריכת לקוח" if initial else "לקוח חדש", parent)
        initial = initial or {}
        self.setMinimumSize(760, 600)
        self.setMaximumWidth(860)
        self.resize(820, 650)
        self.root.setSpacing(SPACE_3)

        heading = QWidget()
        heading.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        heading_layout = QVBoxLayout(heading)
        heading_layout.setContentsMargins(0, 0, 0, 0)
        heading_layout.setSpacing(SPACE_2)
        self.heading_label = QLabel(self.windowTitle())
        self.heading_label.setObjectName("screenTitle")
        self.heading_label.setAccessibleName(self.windowTitle())
        self.heading_description = QLabel("פרטי הלקוח ופרטי איש הקשר")
        self.required_hint = QLabel("* שדה חובה")
        for label in (self.heading_label, self.heading_description, self.required_hint):
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.required_hint.setAccessibleName("סימון שדות חובה")
        for label in (self.heading_label, self.heading_description, self.required_hint):
            row = QWidget()
            row.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addStretch()
            row_layout.addWidget(label)
            heading_layout.addWidget(row)
        self.root.insertWidget(0, heading)

        self.body_layout.removeItem(self.form)
        self.body_layout.setSpacing(DIALOG_SECTION_GAP)
        self.body_layout.addWidget(self._section_label("פרטי לקוח"))
        self._configure_form(self.form)
        self.body_layout.addLayout(self.form)
        self.body_layout.addWidget(self._section_label("פרטי איש קשר"))
        self.contact_form = QFormLayout()
        self._configure_form(self.contact_form)
        self.body_layout.addLayout(self.contact_form)
        self.body_layout.addWidget(self._section_label("הערות"))

        self.fields = {}
        for key, label in (
            ("name", "שם *"),
            ("customer_type", "סוג"),
            ("city", "עיר"),
            ("address", "כתובת"),
            ("phone", "טלפון"),
            ("email", "דוא״ל"),
        ):
            self._add_field(self.form, key, label, initial)
        for key, label in (
            ("contact_name", "איש קשר *"),
            ("contact_phone", "טלפון איש קשר *"),
        ):
            self._add_field(self.contact_form, key, label, initial)
        for key in ("phone", "email", "contact_phone"):
            configure_mixed_direction(self.fields[key])
        self.notes = QPlainTextEdit(str(initial.get("notes") or ""))
        self.notes.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.notes.setAccessibleName("הערות")
        self.notes.setMinimumHeight(132)
        self.body_layout.addWidget(self.notes)
        self.save_button.setObjectName("customerDialogPrimary")
        self.save_button.setText("שמירת שינויים" if initial else "יצירת לקוח")
        self.save_button.style().unpolish(self.save_button)
        self.save_button.style().polish(self.save_button)
        for button in (self.save_button, self.cancel_button):
            button.setMinimumWidth(120)
            button.setMinimumHeight(CONTROL_HEIGHT_LARGE)
        self.fields["name"].setFocus()
        order = list(self.fields.values()) + [self.notes, self.save_button, self.cancel_button]
        for first, second in zip(order, order[1:]):
            QWidget.setTabOrder(first, second)

    @staticmethod
    def _section_label(title: str) -> QLabel:
        label = QLabel(title)
        label.setObjectName("sectionTitle")
        label.setAccessibleName(title)
        return label

    @staticmethod
    def _configure_form(form: QFormLayout) -> None:
        form.setContentsMargins(0, 0, 0, 0)
        form.setVerticalSpacing(DIALOG_ROW_GAP)
        form.setHorizontalSpacing(SPACE_3)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

    def _add_field(self, form: QFormLayout, key: str, label: str, initial: dict) -> None:
        field = QLineEdit(str(initial.get(key) or ""))
        field.setAccessibleName(label.replace(" *", ""))
        field.setMinimumWidth(240)
        self.fields[key] = field
        form.addRow(label, field)

    def values(self) -> dict:
        return {
            **{key: field.text() for key, field in self.fields.items()},
            "notes": self.notes.toPlainText(),
        }
