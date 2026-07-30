from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from desktop_client.app.views.design_tokens import (
    DIALOG_PADDING,
    DIALOG_ROW_GAP,
    DIALOG_SECTION_GAP,
    DIALOG_WIDTH_DEFAULT,
    DIALOG_WIDTH_MAX,
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
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        self.form = QFormLayout()
        self.form.setVerticalSpacing(DIALOG_ROW_GAP)
        body_layout.addLayout(self.form)
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
        self.fields = {}
        for key, label in (
            ("name", "שם *"),
            ("customer_type", "סוג"),
            ("city", "עיר"),
            ("address", "כתובת"),
            ("phone", "טלפון"),
            ("email", "דוא״ל"),
            ("contact_name", "איש קשר *"),
            ("contact_phone", "טלפון איש קשר *"),
        ):
            field = QLineEdit(str(initial.get(key) or ""))
            field.setAccessibleName(label.replace(" *", ""))
            self.fields[key] = field
            self.form.addRow(label, field)
        for key in ("phone", "email", "contact_phone"):
            configure_mixed_direction(self.fields[key])
        self.notes = QPlainTextEdit(str(initial.get("notes") or ""))
        self.notes.setAccessibleName("הערות")
        self.form.addRow("הערות", self.notes)
        self.fields["name"].setFocus()
        order = list(self.fields.values()) + [self.notes, self.save_button, self.cancel_button]
        for first, second in zip(order, order[1:]):
            QWidget.setTabOrder(first, second)

    def values(self) -> dict:
        return {
            **{key: field.text() for key, field in self.fields.items()},
            "notes": self.notes.toPlainText(),
        }
