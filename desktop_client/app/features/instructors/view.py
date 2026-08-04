from __future__ import annotations

from PySide6.QtCore import QEvent, QItemSelectionModel, Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QTableWidgetItem, QVBoxLayout, QWidget

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.shared.ui.account_dialogs import ChangePasswordDialog
from desktop_client.app.shared.ui.common import StatefulWidget
from desktop_client.app.features.instructors.dialogs import InstructorDialog
from desktop_client.app.shared.ui.management_common import ActiveBadge, confirm_action
from desktop_client.app.shared.ui.management_workspace import ManagementWorkspace
from desktop_client.app.shared.ui.management_visuals import ReadOnlyProfileCard, apply_reference_detail_layout, apply_reference_list_layout, install_management_hero, install_scaffold_hero
from desktop_client.app.shared.ui.foundations import ColumnKind, ColumnPolicy, PageScaffold, configure_mixed_direction, set_disabled_explanation, set_item_text


class InstructorsView(StatefulWidget):
    filters_requested=Signal(dict);page_requested=Signal(int,int);instructor_selected=Signal(str);retry_requested=Signal();create_requested=Signal();edit_requested=Signal();deactivate_requested=Signal();reactivate_requested=Signal();change_password_requested=Signal()
    def __init__(self):
        super().__init__();root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0)
        self.workspace=ManagementWorkspace(title="מדריכים",subtitle="ניהול מדריכים ופרטי התקשרות",create_text="מדריך חדש",plural="מדריכים",detail_subtitle="מידע מלא ופעולות עבור המדריך שנבחר",search_placeholder="חיפוש לפי שם, דוא״ל, טלפון או עיר",sort_options=(("full_name","מיון לפי: שם"),("created_at","מיון לפי: תאריך יצירה"),("is_active","מיון לפי: מצב")),headers=("שם מדריך","עיר","טלפון","דוא״ל","מצב"),policies=(ColumnPolicy(ColumnKind.PRIMARY_TEXT,200),ColumnPolicy(ColumnKind.SECONDARY_TEXT,150,230),ColumnPolicy(ColumnKind.TECHNICAL,140),ColumnPolicy(ColumnKind.TECHNICAL,210),ColumnPolicy(ColumnKind.COMPACT,110)),row_action_position="end")
        root.addWidget(self.workspace);self.scaffold=self.workspace.scaffold;self.toolbar=self.workspace.toolbar;self.table=self.workspace.table;self.footer=self.workspace.footer;self.create_button=self.workspace.create_button;self.pages=self.workspace.pages;self.list_page=self.workspace.list_page;self.details_page=self.workspace.details_page;self.back_button=self.workspace.back_button;self._selected_id=None;self._pending_open_id=None
        self.edit_button,self.change_password_button,self.deactivate_button,self.reactivate_button=self.workspace.add_lifecycle_actions(edit="עריכת מדריך",password="שינוי סיסמה",deactivate="השבתת מדריך",reactivate="הפעלת מדריך מחדש")
        self.profile_details=self.workspace.add_card("פרטי מדריך");self.contact_details=self.workspace.add_card("פרטי קשר");self.system_details=self.workspace.add_card("מידע מערכת")
        self.hero=install_management_hero(self.workspace,"instructors-hero.png","תמונת פעילות למסך מדריכים")
        apply_reference_list_layout(self.workspace)
        apply_reference_detail_layout(
            self.workspace,
            back_text="← חזרה לרשימת מדריכים",
            actions=((self.deactivate_button,"destructive"),(self.reactivate_button,"success"),(self.change_password_button,"secondary"),(self.edit_button,"primary")),
            cards=((self.profile_details,"primary"),(self.contact_details,"secondary"),(self.system_details,"system")),
        )
        self.create_button.clicked.connect(self.create_requested);self.edit_button.clicked.connect(self.edit_requested);self.change_password_button.clicked.connect(self.change_password_requested);self.deactivate_button.clicked.connect(self.deactivate_requested);self.reactivate_button.clicked.connect(self.reactivate_requested)
        self.toolbar.search_requested.connect(lambda search,order:self.filters_requested.emit({"search":search or None,"order_by":order or "full_name"}));self.toolbar.sort_combo.currentIndexChanged.connect(self._sort_changed);self.toolbar.refresh_requested.connect(self._reset_toolbar);self.footer.page_requested.connect(self.page_requested);self.table.itemSelectionChanged.connect(self._select);self.table.cellDoubleClicked.connect(lambda row,_column:self._request_open(self._row_id(row)));self.table.installEventFilter(self);self.workspace.empty_action_button.clicked.connect(self._empty_action);self._empty_filtered=False;self.clear_details()
    def _sort_changed(self,_index):self.filters_requested.emit({"search":self.toolbar.search_input.text().strip() or None,"order_by":str(self.toolbar.sort_combo.currentData() or "full_name")})
    def _reset_toolbar(self):
        self.toolbar.search_input.clear();self.toolbar.sort_combo.blockSignals(True);self.toolbar.sort_combo.setCurrentIndex(0);self.toolbar.sort_combo.blockSignals(False);self.filters_requested.emit({"search":None,"city":None,"is_active":None,"order_by":"full_name"})
    def _empty_action(self):self._reset_toolbar() if self._empty_filtered else self.create_requested.emit()
    def eventFilter(self,watched,event):
        if watched is self.table and event.type()==QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter):self._open();return True
        return super().eventFilter(watched,event)
    def _select(self):
        rows=self.table.selectionModel().selectedRows()
        if rows:
            instructor_id=self._row_id(rows[0].row());changed=instructor_id!=self._selected_id;self._selected_id=instructor_id
            if changed:self._clear_forms();self.workspace.detail_title.clear();self.workspace.show_list();self.instructor_selected.emit(instructor_id)
        else:self._selected_id=None
    def _open(self):
        if self._selected_id:self._pending_open_id=self._selected_id
        if self._selected_id and self.workspace.detail_title.text():self._pending_open_id=None;self.workspace.show_details()
    def _row_id(self,row):return str(self.table.item(row,0).data(Qt.ItemDataRole.UserRole))
    def _request_open(self,instructor_id):
        self._pending_open_id=instructor_id;self.select_instructor(instructor_id)
        if self.workspace.detail_title.text() and self._selected_id==instructor_id:self._pending_open_id=None;self.workspace.show_details()
    def show_instructors(self,rows,*,offset,count,filtered):
        self.table.setRowCount(len(rows))
        for ri,row in enumerate(rows):
            self.workspace.set_row_open_action(ri,str(row["id"]),self._request_open)
            for ci,key in enumerate(("full_name","city","phone","email"),start=0):
                item=QTableWidgetItem(str(row.get(key) or "—"));set_item_text(self.table,ri,ci,item,tooltip_direction=Qt.LayoutDirection.LeftToRight if key in {"phone","email"} else Qt.LayoutDirection.RightToLeft);item.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignAbsolute)
                if ci==0:item.setData(Qt.ItemDataRole.UserRole,str(row["id"]))
            status=ActiveBadge();status.set_active(bool(row.get("is_active")));self.workspace.configure_status_badge(status);self.table.setCellWidget(ri,4,status)
        self.footer.set_page(offset=offset,count=count);self.workspace.results_label.setText(f"מדריכים • {len(rows)}");self._empty_filtered=filtered;self.workspace.show_empty_state(empty=not rows,filtered=filtered,plural="מדריכים")
    def show_details(self,details,item):
        self._clear_forms()
        for label,value in details:
            content=QLabel(value);content.setWordWrap(True);content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse);content.setToolTip(value)
            if any(x in label for x in ("דוא","טלפון")):configure_mixed_direction(content)
            target=self.system_details if label in {"מצב","נוצר","עודכן"} else self.contact_details if label in {"טלפון","דוא״ל"} else self.profile_details;self.workspace.add_property_row(target,label,content)
        active=bool(item.get("is_active"));self.workspace.show_detail_identity(str(item.get("full_name") or "פרטי מדריך"),active);self.workspace.set_actions_enabled(True);self.workspace.show_lifecycle(active,self.deactivate_button,self.reactivate_button)
        for button in (self.edit_button,self.change_password_button,self.deactivate_button,self.reactivate_button):set_disabled_explanation(button,"")
        if self._pending_open_id==str(item.get("id")):self._pending_open_id=None;self.workspace.show_details()
    def _clear_forms(self):
        for form in (self.profile_details,self.contact_details,self.system_details):
            while form.rowCount():form.removeRow(0)
    def clear_details(self):
        if hasattr(self,"profile_details"):self._clear_forms();self.workspace.detail_title.clear();self.workspace.set_actions_enabled(False);self.workspace.show_list()
        self._selected_id=None;self._pending_open_id=None
        self.deactivate_button.hide();self.reactivate_button.hide()
        for button in (self.edit_button,self.change_password_button,self.deactivate_button,self.reactivate_button):set_disabled_explanation(button,"יש לבחור מדריך תחילה")
    def reset_to_default(self):
        dialog=getattr(self,"_dialog",None)
        if dialog is not None and dialog.isVisible():dialog.reject()
        self.scaffold.feedback.hide();self.toolbar.search_input.clear();blocked=self.toolbar.sort_combo.blockSignals(True);self.toolbar.sort_combo.setCurrentIndex(0);self.toolbar.sort_combo.blockSignals(blocked);self.table.clearSelection();self.clear_details()
    def show_error(self,message,*,retriable=False,permission=False):self.scaffold.feedback.render(RequestState(RequestPhase.CONNECTION_ERROR if retriable else RequestPhase.SERVER_ERROR,message,"instructors",retryable=retriable))
    def show_success(self,message):self.scaffold.feedback.render(RequestState(RequestPhase.SUCCESS,message,"instructors"))
    def select_instructor(self,instructor_id):
        for row in range(self.table.rowCount()):
            if str(self.table.item(row,0).data(Qt.ItemDataRole.UserRole))==instructor_id:
                changed=self._selected_id!=instructor_id;blocked=self.table.blockSignals(True);index=self.table.model().index(row,0);self.table.selectionModel().setCurrentIndex(index,QItemSelectionModel.SelectionFlag.ClearAndSelect|QItemSelectionModel.SelectionFlag.Rows);self.table.blockSignals(blocked);self._selected_id=instructor_id
                if changed:self._clear_forms();self.workspace.detail_title.clear();self.workspace.show_list();self.instructor_selected.emit(instructor_id)
                break
    def open_form(self,initial,submit):self._dialog=InstructorDialog(initial,self);self._dialog.submitted.connect(submit);self._dialog.open()
    def open_change_password(self,submit):self._dialog=ChangePasswordDialog(self);self._dialog.submitted.connect(submit);self._dialog.open()
    def confirm_deactivation(self,name):return confirm_action(self,"אישור השבתת מדריך",f"להשבית את המדריך {name}? חשבון ההתחברות יושבת עד להפעלה מחדש.")
    def set_loading(self,value):
        self.create_button.setEnabled(not value);self.toolbar.search_button.setEnabled(not value);self.toolbar.refresh_button.setEnabled(not value);self.toolbar.sort_combo.setEnabled(not value)
        if value and not self.table.rowCount():self.workspace.show_loading("טוען מדריכים…")
    def set_detail_loading(self,value):
        if value:self.workspace.set_actions_enabled(False)


