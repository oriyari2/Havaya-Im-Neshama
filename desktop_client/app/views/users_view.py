from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import QLabel, QTableWidgetItem, QVBoxLayout

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.views.common import StatefulWidget
from desktop_client.app.views.management_common import confirm_action
from desktop_client.app.views.management_workspace import ManagementWorkspace
from desktop_client.app.views.ui_foundations import ColumnKind, ColumnPolicy, configure_mixed_direction, set_disabled_explanation, set_item_text
from desktop_client.app.views.user_dialogs import CreateUserDialog, EditUserDialog, ResetPasswordDialog


class UsersView(StatefulWidget):
    filters_requested=Signal(dict);page_requested=Signal(int,int);user_selected=Signal(str);retry_requested=Signal();create_requested=Signal();edit_requested=Signal();activate_requested=Signal();deactivate_requested=Signal();reset_password_requested=Signal()
    def __init__(self):
        super().__init__();root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0)
        self.workspace=ManagementWorkspace(title="מנהלים",subtitle="ניהול חשבונות מנהלים",create_text="מנהל חדש",plural="מנהלים",search_placeholder="חיפוש לפי שם או דוא״ל",sort_options=(),headers=("שם מנהל","דוא״ל","מצב","עודכן"),policies=(ColumnPolicy(ColumnKind.PRIMARY_TEXT,180),ColumnPolicy(ColumnKind.TECHNICAL,220),ColumnPolicy(ColumnKind.COMPACT,110),ColumnPolicy(ColumnKind.TECHNICAL,150)))
        root.addWidget(self.workspace);self.scaffold=self.workspace.scaffold;self.toolbar=self.workspace.toolbar;self.table=self.workspace.table;self.footer=self.workspace.footer;self.create_button=self.workspace.create_button;self.pages=self.workspace.pages;self.list_page=self.workspace.list_page;self.details_page=self.workspace.details_page;self.back_button=self.workspace.back_button;self.view_details_button=self.workspace.view_details_button
        self.edit_button=self.workspace.add_action("עריכת מנהל");self.reset_button=self.workspace.add_action("שינוי סיסמה");self.activate_button=self.workspace.add_action("הפעלה");self.deactivate_button=self.workspace.add_action("מחיקת מנהל",destructive=True)
        self.account_details=self.workspace.add_card("פרטי מנהל");self.system_details=self.workspace.add_card("מידע מערכת")
        for button,signal in ((self.create_button,self.create_requested),(self.edit_button,self.edit_requested),(self.reset_button,self.reset_password_requested),(self.activate_button,self.activate_requested),(self.deactivate_button,self.deactivate_requested)):button.clicked.connect(signal);button.setAccessibleName(button.text())
        self.toolbar.search_requested.connect(lambda search,_sort:self.filters_requested.emit({"search":search or None}));self.toolbar.refresh_requested.connect(lambda:self.filters_requested.emit({"search":None,"is_active":None}));self.footer.page_requested.connect(self.page_requested);self.table.itemSelectionChanged.connect(self._select);self.table.cellDoubleClicked.connect(lambda _r,_c:self._open());self.table.installEventFilter(self);self.view_details_button.clicked.connect(self._open);self.clear_details()
    def eventFilter(self,watched,event):
        if watched is self.table and event.type()==QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter):self._open();return True
        return super().eventFilter(watched,event)
    def _select(self):
        rows=self.table.selectionModel().selectedRows()
        if rows:self.user_selected.emit(str(self.table.item(rows[0].row(),0).data(Qt.ItemDataRole.UserRole)));self.view_details_button.setEnabled(True)
    def _open(self):
        if self.workspace.detail_title.text():self.pages.setCurrentWidget(self.details_page)
    def show_users(self,rows,*,offset,count,filtered):
        rows=[u for u in rows if u.get("role")=="manager"];self.table.setRowCount(len(rows))
        for ri,user in enumerate(rows):
            values=(user.get("display_name") or "מנהל",user["email"],"פעיל" if user["is_active"] else "לא פעיל",str(user["updated_at"]))
            for ci,value in enumerate(values):
                item=QTableWidgetItem(str(value));set_item_text(self.table,ri,ci,item,tooltip_direction=Qt.LayoutDirection.LeftToRight if ci in {1,3} else Qt.LayoutDirection.RightToLeft);item.setTextAlignment((Qt.AlignmentFlag.AlignLeft if ci in {1,3} else Qt.AlignmentFlag.AlignRight)|Qt.AlignmentFlag.AlignVCenter)
                if ci==0:item.setData(Qt.ItemDataRole.UserRole,str(user["id"]))
        self.footer.set_page(offset=offset,count=len(rows));self.state_label.setVisible(not rows);self.state_label.setText("לא נמצאו מנהלים." if filtered else "אין מנהלים להצגה.")
    def show_details(self,user,*,current_user_id):
        self._clear_forms();name=user.get("display_name") or "מנהל";email=QLabel(str(user["email"]));configure_mixed_direction(email);self.account_details.addRow("שם",QLabel(name));self.account_details.addRow("דוא״ל התחברות",email)
        self.system_details.addRow("מצב חשבון",QLabel("פעיל" if user["is_active"] else "לא פעיל"));self.system_details.addRow("נוצר",QLabel(str(user["created_at"])));self.system_details.addRow("עודכן",QLabel(str(user["updated_at"])))
        self.workspace.show_detail_identity(name,bool(user["is_active"]));self.edit_button.setEnabled(True);self.reset_button.setEnabled(True);self.activate_button.setEnabled(not user["is_active"]);self.deactivate_button.setEnabled(bool(user["is_active"] and str(user["id"])!=current_user_id))
        set_disabled_explanation(self.deactivate_button,"לא ניתן למחוק את החשבון המחובר" if str(user["id"])==current_user_id else "המנהל כבר לא פעיל" if not user["is_active"] else "מחיקה לוגית באמצעות השבתת המנהל")
    def _clear_forms(self):
        for form in (self.account_details,self.system_details):
            while form.rowCount():form.removeRow(0)
    def clear_details(self):
        if hasattr(self,"account_details"):self._clear_forms();self.workspace.detail_title.clear();self.workspace.set_actions_enabled(False);self.pages.setCurrentWidget(self.list_page)
        self.view_details_button.setEnabled(False)
    def set_detail_loading(self,value):
        if value:self.workspace.set_actions_enabled(False)
    def set_loading(self,value):super().set_loading(value);self.create_button.setEnabled(not value);self.toolbar.search_button.setEnabled(not value);self.toolbar.refresh_button.setEnabled(not value)
    def show_error(self,message,*,retriable=False,permission=False):self.scaffold.feedback.render(RequestState(RequestPhase.AUTHORIZATION_ERROR if permission else RequestPhase.CONNECTION_ERROR if retriable else RequestPhase.SERVER_ERROR,message,"users",retryable=retriable))
    def show_success(self,message):self.scaffold.feedback.render(RequestState(RequestPhase.SUCCESS,message,"users"))
    def select_user(self,user_id):
        for row in range(self.table.rowCount()):
            if str(self.table.item(row,0).data(Qt.ItemDataRole.UserRole))==user_id:self.table.selectRow(row);break
    def open_create(self,submit):self._dialog=CreateUserDialog(self);self._dialog.submitted.connect(submit);self._dialog.open()
    def open_edit(self,user,submit):self._dialog=EditUserDialog(user,self);self._dialog.submitted.connect(submit);self._dialog.open()
    def open_reset_password(self,user,submit):self._dialog=ResetPasswordDialog(user,self);self._dialog.submitted.connect(submit);self._dialog.open()
    def confirm_deactivation(self,email):return confirm_action(self,"אישור מחיקת מנהל",f"למחוק לוגית את המנהל {email}? החשבון יושבת ולא יוכל להתחבר עד להפעלה מחדש.")
