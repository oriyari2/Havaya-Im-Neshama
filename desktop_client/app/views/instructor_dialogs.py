from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QPlainTextEdit, QWidget

from desktop_client.app.views.customer_dialogs import _BaseFormDialog
from desktop_client.app.views.ui_foundations import configure_mixed_direction


class InstructorDialog(_BaseFormDialog):
    def __init__(self,initial=None,parent=None):
        super().__init__("עריכת מדריך" if initial else "מדריך חדש",parent);initial=initial or {};self.is_create=not bool(initial);self.fields={};self.apply_entity_standard("פרטי המדריך וחשבון ההתחברות");self.body_layout.insertWidget(0,self._section_label("פרטי מדריך"))
        for key,label in (("full_name","שם *"),("email","דוא״ל התחברות *"),("phone","טלפון"),("city","עיר")):
            field=QLineEdit(str(initial.get(key) or ""));field.setAccessibleName(label.replace(" *",""));field.setMinimumWidth(240);self.fields[key]=field;self.form.addRow(label,field)
        configure_mixed_direction(self.fields["email"]);configure_mixed_direction(self.fields["phone"])
        if not self.is_create:self.fields["email"].setReadOnly(True);self.fields["email"].setAccessibleDescription("דוא״ל ההתחברות קבוע ואינו ניתן לעריכה")
        self.password=self.password_confirmation=None
        if self.is_create:
            self.password=QLineEdit();self.password.setEchoMode(QLineEdit.EchoMode.Password);configure_mixed_direction(self.password);self.form.addRow("סיסמה *",self.password)
            self.password_confirmation=QLineEdit();self.password_confirmation.setEchoMode(QLineEdit.EchoMode.Password);configure_mixed_direction(self.password_confirmation);self.form.addRow("אימות סיסמה *",self.password_confirmation)
        self.notes=QPlainTextEdit(str(initial.get("notes") or ""));self.notes.setLayoutDirection(Qt.LayoutDirection.RightToLeft);self.notes.setAccessibleName("הערות");self.notes.setMinimumHeight(132);self.body_layout.addWidget(self._section_label("הערות"));self.body_layout.addWidget(self.notes);self.save_button.setText("שמירת שינויים" if initial else "יצירת מדריך")
        self.fields["full_name"].setFocus()
        order=[*self.fields.values(),*[x for x in (self.password,self.password_confirmation) if x],self.notes,self.save_button,self.cancel_button]
        for first,second in zip(order,order[1:]):QWidget.setTabOrder(first,second)
    def values(self):
        values={**{key:field.text() for key,field in self.fields.items()},"notes":self.notes.toPlainText()}
        if self.password is not None:values.update(password=self.password.text(),password_confirmation=self.password_confirmation.text())
        return values
    def show_error(self,message):
        if self.password is not None:self.password.clear();self.password_confirmation.clear()
        super().show_error(message)
