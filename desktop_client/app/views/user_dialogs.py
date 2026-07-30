from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QLabel, QLineEdit, QWidget

from desktop_client.app.views.customer_dialogs import _BaseFormDialog
from desktop_client.app.views.ui_foundations import configure_mixed_direction


ROLE_LABELS = {"manager": "מנהל", "customer": "לקוח", "instructor": "מדריך"}
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class StableRoleComboBox(QComboBox):
    def wheelEvent(self, event) -> None:
        event.ignore()


class CreateUserDialog(_BaseFormDialog):
    def __init__(self, parent=None) -> None:
        super().__init__("משתמש חדש", parent)
        self.fields = {}
        self.email = QLineEdit(); self.email.setAccessibleName("אימייל להתחברות"); configure_mixed_direction(self.email); self.form.addRow("אימייל להתחברות *", self.email); self.fields["email"] = self.email
        self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.EchoMode.Password); self.password.setAccessibleName("סיסמה"); configure_mixed_direction(self.password); self.form.addRow("סיסמה *", self.password); self.fields["password"] = self.password
        self.confirmation = QLineEdit(); self.confirmation.setEchoMode(QLineEdit.EchoMode.Password); self.confirmation.setAccessibleName("אימות סיסמה"); configure_mixed_direction(self.confirmation); self.form.addRow("אימות סיסמה *", self.confirmation); self.fields["password_confirmation"] = self.confirmation
        self.role = StableRoleComboBox(); self.role.setAccessibleName("תפקיד"); self.role.addItem("בחר תפקיד", "")
        for value in ("manager", "customer", "instructor"): self.role.addItem(ROLE_LABELS[value], value)
        self.form.addRow("תפקיד *", self.role)
        self.manager_name = QLineEdit(); self.manager_name.setAccessibleName("שם מנהל"); self.form.addRow("שם *", self.manager_name); self.fields["manager_name"] = self.manager_name
        self.customer_name = QLineEdit(); self.customer_name.setAccessibleName("שם לקוח"); self.form.addRow("שם לקוח *", self.customer_name); self.fields["customer_name"] = self.customer_name
        self.customer_type = QLineEdit(); self.customer_type.setAccessibleName("סוג לקוח"); self.form.addRow("סוג לקוח *", self.customer_type); self.fields["customer_type"] = self.customer_type
        self.customer_city = QLineEdit(); self.customer_city.setAccessibleName("עיר לקוח"); self.form.addRow("עיר *", self.customer_city); self.fields["customer_city"] = self.customer_city
        self.contact_name = QLineEdit(); self.contact_name.setAccessibleName("שם איש קשר"); self.form.addRow("שם איש קשר *", self.contact_name); self.fields["contact_name"] = self.contact_name
        self.contact_phone = QLineEdit(); self.contact_phone.setAccessibleName("טלפון איש קשר"); configure_mixed_direction(self.contact_phone); self.form.addRow("טלפון איש קשר *", self.contact_phone); self.fields["contact_phone"] = self.contact_phone
        self.instructor_name = QLineEdit(); self.instructor_name.setAccessibleName("שם מדריך"); self.form.addRow("שם מדריך *", self.instructor_name); self.fields["instructor_name"] = self.instructor_name
        self.instructor_phone = QLineEdit(); self.instructor_phone.setAccessibleName("טלפון מדריך"); configure_mixed_direction(self.instructor_phone); self.form.addRow("טלפון מדריך", self.instructor_phone); self.fields["instructor_phone"] = self.instructor_phone
        self.instructor_city = QLineEdit(); self.instructor_city.setAccessibleName("עיר מדריך"); self.form.addRow("עיר *", self.instructor_city); self.fields["instructor_city"] = self.instructor_city
        self.role.currentIndexChanged.connect(self._role_changed)
        for field in self.fields.values(): field.textChanged.connect(self._update_save_enabled)
        self._role_changed(); self.email.setFocus()
        order = [self.email, self.password, self.confirmation, self.role, self.manager_name, self.customer_name, self.customer_type, self.customer_city, self.contact_name, self.contact_phone, self.instructor_name, self.instructor_phone, self.instructor_city, self.save_button, self.cancel_button]
        for first, second in zip(order, order[1:]): QWidget.setTabOrder(first, second)

    def _role_changed(self) -> None:
        role = self.role.currentData()
        customer = role == "customer"; instructor = role == "instructor"
        manager = role == "manager"; self.form.labelForField(self.manager_name).setVisible(manager); self.manager_name.setVisible(manager)
        if not manager: self.manager_name.clear()
        for widget in (self.customer_name, self.customer_type, self.customer_city, self.contact_name, self.contact_phone):
            self.form.labelForField(widget).setVisible(customer); widget.setVisible(customer)
            if not customer: widget.clear()
        for widget in (self.instructor_name, self.instructor_phone, self.instructor_city):
            self.form.labelForField(widget).setVisible(instructor); widget.setVisible(instructor)
            if not instructor: widget.clear()
        self._update_save_enabled()

    def _update_save_enabled(self) -> None:
        role = self.role.currentData()
        email = self.email.text().strip().lower()
        password = self.password.text()
        common_valid = bool(role) and len(email) <= 254 and bool(EMAIL.match(email))
        common_valid = common_valid and 8 <= len(password) <= 128 and password == password.strip()
        common_valid = common_valid and all(character.isprintable() for character in password)
        common_valid = common_valid and password == self.confirmation.text()
        role_valid = role == "manager" and bool(self.manager_name.text().strip())
        role_valid = role_valid or role == "customer" and all(field.text().strip() for field in (self.customer_name, self.customer_type, self.customer_city, self.contact_name, self.contact_phone))
        role_valid = role_valid or role == "instructor" and all(field.text().strip() for field in (self.instructor_name, self.instructor_city))
        self.save_button.setEnabled(bool(common_valid and role_valid))

    def values(self) -> dict:
        return {
            "email": self.email.text(), "password": self.password.text(),
            "password_confirmation": self.confirmation.text(), "role": self.role.currentData(),
            "manager_name": self.manager_name.text(),
            "customer_name": self.customer_name.text(), "customer_type": self.customer_type.text(),
            "customer_city": self.customer_city.text(), "contact_name": self.contact_name.text(),
            "contact_phone": self.contact_phone.text(), "instructor_name": self.instructor_name.text(),
            "instructor_phone": self.instructor_phone.text(), "instructor_city": self.instructor_city.text(),
        }

    def show_error(self, message: str) -> None:
        self.password.clear(); self.confirmation.clear(); super().show_error(message)

    def set_submitting(self, value: bool) -> None:
        super().set_submitting(value)
        if not value:
            self._update_save_enabled()


