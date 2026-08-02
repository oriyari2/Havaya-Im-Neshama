from __future__ import annotations

from PySide6.QtCore import QEvent, QItemSelectionModel, Qt, Signal
from PySide6.QtWidgets import QLabel, QTableWidgetItem, QVBoxLayout

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.views.common import StatefulWidget
from desktop_client.app.views.management_common import ActiveBadge, confirm_action
from desktop_client.app.views.management_workspace import ManagementWorkspace
from desktop_client.app.views.ui_foundations import ColumnKind, ColumnPolicy, configure_mixed_direction, set_disabled_explanation, set_item_text
from desktop_client.app.views.user_dialogs import CreateUserDialog, EditUserDialog, ResetPasswordDialog


class UsersView(StatefulWidget):
    filters_requested=Signal(dict);page_requested=Signal(int,int);user_selected=Signal(str);retry_requested=Signal();create_requested=Signal();edit_requested=Signal();activate_requested=Signal();deactivate_requested=Signal();reset_password_requested=Signal()
    def __init__(self):
        super().__init__();root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0)
        self.workspace=ManagementWorkspace(title="מנהלים",subtitle="ניהול חשבונות מנהלים",create_text="מנהל חדש",plural="מנהלים",detail_subtitle="מידע מלא ופעולות עבור המנהל שנבחר",search_placeholder="חיפוש לפי שם או דוא״ל",sort_options=(("display_name","מיון לפי: שם"),("created_at","מיון לפי: תאריך יצירה"),("is_active","מיון לפי: מצב")),headers=("שם מנהל","דוא״ל","מצב","עודכן"),policies=(ColumnPolicy(ColumnKind.PRIMARY_TEXT,210),ColumnPolicy(ColumnKind.TECHNICAL,240),ColumnPolicy(ColumnKind.COMPACT,110),ColumnPolicy(ColumnKind.TECHNICAL,170)))
        root.addWidget(self.workspace);self.scaffold=self.workspace.scaffold;self.toolbar=self.workspace.toolbar;self.table=self.workspace.table;self.footer=self.workspace.footer;self.create_button=self.workspace.create_button;self.pages=self.workspace.pages;self.list_page=self.workspace.list_page;self.details_page=self.workspace.details_page;self.back_button=self.workspace.back_button;self._selected_id=None;self._pending_open_id=None
        self.edit_button,self.reset_button,self.deactivate_button,self.activate_button=self.workspace.add_lifecycle_actions(edit="עריכת מנהל",password="שינוי סיסמה",deactivate="השבתת מנהל",reactivate="הפעלת מנהל מחדש")
        self.account_details=self.workspace.add_card("פרטי מנהל");self.login_details=self.workspace.add_card("פרטי התחברות");self.system_details=self.workspace.add_card("מידע מערכת")
        for button,signal in ((self.create_button,self.create_requested),(self.edit_button,self.edit_requested),(self.reset_button,self.reset_password_requested),(self.activate_button,self.activate_requested),(self.deactivate_button,self.deactivate_requested)):button.clicked.connect(signal);button.setAccessibleName(button.text())
        self.toolbar.search_requested.connect(lambda search,order:self.filters_requested.emit({"search":search or None,"order_by":order or "display_name"}));self.toolbar.sort_combo.currentIndexChanged.connect(self._sort_changed);self.toolbar.refresh_requested.connect(self._reset_toolbar);self.footer.page_requested.connect(self.page_requested);self.table.itemSelectionChanged.connect(self._select);self.table.cellDoubleClicked.connect(lambda row,_column:self._request_open(self._row_id(row)));self.table.installEventFilter(self);self.workspace.empty_action_button.clicked.connect(self._empty_action);self._empty_filtered=False;self.clear_details()
    def _sort_changed(self,_index):self.filters_requested.emit({"search":self.toolbar.search_input.text().strip() or None,"order_by":str(self.toolbar.sort_combo.currentData() or "display_name")})
    def _reset_toolbar(self):
        self.toolbar.search_input.clear();self.toolbar.sort_combo.blockSignals(True);self.toolbar.sort_combo.setCurrentIndex(0);self.toolbar.sort_combo.blockSignals(False);self.filters_requested.emit({"search":None,"is_active":None,"order_by":"display_name"})
    def _empty_action(self):self._reset_toolbar() if self._empty_filtered else self.create_requested.emit()
    def eventFilter(self,watched,event):
        if watched is self.table and event.type()==QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter):self._open();return True
        return super().eventFilter(watched,event)
    def _select(self):
        rows=self.table.selectionModel().selectedRows()
        if rows:
            user_id=self._row_id(rows[0].row());changed=user_id!=self._selected_id;self._selected_id=user_id
            if changed:self._clear_forms();self.workspace.detail_title.clear();self.workspace.show_list();self.user_selected.emit(user_id)
        else:self._selected_id=None
    def _open(self):
        if self._selected_id:self._pending_open_id=self._selected_id
        if self._selected_id and self.workspace.detail_title.text():self._pending_open_id=None;self.workspace.show_details()
    def _row_id(self,row):return str(self.table.item(row,1).data(Qt.ItemDataRole.UserRole))
    def _request_open(self,user_id):
        self._pending_open_id=user_id;self.select_user(user_id)
        if self.workspace.detail_title.text() and self._selected_id==user_id:self._pending_open_id=None;self.workspace.show_details()
    def show_users(self,rows,*,offset,count,filtered):
        rows=[u for u in rows if u.get("role")=="manager"];self.table.setRowCount(len(rows))
        for ri,user in enumerate(rows):
            self.workspace.set_row_open_action(ri,str(user["id"]),self._request_open)
            values=(user.get("display_name") or "מנהל",user["email"],str(user["updated_at"]))
            for ci,value in zip((1,2,4),values):
                item=QTableWidgetItem(str(value));set_item_text(self.table,ri,ci,item,tooltip_direction=Qt.LayoutDirection.LeftToRight if ci in {2,4} else Qt.LayoutDirection.RightToLeft);item.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignAbsolute)
                if ci==1:item.setData(Qt.ItemDataRole.UserRole,str(user["id"]))
            status=ActiveBadge();status.set_active(bool(user["is_active"]));self.workspace.configure_status_badge(status);self.table.setCellWidget(ri,3,status)
        self.footer.set_page(offset=offset,count=len(rows));self.workspace.results_label.setText(f"מנהלים • {len(rows)}");self._empty_filtered=filtered;self.workspace.show_empty_state(empty=not rows,filtered=filtered,plural="מנהלים")
    def show_details(self,user,*,current_user_id):
        self._clear_forms();name=user.get("display_name") or "מנהל";email=QLabel(str(user["email"]));configure_mixed_direction(email);self.workspace.add_property_row(self.account_details,"שם",QLabel(name));self.workspace.add_property_row(self.login_details,"דוא״ל התחברות",email)
        self.workspace.add_property_row(self.system_details,"מצב חשבון",QLabel("פעיל" if user["is_active"] else "לא פעיל"));self.workspace.add_property_row(self.system_details,"נוצר",QLabel(str(user["created_at"])));self.workspace.add_property_row(self.system_details,"עודכן",QLabel(str(user["updated_at"])))
        active=bool(user["is_active"]);self.workspace.show_detail_identity(name,active);self.workspace.show_lifecycle(active,self.deactivate_button,self.activate_button);self.edit_button.setEnabled(True);self.reset_button.setEnabled(True);self.activate_button.setEnabled(not active);self.deactivate_button.setEnabled(bool(active and str(user["id"])!=current_user_id))
        set_disabled_explanation(self.edit_button,"");set_disabled_explanation(self.reset_button,"");set_disabled_explanation(self.activate_button,"המנהל כבר פעיל" if user["is_active"] else "הפעלת חשבון המנהל")
        set_disabled_explanation(self.deactivate_button,"לא ניתן להשבית את החשבון המחובר" if str(user["id"])==current_user_id else "השבתת חשבון המנהל")
        if self._pending_open_id==str(user.get("id")):self._pending_open_id=None;self.workspace.show_details()
    def _clear_forms(self):
        for form in (self.account_details,self.login_details,self.system_details):
            while form.rowCount():form.removeRow(0)
    def clear_details(self):
        if hasattr(self,"account_details"):self._clear_forms();self.workspace.detail_title.clear();self.workspace.set_actions_enabled(False);self.workspace.show_list()
        self.activate_button.hide();self.deactivate_button.hide()
        self._selected_id=None;self._pending_open_id=None
        for button in (self.edit_button,self.reset_button,self.activate_button,self.deactivate_button):set_disabled_explanation(button,"יש לבחור מנהל תחילה")
    def reset_to_default(self):
        dialog=getattr(self,"_dialog",None)
        if dialog is not None and dialog.isVisible():dialog.reject()
        self.scaffold.feedback.hide();self.toolbar.search_input.clear();blocked=self.toolbar.sort_combo.blockSignals(True);self.toolbar.sort_combo.setCurrentIndex(0);self.toolbar.sort_combo.blockSignals(blocked);self.table.clearSelection();self.clear_details()
    def set_detail_loading(self,value):
        if value:self.workspace.set_actions_enabled(False)
    def set_loading(self,value):
        self.create_button.setEnabled(not value);self.toolbar.search_button.setEnabled(not value);self.toolbar.refresh_button.setEnabled(not value);self.toolbar.sort_combo.setEnabled(not value)
        if value and not self.table.rowCount():self.workspace.show_loading("טוען מנהלים…")
    def show_error(self,message,*,retriable=False,permission=False):self.scaffold.feedback.render(RequestState(RequestPhase.AUTHORIZATION_ERROR if permission else RequestPhase.CONNECTION_ERROR if retriable else RequestPhase.SERVER_ERROR,message,"users",retryable=retriable))
    def show_success(self,message):self.scaffold.feedback.render(RequestState(RequestPhase.SUCCESS,message,"users"))
    def select_user(self,user_id):
        for row in range(self.table.rowCount()):
            if str(self.table.item(row,1).data(Qt.ItemDataRole.UserRole))==user_id:
                changed=self._selected_id!=user_id;blocked=self.table.blockSignals(True);index=self.table.model().index(row,1);self.table.selectionModel().setCurrentIndex(index,QItemSelectionModel.SelectionFlag.ClearAndSelect|QItemSelectionModel.SelectionFlag.Rows);self.table.blockSignals(blocked);self._selected_id=user_id
                if changed:self._clear_forms();self.workspace.detail_title.clear();self.workspace.show_list();self.user_selected.emit(user_id)
                break
    def open_create(self,submit):self._dialog=CreateUserDialog(self);self._dialog.submitted.connect(submit);self._dialog.open()
    def open_edit(self,user,submit):self._dialog=EditUserDialog(user,self);self._dialog.submitted.connect(submit);self._dialog.open()
    def open_reset_password(self,user,submit):self._dialog=ResetPasswordDialog(user,self);self._dialog.submitted.connect(submit);self._dialog.open()
    def confirm_deactivation(self,email):return confirm_action(self,"אישור השבתת מנהל",f"להשבית את המנהל {email}? החשבון לא יוכל להתחבר עד להפעלה מחדש.")
