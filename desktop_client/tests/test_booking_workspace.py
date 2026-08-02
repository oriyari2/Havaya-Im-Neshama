import os
from unittest import TestCase
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFormLayout, QToolButton

from desktop_client.app.presenters.formatting import booking_details, booking_row
from desktop_client.app.views.booking_dialogs import BookingFormDialog
from desktop_client.app.views.bookings_view import BookingsView
from desktop_client.app.views.entity_selector import SearchableEntitySelector


BOOKING={"id":"b1","customer_name":"לקוח","activity_name":"פעילות","event_at":"2026-10-01T10:00:00+00:00","city":"חיפה","venue":"אולם","participant_count":20,"agreed_price":"500","status":"NEW","requires_instructor":True,"notes":"","version":1,"created_at":"2026-01-01","updated_at":"2026-01-02"}


class BookingWorkspaceTests(TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def test_summary_counts_and_quick_queues(self):
        view=BookingsView("manager");view.show_summary({"pending_count":3,"unassigned_count":2,"confirmed_count":4});self.assertIn("3",view.summary_buttons["pending"].text());self.assertIn("4",view.summary_buttons["approved"].text());queues=[];view.queue_requested.connect(queues.append);view.summary_buttons["unassigned"].click();self.assertEqual(queues,["unassigned"])
    def test_row_action_double_click_enter_and_state_restoration(self):
        view=BookingsView("manager");row=booking_row(BOOKING);view.booking_selected.connect(lambda _id:view.show_details(booking_details(BOOKING),[]));view.show_bookings([row],offset=0,count=1,limit=25);action=view.table.cellWidget(0,0).findChild(QToolButton);action.click();self.assertIs(view.pages.currentWidget(),view.details_page);view.back_button.click();view.table.cellDoubleClicked.emit(0,1);self.assertIs(view.pages.currentWidget(),view.details_page);view.back_button.click();view.select_booking("b1");QTest.keyClick(view.table,Qt.Key.Key_Return);self.assertIs(view.pages.currentWidget(),view.details_page)
    def test_state_actions_and_role_visibility(self):
        manager=BookingsView("manager");manager.set_command_availability("NEW");self.assertFalse(manager.confirm_button.isHidden());manager.set_command_availability("CONFIRMED");self.assertTrue(manager.confirm_button.isHidden());manager.set_command_availability("CANCELLED");self.assertTrue(manager.edit_button.isHidden())
        for role in ("customer","instructor"):
            view=BookingsView(role);self.assertTrue(view.command_panel.isHidden());self.assertTrue(view.assignment_group.isHidden());self.assertTrue(view.history_group.isHidden())
    def test_shared_selector_filters_and_stores_real_id(self):
        selector=SearchableEntitySelector("בחירה");selector.set_items([{"id":"1","name":"אלפא"},{"id":"2","name":"בטא"}],label_key="name");selector.combo.completer().setCompletionPrefix("אל");self.assertEqual(selector.combo.completer().completionCount(),1);selector.select_id("1");self.assertEqual(selector.selected_id(),"1");selector.combo.lineEdit().setText("טקסט חופשי");selector._typed("טקסט חופשי");self.assertIsNone(selector.selected_id());self.assertEqual(selector.layoutDirection(),Qt.LayoutDirection.RightToLeft)
    def test_booking_selectors_reject_arbitrary_clear_dependencies_and_hide_inactive(self):
        dialog=BookingFormDialog(customers=[{"id":"c1","name":"לקוח","is_active":True}],activities=[{"id":"a1","name":"פעילה","is_active":True},{"id":"a2","name":"מושבתת","is_active":False}],instructors=[{"id":"i1","full_name":"מדריך","is_active":True}]);self.assertEqual(dialog.activity.count(),2);dialog.customer_selector.select_id("c1");dialog.activity_selector.select_id("a1");dialog.instructor_selector.select_id("i1");self.assertEqual(dialog.values()["instructor_id"],"i1");dialog.activity_selector.clear_selection();self.assertIsNone(dialog.instructor_selector.selected_id());dialog.activity.lineEdit().setText("לא קיימת");dialog.activity_selector._typed("לא קיימת");self.assertNotIn("activity_id",dialog.values());dialog.accept();self.assertFalse(dialog.field_errors["activity_id"].isHidden())
    def test_selector_loading_empty_keyboard_and_rtl_details_geometry(self):
        selector=SearchableEntitySelector("בחירה");selector.set_loading(True);self.assertFalse(selector.combo.isEnabled());selector.set_loading(False);selector.set_items([],label_key="name");self.assertFalse(selector.state.isHidden());selector.combo.setFocus();QTest.keyClick(selector.combo,Qt.Key.Key_Down)
        view=BookingsView("manager");view.show_details(booking_details(BOOKING),[])
        for form in (view.booking_details,view.customer_details,view.system_details):
            for row in range(form.rowCount()):self.assertTrue(form.itemAt(row,QFormLayout.ItemRole.LabelRole).widget().alignment()&Qt.AlignmentFlag.AlignRight);self.assertTrue(form.itemAt(row,QFormLayout.ItemRole.FieldRole).widget().alignment()&Qt.AlignmentFlag.AlignRight)