class InstructorProfileView(StatefulWidget):
    retry_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.scaffold = PageScaffold("הפרופיל שלי", "פרטי המדריך ופרטי הקשר השמורים במערכת")
        self.scaffold.root.setContentsMargins(16, 12, 16, 16)
        self.scaffold.root.setSpacing(8)
        root.addWidget(self.scaffold)
        self.hero = install_scaffold_hero(self.scaffold, "instructors-hero.png", "תמונת פרופיל מדריך")
        self.scaffold.main_content.addWidget(self.state_label)

        body = QWidget()
        body.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(12)
        body_layout.setDirection(QHBoxLayout.Direction.LeftToRight)

        left_column = QWidget()
        left_column.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        self.contact_card = ReadOnlyProfileCard("פרטי קשר", "secondary")
        self.system_card = ReadOnlyProfileCard("מידע מערכת", "system")
        left_layout.addWidget(self.contact_card)
        left_layout.addWidget(self.system_card)
        left_layout.addStretch(1)

        self.profile_card = ReadOnlyProfileCard("פרטי מדריך", "primary")
        self.profile_card.setMinimumWidth(430)
        self.profile_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        body_layout.addWidget(left_column, 1)
        body_layout.addWidget(self.profile_card, 1)
        self.scaffold.main_content.addWidget(body, 1)

        self.details = self.profile_card
        self.contact_details = self.contact_card
        self.system_details = self.system_card

    def show_profile(self, details):
        for card in (self.profile_card, self.contact_card, self.system_card):
            card.clear_rows()
        for label, value in details:
            mixed = any(token in label for token in ("דוא", "טלפון", "מזהה", "נוצר", "עודכן"))
            if label in {"טלפון", "דוא״ל"}:
                target = self.contact_card
            elif label in {"מצב", "נוצר", "עודכן"}:
                target = self.system_card
            else:
                target = self.profile_card
            target.add_row(label, value, mixed_direction=mixed)

    def show_error(self, message, *, retriable=False, permission=False):
        self.show_empty(message)
