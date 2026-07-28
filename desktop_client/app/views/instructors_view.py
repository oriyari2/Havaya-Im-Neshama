from PySide6.QtCore import Qt,Signal
from PySide6.QtWidgets import QComboBox,QFormLayout,QGroupBox,QHBoxLayout,QLabel,QPushButton,QSplitter,QTableWidget,QTableWidgetItem,QVBoxLayout
from desktop_client.app.views.common import StatefulWidget
from desktop_client.app.views.instructor_dialogs import InstructorDialog
from desktop_client.app.views.management_common import ActiveBadge,PaginationFooter,RetryState,SearchToolbar,confirm_action
class InstructorsView(StatefulWidget):
    filters_requested=Signal(dict);page_requested=Signal(int,int);instructor_selected=Signal(str);retry_requested=Signal();create_requested=Signal();edit_requested=Signal();delete_requested=Signal()
    def __init__(self):
        super().__init__();root=QVBoxLayout(self);title=QLabel("מדריכים");title.setObjectName("screenTitle");root.addWidget(title);self.retry_state=RetryState();self.retry_state.hide();self.retry_state.retry_requested.connect(self.retry_requested);root.addWidget(self.retry_state);root.addWidget(self.state_label);self.toolbar=SearchToolbar(placeholder="חיפוש מדריכים",sort_options=(("full_name","שם"),("created_at","תאריך יצירה")));self.toolbar.search_requested.connect(lambda s,o:self.filters_requested.emit({"search":s or None,"order_by":o}));self.toolbar.refresh_requested.connect(self.retry_requested);root.addWidget(self.toolbar)
        filters=QHBoxLayout();self.city=QComboBox();self.city.setEditable(True);self.city.addItem("כל הערים","");self.active=QComboBox();self.active.addItem("הכול",None);self.active.addItem("פעילים",True);self.active.addItem("לא פעילים",False);apply=QPushButton("החל סינון");apply.clicked.connect(lambda:self.filters_requested.emit({"city":self.city.currentText().strip() if self.city.currentIndex() else None,"is_active":self.active.currentData()}));filters.addWidget(self.city);filters.addWidget(self.active);filters.addWidget(apply);root.addLayout(filters)
        actions=QHBoxLayout();self.create_button=QPushButton("מדריך חדש");self.edit_button=QPushButton("עריכה");self.delete_button=QPushButton("מחיקה")
        for b,s in ((self.create_button,self.create_requested),(self.edit_button,self.edit_requested),(self.delete_button,self.delete_requested)):b.clicked.connect(s);actions.addWidget(b)
        root.addLayout(actions);split=QSplitter();self.table=QTableWidget(0,5);self.table.setHorizontalHeaderLabels(["שם","טלפון","דוא״ל","עיר","מצב"]);self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows);self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);self.table.itemSelectionChanged.connect(self._select);split.addWidget(self.table);group=QGroupBox("פרטי מדריך");self.details=QFormLayout(group);split.addWidget(group);split.setStretchFactor(0,2);root.addWidget(split);self.footer=PaginationFooter();self.footer.page_requested.connect(self.page_requested);root.addWidget(self.footer);self.clear_details()
    def _select(self):
        rows=self.table.selectionModel().selectedRows()
        if rows:self.instructor_selected.emit(str(self.table.item(rows[0].row(),0).data(Qt.ItemDataRole.UserRole)))
    def show_instructors(self,rows,*,offset,count,filtered):
        self.retry_state.hide();self.table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            for c,k in enumerate(("full_name","phone","email","city")):
                item=QTableWidgetItem(str(x[k]));self.table.setItem(r,c,item)
                if c==0:item.setData(Qt.ItemDataRole.UserRole,x["id"])
            badge=ActiveBadge();badge.set_active(x["is_active"]);self.table.setCellWidget(r,4,badge)
        self.footer.set_page(offset=offset,count=count)
        if not rows:self.show_empty("לא נמצאו מדריכים." if filtered else "אין מדריכים להצגה.")
    def show_details(self,details,item):
        while self.details.rowCount():self.details.removeRow(0)
        for l,v in details:self.details.addRow(l,QLabel(v))
        self.edit_button.setEnabled(True);self.delete_button.setEnabled(True)
    def clear_details(self):
        for n in ("edit_button","delete_button"):
            b=getattr(self,n,None)
            if b:b.setEnabled(False)
    def show_error(self,m,*,retriable=False,permission=False):self.retry_state.show_message(m,retriable=retriable)
    def show_success(self,m):self.state_label.setText(m);self.state_label.show()
    def select_instructor(self,i):
        for r in range(self.table.rowCount()):
            if str(self.table.item(r,0).data(Qt.ItemDataRole.UserRole))==i:self.table.selectRow(r);break
    def open_form(self,initial,submit):self._dialog=InstructorDialog(initial,self);self._dialog.submitted.connect(submit);self._dialog.open()
    def confirm_deletion(self,name):return confirm_action(self,"אישור מחיקה",f"למחוק לצמיתות את המדריך {name}? לא ניתן לבטל פעולה זו.")
class InstructorProfileView(StatefulWidget):
    retry_requested=Signal()
    def __init__(self):
        super().__init__();root=QVBoxLayout(self);title=QLabel("הפרופיל שלי");title.setObjectName("screenTitle");root.addWidget(title);self.retry_state=RetryState();self.retry_state.hide();self.retry_state.retry_requested.connect(self.retry_requested);root.addWidget(self.retry_state);root.addWidget(self.state_label);group=QGroupBox("פרטי מדריך");self.details=QFormLayout(group);root.addWidget(group)
    def show_profile(self,details):
        self.retry_state.hide()
        while self.details.rowCount():self.details.removeRow(0)
        for l,v in details:self.details.addRow(l,QLabel(v))
    def show_error(self,m,*,retriable=False,permission=False):self.retry_state.show_message(m,retriable=retriable)
