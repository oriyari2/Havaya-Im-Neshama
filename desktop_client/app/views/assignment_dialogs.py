from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog,QHBoxLayout,QLineEdit,QPushButton,QTableWidget,QTableWidgetItem,QVBoxLayout
from desktop_client.app.views.management_common import PaginationFooter,RetryState
class InstructorSelectorDialog(QDialog):
    def __init__(self,activity,query_handler,choose_handler,parent=None):
        super().__init__(parent);self.activity=activity;self.query_handler=query_handler;self.choose_handler=choose_handler;self.filters={"search":None,"city":None,"is_active":True,"order_by":"full_name","limit":25,"offset":0};self.setWindowTitle(f"בחירת מדריך — {activity['activity_name']}");root=QVBoxLayout(self);bar=QHBoxLayout();self.search=QLineEdit();self.search.setPlaceholderText("חיפוש");self.city=QLineEdit();self.city.setPlaceholderText("עיר");go=QPushButton("חיפוש");go.clicked.connect(self._search);bar.addWidget(self.search);bar.addWidget(self.city);bar.addWidget(go);root.addLayout(bar);self.retry=RetryState();self.retry.hide();self.retry.retry_requested.connect(lambda:self.query_handler(dict(self.filters)));root.addWidget(self.retry);self.table=QTableWidget(0,3);self.table.setHorizontalHeaderLabels(["שם","עיר","טלפון"]);self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows);self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);root.addWidget(self.table);self.footer=PaginationFooter();self.footer.page_requested.connect(self._page);root.addWidget(self.footer);choose=QPushButton("שייך מדריך");choose.clicked.connect(self._choose);root.addWidget(choose)
    def _search(self):self.filters.update(search=self.search.text().strip() or None,city=self.city.text().strip() or None,offset=0);self.query_handler(dict(self.filters))
    def _page(self,o,l):self.filters.update(offset=o,limit=l);self.query_handler(dict(self.filters))
    def show_instructors(self,items,*,offset,count):
        self.retry.hide();self.table.setRowCount(len(items))
        for r,x in enumerate(items):
            for c,k in enumerate(("full_name","city","phone")):
                value=(str(x.get(k) or "—")+(" (כבר משויך)" if c==0 and x.get("_already_assigned") else ""));item=QTableWidgetItem(value);self.table.setItem(r,c,item)
                if c==0:item.setData(Qt.ItemDataRole.UserRole,x)
        self.footer.set_page(offset=offset,count=count)
    def show_error(self,m,*,retriable=False):self.retry.show_message(m,retriable=retriable)
    def _choose(self):
        rows=self.table.selectionModel().selectedRows()
        if rows:
            value=self.table.item(rows[0].row(),0).data(Qt.ItemDataRole.UserRole)
            if not value.get("_already_assigned"):self.choose_handler(value)
    def close_success(self):self.accept()