class EditUserDialog(_BaseFormDialog):
    def __init__(self, user: dict, parent=None) -> None:
        super().__init__("עריכת משתמש", parent); self.fields = {}
        self.email = QLineEdit(str(user["email"])); self.email.setAccessibleName("דוא״ל"); configure_mixed_direction(self.email); self.form.addRow("דוא״ל *", self.email); self.fields["email"] = self.email
        self.role = QLabel(ROLE_LABELS.get(str(user["role"]), str(user["role"]))); self.role.setAccessibleName("תפקיד לקריאה בלבד"); self.form.addRow("תפקיד", self.role)
        name = user.get("display_name") or user.get("customer_name") or user.get("instructor_name") or "מנהל"
        self.profile = QLabel(str(name)); self.profile.setAccessibleName("שם לקריאה בלבד"); self.form.addRow("שם", self.profile); self.email.setFocus()

    def values(self) -> dict: return {"email": self.email.text()}


class ResetPasswordDialog(_BaseFormDialog):
    def __init__(self, user: dict, parent=None) -> None:
        super().__init__("איפוס סיסמה", parent); self.fields = {}
        target = QLabel(str(user["email"])); configure_mixed_direction(target); target.setAccessibleName("משתמש יעד"); self.form.addRow("משתמש", target)
        self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.EchoMode.Password); self.password.setAccessibleName("סיסמה חדשה"); configure_mixed_direction(self.password); self.form.addRow("סיסמה חדשה *", self.password); self.fields["password"] = self.password
        self.confirmation = QLineEdit(); self.confirmation.setEchoMode(QLineEdit.EchoMode.Password); self.confirmation.setAccessibleName("אימות סיסמה חדשה"); configure_mixed_direction(self.confirmation); self.form.addRow("אימות סיסמה *", self.confirmation); self.fields["password_confirmation"] = self.confirmation; self.password.setFocus()

    def values(self) -> dict: return {"password": self.password.text(), "password_confirmation": self.confirmation.text()}
    def show_error(self, message: str) -> None: self.password.clear(); self.confirmation.clear(); super().show_error(message)
