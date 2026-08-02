from __future__ import annotations

from PySide6.QtCore import QEvent, QItemSelectionModel, Qt, Signal
from PySide6.QtWidgets import QComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.views.assignment_dialogs import InstructorSelectorDialog
from desktop_client.app.views.booking_dialogs import BookingFormDialog
from desktop_client.app.views.common import StatefulWidget
from desktop_client.app.views.design_tokens import SPACE_2, SPACE_3, SPACE_4
from desktop_client.app.views.management_common import RetryState, confirm_action
from desktop_client.app.views.management_workspace import ManagementWorkspace
from desktop_client.app.views.ui_foundations import ColumnKind, ColumnPolicy, set_item_text


class BookingsView(StatefulWidget):
    filters_requested=Signal(dict);booking_selected=Signal(str);create_requested=Signal();edit_requested=Signal();confirm_requested=Signal();cancel_requested=Signal();complete_requested=Signal();page_requested=Signal(int,int);assignment_add_requested=Signal(dict);assignment_add_and_confirm_requested=Signal(dict);assignment_remove_requested=Signal(dict,dict);queue_requested=Signal(str)
    def __init__(self, role):
        super().__init__();self.role=role;self._selected_id=None;self._pending_open_id=None;self._empty_filtered=False
        root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0)
        self.workspace=ManagementWorkspace(title="ניהול הזמנות" if role=="manager" else "ההזמנות שלי" if role=="customer" else "האירועים שלי",subtitle="מעקב אחר הזמנות, אישורים ושיבוץ מדריכים",create_text="הזמנה חדשה" if role=="manager" else "בקשת הזמנה חדשה",plural="הזמנות",detail_subtitle="מצב תפעולי ופרטי ההזמנה",search_placeholder="חיפוש ברשימת ההזמנות",sort_options=(("event_at","מיון לפי: מועד"),),headers=("לקוח","פעילות","מועד","מיקום","משתתפים","מצב"),policies=(ColumnPolicy(ColumnKind.PRIMARY_TEXT,180),ColumnPolicy(ColumnKind.PRIMARY_TEXT,190),ColumnPolicy(ColumnKind.TECHNICAL,160),ColumnPolicy(ColumnKind.SECONDARY_TEXT,170,240),ColumnPolicy(ColumnKind.COMPACT,100),ColumnPolicy(ColumnKind.COMPACT,130)))
        root.addWidget(self.workspace)
        for name in ("scaffold","toolbar","table","footer","create_button","pages","list_page","details_page","back_button"):setattr(self,name,getattr(self.workspace,name))
        self.pagination=self.footer;self.command_panel=self.workspace.actions_container;self.actions=self.command_panel;self.create_button.setVisible(role in {"manager","customer"})
        self._build_summary();self._build_filters();self._build_details()
        self.command_panel.setVisible(role=="manager")
        self.create_button.clicked.connect(self.create_requested);self.edit_button.clicked.connect(self.edit_requested);self.confirm_button.clicked.connect(self.confirm_requested);self.cancel_button.clicked.connect(self.cancel_requested);self.complete_button.clicked.connect(self.complete_requested)
        self.toolbar.search_requested.connect(lambda search,_sort:self._emit_filters(search=search));self.toolbar.sort_combo.currentIndexChanged.connect(lambda _i:self._emit_filters());self.toolbar.refresh_requested.connect(self._reset);self.apply_filters_button.clicked.connect(self._emit_filters);self.filter_button.clicked.connect(lambda:self.filter_panel.setVisible(not self.filter_panel.isVisible()));self.footer.page_requested.connect(self.page_requested)
        self.table.itemSelectionChanged.connect(self._select);self.table.cellDoubleClicked.connect(lambda row,_column:self._request_open(self._row_id(row)));self.table.installEventFilter(self);self.workspace.empty_action_button.clicked.connect(lambda:self._reset() if self._empty_filtered else self.create_requested.emit());self.clear_details()
    def _build_summary(self):
        self.summary_panel=QWidget();layout=QHBoxLayout(self.summary_panel);layout.setDirection(QHBoxLayout.Direction.RightToLeft);layout.setContentsMargins(0,0,0,0);layout.setSpacing(SPACE_3);self.summary_buttons={}
        for key,title in (("pending","ממתינות לאישור"),("unassigned","ממתינות לשיבוץ מדריך"),("approved","מאושרות")):
            button=QPushButton(f"{title}\n0");button.setProperty("summaryQueue",key);button.setMinimumHeight(68);button.clicked.connect(lambda _checked=False,value=key:self.queue_requested.emit(value));layout.addWidget(button);self.summary_buttons[key]=button
        self.list_page.layout().insertWidget(0,self.summary_panel);self.summary_panel.setVisible(self.role=="manager")
    def _build_filters(self):
        toolbar_layout=self.toolbar.layout();toolbar_layout.removeWidget(self.toolbar.refresh_button);self.filter_button=QPushButton("סינון");toolbar_layout.addWidget(self.filter_button);toolbar_layout.addWidget(self.toolbar.refresh_button)
        self.filter_panel=QWidget();layout=QHBoxLayout(self.filter_panel);layout.setDirection(QHBoxLayout.Direction.RightToLeft);layout.setContentsMargins(0,SPACE_2,0,0)
        self.status_filter=QComboBox();self.status_filter.addItem("כל הסטטוסים","")
        for value,label in (("NEW","ממתינה לאישור"),("CONFIRMED","מאושרת"),("COMPLETED","הושלמה"),("CANCELLED","בוטלה")):self.status_filter.addItem(label,value)
        self.from_filter=QLineEdit();self.from_filter.setPlaceholderText("מתאריך YYYY-MM-DD");self.to_filter=QLineEdit();self.to_filter.setPlaceholderText("עד תאריך YYYY-MM-DD");self.apply_filters_button=QPushButton("החלת סינון")
        for widget in (self.status_filter,self.from_filter,self.to_filter,self.apply_filters_button):layout.addWidget(widget)
        layout.addStretch();self.toolbar.parentWidget().layout().addWidget(self.filter_panel);self.filter_panel.hide();self.filter_summary=QLabel();self.filter_summary.setAlignment(Qt.AlignmentFlag.AlignRight);self.toolbar.parentWidget().layout().addWidget(self.filter_summary);self.filter_summary.hide()
        self.customer_filter=QComboBox();self.activity_filter=QComboBox();self.instructor_filter=QComboBox()
    def _build_details(self):
        self.edit_button=self.workspace.add_action("עריכת פרטים");self.confirm_button=self.workspace.add_action("אישור הזמנה");self.complete_button=self.workspace.add_action("סימון כהושלמה");self.cancel_button=self.workspace.add_action("ביטול הזמנה",destructive=True)
        self.booking_details=self.workspace.add_card("פרטי הזמנה");self.customer_details=self.workspace.add_card("לקוח");self.system_details=self.workspace.add_card("מידע מערכת")
        self.assignment_group=QFrame();self.assignment_group.setObjectName("detailPanel");assignment_layout=QVBoxLayout(self.assignment_group);assignment_layout.setContentsMargins(SPACE_4,SPACE_4,SPACE_4,SPACE_4);heading=QLabel("שיבוץ מדריך");heading.setObjectName("sectionTitle");heading.setAlignment(Qt.AlignmentFlag.AlignRight);assignment_layout.addWidget(heading);self.assignment_hint=QLabel("בחרו פעילות בהזמנה כדי לנהל את השיבוץ.");self.assignment_hint.setAlignment(Qt.AlignmentFlag.AlignRight);assignment_layout.addWidget(self.assignment_hint);self.assignment_state=RetryState();self.assignment_state.hide();assignment_layout.addWidget(self.assignment_state);self.assignment_tree=QTreeWidget();self.assignment_tree.setHeaderLabels(["פעילות / מדריך","מצב","עיר"]);self.assignment_tree.setLayoutDirection(Qt.LayoutDirection.RightToLeft);self.assignment_tree.itemSelectionChanged.connect(self._assignment_selection);assignment_layout.addWidget(self.assignment_tree);actions=QHBoxLayout();actions.setDirection(QHBoxLayout.Direction.RightToLeft);self.assign_button=QPushButton("שיבוץ מדריך");self.assign_and_confirm_button=QPushButton("שיבוץ ואישור");self.remove_assignment_button=QPushButton("הסרת שיבוץ");actions.addWidget(self.assign_button);actions.addWidget(self.assign_and_confirm_button);actions.addWidget(self.remove_assignment_button);actions.addStretch();assignment_layout.addLayout(actions);self.workspace.details_widget.layout().insertWidget(self.workspace.details_widget.layout().count()-1,self.assignment_group);self.assignment_group.setVisible(self.role=="manager");self.assign_button.clicked.connect(self._emit_assign);self.assign_and_confirm_button.clicked.connect(self._emit_assign_and_confirm);self.remove_assignment_button.clicked.connect(self._emit_remove)
        for button in (self.assign_button,self.assign_and_confirm_button,self.remove_assignment_button):button.setEnabled(False)
        self.history_group=QFrame();self.history_group.setObjectName("detailPanel");history_layout=QVBoxLayout(self.history_group);history_heading=QLabel("היסטוריית שינויים");history_heading.setObjectName("sectionTitle");history_heading.setAlignment(Qt.AlignmentFlag.AlignRight);history_layout.addWidget(history_heading);self.history_table=QTableWidget(0,4);self.history_table.setHorizontalHeaderLabels(["אירוע","סיכום","מועד","מבצע"]);history_layout.addWidget(self.history_table);self.workspace.details_widget.layout().insertWidget(self.workspace.details_widget.layout().count()-1,self.history_group);self.history_group.setVisible(self.role=="manager")
    def eventFilter(self,watched,event):
        if watched is self.table and event.type()==QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter):self._open();return True
        return super().eventFilter(watched,event)
    def _row_id(self,row):return str(self.table.item(row,1).data(Qt.ItemDataRole.UserRole))
    def _select(self):
        rows=self.table.selectionModel().selectedRows()
        if not rows:self._selected_id=None;return
        booking_id=self._row_id(rows[0].row());changed=booking_id!=self._selected_id;self._selected_id=booking_id
        if changed:self._clear_forms();self.workspace.detail_title.clear();self.workspace.show_list();self.booking_selected.emit(booking_id)
    def _open(self):
        if self._selected_id:self._pending_open_id=self._selected_id
        if self._selected_id and self.workspace.detail_title.text():self._pending_open_id=None;self.workspace.show_details()
    def _request_open(self,booking_id):self._pending_open_id=booking_id;self.select_booking(booking_id);self._open()
    def _emit_filters(self,search=None):
        values={"status":self.status_filter.currentData(),"from_date":self.from_filter.text().strip(),"to_date":self.to_filter.text().strip(),"search":search if search is not None else self.toolbar.search_input.text().strip(),"order_by":"event_at","limit":self.footer.limit,"offset":0};parts=[self.status_filter.currentText()] if self.status_filter.currentData() else [];self.filter_summary.setText("מסננים פעילים: "+" · ".join(parts));self.filter_summary.setVisible(bool(parts));self.filters_requested.emit(values)
    def _reset(self,emit=True):
        self.toolbar.search_input.clear();self.status_filter.setCurrentIndex(0);self.from_filter.clear();self.to_filter.clear();self.filter_panel.hide();self.filter_summary.hide();self.table.clearSelection();self.clear_details()
        if emit:self.filters_requested.emit({"status":None,"from_date":None,"to_date":None,"search":None,"order_by":"event_at","limit":25,"offset":0,"_clear_selection":True})
    def reset_to_default(self):
        self._reset(False)
    def show_summary(self,summary):
        values={"pending":summary.get("pending_count",0),"unassigned":summary.get("unassigned_count",0),"approved":summary.get("confirmed_count",0)}
        titles={"pending":"ממתינות לאישור","unassigned":"ממתינות לשיבוץ מדריך","approved":"מאושרות"}
        for key,value in values.items():self.summary_buttons[key].setText(f"{titles[key]}\n{value}")
    def show_bookings(self,rows,*,offset=0,count=0,limit=25,selected_id=None):
        self.table.setRowCount(len(rows))
        for r,row in enumerate(rows):
            self.workspace.set_row_open_action(r,row["id"],self._request_open);values=(row.get("customer","—"),row.get("activity","—"),row.get("event_at","—")," · ".join(x for x in (row.get("city"),row.get("venue")) if x and x!="—") or "—",row.get("participants","—"))
            for c,value in enumerate(values,start=1):item=QTableWidgetItem(str(value));item.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignAbsolute);set_item_text(self.table,r,c,item,tooltip_direction=Qt.LayoutDirection.RightToLeft);item.setData(Qt.ItemDataRole.UserRole,row["id"] if c==1 else item.data(Qt.ItemDataRole.UserRole))
            status=QLabel(str(row.get("status") or "—"));status.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignAbsolute);status.setContentsMargins(SPACE_3,0,SPACE_3,0);status.setProperty("bookingState",str(row.get("status_code") or ""));self.table.setCellWidget(r,6,status)
        self.footer.limit=limit;self.footer.set_page(offset=offset,count=count);self._empty_filtered=bool(self.toolbar.search_input.text() or self.status_filter.currentData());self.workspace.show_empty_state(empty=not rows,filtered=self._empty_filtered,plural="הזמנות");self.footer.setVisible(bool(rows));self.workspace.results_label.setText(f"הזמנות • {len(rows)}")
    def show_filter_options(self,customers,activities,instructors):pass
    def show_details(self,details,history):
        self._clear_forms();identity="פרטי הזמנה";status=""
        for label,value in details:
            if label=="לקוח":identity=value
            if label=="סטטוס":status=value
            content=QLabel(value);content.setWordWrap(True);target=self.customer_details if label=="לקוח" else self.system_details if label in {"מזהה","סטטוס"} else self.booking_details;self.workspace.add_property_row(target,label,content)
        self.workspace.detail_title.setText(identity);self.workspace.detail_status.setText(status);self.workspace.detail_subtitle.setText("מצב תפעולי, שיבוץ והיסטוריית ההזמנה");self.history_table.setRowCount(len(history))
        for r,event in enumerate(history):
            for c,key in enumerate(("event_type","summary","occurred_at","actor")):self.history_table.setItem(r,c,QTableWidgetItem(event[key]))
        if self._pending_open_id==self._selected_id:self._pending_open_id=None;self.workspace.show_details()
    def _clear_forms(self):
        for form in (self.booking_details,self.customer_details,self.system_details):
            while form.rowCount():form.removeRow(0)
    def clear_details(self):
        if hasattr(self,"booking_details"):self._clear_forms();self.workspace.detail_title.clear();self.workspace.show_list();self.workspace.set_actions_enabled(False);self.assignment_tree.clear()
        self._selected_id=None;self._pending_open_id=None
    def select_booking(self,booking_id):
        for row in range(self.table.rowCount()):
            if self._row_id(row)==booking_id:
                changed=self._selected_id!=booking_id;blocked=self.table.blockSignals(True);index=self.table.model().index(row,1);self.table.selectionModel().setCurrentIndex(index,QItemSelectionModel.SelectionFlag.ClearAndSelect|QItemSelectionModel.SelectionFlag.Rows);self.table.blockSignals(blocked);self._selected_id=booking_id
                if changed:self.booking_selected.emit(booking_id)
                break
    def set_command_availability(self,status):
        terminal=status in {"COMPLETED","CANCELLED"};self.edit_button.setVisible(self.role=="manager" and not terminal);self.confirm_button.setVisible(self.role=="manager" and status=="NEW");self.cancel_button.setVisible(self.role=="manager" and not terminal);self.complete_button.setVisible(self.role=="manager" and status in {"NEW","CONFIRMED"});self.edit_button.setEnabled(not terminal);self.confirm_button.setEnabled(status=="NEW");self.cancel_button.setEnabled(not terminal);self.complete_button.setEnabled(status in {"NEW","CONFIRMED"});self.assign_and_confirm_button.setVisible(status=="NEW")
    def set_loading(self,value):self.toolbar.setEnabled(not value);self.create_button.setEnabled(not value)
    def show_error(self,message,**_kwargs):self.scaffold.feedback.render(RequestState(RequestPhase.SERVER_ERROR,message,"bookings"))
    def show_success(self,message):self.scaffold.feedback.render(RequestState(RequestPhase.SUCCESS,message,"bookings"))
    def set_assignments_loading(self,value):self.assignment_group.setEnabled(not value)
    def show_assignments_error(self,message,*,retriable=False):self.assignment_state.show_message(message,retriable=retriable)
    def show_assignments(self,activities):
        self.assignment_state.hide();self.assignment_tree.clear()
        for activity in activities:
            top=QTreeWidgetItem([activity["activity_name"],"נדרש שיבוץ" if activity["assignment_required"] and not activity["assignments"] else "משויך" if activity["assignments"] else "לא נדרש",""]);top.setData(0,Qt.ItemDataRole.UserRole,{"activity":activity});self.assignment_tree.addTopLevelItem(top)
            for assignment in activity["assignments"]:child=QTreeWidgetItem([assignment["instructor_name"],"שיבוץ פעיל",assignment.get("instructor_city") or "—"]);child.setData(0,Qt.ItemDataRole.UserRole,{"activity":activity,"assignment":assignment});top.addChild(child)
            top.setExpanded(True)
    def _assignment_selection(self):
        items=self.assignment_tree.selectedItems();data=items[0].data(0,Qt.ItemDataRole.UserRole) if items else {};activity=data.get("activity") or {};self.assign_button.setEnabled(bool(activity and activity.get("assignment_required")));self.assign_and_confirm_button.setEnabled(bool(activity));self.remove_assignment_button.setEnabled(bool(data.get("assignment")))
    def _emit_assign(self):
        items=self.assignment_tree.selectedItems()
        if items:self.assignment_add_requested.emit(items[0].data(0,Qt.ItemDataRole.UserRole)["activity"])
    def _emit_assign_and_confirm(self):
        items=self.assignment_tree.selectedItems()
        if items:self.assignment_add_and_confirm_requested.emit(items[0].data(0,Qt.ItemDataRole.UserRole)["activity"])
    def _emit_remove(self):
        items=self.assignment_tree.selectedItems();data=items[0].data(0,Qt.ItemDataRole.UserRole) if items else {}
        if data.get("assignment"):self.assignment_remove_requested.emit(data["activity"],data["assignment"])
    def open_instructor_selector(self,activity,query_handler,choose_handler):self._selector=InstructorSelectorDialog(activity,query_handler,choose_handler,self);self._selector.open();return self._selector
    def confirm_assignment_removal(self,instructor_name,activity_name):return confirm_action(self,"הסרת שיבוץ",f"להסיר את {instructor_name} מהפעילות {activity_name}? היסטוריית האירועים תישמר.")
    def collect_create_booking(self,customers,activities,instructors,*,role="manager",preselected_activity_id=None):
        dialog=BookingFormDialog(customers=customers,activities=activities,instructors=instructors,role=role,preselected_activity_id=preselected_activity_id,parent=self);return dialog.values() if dialog.exec()==dialog.DialogCode.Accepted else None
    def collect_booking_changes(self,booking):
        dialog=BookingFormDialog(booking=booking,parent=self);return dialog.values() if dialog.exec()==dialog.DialogCode.Accepted else None
    def confirm_cancellation(self):return confirm_action(self,"אישור ביטול","לבטל את ההזמנה? היסטוריית ההזמנה תישמר.")
    def confirm_completion(self):return confirm_action(self,"השלמת הזמנה","לסמן את ההזמנה כהושלמה?")
