from __future__ import annotations

from PySide6.QtCore import QEvent, QItemSelectionModel, Qt, Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QFrame, QHeaderView, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QToolButton, QVBoxLayout, QWidget

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.features.bookings.assignment_dialogs import InstructorSelectorDialog
from desktop_client.app.features.bookings.dialogs import BookingFormDialog
from desktop_client.app.shared.ui.common import StatefulWidget
from desktop_client.app.shared.ui.design_tokens import SPACE_2, SPACE_3, SPACE_4
from desktop_client.app.shared.ui.filter_popup import FloatingFilterPopup
from desktop_client.app.shared.ui.management_common import RetryState, confirm_action
from desktop_client.app.shared.ui.management_workspace import ManagementWorkspace
from desktop_client.app.shared.ui.management_visuals import apply_reference_detail_layout, apply_reference_list_layout, install_management_hero, style_reference_button, style_reference_extra_panel
from desktop_client.app.shared.ui.foundations import ColumnKind, ColumnPolicy, set_item_text


class BookingsView(StatefulWidget):
    filters_requested=Signal(dict);booking_selected=Signal(str);create_requested=Signal();edit_requested=Signal();confirm_requested=Signal();cancel_requested=Signal();complete_requested=Signal();page_requested=Signal(int,int);assignment_add_requested=Signal(dict);assignment_add_and_confirm_requested=Signal(dict);assignment_replace_requested=Signal(dict,dict);assignment_remove_requested=Signal(dict,dict);assignment_request_requested=Signal(dict);assignment_request_approve_requested=Signal(dict,dict);assignment_request_reject_requested=Signal(dict,dict);queue_requested=Signal(str)
    def __init__(self, role):
        super().__init__();self.role=role;self._selected_id=None;self._pending_open_id=None;self._empty_filtered=False;self._list_context=None
        root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0)
        self.workspace=ManagementWorkspace(title="ניהול הזמנות" if role=="manager" else "ההזמנות שלי" if role=="customer" else "האירועים שלי",subtitle="ניהול הזמנות, מועדים, אישורים ושיבוץ מדריכים" if role=="manager" else "מעקב אחר ההזמנות והאירועים שלך" if role=="customer" else "האירועים המשובצים לך ומידע תפעולי",create_text="הזמנה חדשה" if role=="manager" else "בקשת הזמנה חדשה",plural="הזמנות",detail_subtitle="מצב תפעולי ופרטי ההזמנה",search_placeholder="חיפוש ברשימת ההזמנות",sort_options=(("event_at","מיון לפי: מועד, הקרוב ביותר"),("event_at_desc","מיון לפי: מועד, הרחוק ביותר"),("customer_name","מיון לפי: שם לקוח")),headers=("לקוח","פעילות","מועד","מיקום","משתתפים","מצב"),policies=(ColumnPolicy(ColumnKind.PRIMARY_TEXT,180),ColumnPolicy(ColumnKind.PRIMARY_TEXT,190),ColumnPolicy(ColumnKind.TECHNICAL,160),ColumnPolicy(ColumnKind.SECONDARY_TEXT,170,240),ColumnPolicy(ColumnKind.COMPACT,100),ColumnPolicy(ColumnKind.COMPACT,130)),row_action_position="end")
        root.addWidget(self.workspace)
        for name in ("scaffold","toolbar","table","footer","create_button","pages","list_page","details_page","back_button"):setattr(self,name,getattr(self.workspace,name))
        self.pagination=self.footer;self.command_panel=self.workspace.actions_container;self.actions=self.command_panel;self.create_button.setVisible(role in {"manager","customer"})
        self._build_summary();self._build_filters();self._build_details()
        self.command_panel.setVisible(role=="manager")
        hero_image={"manager":"bookings-manager-hero.png","instructor":"bookings-instructor-hero.png","customer":"bookings-customer-hero.png"}.get(role,"bookings-manager-hero.png")
        self.hero=install_management_hero(self.workspace,hero_image,"תמונת פעילות למסך הזמנות ואירועים")
        apply_reference_list_layout(self.workspace,extra_toolbar_controls=(self.filter_button,))
        # Local complete styles avoid global-QSS specificity making primary text white on white.
        style_reference_button(self.toolbar.search_button, "primary")
        style_reference_button(self.filter_button, "secondary")
        style_reference_button(self.toolbar.refresh_button, "secondary")
        style_reference_button(self.filter_popup.apply_button, "primary")
        style_reference_button(self.filter_popup.clear_button, "secondary")
        style_reference_button(self.workspace.empty_action_button, "secondary")
        self.toolbar.search_button.setMinimumWidth(92)
        self.filter_button.setMinimumWidth(88)
        self.toolbar.refresh_button.setMinimumWidth(88)
        self.filter_popup.apply_button.setMinimumWidth(122)
        self.filter_popup.clear_button.setMinimumWidth(122)
        self.workspace.empty_action_button.setMinimumWidth(176)
        back_text="← חזרה לרשימת הזמנות" if role=="manager" else "← חזרה להזמנות שלי" if role=="customer" else "← חזרה לאירועים שלי"
        apply_reference_detail_layout(
            self.workspace,
            back_text=back_text,
            actions=((self.cancel_button,"destructive"),(self.complete_button,"secondary"),(self.confirm_button,"success"),(self.edit_button,"primary")),
            cards=((self.booking_details,"primary"),(self.customer_details,"secondary"),(self.system_details,"system")),
        )
        style_reference_extra_panel(self.assignment_group,role="assignment")
        style_reference_extra_panel(self.history_group,role="history")
        self.history_table.setProperty("managementReferenceTable",True)
        self.history_table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignAbsolute)
        self.create_button.clicked.connect(self.create_requested);self.edit_button.clicked.connect(self.edit_requested);self.confirm_button.clicked.connect(self.confirm_requested);self.cancel_button.clicked.connect(self.cancel_requested);self.complete_button.clicked.connect(self.complete_requested)
        self.toolbar.search_requested.connect(lambda search,_sort:self._emit_filters(search=search));self.toolbar.sort_combo.currentIndexChanged.connect(lambda _i:self._emit_filters());self.toolbar.refresh_requested.connect(self._reset);self.filter_popup.apply_requested.connect(self._apply_popover_filters);self.filter_popup.clear_requested.connect(self._clear_and_apply_filters);self.filter_button.clicked.connect(self.filter_popup.toggle);self.footer.page_requested.connect(self.page_requested)
        self.table.itemSelectionChanged.connect(self._select);self.table.cellDoubleClicked.connect(lambda row,_column:self._request_open(self._row_id(row)));self.table.installEventFilter(self);self.workspace.empty_action_button.clicked.connect(self._empty_action);self.clear_details()
    def _empty_action(self):
        if self._list_context=="open":self.queue_requested.emit("open")
        elif self._empty_filtered:self._reset()
        elif self.role in {"manager","customer"}:self.create_requested.emit()
    def _build_summary(self):
        self.summary_panel=QWidget();layout=QHBoxLayout(self.summary_panel);layout.setDirection(QHBoxLayout.Direction.RightToLeft);layout.setContentsMargins(0,0,0,0);layout.setSpacing(SPACE_3);self.summary_buttons={}
        queues = (("pending","ממתינות לאישור"),("unassigned","ממתינות לשיבוץ מדריך"),("approved","מאושרות")) if self.role == "manager" else (("open","אירועים פתוחים לשיבוץ"),) if self.role == "instructor" else ()
        for key,title in queues:
            initial = f"{title}\n0" if self.role == "manager" else title
            button=QPushButton(initial);button.setProperty("summaryQueue",key);button.setMinimumHeight(52 if self.role == "instructor" else 68);button.clicked.connect(lambda _checked=False,value=key:self.queue_requested.emit(value));style_reference_button(button,"secondary")
            if self.role == "instructor":
                button.setMinimumWidth(220);button.setMaximumWidth(300)
            layout.addWidget(button);self.summary_buttons[key]=button
        if self.role == "instructor" and queues:layout.addStretch(1)
        self.list_page.layout().insertWidget(0,self.summary_panel);self.summary_panel.setVisible(bool(queues))
    def _build_filters(self):
        toolbar_layout=self.toolbar.layout();toolbar_layout.removeWidget(self.toolbar.refresh_button);self.filter_button=QPushButton("סינון");toolbar_layout.addWidget(self.filter_button);toolbar_layout.addWidget(self.toolbar.refresh_button)
        toolbar_panel=self.toolbar.parentWidget();self.filter_popup=FloatingFilterPopup(self.filter_button,self.list_page)
        self.status_checks={};status_body=QWidget();status_layout=QVBoxLayout(status_body);status_layout.setContentsMargins(0,0,SPACE_3,0);status_layout.setSpacing(SPACE_2)
        for value,label in (("NEW","חדש / ממתין לאישור"),("CONFIRMED","מאושר"),("CANCELLED","בוטל"),("COMPLETED","הושלם")):
            check=QCheckBox(label);check.setLayoutDirection(Qt.LayoutDirection.RightToLeft);status_layout.addWidget(check);self.status_checks[value]=check
        self.filter_popup.add_section("סטטוס",status_body)
        assignment_body=QWidget();assignment_layout=QVBoxLayout(assignment_body);assignment_layout.setContentsMargins(0,0,0,0);self.unassigned_check=QCheckBox("דורש שיבוץ");self.assigned_check=QCheckBox("שובץ");assignment_layout.addWidget(self.unassigned_check);assignment_layout.addWidget(self.assigned_check);self.assignment_checks={"unassigned":self.unassigned_check,"assigned":self.assigned_check};self.filter_popup.add_section("שיבוץ מדריך",assignment_body)
        date_body=QWidget();date_layout=QVBoxLayout(date_body);date_layout.setContentsMargins(0,0,0,0);self.from_filter=QLineEdit();self.from_filter.setPlaceholderText("מתאריך YYYY-MM-DD");self.to_filter=QLineEdit();self.to_filter.setPlaceholderText("עד תאריך YYYY-MM-DD");date_layout.addWidget(self.from_filter);date_layout.addWidget(self.to_filter);self.filter_popup.add_section("טווח תאריכים",date_body)
        self.activity_checks={};self.activity_body=QWidget();self.activity_layout=QVBoxLayout(self.activity_body);self.activity_layout.setContentsMargins(0,0,0,0);self.activity_empty=QLabel("אין פעילויות זמינות");self.activity_empty.setAlignment(Qt.AlignmentFlag.AlignRight);self.activity_layout.addWidget(self.activity_empty);self.filter_popup.add_section("פעילות",self.activity_body)
        self.instructor_checks={};self.instructor_body=QWidget();self.instructor_layout=QVBoxLayout(self.instructor_body);self.instructor_layout.setContentsMargins(0,0,0,0);self.instructor_empty=QLabel("אין מדריכים זמינים");self.instructor_empty.setAlignment(Qt.AlignmentFlag.AlignRight);self.instructor_layout.addWidget(self.instructor_empty);self.filter_popup.add_section("מדריכים",self.instructor_body)
        self.apply_filters_button=self.filter_popup.apply_button;self.clear_filters_button=self.filter_popup.clear_button
        self.chips=QWidget();self.chips_layout=QHBoxLayout(self.chips);self.chips_layout.setDirection(QHBoxLayout.Direction.RightToLeft);self.chips_layout.setContentsMargins(0,0,0,0);self.chips_layout.setSpacing(SPACE_2);self.chips_layout.addStretch();toolbar_panel.layout().addWidget(self.chips);self.chips.hide()
        self.status_filter=QComboBox();self.customer_filter=QComboBox();self.activity_filter=QComboBox();self.instructor_filter=QComboBox()
    def _build_details(self):
        self.edit_button=self.workspace.add_action("עריכת פרטים");self.confirm_button=self.workspace.add_action("אישור הזמנה");self.complete_button=self.workspace.add_action("סימון כהושלמה");self.cancel_button=self.workspace.add_action("ביטול הזמנה",destructive=True)
        self.booking_details=self.workspace.add_card("פרטי הזמנה");self.customer_details=self.workspace.add_card("לקוח");self.system_details=self.workspace.add_card("מידע מערכת")
        right = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute

        self.assignment_group = QFrame()
        self.assignment_group.setObjectName("detailPanel")
        self.assignment_group.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        assignment_layout = QVBoxLayout(self.assignment_group)
        assignment_layout.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_3)
        assignment_layout.setSpacing(SPACE_2)

        heading = QLabel("שיבוץ מדריך")
        heading.setObjectName("sectionTitle")
        heading.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        heading.setAlignment(right)
        assignment_layout.addWidget(heading)

        self.assignment_hint = QLabel("מצב השיבוץ לפעילויות בהזמנה")
        self.assignment_hint.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.assignment_hint.setAlignment(right)
        assignment_layout.addWidget(self.assignment_hint)

        self.assignment_state = RetryState()
        self.assignment_state.hide()
        assignment_layout.addWidget(self.assignment_state)

        self.assignment_cards = QWidget()
        self.assignment_cards.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.assignment_cards_layout = QVBoxLayout(self.assignment_cards)
        self.assignment_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.assignment_cards_layout.setSpacing(SPACE_2)
        assignment_layout.addWidget(self.assignment_cards)
        self.workspace.details_widget.layout().insertWidget(
            self.workspace.details_widget.layout().count() - 1, self.assignment_group
        )
        self.assignment_group.setVisible(self.role == "manager")

        self.history_group = QFrame()
        self.history_group.setObjectName("detailPanel")
        self.history_group.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        history_layout = QVBoxLayout(self.history_group)
        history_layout.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_3)
        history_layout.setSpacing(SPACE_2)

        history_heading = QLabel("היסטוריית שינויים")
        history_heading.setObjectName("sectionTitle")
        history_heading.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        history_heading.setAlignment(right)
        history_layout.addWidget(history_heading)

        self.history_table = QTableWidget(0, 4)
        self.history_table.setHorizontalHeaderLabels(["אירוע", "סיכום", "מועד", "מבצע"])
        self.history_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.history_table.verticalHeader().hide()
        self.history_table.setMinimumHeight(190)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.horizontalHeader().setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.history_table.horizontalHeader().setDefaultAlignment(right)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for column in range(self.history_table.columnCount()):
            header_item = self.history_table.horizontalHeaderItem(column)
            if header_item is not None:
                header_item.setTextAlignment(right)
        history_layout.addWidget(self.history_table)
        self.workspace.details_widget.layout().insertWidget(
            self.workspace.details_widget.layout().count() - 1, self.history_group
        )
        self.history_group.setVisible(self.role == "manager")
    def eventFilter(self,watched,event):
        if watched is self.table and event.type()==QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter):self._open();return True
        return super().eventFilter(watched,event)
    def _row_id(self,row):return str(self.table.item(row,0).data(Qt.ItemDataRole.UserRole))
    def _select(self):
        rows=self.table.selectionModel().selectedRows()
        if not rows:self._selected_id=None;return
        booking_id=self._row_id(rows[0].row());changed=booking_id!=self._selected_id;self._selected_id=booking_id
        if changed:self._clear_forms();self.workspace.detail_title.clear();self.workspace.show_list();self.booking_selected.emit(booking_id)
    def _open(self):
        if self._selected_id:self._pending_open_id=self._selected_id
        if self._selected_id and self.workspace.detail_title.text():self._pending_open_id=None;self.workspace.show_details()
    def _request_open(self,booking_id):self._pending_open_id=booking_id;self.select_booking(booking_id);self._open()
    def prepare_list_navigation(self, *, clear_filters=False):
        """Clear stale detail intent before a list/queue navigation.

        This deliberately does not emit filter signals. The presenter owns the
        next list request and decides which filters/queue to load.
        """
        self._pending_open_id=None;self._selected_id=None
        blocked=self.table.blockSignals(True);self.table.clearSelection();self.table.blockSignals(blocked)
        self.filter_popup.hide();self.workspace.show_list();self._clear_forms();self.workspace.detail_title.clear();self._clear_assignment_cards()
        if clear_filters:
            self.toolbar.search_input.clear();blocked_sort=self.toolbar.sort_combo.blockSignals(True);self.toolbar.sort_combo.setCurrentIndex(0);self.toolbar.sort_combo.blockSignals(blocked_sort);self._clear_filter_choices()
    def set_list_context(self, context):
        self._list_context=context
    def _selected_filters(self,group):
        return [key for key,widget in group.items() if widget.isChecked()]
    def _emit_filters(self,search=None):
        values={"status":self._selected_filters(self.status_checks),"activity_id":self._selected_filters(self.activity_checks),"instructor_id":self._selected_filters(self.instructor_checks),"assignment_state":self._selected_filters(self.assignment_checks),"from_date":self.from_filter.text().strip(),"to_date":self.to_filter.text().strip(),"search":search if search is not None else self.toolbar.search_input.text().strip(),"order_by":str(self.toolbar.sort_combo.currentData() or "event_at"),"limit":self.footer.limit,"offset":0};self._render_filter_chips();self.filters_requested.emit(values)
    def _apply_popover_filters(self):
        self.filter_popup.hide()
        self._emit_filters()
    def _clear_filter_choices(self):
        for widget in (*self.status_checks.values(),*self.activity_checks.values(),*self.instructor_checks.values(),*self.assignment_checks.values()):widget.setChecked(False)
        self.from_filter.clear();self.to_filter.clear();self._render_filter_chips()
    def _clear_and_apply_filters(self):
        self._clear_filter_choices();self.filter_popup.hide();self._emit_filters()
    def _render_filter_chips(self):
        while self.chips_layout.count()>1:
            item=self.chips_layout.takeAt(0)
            if item.widget():item.widget().deleteLater()
        entries=[]
        for key in self._selected_filters(self.status_checks):entries.append((self.status_checks[key].text(),lambda _checked=False,value=key:self._remove_filter("status",value)))
        for key in self._selected_filters(self.assignment_checks):entries.append((self.assignment_checks[key].text(),lambda _checked=False,value=key:self._remove_filter("assignment",value)))
        for key in self._selected_filters(self.activity_checks):entries.append((self.activity_checks[key].text(),lambda _checked=False,value=key:self._remove_filter("activity",value)))
        for key in self._selected_filters(self.instructor_checks):entries.append((self.instructor_checks[key].text(),lambda _checked=False,value=key:self._remove_filter("instructor",value)))
        if self.from_filter.text().strip():entries.append((f"מ־{self.from_filter.text().strip()}",lambda:self._remove_filter("from",None)))
        if self.to_filter.text().strip():entries.append((f"עד {self.to_filter.text().strip()}",lambda:self._remove_filter("to",None)))
        for text,callback in entries:
            chip=QToolButton();chip.setText(f"{text}  ×");chip.setProperty("filterChip",True);chip.clicked.connect(callback);self.chips_layout.insertWidget(self.chips_layout.count()-1,chip)
        self.chips.setVisible(bool(entries))
    def _remove_filter(self,kind,key):
        if kind=="status":self.status_checks[key].setChecked(False)
        elif kind=="activity":self.activity_checks[key].setChecked(False)
        elif kind=="instructor":self.instructor_checks[key].setChecked(False)
        elif kind=="assignment":self.assignment_checks[key].setChecked(False)
        elif kind=="from":self.from_filter.clear()
        elif kind=="to":self.to_filter.clear()
        self._emit_filters()
    def _reset(self,emit=True):
        self.prepare_list_navigation(clear_filters=True);self._list_context=None
        if emit:self.filters_requested.emit({"status":None,"activity_id":None,"instructor_id":None,"assignment_state":None,"from_date":None,"to_date":None,"search":None,"order_by":"event_at","limit":25,"offset":0,"_clear_selection":True})
    def reset_to_default(self):
        self.prepare_list_navigation(clear_filters=True);self._list_context=None
    def show_summary(self,summary):
        values={"pending":summary.get("pending_count",0),"unassigned":summary.get("unassigned_count",0),"approved":summary.get("confirmed_count",0)}
        titles={"pending":"ממתינות לאישור","unassigned":"ממתינות לשיבוץ מדריך","approved":"מאושרות"}
        for key,value in values.items():
            if key in self.summary_buttons:
                self.summary_buttons[key].setText(f"{titles[key]}\n{value}")
    def show_bookings(self,rows,*,offset=0,count=0,limit=25,selected_id=None):
        open_registration = self.role == "instructor" and self._list_context == "open"
        action_column = self.workspace.row_action_column
        sizer = getattr(self.table, "_task20_column_sizer", None)
        if sizer is not None:
            policies = list(sizer.policies)
            policies[action_column] = ColumnPolicy(ColumnKind.ACTION, 156, 156) if open_registration else ColumnPolicy(ColumnKind.ACTION, 52, 52)
            sizer.policies = tuple(policies)
            sizer.apply()
        header = self.table.horizontalHeaderItem(action_column)
        if header is not None:
            header.setText("הרשמה" if open_registration else "")
        self.table.setRowCount(len(rows))
        for r,row in enumerate(rows):
            if open_registration:
                request_status = str(row.get("my_request_status") or "")
                label = "בקשה ממתינה" if request_status == "PENDING" else "אושרת לאירוע" if request_status == "APPROVED" else "הירשם שוב" if request_status == "REJECTED" else "הירשם לאירוע"
                register = QPushButton(label)
                register.setAccessibleName(f"{label}: {row.get('activity') or 'אירוע'}")
                register.setMinimumWidth(132)
                register.setMaximumWidth(144)
                style_reference_button(register, "secondary" if request_status == "PENDING" else "success" if request_status == "APPROVED" else "primary")
                register.setEnabled(bool(row.get("booking_activity_id")) and request_status not in {"PENDING", "APPROVED"})
                register.clicked.connect(lambda _checked=False, value=dict(row): self.assignment_request_requested.emit(value))
                self.table.setCellWidget(r, action_column, register)
            else:
                self.workspace.set_row_open_action(r,row["id"],self._request_open)
            values=(row.get("customer","—"),row.get("activity","—"),row.get("event_at","—")," · ".join(x for x in (row.get("city"),row.get("venue")) if x and x!="—") or "—",row.get("participants","—"))
            for c,value in enumerate(values,start=0):item=QTableWidgetItem(str(value));item.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignAbsolute);set_item_text(self.table,r,c,item,tooltip_direction=Qt.LayoutDirection.RightToLeft);item.setData(Qt.ItemDataRole.UserRole,row["id"] if c==0 else item.data(Qt.ItemDataRole.UserRole))
            status=QLabel(str(row.get("status") or "—"));status.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignAbsolute);status.setContentsMargins(SPACE_3,0,SPACE_3,0);status.setProperty("bookingState",str(row.get("status_code") or ""));self.table.setCellWidget(r,5,status)
        self.footer.limit=limit;self.footer.set_page(offset=offset,count=count);self._empty_filtered=bool(self.toolbar.search_input.text() or self._selected_filters(self.status_checks) or self._selected_filters(self.activity_checks) or self._selected_filters(self.instructor_checks) or self._selected_filters(self.assignment_checks) or self.from_filter.text() or self.to_filter.text());self.workspace.show_empty_state(empty=not rows,filtered=self._empty_filtered,plural="אירועים" if self.role=="instructor" else "הזמנות");self.footer.setVisible(bool(rows))
        title="אירועים פתוחים לשיבוץ" if self._list_context=="open" else "ממתינים לשיבוץ מדריך" if self._list_context=="unassigned" else "אירועים" if self.role=="instructor" else "הזמנות"
        self.workspace.results_label.setText(f"{title} • {len(rows)}")
        if not rows and self._list_context=="open":
            self.workspace.empty_title.setText("אין כרגע אירועים פתוחים לשיבוץ")
            self.workspace.empty_description.setText("הרשימה מתעדכנת מול השרת. אירוע שדורש מדריך ושעדיין לא שובץ יופיע כאן.")
            self.workspace.empty_action_button.setText("רענון הרשימה")
        elif not rows and self._empty_filtered:
            self.workspace.empty_action_button.setText("ניקוי הסינון")
    def show_filter_options(self,customers,activities,instructors):
        while self.activity_layout.count()>1:
            item=self.activity_layout.takeAt(0)
            if item.widget():item.widget().deleteLater()
        self.activity_checks={}
        for activity in activities:
            key=str(activity["id"]);check=QCheckBox(str(activity.get("name") or key));check.setLayoutDirection(Qt.LayoutDirection.RightToLeft);self.activity_layout.insertWidget(self.activity_layout.count()-1,check);self.activity_checks[key]=check
        self.activity_empty.setVisible(not bool(activities))
        while self.instructor_layout.count()>1:
            item=self.instructor_layout.takeAt(0)
            if item.widget():item.widget().deleteLater()
        self.instructor_checks={}
        for instructor in instructors:
            key=str(instructor["id"]);check=QCheckBox(str(instructor.get("full_name") or instructor.get("name") or key));check.setLayoutDirection(Qt.LayoutDirection.RightToLeft);self.instructor_layout.insertWidget(self.instructor_layout.count()-1,check);self.instructor_checks[key]=check
        self.instructor_empty.setVisible(not bool(instructors))
    def show_details(self,details,history):
        self._clear_forms();identity="פרטי הזמנה";status=""
        customer_labels={"לקוח","איש קשר","טלפון לקוח"}
        for label,value in details:
            if label=="לקוח":identity=value
            if label=="סטטוס":status=value
            content=QLabel(value);content.setWordWrap(True)
            if label=="טלפון לקוח":
                content.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
                content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            target=self.customer_details if label in customer_labels else self.system_details if label in {"מזהה","סטטוס"} else self.booking_details
            self.workspace.add_property_row(target,label,content)
        self.workspace.detail_title.setText(identity);self.workspace.detail_status.setText(status);self.workspace.detail_subtitle.setText("מצב תפעולי, שיבוץ והיסטוריית ההזמנה");self.history_table.setRowCount(len(history))
        right = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute
        for r, event in enumerate(history):
            for c, key in enumerate(("event_type", "summary", "occurred_at", "actor")):
                item = QTableWidgetItem(str(event.get(key) or "—"))
                item.setTextAlignment(right)
                self.history_table.setItem(r, c, item)
        self.history_table.resizeRowsToContents()
        if self._pending_open_id==self._selected_id:self._pending_open_id=None;self.workspace.show_details()

    def set_open_event_mode(self, active):
        self.assignment_group.setVisible(self.role == "manager" or (self.role == "instructor" and bool(active)))
        if self.role == "instructor":
            self.assignment_hint.setText("אפשר לשלוח בקשת שיבוץ. המנהל יאשר או ידחה אותה." if active else "מצב השיבוץ לפעילויות בהזמנה")
    def _clear_forms(self):
        for form in (self.booking_details,self.customer_details,self.system_details):
            while form.rowCount():form.removeRow(0)
    def clear_details(self):
        if hasattr(self,"booking_details"):self._clear_forms();self.workspace.detail_title.clear();self.workspace.show_list();self.workspace.set_actions_enabled(False);self._clear_assignment_cards()
        self._selected_id=None;self._pending_open_id=None
    def select_booking(self,booking_id):
        for row in range(self.table.rowCount()):
            if self._row_id(row)==booking_id:
                changed=self._selected_id!=booking_id;blocked=self.table.blockSignals(True);index=self.table.model().index(row,0);self.table.selectionModel().setCurrentIndex(index,QItemSelectionModel.SelectionFlag.ClearAndSelect|QItemSelectionModel.SelectionFlag.Rows);self.table.blockSignals(blocked);self._selected_id=booking_id
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
    def _add_assignment_card(self, activity):
        right = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute
        card = QFrame()
        card.setObjectName("assignmentCard")
        card.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        row = QHBoxLayout(card)
        row.setDirection(QHBoxLayout.Direction.RightToLeft)
        row.setContentsMargins(SPACE_3, SPACE_2, SPACE_3, SPACE_2)
        row.setSpacing(SPACE_2)

        identity_widget = QWidget()
        identity_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        identity = QVBoxLayout(identity_widget)
        identity.setContentsMargins(0, 0, 0, 0)
        identity.setSpacing(4)

        name = QLabel(activity["activity_name"])
        name.setObjectName("sectionTitle")
        name.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        name.setAlignment(right)
        identity.addWidget(name)

        if self.role == "instructor":
            if not activity.get("assignment_required"):
                state_text = "כבר שובץ מדריך לפעילות זו"
            else:
                request_status = activity.get("my_request_status")
                state_text = {
                    "PENDING": "בקשת השיבוץ שלך ממתינה לאישור המנהל",
                    "APPROVED": "בקשת השיבוץ שלך אושרה",
                    "REJECTED": "בקשת השיבוץ הקודמת נדחתה",
                }.get(request_status, "הפעילות פתוחה לבקשות שיבוץ")
            status = QLabel(state_text)
            status.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            status.setAlignment(right)
            status.setWordWrap(True)
            identity.addWidget(status)
            row.addWidget(identity_widget, 1)
            if activity.get("assignment_required") and activity.get("my_request_status") != "PENDING":
                request = QPushButton("שליחת בקשת שיבוץ" if activity.get("my_request_status") != "REJECTED" else "שליחת בקשה מחדש")
                style_reference_button(request, "primary")
                request.clicked.connect(lambda _checked=False, value=activity: self.assignment_request_requested.emit(value))
                row.addWidget(request)
            self.assignment_cards_layout.addWidget(card)
            return

        assignments = activity.get("assignments") or []
        if not activity.get("assignment_required"):
            status = QLabel("לא נדרש מדריך")
            status.setProperty("assignmentState", "neutral")
            status.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            status.setAlignment(right)
            identity.addWidget(status)
            row.addWidget(identity_widget, 1)
            self.assignment_cards_layout.addWidget(card)
            return

        assignment = assignments[0] if assignments else None
        status = QLabel("משובץ" if assignment else "ממתין לשיבוץ")
        status.setProperty("assignmentState", "assigned" if assignment else "waiting")
        status.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        status.setAlignment(right)
        identity.addWidget(status)

        description = QLabel(assignment.get("instructor_name") if assignment else "לא שובץ מדריך")
        description.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        description.setAlignment(right)
        identity.addWidget(description)
        row.addWidget(identity_widget, 1)

        if assignment:
            replace = QPushButton("החלפת מדריך")
            remove = QPushButton("הסרת שיבוץ")
            replace.clicked.connect(lambda _checked=False, a=activity, current=assignment: self.assignment_replace_requested.emit(a, current))
            remove.clicked.connect(lambda _checked=False, a=activity, current=assignment: self.assignment_remove_requested.emit(a, current))
            row.addWidget(replace)
            row.addWidget(remove)
        else:
            requests = activity.get("requests") or []
            if requests:
                request_box = QWidget()
                request_layout = QVBoxLayout(request_box)
                request_layout.setContentsMargins(0, 0, 0, 0)
                request_layout.setSpacing(4)
                for request_model in requests:
                    request_row = QWidget()
                    request_row_layout = QHBoxLayout(request_row)
                    request_row_layout.setDirection(QHBoxLayout.Direction.RightToLeft)
                    request_row_layout.setContentsMargins(0, 0, 0, 0)
                    request_label = QLabel(f"{request_model.get('instructor_name') or 'מדריך'} ביקש להשתבץ")
                    request_label.setAlignment(right)
                    request_row_layout.addWidget(request_label, 1)
                    approve = QPushButton("אישור שיבוץ")
                    reject = QPushButton("דחייה")
                    style_reference_button(approve, "primary")
                    style_reference_button(reject, "destructive")
                    approve.clicked.connect(lambda _checked=False, a=activity, req=request_model: self.assignment_request_approve_requested.emit(a, req))
                    reject.clicked.connect(lambda _checked=False, a=activity, req=request_model: self.assignment_request_reject_requested.emit(a, req))
                    request_row_layout.addWidget(approve)
                    request_row_layout.addWidget(reject)
                    request_layout.addWidget(request_row)
                identity.addWidget(request_box)
            assign = QPushButton("שיבוץ מדריך")
            style_reference_button(assign, "primary")
            assign.clicked.connect(lambda _checked=False, value=activity: self.assignment_add_requested.emit(value))
            row.addWidget(assign)

        self.assignment_cards_layout.addWidget(card)
    def open_instructor_selector(self,activity,query_handler,choose_handler):self._selector=InstructorSelectorDialog(activity,query_handler,choose_handler,self);self._selector.open();return self._selector
    def confirm_assignment_removal(self,instructor_name,activity_name):return confirm_action(self,"הסרת שיבוץ",f"להסיר את {instructor_name} מהפעילות {activity_name}? היסטוריית האירועים תישמר.")
    def collect_create_booking(self,customers,activities,instructors,*,role="manager",preselected_activity_id=None):
        dialog=BookingFormDialog(customers=customers,activities=activities,instructors=instructors,role=role,preselected_activity_id=preselected_activity_id,parent=self);return dialog.values() if dialog.exec()==dialog.DialogCode.Accepted else None
    def collect_booking_changes(self,booking):
        dialog=BookingFormDialog(booking=booking,parent=self);return dialog.values() if dialog.exec()==dialog.DialogCode.Accepted else None
    def confirm_cancellation(self):return confirm_action(self,"אישור ביטול","לבטל את ההזמנה? היסטוריית ההזמנה תישמר.")
    def confirm_completion(self):return confirm_action(self,"השלמת הזמנה","לסמן את ההזמנה כהושלמה?")
