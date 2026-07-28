from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog,QDialogButtonBox,QFormLayout,QLabel,QLineEdit,QPlainTextEdit,QVBoxLayout
class InstructorDialog(QDialog):
    submitted=Signal(dict,object)
    def __init__(self,initial=None,parent=None):
        super().__init__(parent);initial=initial or {};self.setWindowTitle("עריכת מדריך" if initial else "מדריך חדש");root=QVBoxLayout(self);form=QFormLayout();root.addLayout(form);self.fields={}
        for k,l in (("full_name","שם *"),("phone","טלפון"),("email","דוא״ל פרופיל"),("city","עיר")):self.fields[k]=QLineEdit(str(initial.get(k) or ""));form.addRow(l,self.fields[k])
        self.notes=QPlainTextEdit(str(initial.get("notes") or ""));form.addRow("הערות",self.notes);self.error=QLabel();self.error.hide();root.addWidget(self.error);self.buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel);self.buttons.accepted.connect(lambda:self.submitted.emit(self.values(),self));self.buttons.rejected.connect(self.reject);root.addWidget(self.buttons)
    def values(self):return {**{k:w.text() for k,w in self.fields.items()},"notes":self.notes.toPlainText()}
    def set_submitting(self,v):self.buttons.setEnabled(not v)
    def show_error(self,m):self.error.setText(m);self.error.show()
    def close_success(self):self.accept()
