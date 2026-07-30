from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QComboBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from desktop_client.app.views.activity_dialogs import ActivityDialog
from desktop_client.app.views.common import StatefulWidget
from desktop_client.app.views.management_common import ActiveBadge, PaginationFooter, RetryState, SearchToolbar, confirm_action


def _positive_integer(value) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if number >= 0 else None


def _image_label(image: dict) -> str:
    raw_name = image.get("original_filename")
    name = raw_name.strip() if isinstance(raw_name, str) and raw_name.strip() else "תמונה ללא שם"
    width, height = _positive_integer(image.get("width")), _positive_integer(image.get("height"))
    dimensions = f"{width}×{height}" if width is not None and height is not None else "ממדים לא זמינים"
    byte_count = _positive_integer(image.get("bytes"))
    size = f"{byte_count // 1024} KiB" if byte_count is not None else "גודל לא זמין"
    primary = " • ראשית" if image.get("is_primary") else ""
    return " • ".join((name, dimensions, size)) + primary


class ActivitiesView(StatefulWidget):
    filters_requested = Signal(dict); page_requested = Signal(int, int); activity_selected = Signal(str); retry_requested = Signal()
    create_requested = Signal(); edit_requested = Signal(); deactivate_requested = Signal(); reactivate_requested = Signal()
    image_selected = Signal(str); upload_image_requested = Signal(str); delete_image_requested = Signal(); preview_retry_requested = Signal()
    booking_requested = Signal(str)
    def __init__(self, role: str) -> None:
        super().__init__(); self.role = role; root = QVBoxLayout(self); title = QLabel("ניהול פעילויות" if role == "manager" else "קטלוג פעילויות"); title.setObjectName("screenTitle"); root.addWidget(title); self.retry_state = RetryState(); self.retry_state.hide(); self.retry_state.retry_requested.connect(self.retry_requested); root.addWidget(self.retry_state); root.addWidget(self.state_label)
        self.toolbar = SearchToolbar(placeholder="חיפוש בשם או בתוכן הפעילות"); self.toolbar.search_requested.connect(lambda search, _sort: self.filters_requested.emit({"search": search or None})); self.toolbar.refresh_requested.connect(self.retry_requested); root.addWidget(self.toolbar)
        filters = QHBoxLayout(); self.audience = QComboBox(); self.audience.setEditable(True); self.audience.addItem("כל קהלי היעד", ""); self.season = QComboBox(); self.season.setEditable(True); self.season.addItem("כל העונות", ""); self.tag = QComboBox(); self.tag.setEditable(True); self.tag.addItem("כל התגיות", ""); self.active = QComboBox(); self.active.addItem("הכול", None); self.active.addItem("פעילות", True); self.active.addItem("לא פעילות", False); self.active.setVisible(role == "manager"); apply = QPushButton("החל סינון"); apply.clicked.connect(self._filters)
        for widget in (self.audience, self.season, self.tag, self.active, apply): filters.addWidget(widget)
        root.addLayout(filters); self.actions = QWidget(); actions = QHBoxLayout(self.actions); self.create_button = QPushButton("פעילות חדשה"); self.edit_button = QPushButton("עריכה"); self.deactivate_button = QPushButton("השבתה"); self.reactivate_button = QPushButton("הפעלה מחדש")
        for button, signal in ((self.create_button,self.create_requested),(self.edit_button,self.edit_requested),(self.deactivate_button,self.deactivate_requested),(self.reactivate_button,self.reactivate_requested)): button.clicked.connect(signal); actions.addWidget(button)
        root.addWidget(self.actions); split = QSplitter(); columns = ["שם", "קהל יעד", "משך", "קיבולת", "עונה", "תמחור"] + (["מצב"] if role == "manager" else []); self.table = QTableWidget(0,len(columns)); self.table.setHorizontalHeaderLabels(columns); self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); self.table.itemSelectionChanged.connect(self._select); split.addWidget(self.table)
        detail_panel = QWidget(); detail_layout = QVBoxLayout(detail_panel); group = QGroupBox("פרטי פעילות"); self.details = QFormLayout(group); detail_layout.addWidget(group)
        self.booking_button = QPushButton("יצירת הזמנה" if role == "manager" else "בקשת הזמנה")
        self.booking_button.setVisible(role in {"manager", "customer"}); self.booking_button.setEnabled(False)
        self.booking_button.clicked.connect(self._request_booking); detail_layout.addWidget(self.booking_button)
        self.media_group = QGroupBox("תמונות פעילות"); media = QVBoxLayout(self.media_group); self.preview = QLabel("אין תמונות להצגה."); self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter); self.preview.setMinimumSize(260,160); self.preview.setWordWrap(True); media.addWidget(self.preview)
        self.image_list = QListWidget(); self.image_list.setMaximumHeight(110); self.image_list.currentItemChanged.connect(self._image_changed); media.addWidget(self.image_list)
        self.preview_retry = QPushButton("נסו שוב להציג תמונה"); self.preview_retry.clicked.connect(self.preview_retry_requested); self.preview_retry.hide(); media.addWidget(self.preview_retry)
        self.media_actions = QWidget(); media_actions = QHBoxLayout(self.media_actions); self.upload_image_button = QPushButton("העלאת תמונה"); self.delete_image_button = QPushButton("מחיקת תמונה"); self.upload_image_button.clicked.connect(self._choose_image); self.delete_image_button.clicked.connect(self.delete_image_requested); media_actions.addWidget(self.upload_image_button); media_actions.addWidget(self.delete_image_button); media.addWidget(self.media_actions)
        detail_layout.addWidget(self.media_group); detail_layout.addStretch(); split.addWidget(detail_panel); split.setStretchFactor(0,2); root.addWidget(split); self.footer = PaginationFooter(); self.footer.page_requested.connect(self.page_requested); root.addWidget(self.footer); self.clear_details(); self.set_manager_actions(role == "manager"); self.set_media_actions(role == "manager")
    def set_manager_actions(self, manager: bool) -> None: self.actions.setVisible(manager)
    def set_media_actions(self, manager: bool) -> None: self.media_actions.setVisible(manager)
    def _filters(self) -> None:
        values = {"target_audience": self.audience.currentText().strip() if self.audience.currentIndex() else None, "season": self.season.currentText().strip() if self.season.currentIndex() else None, "tag": self.tag.currentText().strip() if self.tag.currentIndex() else None}
        if self.role == "manager": values["is_active"] = self.active.currentData()
        self.filters_requested.emit(values)
    def _select(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if rows:
            self.booking_button.setEnabled(self.role in {"manager", "customer"})
            self.activity_selected.emit(str(self.table.item(rows[0].row(),0).data(Qt.ItemDataRole.UserRole)))
    def _request_booking(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if rows: self.booking_requested.emit(str(self.table.item(rows[0].row(),0).data(Qt.ItemDataRole.UserRole)))
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
        if getattr(self,"image_list",None) is not None: self.clear_media()
        if getattr(self,"booking_button",None) is not None: self.booking_button.setEnabled(False)
    def select_activity(self, activity_id: str) -> None:
        for r in range(self.table.rowCount()):
            if str(self.table.item(r,0).data(Qt.ItemDataRole.UserRole))==activity_id: self.table.selectRow(r); break
    def open_activity_form(self, initial, submit) -> None: self._dialog=ActivityDialog(initial,self); self._dialog.submitted.connect(submit); self._dialog.open()
    def confirm_deactivation(self,name: str) -> bool: return confirm_action(self,"אישור השבתה",f"להשבית את הפעילות {name}? הפעילות תהפוך ללא פעילה אך לא תימחק לצמיתות.")
    def show_images(self, images) -> None:
        self.image_list.blockSignals(True); self.image_list.clear()
        for image in images:
            item = QListWidgetItem(_image_label(image)); item.setData(Qt.ItemDataRole.UserRole,str(image.get("id"))); self.image_list.addItem(item)
        self.image_list.blockSignals(False); self.delete_image_button.setEnabled(False)
    def select_image(self, image_id: str) -> None:
        self.image_list.blockSignals(True)
        for index in range(self.image_list.count()):
            item=self.image_list.item(index)
            if str(item.data(Qt.ItemDataRole.UserRole))==image_id: self.image_list.setCurrentItem(item); self.delete_image_button.setEnabled(self.role=="manager"); break
        self.image_list.blockSignals(False)
    def _image_changed(self,current,previous) -> None:
        if current is not None: self.image_selected.emit(str(current.data(Qt.ItemDataRole.UserRole)))
    def _choose_image(self) -> None:
        path,_=QFileDialog.getOpenFileName(self,"בחירת תמונה","","תמונות (*.jpg *.jpeg *.png *.webp)")
        if path: self.upload_image_requested.emit(path)
    def set_media_submitting(self,submitting: bool) -> None:
        self.upload_image_button.setEnabled(not submitting); self.delete_image_button.setEnabled(not submitting and self.role=="manager" and self.image_list.currentItem() is not None)
    def set_preview_loading(self,loading: bool) -> None:
        if loading: self.preview.clear(); self.preview.setText("טוען תמונה…"); self.preview_retry.hide()
    def show_preview(self,data: bytes) -> bool:
        pixmap=QPixmap(); valid=pixmap.loadFromData(data)
        if not valid: self.show_preview_error("לא ניתן לפענח את קובץ התמונה."); return False
        self.preview.setText(""); self.preview.setPixmap(pixmap.scaled(self.preview.size(),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)); self.preview_retry.hide(); return True
    def show_preview_error(self,message: str) -> None: self.preview.clear(); self.preview.setText(message); self.preview_retry.show()
    def show_no_images(self) -> None: self.preview.clear(); self.preview.setText("אין תמונות להצגה."); self.preview_retry.hide(); self.delete_image_button.setEnabled(False)
    def clear_media(self) -> None: self.image_list.clear(); self.show_no_images()
    def confirm_image_deletion(self,name: str) -> bool: return confirm_action(self,"אישור מחיקת תמונה",f"למחוק את {name}? הקובץ יימחק גם משירות התמונות.")
