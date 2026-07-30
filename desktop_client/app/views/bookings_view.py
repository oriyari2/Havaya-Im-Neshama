from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop_client.app.views.common import StatefulWidget, create_booking_table, populate_booking_table
from desktop_client.app.views.booking_dialogs import BookingFormDialog
from desktop_client.app.views.assignment_dialogs import InstructorSelectorDialog
from desktop_client.app.views.management_common import RetryState,confirm_action
from desktop_client.app.views.management_common import PaginationFooter


class BookingsView(StatefulWidget):
    filters_requested = Signal(dict)
    booking_selected = Signal(str)
    create_requested = Signal()
    edit_requested = Signal()
    confirm_requested = Signal()
    cancel_requested = Signal()
    complete_requested = Signal()
    page_requested = Signal(int, int)
    assignment_add_requested = Signal(dict)
    assignment_remove_requested = Signal(dict,dict)

    def __init__(self, role: str) -> None:
        super().__init__()
        self.role = role
        layout = QVBoxLayout(self)
        title_text = {"customer": "ההזמנות שלי", "instructor": "האירועים שלי"}.get(role, "הזמנות")
        title = QLabel(title_text)
        title.setObjectName("screenTitle")
        layout.addWidget(title)
        layout.addWidget(self.state_label)

        self.filter_panel = QWidget()
        filter_layout = QHBoxLayout(self.filter_panel)
        self.status_filter = QComboBox()
        self.status_filter.addItem("כל הסטטוסים", "")
        for value, label in (("NEW", "חדש"), ("CONFIRMED", "מאושר"), ("COMPLETED", "הושלם"), ("CANCELLED", "בוטל")):
            self.status_filter.addItem(label, value)
        self.customer_filter = QComboBox()
        self.customer_filter.setEditable(True)
        self.customer_filter.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.customer_filter.addItem("כל הלקוחות", "")
        self.activity_filter = QComboBox()
        self.activity_filter.setEditable(True)
        self.activity_filter.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.activity_filter.addItem("כל הפעילויות", "")
        self.instructor_filter = QComboBox()
        self.instructor_filter.setEditable(True)
        self.instructor_filter.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.instructor_filter.addItem("כל המדריכים", "")
        self.from_filter = QLineEdit()
        self.from_filter.setPlaceholderText("מתאריך YYYY-MM-DD")
        self.to_filter = QLineEdit()
        self.to_filter.setPlaceholderText("עד תאריך YYYY-MM-DD")
        for widget in (self.status_filter, self.customer_filter, self.activity_filter, self.instructor_filter, self.from_filter, self.to_filter):
            filter_layout.addWidget(widget)
        refresh_button = QPushButton("סינון ורענון")
        refresh_button.clicked.connect(self._emit_filters)
        filter_layout.addWidget(refresh_button)
        for widget in (self.customer_filter, self.activity_filter, self.instructor_filter, self.from_filter, self.to_filter):
            widget.setVisible(role == "manager")
        self.filter_panel.setVisible(True)
        layout.addWidget(self.filter_panel)

        self.command_panel = QWidget()
        command_layout = QHBoxLayout(self.command_panel)
        self.create_button = QPushButton("הזמנה חדשה")
        self.edit_button = QPushButton("עריכת פרטים")
        self.confirm_button = QPushButton("אישור הזמנה")
        self.cancel_button = QPushButton("ביטול הזמנה")
        self.complete_button = QPushButton("סימון כהושלמה")
        self.create_button.clicked.connect(self.create_requested.emit)
        self.edit_button.clicked.connect(self.edit_requested.emit)
        self.confirm_button.clicked.connect(self.confirm_requested.emit)
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        self.complete_button.clicked.connect(self.complete_requested.emit)
        for button in (self.create_button, self.edit_button, self.confirm_button, self.complete_button, self.cancel_button):
            command_layout.addWidget(button)
        self.command_panel.setVisible(role in {"manager", "customer"})
        for button in (self.edit_button, self.confirm_button, self.cancel_button, self.complete_button):
            button.setVisible(role == "manager")
        if role == "customer":
            self.create_button.setText("בקשת הזמנה חדשה")
        self._set_selection_commands_enabled(False)
        layout.addWidget(self.command_panel)

        splitter = QSplitter()
        self.table = create_booking_table()
        self.table.itemSelectionChanged.connect(self._emit_selection)
        splitter.addWidget(self.table)

        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_group = QGroupBox("פרטי הזמנה")
        self.details_form = QFormLayout(details_group)
        details_layout.addWidget(details_group)
        self.history_group = QGroupBox("היסטוריית שינויים")
        history_layout = QVBoxLayout(self.history_group)
        self.history_table = QTableWidget(0, 4)
        self.history_table.setHorizontalHeaderLabels(["אירוע", "סיכום", "מועד", "מבצע"])
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        history_layout.addWidget(self.history_table)
        self.history_group.setVisible(role == "manager")
        details_layout.addWidget(self.history_group)
        self.assignment_group=QGroupBox("שיוכי מדריכים");assignment_layout=QVBoxLayout(self.assignment_group);self.assignment_state=RetryState();self.assignment_state.hide();assignment_layout.addWidget(self.assignment_state);self.assignment_tree=QTreeWidget();self.assignment_tree.setHeaderLabels(["פעילות / מדריך","מצב","עיר"]);self.assignment_tree.itemSelectionChanged.connect(self._assignment_selection);assignment_layout.addWidget(self.assignment_tree);assignment_actions=QHBoxLayout();self.assign_button=QPushButton("שייך מדריך");self.remove_assignment_button=QPushButton("הסר שיוך");self.assign_button.clicked.connect(self._emit_assign);self.remove_assignment_button.clicked.connect(self._emit_remove);assignment_actions.addWidget(self.assign_button);assignment_actions.addWidget(self.remove_assignment_button);assignment_layout.addLayout(assignment_actions);self.assignment_group.setVisible(role=="manager");details_layout.addWidget(self.assignment_group);self.assign_button.setEnabled(False);self.remove_assignment_button.setEnabled(False)
        splitter.addWidget(details_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)
        self.pagination = PaginationFooter(limit=25)
        self.pagination.page_requested.connect(self.page_requested.emit)
        layout.addWidget(self.pagination)

    def _emit_filters(self) -> None:
        self.filters_requested.emit(
            {
                "status": self.status_filter.currentData(),
                "customer_id": self.customer_filter.currentData(),
                "activity_id": self.activity_filter.currentData(),
                "instructor_id": self.instructor_filter.currentData(),
                "from_date": self.from_filter.text().strip(),
                "to_date": self.to_filter.text().strip(),
                "limit": self.pagination.limit,
                "offset": 0,
            }
        )

    def _emit_selection(self) -> None:
        selected = self.table.selectedItems()
        if selected:
            booking_id = self.table.item(selected[0].row(), 0).data(Qt.ItemDataRole.UserRole)
            self.booking_selected.emit(str(booking_id))
            self._set_selection_commands_enabled(True)

    def _set_selection_commands_enabled(self, enabled: bool) -> None:
        for button in (getattr(self, "edit_button", None), getattr(self, "confirm_button", None), getattr(self, "complete_button", None), getattr(self, "cancel_button", None)):
            if button is not None:
                button.setEnabled(enabled)

    def set_command_availability(self, status: str) -> None:
        terminal = status in {"COMPLETED", "CANCELLED"}
        self.edit_button.setEnabled(not terminal)
        self.confirm_button.setEnabled(status == "NEW")
        self.cancel_button.setEnabled(not terminal)
        self.complete_button.setEnabled(not terminal)

    def show_bookings(self, rows: list[dict[str, str]], *, offset=0, count=0, limit=25, selected_id=None) -> None:
        self.state_label.hide()
        populate_booking_table(self.table, rows)
        self.pagination.limit = limit
        self.pagination.set_page(offset=offset, count=count)
        if selected_id:
            for row in range(self.table.rowCount()):
                if str(self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)) == selected_id:
                    self.table.selectRow(row)
                    break
        if not rows:
            self.show_empty("לא נמצאו הזמנות.")

    def show_filter_options(self, customers, activities, instructors):
        def fill(combo, rows, label_key):
            selected = combo.currentData()
            combo.blockSignals(True)
            combo.clear(); combo.addItem("הכול", "")
            for row in rows:
                combo.addItem(str(row.get(label_key) or row["id"]), str(row["id"]))
            index = combo.findData(selected)
            combo.setCurrentIndex(max(0, index))
            combo.blockSignals(False)
        fill(self.customer_filter, customers, "name")
        fill(self.activity_filter, activities, "name")
        fill(self.instructor_filter, instructors, "full_name")

    def show_details(self, details: list[tuple[str, str]], history: list[dict[str, str]]) -> None:
        while self.details_form.rowCount():
            self.details_form.removeRow(0)
        for label, value in details:
            self.details_form.addRow(label, QLabel(value))
        self.history_table.setRowCount(len(history))
        for row_index, event in enumerate(history):
            for column_index, key in enumerate(("event_type", "summary", "occurred_at", "actor")):
                self.history_table.setItem(row_index, column_index, QTableWidgetItem(event[key]))

    def show_success(self, message: str) -> None:
        self.state_label.setText(message)
        self.state_label.show()

    def set_assignments_loading(self,value:bool)->None:
        self.assignment_group.setEnabled(not value)
    def show_assignments_error(self,message:str,*,retriable=False)->None:self.assignment_state.show_message(message,retriable=retriable)
    def show_assignments(self,activities:list[dict])->None:
        self.assignment_state.hide();self.assignment_tree.clear()
        for activity in activities:
            top=QTreeWidgetItem([activity["activity_name"],"נדרש שיוך" if activity["assignment_required"] else "משויך",""]);top.setData(0,Qt.ItemDataRole.UserRole,{"activity":activity});self.assignment_tree.addTopLevelItem(top)
            for assignment in activity["assignments"]:
                child=QTreeWidgetItem([assignment["instructor_name"],"שיוך פעיל",assignment.get("instructor_city") or "—"]);child.setData(0,Qt.ItemDataRole.UserRole,{"activity":activity,"assignment":assignment});top.addChild(child)
            top.setExpanded(True)
        if not activities:self.assignment_state.show_message("אין פעילויות הזמנה להצגה.",retriable=False)
    def _assignment_selection(self):
        items=self.assignment_tree.selectedItems();data=items[0].data(0,Qt.ItemDataRole.UserRole) if items else {};self.assign_button.setEnabled(bool(data.get("activity")));self.remove_assignment_button.setEnabled(bool(data.get("assignment")))
    def _emit_assign(self):
        items=self.assignment_tree.selectedItems()
        if items:self.assignment_add_requested.emit(items[0].data(0,Qt.ItemDataRole.UserRole)["activity"])
    def _emit_remove(self):
        items=self.assignment_tree.selectedItems();data=items[0].data(0,Qt.ItemDataRole.UserRole) if items else {}
        if data.get("assignment"):self.assignment_remove_requested.emit(data["activity"],data["assignment"])
    def open_instructor_selector(self,activity,query_handler,choose_handler):
        self._selector=InstructorSelectorDialog(activity,query_handler,choose_handler,self);self._selector.open();return self._selector
    def confirm_assignment_removal(self,instructor_name,activity_name):return confirm_action(self,"הסרת שיוך",f"להסיר את {instructor_name} מהפעילות {activity_name}? היסטוריית האירועים תישמר והמדריך עצמו לא יימחק.")

    def collect_create_booking(self, customers: list[dict], activities: list[dict], *, role="manager", preselected_activity_id=None) -> dict[str, object] | None:
        if (role == "manager" and not customers) or not activities:
            self.show_error("נדרשים לקוח ופעילות פעילים כדי ליצור הזמנה." if role == "manager" else "נדרשת פעילות פעילה כדי לשלוח בקשת הזמנה.")
            return None
        dialog = BookingFormDialog(customers=customers, activities=activities, role=role, preselected_activity_id=preselected_activity_id, parent=self)
        return dialog.values() if dialog.exec() == dialog.DialogCode.Accepted else None

    def collect_booking_changes(self, booking: dict) -> dict[str, object] | None:
        dialog = BookingFormDialog(booking=booking, parent=self)
        return dialog.values() if dialog.exec() == dialog.DialogCode.Accepted else None

    def confirm_cancellation(self) -> bool:
        answer = QMessageBox.question(
            self,
            "אישור ביטול",
            "האם לבטל את ההזמנה? לא ניתן להחזיר הזמנה מבוטלת לסטטוס קודם.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def confirm_completion(self) -> bool:
        return confirm_action(self, "השלמת הזמנה", "לסמן את ההזמנה כהושלמה? לא ניתן לשנות סטטוס לאחר מכן.")
