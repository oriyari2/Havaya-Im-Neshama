from __future__ import annotations

from PySide6.QtCore import QEvent, QItemSelectionModel, Qt, Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QTableWidget, QTableWidgetItem, QToolButton, QVBoxLayout, QWidget

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.views.assignment_dialogs import InstructorSelectorDialog
from desktop_client.app.views.booking_dialogs import BookingFormDialog
from desktop_client.app.views.common import StatefulWidget
from desktop_client.app.views.design_tokens import SPACE_2, SPACE_3, SPACE_4
from desktop_client.app.views.management_common import RetryState, confirm_action
from desktop_client.app.views.management_workspace import ManagementWorkspace
from desktop_client.app.views.ui_foundations import ColumnKind, ColumnPolicy, set_item_text


class BookingsView(StatefulWidget):
    filters_requested=Signal(dict);booking_selected=Signal(str);create_requested=Signal();edit_requested=Signal();confirm_requested=Signal();cancel_requested=Signal();complete_requested=Signal();page_requested=Signal(int,int);assignment_add_requested=Signal(dict);assignment_add_and_confirm_requested=Signal(dict);assignment_replace_requested=Signal(dict,dict);assignment_remove_requested=Signal(dict,dict);queue_requested=Signal(str)
    def __init__(self, role):
        super().__init__();self.role=role;self._selected_id=None;self._pending_open_id=None;self._empty_filtered=False
        root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0)
        self.workspace=ManagementWorkspace(title="ניהול הזמנות" if role=="manager" else "ההזמנות שלי" if role=="customer" else "האירועים שלי",subtitle="מעקב אחר הזמנות, אישורים ושיבוץ מדריכים",create_text="הזמנה חדשה" if role=="manager" else "בקשת הזמנה חדשה",plural="הזמנות",detail_subtitle="מצב תפעולי ופרטי ההזמנה",search_placeholder="חיפוש ברשימת ההזמנות",sort_options=(("event_at","מיון לפי: מועד"),("customer_name","מיון לפי: שם לקוח")),headers=("לקוח","פעילות","מועד","מיקום","משתתפים","מצב"),policies=(ColumnPolicy(ColumnKind.PRIMARY_TEXT,180),ColumnPolicy(ColumnKind.PRIMARY_TEXT,190),ColumnPolicy(ColumnKind.TECHNICAL,160),ColumnPolicy(ColumnKind.SECONDARY_TEXT,170,240),ColumnPolicy(ColumnKind.COMPACT,100),ColumnPolicy(ColumnKind.COMPACT,130)))
        root.addWidget(self.workspace)
        for name in ("scaffold","toolbar","table","footer","create_button","pages","list_page","details_page","back_button"):setattr(self,name,getattr(self.workspace,name))
        self.pagination=self.footer;self.command_panel=self.workspace.actions_container;self.actions=self.command_panel;self.create_button.setVisible(role in {"manager","customer"})
        self._build_summary();self._build_filters();self._build_details()
        self.command_panel.setVisible(role=="manager")
        self.create_button.clicked.connect(self.create_requested);self.edit_button.clicked.connect(self.edit_requested);self.confirm_button.clicked.connect(self.confirm_requested);self.cancel_button.clicked.connect(self.cancel_requested);self.complete_button.clicked.connect(self.complete_requested)
        self.toolbar.search_requested.connect(lambda search,_sort:self._emit_filters(search=search));self.toolbar.sort_combo.currentIndexChanged.connect(lambda _i:self._emit_filters());self.toolbar.refresh_requested.connect(self._reset);self.apply_filters_button.clicked.connect(self._apply_popover_filters);self.clear_filters_button.clicked.connect(self._clear_and_apply_filters);self.filter_button.clicked.connect(self._toggle_filter_popover);self.footer.page_requested.connect(self.page_requested)
        self.table.itemSelectionChanged.connect(self._select);self.table.cellDoubleClicked.connect(lambda row,_column:self._request_open(self._row_id(row)));self.table.installEventFilter(self);self.workspace.empty_action_button.clicked.connect(lambda:self._reset() if self._empty_filtered else self.create_requested.emit());self.clear_details()
    def _build_summary(self):
        self.summary_panel=QWidget();layout=QHBoxLayout(self.summary_panel);layout.setDirection(QHBoxLayout.Direction.RightToLeft);layout.setContentsMargins(0,0,0,0);layout.setSpacing(SPACE_3);self.summary_buttons={}
        for key,title in (("pending","ממתינות לאישור"),("unassigned","ממתינות לשיבוץ מדריך"),("approved","מאושרות")):
            button=QPushButton(f"{title}\n0");button.setProperty("summaryQueue",key);button.setMinimumHeight(68);button.clicked.connect(lambda _checked=False,value=key:self.queue_requested.emit(value));layout.addWidget(button);self.summary_buttons[key]=button
        self.list_page.layout().insertWidget(0,self.summary_panel);self.summary_panel.setVisible(self.role=="manager")
    def _build_filters(self):
        toolbar_layout=self.toolbar.layout();toolbar_layout.removeWidget(self.toolbar.refresh_button);self.filter_button=QPushButton("סינון");toolbar_layout.addWidget(self.filter_button);toolbar_layout.addWidget(self.toolbar.refresh_button)
        toolbar_panel=self.toolbar.parentWidget();self.filter_popover=QFrame(self.list_page);self.filter_popover.setObjectName("filterPopover");self.filter_popover.setLayoutDirection(Qt.LayoutDirection.RightToLeft);self.filter_popover.setFixedWidth(340);popover=QVBoxLayout(self.filter_popover);popover.setContentsMargins(SPACE_4,SPACE_3,SPACE_4,SPACE_3);popover.setSpacing(SPACE_2)
        self.status_checks={};status_body=QWidget();status_layout=QVBoxLayout(status_body);status_layout.setContentsMargins(0,0,SPACE_3,0);status_layout.setSpacing(SPACE_2)
        for value,label in (("NEW","חדש / ממתין לאישור"),("CONFIRMED","מאושר"),("CANCELLED","בוטל"),("COMPLETED","הושלם")):
            check=QCheckBox(label);check.setLayoutDirection(Qt.LayoutDirection.RightToLeft);check.toggled.connect(lambda checked,key=value:self._exclusive_filter(self.status_checks,key,checked));status_layout.addWidget(check);self.status_checks[value]=check
        self._add_filter_section(popover,"סטטוס",status_body)
        assignment_body=QWidget();assignment_layout=QVBoxLayout(assignment_body);assignment_layout.setContentsMargins(0,0,SPACE_3,0);self.unassigned_check=QCheckBox("דורש שיבוץ");assignment_layout.addWidget(self.unassigned_check);self._add_filter_section(popover,"שיבוץ מדריך",assignment_body)
        date_body=QWidget();date_layout=QVBoxLayout(date_body);date_layout.setContentsMargins(0,0,SPACE_3,0);self.from_filter=QLineEdit();self.from_filter.setPlaceholderText("מתאריך YYYY-MM-DD");self.to_filter=QLineEdit();self.to_filter.setPlaceholderText("עד תאריך YYYY-MM-DD");date_layout.addWidget(self.from_filter);date_layout.addWidget(self.to_filter);self._add_filter_section(popover,"טווח תאריכים",date_body)
        self.activity_checks={};self.activity_body=QWidget();self.activity_layout=QVBoxLayout(self.activity_body);self.activity_layout.setContentsMargins(0,0,SPACE_3,0);self.activity_empty=QLabel("אין פעילויות זמינות");self.activity_empty.setAlignment(Qt.AlignmentFlag.AlignRight);self.activity_layout.addWidget(self.activity_empty);activity_scroll=QScrollArea();activity_scroll.setWidgetResizable(True);activity_scroll.setFrameShape(QScrollArea.Shape.NoFrame);activity_scroll.setMaximumHeight(150);activity_scroll.setWidget(self.activity_body);self._add_filter_section(popover,"פעילות",activity_scroll)
        actions=QHBoxLayout();actions.setDirection(QHBoxLayout.Direction.RightToLeft);self.apply_filters_button=QPushButton("החלת סינון");self.apply_filters_button.setProperty("buttonRole","managementPrimary");self.clear_filters_button=QPushButton("ניקוי הכול");actions.addWidget(self.apply_filters_button);actions.addWidget(self.clear_filters_button);popover.addLayout(actions);self.filter_popover.hide()
        self.chips=QWidget();self.chips_layout=QHBoxLayout(self.chips);self.chips_layout.setDirection(QHBoxLayout.Direction.RightToLeft);self.chips_layout.setContentsMargins(0,0,0,0);self.chips_layout.setSpacing(SPACE_2);self.chips_layout.addStretch();toolbar_panel.layout().addWidget(self.chips);self.chips.hide()
        self.status_filter=QComboBox();self.customer_filter=QComboBox();self.activity_filter=QComboBox();self.instructor_filter=QComboBox()
    def _add_filter_section(self,layout,title,body):
        toggle=QToolButton();toggle.setText(title);toggle.setCheckable(True);toggle.setChecked(True);toggle.setArrowType(Qt.ArrowType.DownArrow);toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon);toggle.setLayoutDirection(Qt.LayoutDirection.RightToLeft);toggle.clicked.connect(lambda checked,w=body,b=toggle:(w.setVisible(checked),b.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.LeftArrow)));layout.addWidget(toggle);layout.addWidget(body)
    @staticmethod
    def _exclusive_filter(group,key,checked):
        if not checked:return
        for value,widget in group.items():
            if value!=key:
                blocked=widget.blockSignals(True);widget.setChecked(False);widget.blockSignals(blocked)
    def _toggle_filter_popover(self):
        if self.filter_popover.isVisible():self.filter_popover.hide();return
        point=self.filter_button.mapTo(self.filter_popover.parentWidget(),self.filter_button.rect().bottomRight());self.filter_popover.adjustSize();parent=self.filter_popover.parentWidget();x=max(0,min(point.x()-self.filter_popover.width(),parent.width()-self.filter_popover.width()));y=max(0,min(point.y()+SPACE_2,parent.height()-self.filter_popover.height()-SPACE_2));self.filter_popover.move(x,y);self.filter_popover.raise_();self.filter_popover.show()
    def _build_details(self):
        self.edit_button=self.workspace.add_action("עריכת פרטים");self.confirm_button=self.workspace.add_action("אישור הזמנה");self.complete_button=self.workspace.add_action("סימון כהושלמה");self.cancel_button=self.workspace.add_action("ביטול הזמנה",destructive=True)
        self.booking_details=self.workspace.add_card("פרטי הזמנה");self.customer_details=self.workspace.add_card("לקוח");self.system_details=self.workspace.add_card("מידע מערכת")
        self.assignment_group=QFrame();self.assignment_group.setObjectName("detailPanel");assignment_layout=QVBoxLayout(self.assignment_group);assignment_layout.setContentsMargins(SPACE_4,SPACE_4,SPACE_4,SPACE_4);assignment_layout.setSpacing(SPACE_3);heading=QLabel("שיבוץ מדריך");heading.setObjectName("sectionTitle");heading.setAlignment(Qt.AlignmentFlag.AlignRight);assignment_layout.addWidget(heading);self.assignment_hint=QLabel("מצב השיבוץ לפעילויות בהזמנה");self.assignment_hint.setAlignment(Qt.AlignmentFlag.AlignRight);assignment_layout.addWidget(self.assignment_hint);self.assignment_state=RetryState();self.assignment_state.hide();assignment_layout.addWidget(self.assignment_state);self.assignment_cards=QWidget();self.assignment_cards_layout=QVBoxLayout(self.assignment_cards);self.assignment_cards_layout.setContentsMargins(0,0,0,0);self.assignment_cards_layout.setSpacing(SPACE_2);assignment_layout.addWidget(self.assignment_cards);self.workspace.details_widget.layout().insertWidget(self.workspace.details_widget.layout().count()-1,self.assignment_group);self.assignment_group.setVisible(self.role=="manager")
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
    def _selected_filter(self,group):
        return next((key for key,widget in group.items() if widget.isChecked()),None)
    def _emit_filters(self,search=None):
        status=self._selected_filter(self.status_checks);activity=self._selected_filter(self.activity_checks);values={"status":status,"activity_id":activity,"from_date":self.from_filter.text().strip(),"to_date":self.to_filter.text().strip(),"search":search if search is not None else self.toolbar.search_input.text().strip(),"order_by":str(self.toolbar.sort_combo.currentData() or "event_at"),"limit":self.footer.limit,"offset":0};self._render_filter_chips();self.filters_requested.emit(values)
    def _apply_popover_filters(self):
        self.filter_popover.hide()
        if self.unassigned_check.isChecked():
            for widget in (*self.status_checks.values(),*self.activity_checks.values()):widget.setChecked(False)
            self.from_filter.clear();self.to_filter.clear();self._render_filter_chips();self.queue_requested.emit("unassigned")
        else:self._emit_filters()
    def _clear_filter_choices(self):
        for widget in (*self.status_checks.values(),*self.activity_checks.values(),self.unassigned_check):widget.setChecked(False)
        self.from_filter.clear();self.to_filter.clear();self._render_filter_chips()
    def _clear_and_apply_filters(self):
        self._clear_filter_choices();self.filter_popover.hide();self._emit_filters()
    def _render_filter_chips(self):
        while self.chips_layout.count()>1:
            item=self.chips_layout.takeAt(0)
            if item.widget():item.widget().deleteLater()
        entries=[];status=self._selected_filter(self.status_checks);activity=self._selected_filter(self.activity_checks)
        if status:entries.append((self.status_checks[status].text(),lambda:self._remove_filter("status",status)))
        if self.unassigned_check.isChecked():entries.append((self.unassigned_check.text(),lambda:self._remove_filter("unassigned",None)))
        if activity:entries.append((self.activity_checks[activity].text(),lambda:self._remove_filter("activity",activity)))
        if self.from_filter.text().strip():entries.append((f"מ־{self.from_filter.text().strip()}",lambda:self._remove_filter("from",None)))
        if self.to_filter.text().strip():entries.append((f"עד {self.to_filter.text().strip()}",lambda:self._remove_filter("to",None)))
        for text,callback in entries:
            chip=QToolButton();chip.setText(f"{text}  ×");chip.setProperty("filterChip",True);chip.clicked.connect(callback);self.chips_layout.insertWidget(self.chips_layout.count()-1,chip)
        self.chips.setVisible(bool(entries))
    def _remove_filter(self,kind,key):
        if kind=="status":self.status_checks[key].setChecked(False)
        elif kind=="activity":self.activity_checks[key].setChecked(False)
        elif kind=="unassigned":self.unassigned_check.setChecked(False)
        elif kind=="from":self.from_filter.clear()
        elif kind=="to":self.to_filter.clear()
        self._emit_filters()
    def _reset(self,emit=True):
        self.toolbar.search_input.clear();blocked=self.toolbar.sort_combo.blockSignals(True);self.toolbar.sort_combo.setCurrentIndex(0);self.toolbar.sort_combo.blockSignals(blocked);self._clear_filter_choices();self.filter_popover.hide();self.table.clearSelection();self.clear_details()
        if emit:self.filters_requested.emit({"status":None,"activity_id":None,"from_date":None,"to_date":None,"search":None,"order_by":"event_at","limit":25,"offset":0,"_clear_selection":True})
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
        self.footer.limit=limit;self.footer.set_page(offset=offset,count=count);self._empty_filtered=bool(self.toolbar.search_input.text() or self._selected_filter(self.status_checks) or self._selected_filter(self.activity_checks) or self.unassigned_check.isChecked() or self.from_filter.text() or self.to_filter.text());self.workspace.show_empty_state(empty=not rows,filtered=self._empty_filtered,plural="הזמנות");self.footer.setVisible(bool(rows));self.workspace.results_label.setText(f"הזמנות • {len(rows)}")
    def show_filter_options(self,customers,activities,instructors):
        while self.activity_layout.count()>1:
            item=self.activity_layout.takeAt(0)
            if item.widget():item.widget().deleteLater()
        self.activity_checks={}
        for activity in activities:
            key=str(activity["id"]);check=QCheckBox(str(activity.get("name") or key));check.setLayoutDirection(Qt.LayoutDirection.RightToLeft);check.toggled.connect(lambda checked,value=key:self._exclusive_filter(self.activity_checks,value,checked));self.activity_layout.insertWidget(self.activity_layout.count()-1,check);self.activity_checks[key]=check
        self.activity_empty.setVisible(not bool(activities))
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
        if hasattr(self,"booking_details"):self._clear_forms();self.workspace.detail_title.clear();self.workspace.show_list();self.workspace.set_actions_enabled(False);self._clear_assignment_cards()
        self._selected_id=None;self._pending_open_id=None
    def select_booking(self,booking_id):
        for row in range(self.table.rowCount()):
            if self._row_id(row)==booking_id:
                changed=self._selected_id!=booking_id;blocked=self.table.blockSignals(True);index=self.table.model().index(row,1);self.table.selectionModel().setCurrentIndex(index,QItemSelectionModel.SelectionFlag.ClearAndSelect|QItemSelectionModel.SelectionFlag.Rows);self.table.blockSignals(blocked);self._selected_id=booking_id
                if changed:self.booking_selected.emit(booking_id)
                break
    def set_command_availability(self,status):
        terminal=status in {"COMPLETED","CANCELLED"};self.edit_button.setVisible(self.role=="manager" and not terminal);self.confirm_button.setVisible(self.role=="manager" and status=="NEW");self.cancel_button.setVisible(self.role=="manager" and not terminal);self.complete_button.setVisible(self.role=="manager" and status in {"NEW","CONFIRMED"});self.edit_button.setEnabled(not terminal);self.confirm_button.setEnabled(status=="NEW");self.cancel_button.setEnabled(not terminal);self.complete_button.setEnabled(status in {"NEW","CONFIRMED"})
    def set_loading(self,value):self.toolbar.setEnabled(not value);self.create_button.setEnabled(not value)
    def show_error(self,message,**_kwargs):self.scaffold.feedback.render(RequestState(RequestPhase.SERVER_ERROR,message,"bookings"))
    def show_success(self,message):self.scaffold.feedback.render(RequestState(RequestPhase.SUCCESS,message,"bookings"))
    def set_assignments_loading(self,value):self.assignment_group.setEnabled(not value)
    def show_assignments_error(self,message,*,retriable=False):self.assignment_state.show_message(message,retriable=retriable)
    def show_assignments(self,activities):
        self.assignment_state.hide();self._clear_assignment_cards()
        for activity in activities:self._add_assignment_card(activity)
    def _clear_assignment_cards(self):
        if not hasattr(self,"assignment_cards_layout"):return
        while self.assignment_cards_layout.count():
            item=self.assignment_cards_layout.takeAt(0)
            if item.widget():item.widget().deleteLater()
    def _add_assignment_card(self,activity):
        card=QFrame();card.setObjectName("assignmentCard");row=QHBoxLayout(card);row.setDirection(QHBoxLayout.Direction.RightToLeft);row.setContentsMargins(SPACE_3,SPACE_2,SPACE_3,SPACE_2);row.setSpacing(SPACE_2);identity=QVBoxLayout();name=QLabel(activity["activity_name"]);name.setObjectName("sectionTitle");name.setAlignment(Qt.AlignmentFlag.AlignRight);identity.addWidget(name);assignments=activity.get("assignments") or []
        if not activity.get("assignment_required"):
            status=QLabel("לא נדרש מדריך");status.setProperty("assignmentState","neutral");identity.addWidget(status);row.addLayout(identity);row.addStretch();self.assignment_cards_layout.addWidget(card);return
        assignment=assignments[0] if assignments else None;status=QLabel("משובץ" if assignment else "ממתין לשיבוץ");status.setProperty("assignmentState","assigned" if assignment else "waiting");status.setAlignment(Qt.AlignmentFlag.AlignRight);identity.addWidget(status);description=QLabel(assignment.get("instructor_name") if assignment else "לא שובץ מדריך");description.setAlignment(Qt.AlignmentFlag.AlignRight);identity.addWidget(description);row.addLayout(identity);row.addStretch()
        if assignment:
            replace=QPushButton("החלפת מדריך");remove=QPushButton("הסרת שיבוץ");replace.clicked.connect(lambda _checked=False,a=activity,current=assignment:self.assignment_replace_requested.emit(a,current));remove.clicked.connect(lambda _checked=False,a=activity,current=assignment:self.assignment_remove_requested.emit(a,current));row.addWidget(replace);row.addWidget(remove)
        else:
            assign=QPushButton("שיבוץ מדריך");assign.setProperty("buttonRole","managementPrimary");assign.clicked.connect(lambda _checked=False,value=activity:self.assignment_add_requested.emit(value));row.addWidget(assign)
        self.assignment_cards_layout.addWidget(card)
    def open_instructor_selector(self,activity,query_handler,choose_handler):self._selector=InstructorSelectorDialog(activity,query_handler,choose_handler,self);self._selector.open();return self._selector
    def confirm_assignment_removal(self,instructor_name,activity_name):return confirm_action(self,"הסרת שיבוץ",f"להסיר את {instructor_name} מהפעילות {activity_name}? היסטוריית האירועים תישמר.")
    def collect_create_booking(self,customers,activities,instructors,*,role="manager",preselected_activity_id=None):
        dialog=BookingFormDialog(customers=customers,activities=activities,instructors=instructors,role=role,preselected_activity_id=preselected_activity_id,parent=self);return dialog.values() if dialog.exec()==dialog.DialogCode.Accepted else None
    def collect_booking_changes(self,booking):
        dialog=BookingFormDialog(booking=booking,parent=self);return dialog.values() if dialog.exec()==dialog.DialogCode.Accepted else None
    def confirm_cancellation(self):return confirm_action(self,"אישור ביטול","לבטל את ההזמנה? היסטוריית ההזמנה תישמר.")
    def confirm_completion(self):return confirm_action(self,"השלמת הזמנה","לסמן את ההזמנה כהושלמה?")
