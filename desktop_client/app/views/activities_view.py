from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from desktop_client.app.views.activity_dialogs import ActivityDialog
from desktop_client.app.views.common import StatefulWidget
from desktop_client.app.views.management_common import ActiveBadge, PaginationFooter, RetryState, SearchToolbar, confirm_action


class ActivitiesView(StatefulWidget):
    filters_requested = Signal(dict); page_requested = Signal(int, int); activity_selected = Signal(str); retry_requested = Signal()
    create_requested = Signal(); edit_requested = Signal(); deactivate_requested = Signal(); reactivate_requested = Signal()
    def __init__(self, role: str) -> None:
        super().__init__(); self.role = role; root = QVBoxLayout(self); title = QLabel("ניהול פעילויות" if role == "manager" else "קטלוג פעילויות"); title.setObjectName("screenTitle"); root.addWidget(title); self.retry_state = RetryState(); self.retry_state.hide(); self.retry_state.retry_requested.connect(self.retry_requested); root.addWidget(self.retry_state); root.addWidget(self.state_label)
        self.toolbar = SearchToolbar(placeholder="חיפוש בשם או בתוכן הפעילות"); self.toolbar.search_requested.connect(lambda search, _sort: self.filters_requested.emit({"search": search or None})); self.toolbar.refresh_requested.connect(self.retry_requested); root.addWidget(self.toolbar)
        filters = QHBoxLayout(); self.audience = QComboBox(); self.audience.setEditable(True); self.audience.addItem("כל קהלי היעד", ""); self.season = QComboBox(); self.season.setEditable(True); self.season.addItem("כל העונות", ""); self.tag = QComboBox(); self.tag.setEditable(True); self.tag.addItem("כל התגיות", ""); self.active = QComboBox(); self.active.addItem("הכול", None); self.active.addItem("פעילות", True); self.active.addItem("לא פעילות", False); self.active.setVisible(role == "manager"); apply = QPushButton("החל סינון"); apply.clicked.connect(self._filters)
        for widget in (self.audience, self.season, self.tag, self.active, apply): filters.addWidget(widget)
        root.addLayout(filters); self.actions = QWidget(); actions = QHBoxLayout(self.actions); self.create_button = QPushButton("פעילות חדשה"); self.edit_button = QPushButton("עריכה"); self.deactivate_button = QPushButton("השבתה"); self.reactivate_button = QPushButton("הפעלה מחדש")
        for button, signal in ((self.create_button,self.create_requested),(self.edit_button,self.edit_requested),(self.deactivate_button,self.deactivate_requested),(self.reactivate_button,self.reactivate_requested)): button.clicked.connect(signal); actions.addWidget(button)
        root.addWidget(self.actions); split = QSplitter(); columns = ["שם", "קהל יעד", "משך", "קיבולת", "עונה", "תמחור"] + (["מצב"] if role == "manager" else []); self.table = QTableWidget(0,len(columns)); self.table.setHorizontalHeaderLabels(columns); self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); self.table.itemSelectionChanged.connect(self._select); split.addWidget(self.table); group = QGroupBox("פרטי פעילות"); self.details = QFormLayout(group); split.addWidget(group); split.setStretchFactor(0,2); root.addWidget(split); self.footer = PaginationFooter(); self.footer.page_requested.connect(self.page_requested); root.addWidget(self.footer); self.clear_details(); self.set_manager_actions(role == "manager")
    def set_manager_actions(self, manager: bool) -> None: self.actions.setVisible(manager)
    def _filters(self) -> None:
        values = {"target_audience": self.audience.currentText().strip() if self.audience.currentIndex() else None, "season": self.season.currentText().strip() if self.season.currentIndex() else None, "tag": self.tag.currentText().strip() if self.tag.currentIndex() else None}
        if self.role == "manager": values["is_active"] = self.active.currentData()
        self.filters_requested.emit(values)
    def _select(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if rows: self.activity_selected.emit(str(self.table.item(rows[0].row(),0).data(Qt.ItemDataRole.UserRole)))
    def set_loading(self, value: bool) -> None: super().set_loading(value); self.toolbar.setEnabled(not value); self.footer.setEnabled(not value)
    def show_error(self, message: str, *, retriable=False, permission=False) -> None: self.retry_state.show_message(message, retriable=retriable)
    def show_success(self, message: str) -> None: self.state_label.setText(message); self.state_label.show()
    def show_activities(self, rows, *, offset, count, filtered) -> None:
        self.retry_state.hide(); self.table.setRowCount(len(rows)); keys = ("name","target_audience","duration_minutes","recommended_capacity","season","pricing_rule")
        for r,row in enumerate(rows):
            for c,key in enumerate(keys):
                item=QTableWidgetItem(str(row[key])); self.table.setItem(r,c,item)
                if c==0: item.setData(Qt.ItemDataRole.UserRole,row["id"])
            if self.role == "manager": badge=ActiveBadge(); badge.set_active(bool(row["is_active"])); self.table.setCellWidget(r,6,badge)
        self.footer.set_page(offset=offset,count=count)
        if not rows: self.show_empty("לא נמצאו פעילויות התואמות לסינון." if filtered else "אין פעילויות להצגה.")
    def show_details(self, details, activity) -> None:
        while self.details.rowCount(): self.details.removeRow(0)
        for label,value in details: self.details.addRow(label,QLabel(value))
        active=bool(activity.get("is_active")); self.edit_button.setEnabled(self.role=="manager"); self.deactivate_button.setEnabled(self.role=="manager" and active); self.reactivate_button.setEnabled(self.role=="manager" and not active)
    def clear_details(self) -> None:
        while getattr(self,"details",None) is not None and self.details.rowCount(): self.details.removeRow(0)
        for name in ("edit_button","deactivate_button","reactivate_button"):
            button=getattr(self,name,None)
            if button: button.setEnabled(False)
    def select_activity(self, activity_id: str) -> None:
        for r in range(self.table.rowCount()):
            if str(self.table.item(r,0).data(Qt.ItemDataRole.UserRole))==activity_id: self.table.selectRow(r); break
    def open_activity_form(self, initial, submit) -> None: self._dialog=ActivityDialog(initial,self); self._dialog.submitted.connect(submit); self._dialog.open()
    def confirm_deactivation(self,name: str) -> bool: return confirm_action(self,"אישור השבתה",f"להשבית את הפעילות {name}? הפעילות תהפוך ללא פעילה אך לא תימחק לצמיתות.")
