from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QPlainTextEdit, QVBoxLayout


class _BaseFormDialog(QDialog):
    submitted = Signal(dict, object)
    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent); self.setWindowTitle(title); self.root = QVBoxLayout(self); self.form = QFormLayout(); self.root.addLayout(self.form); self.error_label = QLabel(); self.error_label.hide(); self.root.addWidget(self.error_label); self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel); self.buttons.accepted.connect(lambda: self.submitted.emit(self.values(), self)); self.buttons.rejected.connect(self.reject); self.root.addWidget(self.buttons)
    def values(self) -> dict: raise NotImplementedError
    def set_submitting(self, value: bool) -> None: self.buttons.setEnabled(not value)
    def show_error(self, message: str) -> None: self.error_label.setText(message); self.error_label.show()
    def close_success(self) -> None: self.accept()


class CustomerDialog(_BaseFormDialog):
    def __init__(self, initial=None, parent=None) -> None:
        super().__init__("עריכת לקוח" if initial else "לקוח חדש", parent); initial = initial or {}; self.fields = {}
        for key, label in (("name", "שם *"), ("customer_type", "סוג"), ("city", "עיר"), ("address", "כתובת"), ("phone", "טלפון"), ("email", "דוא״ל")):
            self.fields[key] = QLineEdit(str(initial.get(key) or "")); self.form.addRow(label, self.fields[key])
        self.notes = QPlainTextEdit(str(initial.get("notes") or "")); self.form.addRow("הערות", self.notes); self.active = QCheckBox("פעיל"); self.active.setChecked(bool(initial.get("is_active", True))); self.form.addRow(self.active)
    def values(self) -> dict:
        return {**{key: field.text() for key, field in self.fields.items()}, "notes": self.notes.toPlainText(), "is_active": self.active.isChecked()}


class ContactDialog(_BaseFormDialog):
    def __init__(self, initial=None, parent=None) -> None:
        super().__init__("עריכת איש קשר" if initial else "איש קשר חדש", parent); initial = initial or {}; self.fields = {}
        for key, label in (("full_name", "שם מלא *"), ("role_title", "תפקיד"), ("phone", "טלפון"), ("email", "דוא״ל")):
            self.fields[key] = QLineEdit(str(initial.get(key) or "")); self.form.addRow(label, self.fields[key])
        self.notes = QPlainTextEdit(str(initial.get("notes") or "")); self.form.addRow("הערות", self.notes); self.primary = QCheckBox("ראשי"); self.primary.setChecked(bool(initial.get("is_primary"))); self.form.addRow(self.primary); self.active = QCheckBox("פעיל"); self.active.setChecked(bool(initial.get("is_active", True))); self.form.addRow(self.active)
    def values(self) -> dict:
        return {**{key: field.text() for key, field in self.fields.items()}, "notes": self.notes.toPlainText(), "is_primary": self.primary.isChecked(), "is_active": self.active.isChecked()}
