from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QLabel, QLineEdit, QWidget

from desktop_client.app.views.customer_dialogs import _BaseFormDialog
from desktop_client.app.views.ui_foundations import configure_mixed_direction


ROLE_LABELS = {"manager": "מנהל", "customer": "לקוח", "instructor": "מדריך"}


class CreateUserDialog(_BaseFormDialog):
    def __init__(self, customers: list[dict], instructors: list[dict], parent=None) -> None:
        super().__init__("משתמש חדש", parent)
        self.fields = {}
        self.email = QLineEdit(); self.email.setAccessibleName("דוא״ל"); configure_mixed_direction(self.email); self.form.addRow("דוא״ל *", self.email); self.fields["email"] = self.email
        self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.EchoMode.Password); self.password.setAccessibleName("סיסמה"); configure_mixed_direction(self.password); self.form.addRow("סיסמה *", self.password); self.fields["password"] = self.password
        self.confirmation = QLineEdit(); self.confirmation.setEchoMode(QLineEdit.EchoMode.Password); self.confirmation.setAccessibleName("אימות סיסמה"); configure_mixed_direction(self.confirmation); self.form.addRow("אימות סיסמה *", self.confirmation); self.fields["password_confirmation"] = self.confirmation
        self.role = QComboBox(); self.role.setAccessibleName("תפקיד"); self.role.addItem("בחרו תפקיד", "")
        for value in ("manager", "customer", "instructor"): self.role.addItem(ROLE_LABELS[value], value)
        self.form.addRow("תפקיד *", self.role)
        self.customer = QComboBox(); self.customer.setAccessibleName("פרופיל לקוח"); self.customer.addItem("בחרו לקוח", None)
        for item in customers: self.customer.addItem(str(item["name"]), str(item["id"]))
        self.customer_label = QLabel("פרופיל לקוח *"); self.form.addRow(self.customer_label, self.customer)
        self.instructor = QComboBox(); self.instructor.setAccessibleName("פרופיל מדריך"); self.instructor.addItem("בחרו מדריך", None)
        for item in instructors: self.instructor.addItem(str(item["full_name"]), str(item["id"]))
        self.instructor_label = QLabel("פרופיל מדריך *"); self.form.addRow(self.instructor_label, self.instructor)
        self.role.currentIndexChanged.connect(self._role_changed); self._role_changed(); self.email.setFocus()
        order = [self.email, self.password, self.confirmation, self.role, self.customer, self.instructor, self.save_button, self.cancel_button]
        for first, second in zip(order, order[1:]): QWidget.setTabOrder(first, second)

    def _role_changed(self) -> None:
        role = self.role.currentData()
        customer = role == "customer"; instructor = role == "instructor"
        self.customer_label.setVisible(customer); self.customer.setVisible(customer)
        self.instructor_label.setVisible(instructor); self.instructor.setVisible(instructor)
        if not customer: self.customer.setCurrentIndex(0)
        if not instructor: self.instructor.setCurrentIndex(0)

    def values(self) -> dict:
        return {"email": self.email.text(), "password": self.password.text(), "password_confirmation": self.confirmation.text(), "role": self.role.currentData(), "customer_id": self.customer.currentData(), "instructor_id": self.instructor.currentData()}

    def show_error(self, message: str) -> None:
        self.password.clear(); self.confirmation.clear(); super().show_error(message)


class EditUserDialog(_BaseFormDialog):
    def __init__(self, user: dict, parent=None) -> None:
        super().__init__("עריכת משתמש", parent); self.fields = {}
        self.email = QLineEdit(str(user["email"])); self.email.setAccessibleName("דוא״ל"); configure_mixed_direction(self.email); self.form.addRow("דוא״ל *", self.email); self.fields["email"] = self.email
        self.role = QLabel(ROLE_LABELS.get(str(user["role"]), str(user["role"]))); self.role.setAccessibleName("תפקיד לקריאה בלבד"); self.form.addRow("תפקיד", self.role)
        profile = user.get("customer_name") or user.get("instructor_name") or "לא נדרש"
        self.profile = QLabel(str(profile)); self.profile.setAccessibleName("פרופיל מקושר לקריאה בלבד"); self.form.addRow("פרופיל מקושר", self.profile); self.email.setFocus()

    def values(self) -> dict: return {"email": self.email.text()}


class ResetPasswordDialog(_BaseFormDialog):
    def __init__(self, user: dict, parent=None) -> None:
        super().__init__("איפוס סיסמה", parent); self.fields = {}
        target = QLabel(str(user["email"])); configure_mixed_direction(target); target.setAccessibleName("משתמש יעד"); self.form.addRow("משתמש", target)
        self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.EchoMode.Password); self.password.setAccessibleName("סיסמה חדשה"); configure_mixed_direction(self.password); self.form.addRow("סיסמה חדשה *", self.password); self.fields["password"] = self.password
        self.confirmation = QLineEdit(); self.confirmation.setEchoMode(QLineEdit.EchoMode.Password); self.confirmation.setAccessibleName("אימות סיסמה חדשה"); configure_mixed_direction(self.confirmation); self.form.addRow("אימות סיסמה *", self.confirmation); self.fields["password_confirmation"] = self.confirmation; self.password.setFocus()

    def values(self) -> dict: return {"password": self.password.text(), "password_confirmation": self.confirmation.text()}
    def show_error(self, message: str) -> None: self.password.clear(); self.confirmation.clear(); super().show_error(message)
