from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QPlainTextEdit, QVBoxLayout


class ActivityDialog(QDialog):
    submitted = Signal(dict, object)
    def __init__(self, initial: dict | None = None, parent=None) -> None:
        super().__init__(parent); initial = initial or {}; self.setWindowTitle("עריכת פעילות" if initial else "פעילות חדשה"); root = QVBoxLayout(self); form = QFormLayout(); root.addLayout(form); self.lines = {}
        for key, label in (("name", "שם *"), ("target_audience", "קהל יעד"), ("duration_minutes", "משך בדקות"), ("recommended_capacity", "קיבולת מומלצת"), ("season", "עונה"), ("tags", "תגיות")):
            self.lines[key] = QLineEdit(str(initial.get(key) or "")); form.addRow(label, self.lines[key])
        self.texts = {}
        for key, label in (("description", "תיאור"), ("pricing_rule", "כלל תמחור"), ("required_equipment", "ציוד נדרש"), ("preparation_notes", "הערות הכנה")):
            self.texts[key] = QPlainTextEdit(str(initial.get(key) or "")); self.texts[key].setMaximumHeight(80); form.addRow(label, self.texts[key])
        self.active = QCheckBox("פעילה"); self.active.setChecked(bool(initial.get("is_active", True))); form.addRow(self.active); self.error_label = QLabel(); self.error_label.setObjectName("errorLabel"); self.error_label.hide(); root.addWidget(self.error_label); self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel); self.buttons.accepted.connect(lambda: self.submitted.emit(self.values(), self)); self.buttons.rejected.connect(self.reject); root.addWidget(self.buttons)
    def values(self) -> dict:
        return {**{k: w.text() for k, w in self.lines.items()}, **{k: w.toPlainText() for k, w in self.texts.items()}, "is_active": self.active.isChecked()}
    def set_submitting(self, value: bool) -> None: self.buttons.setEnabled(not value)
    def show_error(self, message: str) -> None: self.error_label.setText(message); self.error_label.show()
    def close_success(self) -> None: self.accept()
