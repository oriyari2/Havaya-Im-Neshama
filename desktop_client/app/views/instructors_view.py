from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import QApplication, QFormLayout, QGroupBox, QLabel, QTableWidgetItem, QVBoxLayout, QWidget

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.views.account_dialogs import ChangePasswordDialog
from desktop_client.app.views.common import StatefulWidget
from desktop_client.app.views.instructor_dialogs import InstructorDialog
from desktop_client.app.views.management_common import confirm_action
from desktop_client.app.views.management_workspace import ManagementWorkspace
from desktop_client.app.views.ui_foundations import ColumnKind, ColumnPolicy, configure_mixed_direction, set_disabled_explanation, set_item_text


class InstructorsView(StatefulWidget):
    filters_requested=Signal(dict);page_requested=Signal(int,int);instructor_selected=Signal(str);retry_requested=Signal();create_requested=Signal();edit_requested=Signal();delete_requested=Signal();change_password_requested=Signal()
    def __init__(self):
        super().__init__();root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0)
        self.workspace=ManagementWorkspace(title="מדריכים",subtitle="ניהול מדריכים ופרטי התקשרות",create_text="מדריך חדש",plural="מדריכים",search_placeholder="חיפוש לפי שם, דוא״ל, טלפון או עיר",sort_options=(("full_name","מיון לפי: שם"),("city","מיון לפי: עיר"),("phone","מיון לפי: טלפון"),("email","מיון לפי: דוא״ל"),("is_active","מיון לפי: מצב"),("created_at","מיון לפי: תאריך יצירה"),("updated_at","מיון לפי: תאריך עדכון")),headers=("שם מדריך","עיר","טלפון","דוא״ל","מצב"),policies=(ColumnPolicy(ColumnKind.PRIMARY_TEXT,200),ColumnPolicy(ColumnKind.SECONDARY_TEXT,150,230),ColumnPolicy(ColumnKind.TECHNICAL,140),ColumnPolicy(ColumnKind.TECHNICAL,210),ColumnPolicy(ColumnKind.COMPACT,110)))
        root.addWidget(self.workspace);self.scaffold=self.workspace.scaffold;self.toolbar=self.workspace.toolbar;self.table=self.workspace.table;self.footer=self.workspace.footer;self.create_button=self.workspace.create_button;self.pages=self.workspace.pages;self.list_page=self.workspace.list_page;self.details_page=self.workspace.details_page;self.back_button=self.workspace.back_button;self.view_details_button=self.workspace.view_details_button
        self.edit_button=self.workspace.add_action("עריכת מדריך");self.change_password_button=self.workspace.add_action("שינוי סיסמה");self.delete_button=self.workspace.add_action("מחיקת מדריך",destructive=True)
        self.profile_details=self.workspace.add_card("פרטי מדריך");self.system_details=self.workspace.add_card("מידע מערכת")
        self.create_button.clicked.connect(self.create_requested);self.edit_button.clicked.connect(self.edit_requested);self.change_password_button.clicked.connect(self.change_password_requested);self.delete_button.clicked.connect(self.delete_requested)
        self.toolbar.search_requested.connect(lambda search,order:self.filters_requested.emit({"search":search or None,"order_by":order or "full_name"}));self.toolbar.sort_combo.currentIndexChanged.connect(self._sort_changed);self.toolbar.refresh_requested.connect(self._reset_toolbar);self.footer.page_requested.connect(self.page_requested);self.table.itemSelectionChanged.connect(self._select);self.table.cellDoubleClicked.connect(lambda _r,_c:self._open());self.table.installEventFilter(self);self.view_details_button.clicked.connect(self._open);self.clear_details()
    def _sort_changed(self,_index):self.filters_requested.emit({"search":self.toolbar.search_input.text().strip() or None,"order_by":str(self.toolbar.sort_combo.currentData() or "full_name")})
    def _reset_toolbar(self):
        self.toolbar.search_input.clear();self.toolbar.sort_combo.blockSignals(True);self.toolbar.sort_combo.setCurrentIndex(0);self.toolbar.sort_combo.blockSignals(False);self.filters_requested.emit({"search":None,"city":None,"is_active":None,"order_by":"full_name"})
    def eventFilter(self,watched,event):
        if watched is self.table and event.type()==QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter):self._open();return True
        return super().eventFilter(watched,event)
    def _select(self):
        rows=self.table.selectionModel().selectedRows()
        if rows:self.instructor_selected.emit(str(self.table.item(rows[0].row(),0).data(Qt.ItemDataRole.UserRole)));self.view_details_button.setEnabled(True)
    def _open(self):
        if self.workspace.detail_title.text():self.pages.setCurrentWidget(self.details_page)
    def show_instructors(self,rows,*,offset,count,filtered):
        self.table.setRowCount(len(rows))
        for ri,row in enumerate(rows):
            for ci,key in enumerate(("full_name","city","phone","email")):
                item=QTableWidgetItem(str(row.get(key) or "—"));set_item_text(self.table,ri,ci,item,tooltip_direction=Qt.LayoutDirection.LeftToRight if key in {"phone","email"} else Qt.LayoutDirection.RightToLeft);item.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignAbsolute)
                if ci==0:item.setData(Qt.ItemDataRole.UserRole,str(row["id"]))
            status=QTableWidgetItem("פעיל" if row.get("is_active") else "לא פעיל");status.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter);self.table.setItem(ri,4,status)
        self.footer.set_page(offset=offset,count=count);self.workspace.empty_label.setVisible(not rows);self.workspace.empty_label.setText("לא נמצאו מדריכים." if filtered else "אין מדריכים להצגה.")
    def show_details(self,details,item):
        self._clear_forms()
        for label,value in details:
            content=QLabel(value);content.setWordWrap(True);content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse);content.setToolTip(value)
            if any(x in label for x in ("דוא","טלפון")):configure_mixed_direction(content)
            (self.system_details if label in {"מצב","נוצר","עודכן"} else self.profile_details).addRow(label,content)
        self.workspace.show_detail_identity(str(item.get("full_name") or "פרטי מדריך"),bool(item.get("is_active")));self.workspace.set_actions_enabled(True)
    def _clear_forms(self):
        for form in (self.profile_details,self.system_details):
            while form.rowCount():form.removeRow(0)
    def clear_details(self):
        if hasattr(self,"profile_details"):self._clear_forms();self.workspace.detail_title.clear();self.workspace.set_actions_enabled(False);self.pages.setCurrentWidget(self.list_page)
        self.view_details_button.setEnabled(False)
    def show_error(self,message,*,retriable=False,permission=False):self.scaffold.feedback.render(RequestState(RequestPhase.CONNECTION_ERROR if retriable else RequestPhase.SERVER_ERROR,message,"instructors",retryable=retriable))
    def show_success(self,message):self.scaffold.feedback.render(RequestState(RequestPhase.SUCCESS,message,"instructors"))
    def select_instructor(self,instructor_id):
        for row in range(self.table.rowCount()):
            if str(self.table.item(row,0).data(Qt.ItemDataRole.UserRole))==instructor_id:self.table.selectRow(row);break
    def open_form(self,initial,submit):self._dialog=InstructorDialog(initial,self);self._dialog.submitted.connect(submit);self._dialog.open()
    def open_change_password(self,submit):self._dialog=ChangePasswordDialog(self);self._dialog.submitted.connect(submit);self._dialog.open()
    def confirm_deletion(self,name):return confirm_action(self,"אישור מחיקה",f"למחוק לצמיתות את המדריך {name}? לא ניתן לבטל פעולה זו.")
    def set_loading(self,value):
        self.create_button.setEnabled(not value);self.toolbar.search_button.setEnabled(not value);self.toolbar.refresh_button.setEnabled(not value);self.toolbar.sort_combo.setEnabled(not value)
        if value and not self.table.rowCount():self.workspace.empty_label.setText("טוען מדריכים…");self.workspace.empty_label.show()
        elif value is False and self.workspace.empty_label.text()=="טוען מדריכים…":self.workspace.empty_label.hide()
    def set_detail_loading(self,value):
        if value:self.workspace.set_actions_enabled(False)


class InstructorProfileView(StatefulWidget):
    retry_requested=Signal()
    def __init__(self):
        super().__init__();root=QVBoxLayout(self);title=QLabel("הפרופיל שלי");title.setObjectName("screenTitle");root.addWidget(title);group=QGroupBox("פרטי מדריך");self.details=QFormLayout(group);root.addWidget(group)
    def show_profile(self,details):
        while self.details.rowCount():self.details.removeRow(0)
        for label,value in details:self.details.addRow(label,QLabel(value))
    def show_error(self,message,*,retriable=False,permission=False):self.show_empty(message)
