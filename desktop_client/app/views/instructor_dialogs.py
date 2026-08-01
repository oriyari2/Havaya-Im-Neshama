from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QPlainTextEdit, QVBoxLayout

from desktop_client.app.views.ui_foundations import configure_mixed_direction


class InstructorDialog(QDialog):
    submitted = Signal(dict, object)

    def __init__(self, initial=None, parent=None):
        super().__init__(parent)
        initial = initial or {}
        self.is_create = not bool(initial)
        self.setWindowTitle("עריכת מדריך" if initial else "מדריך חדש")
        root = QVBoxLayout(self)
        self.form = QFormLayout()
        root.addLayout(self.form)
        self.fields = {}
        labels = (
            ("full_name", "שם *"),
            ("phone", "טלפון"),
            ("email", "אימייל להתחברות *" if self.is_create else "דוא״ל פרופיל"),
            ("city", "עיר"),
        )
        for key, label in labels:
            self.fields[key] = QLineEdit(str(initial.get(key) or ""))
            self.form.addRow(label, self.fields[key])
        configure_mixed_direction(self.fields["phone"])
        configure_mixed_direction(self.fields["email"])
        self.password = None
        self.password_confirmation = None
        if self.is_create:
            self.password = QLineEdit()
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            configure_mixed_direction(self.password)
            self.form.addRow("סיסמה *", self.password)
            self.password_confirmation = QLineEdit()
            self.password_confirmation.setEchoMode(QLineEdit.EchoMode.Password)
            configure_mixed_direction(self.password_confirmation)
            self.form.addRow("אימות סיסמה *", self.password_confirmation)
        self.notes = QPlainTextEdit(str(initial.get("notes") or ""))
        self.form.addRow("הערות", self.notes)
        self.error = QLabel()
        self.error.hide()
        root.addWidget(self.error)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(lambda: self.submitted.emit(self.values(), self))
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)

    def values(self):
        values = {**{key: widget.text() for key, widget in self.fields.items()}, "notes": self.notes.toPlainText()}
        if self.password is not None and self.password_confirmation is not None:
            values.update(password=self.password.text(), password_confirmation=self.password_confirmation.text())
        return values

    def set_submitting(self, value):
        self.buttons.setEnabled(not value)

    def show_error(self, message):
        if self.password is not None and self.password_confirmation is not None:
            self.password.clear()
            self.password_confirmation.clear()
        self.error.setText(message)
        self.error.show()

    def close_success(self):
        self.accept()
