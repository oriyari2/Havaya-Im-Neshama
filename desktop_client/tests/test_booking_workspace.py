import os
from unittest import TestCase

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QWidget,
)

from desktop_client.app.features.bookings.formatting import booking_details, booking_row
from desktop_client.app.features.bookings.dialogs import BookingFormDialog
from desktop_client.app.features.bookings.view import BookingsView
from desktop_client.app.shared.ui.entity_selector import SearchableEntitySelector


BOOKING = {
    "id": "b1",
    "customer_name": "לקוח",
    "activity_name": "פעילות",
    "event_at": "2026-10-01T10:00:00+00:00",
    "city": "חיפה",
    "venue": "אולם",
    "participant_count": 20,
    "agreed_price": "500",
    "status": "NEW",
    "requires_instructor": True,
    "notes": "",
    "version": 1,
    "created_at": "2026-01-01",
    "updated_at": "2026-01-02",
}


class BookingWorkspaceTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def tearDown(self):
        # Flush deferred Qt events between tests. This matters especially when
        # an assertion fails before a widget's normal close path is reached.
        self.app.processEvents()

    def _track(self, widget):
        self.addCleanup(self._safe_close, widget)
        return widget

    @staticmethod
    def _safe_close(widget):
        try:
            widget.close()
            widget.deleteLater()
        except RuntimeError:
            # The wrapped C++ object may already have been destroyed.
            pass

    @staticmethod
    def _row_action_button(view, row=0):
        # The branded management table keeps business data at the start and
        # places the open-row action at the physical end.
        action_column = view.table.columnCount() - 1
        host = view.table.cellWidget(row, action_column)
        if host is None:
            return None
        if isinstance(host, QToolButton):
            return host
        return host.findChild(QToolButton)

    def test_manager_uses_filters_instead_of_duplicate_quick_queues(self):
        view = self._track(BookingsView("manager"))
        self.assertEqual(view.summary_buttons, {})
        self.assertTrue(view.summary_panel.isHidden())
        self.assertFalse(view.filter_button.isHidden())
        self.assertFalse(view.assignment_section.isHidden())


    def test_instructor_open_event_request_controls_and_customer_contact(self):
        view = self._track(BookingsView("instructor"))
        self.assertIn("open", view.summary_buttons)
        self.assertEqual(view.summary_buttons["open"].text(), "אירועים פתוחים לשיבוץ")
        self.assertTrue(view.assignment_group.isHidden())

        emitted = []
        view.assignment_request_requested.connect(lambda activity: emitted.append(activity["booking_activity_id"]))
        view.set_open_event_mode(True)
        self.assertFalse(view.assignment_group.isHidden())
        view.show_assignments([{
            "booking_activity_id": "ba1",
            "activity_id": "a1",
            "activity_name": "פעילות פתוחה",
            "assignment_required": True,
            "my_request_status": None,
        }])
        buttons = [button for button in view.assignment_group.findChildren(type(view.create_button)) if button.text() == "שליחת בקשת שיבוץ"]
        self.assertEqual(len(buttons), 1)
        buttons[0].click()
        self.assertEqual(emitted, ["ba1"])

        details = booking_details({
            **BOOKING,
            "customer_contact_name": "איש קשר",
            "customer_phone": "050-1234567",
        })
        view.show_details(details, [])
        rendered = []
        for row in range(view.customer_details.rowCount()):
            field = view.customer_details.itemAt(row, QFormLayout.ItemRole.FieldRole).widget()
            rendered.append(field.text())
        self.assertIn("לקוח", rendered)
        self.assertIn("איש קשר", rendered)
        self.assertIn("050-1234567", rendered)


    def test_instructor_open_event_list_has_direct_registration_button(self):
        view = self._track(BookingsView("instructor"))
        view.set_list_context("open")
        emitted = []
        view.assignment_request_requested.connect(emitted.append)
        row = booking_row({
            **BOOKING,
            "booking_activity_id": "ba-open-1",
            "my_request_status": None,
        })

        view.show_bookings([row], offset=0, count=1, limit=25)

        action_column = view.workspace.row_action_column
        button = view.table.cellWidget(0, action_column)
        self.assertIsInstance(button, QPushButton)
        self.assertEqual(button.text(), "הירשם לאירוע")
        self.assertTrue(button.isEnabled())
        self.assertEqual(view.table.horizontalHeaderItem(action_column).text(), "הרשמה")
        button.click()
        self.assertEqual(emitted[0]["booking_id"], "b1")
        self.assertEqual(emitted[0]["booking_activity_id"], "ba-open-1")

        pending = booking_row({
            **BOOKING,
            "booking_activity_id": "ba-open-1",
            "my_request_status": "PENDING",
        })
        view.show_bookings([pending], offset=0, count=1, limit=25)
        pending_button = view.table.cellWidget(0, action_column)
        self.assertEqual(pending_button.text(), "בקשה ממתינה")
        self.assertFalse(pending_button.isEnabled())

    def test_booking_search_and_filter_action_text_remains_visible_under_global_qss(self):
        view = self._track(BookingsView("instructor"))
        self.assertEqual(view.toolbar.search_button.text(), "חיפוש")
        self.assertEqual(view.filter_button.text(), "סינון")
        self.assertTrue(view.filter_popup.apply_button.text().strip())
        self.assertEqual(view.toolbar.refresh_button.text(), "איפוס")
        self.assertEqual(view.filter_button.minimumWidth(), view.toolbar.refresh_button.minimumWidth())
        for button in (view.toolbar.search_button, view.filter_button, view.toolbar.refresh_button, view.filter_popup.apply_button, view.filter_popup.clear_button, view.workspace.empty_action_button):
            style = button.styleSheet()
            self.assertIn("background:", style)
            self.assertIn("color:", style)
            self.assertIn("QPushButton:disabled", style)

    def test_queue_navigation_clears_stale_filter_and_pending_detail_state(self):
        view = self._track(BookingsView("instructor"))
        view.status_checks["CANCELLED"].setChecked(True)
        view._render_filter_chips()
        view._selected_id = "old-booking"
        view._pending_open_id = "old-booking"
        view.prepare_list_navigation(clear_filters=True)
        view.set_list_context("open")
        self.assertFalse(view.status_checks["CANCELLED"].isChecked())
        self.assertTrue(view.chips.isHidden())
        self.assertIsNone(view._selected_id)
        self.assertIsNone(view._pending_open_id)
        self.assertIs(view.pages.currentWidget(), view.list_page)
        view.show_bookings([], offset=0, count=0, limit=25)
        self.assertEqual(view.workspace.empty_title.text(), "אין כרגע אירועים פתוחים לשיבוץ")
        self.assertEqual(view.workspace.empty_action_button.text(), "רענון הרשימה")

    def test_row_action_double_click_enter_and_state_restoration(self):
        view = self._track(BookingsView("manager"))
        row = booking_row(BOOKING)

        view.booking_selected.connect(
            lambda _id: view.show_details(booking_details(BOOKING), [])
        )
        view.show_bookings([row], offset=0, count=1, limit=25)

        action = self._row_action_button(view)
        self.assertIsNotNone(action)
        action.click()
        self.assertIs(view.pages.currentWidget(), view.details_page)

        view.back_button.click()
        self.assertIs(view.pages.currentWidget(), view.list_page)

        # Double-clicking any business-data column opens the same booking.
        view.table.cellDoubleClicked.emit(0, 1)
        self.assertIs(view.pages.currentWidget(), view.details_page)

        view.back_button.click()
        view.select_booking("b1")
        QTest.keyClick(view.table, Qt.Key.Key_Return)
        self.assertIs(view.pages.currentWidget(), view.details_page)

    def test_state_actions_and_role_visibility(self):
        manager = self._track(BookingsView("manager"))
        manager.set_command_availability("NEW")
        self.assertFalse(manager.confirm_button.isHidden())

        manager.set_command_availability("CONFIRMED")
        self.assertTrue(manager.confirm_button.isHidden())

        manager.set_command_availability("CANCELLED")
        self.assertTrue(manager.edit_button.isHidden())

        for role in ("customer", "instructor"):
            view = self._track(BookingsView(role))
            self.assertTrue(view.command_panel.isHidden())
            self.assertTrue(view.assignment_group.isHidden())
            self.assertTrue(view.history_group.isHidden())

    def test_shared_selector_filters_and_stores_real_id(self):
        selector = self._track(SearchableEntitySelector("בחירה"))
        selector.set_items(
            [{"id": "1", "name": "אלפא"}, {"id": "2", "name": "בטא"}],
            label_key="name",
        )

        selector.combo.completer().setCompletionPrefix("אל")
        self.assertEqual(selector.combo.completer().completionCount(), 1)

        selector.select_id("1")
        self.assertEqual(selector.selected_id(), "1")

        selector.combo.lineEdit().setText("טקסט חופשי")
        selector._typed("טקסט חופשי")
        self.assertIsNone(selector.selected_id())
        self.assertEqual(
            selector.layoutDirection(),
            Qt.LayoutDirection.RightToLeft,
        )

    def test_booking_selectors_reject_arbitrary_clear_dependencies_and_hide_inactive(self):
        dialog = self._track(
            BookingFormDialog(
                customers=[{"id": "c1", "name": "לקוח", "is_active": True}],
                activities=[
                    {"id": "a1", "name": "פעילה", "is_active": True},
                    {"id": "a2", "name": "מושבתת", "is_active": False},
                ],
                instructors=[
                    {"id": "i1", "full_name": "מדריך", "is_active": True}
                ],
            )
        )

        # Placeholder + one active activity. Inactive activity is hidden.
        self.assertEqual(dialog.activity.count(), 2)

        dialog.customer_selector.select_id("c1")
        dialog.activity_selector.select_id("a1")
        dialog.instructor_selector.select_id("i1")
        self.assertEqual(dialog.values()["instructor_id"], "i1")

        dialog.activity_selector.clear_selection()
        self.assertIsNone(dialog.instructor_selector.selected_id())

        dialog.activity.lineEdit().setText("לא קיימת")
        dialog.activity_selector._typed("לא קיימת")
        self.assertNotIn("activity_id", dialog.values())

        dialog.accept()
        self.assertFalse(dialog.field_errors["activity_id"].isHidden())

    def test_selector_loading_empty_keyboard_and_rtl_details_geometry(self):
        selector = self._track(SearchableEntitySelector("בחירה"))
        selector.set_loading(True)
        self.assertFalse(selector.combo.isEnabled())

        selector.set_loading(False)
        selector.set_items([], label_key="name")
        self.assertFalse(selector.state.isHidden())

        selector.combo.setFocus()
        QTest.keyClick(selector.combo, Qt.Key.Key_Down)

        view = self._track(BookingsView("manager"))
        view.show_details(booking_details(BOOKING), [])

        # Detail cards still use the shared property-form foundation.
        for form in (
            view.booking_details,
            view.customer_details,
            view.system_details,
        ):
            for row in range(form.rowCount()):
                label_item = form.itemAt(row, QFormLayout.ItemRole.LabelRole)
                field_item = form.itemAt(row, QFormLayout.ItemRole.FieldRole)
                self.assertIsNotNone(label_item)
                self.assertIsNotNone(field_item)
                self.assertTrue(
                    label_item.widget().alignment()
                    & Qt.AlignmentFlag.AlignRight
                )
                self.assertTrue(
                    field_item.widget().alignment()
                    & Qt.AlignmentFlag.AlignRight
                )

    def test_filter_popover_applies_supported_filters_and_chips_remove_individually(self):
        view = self._track(BookingsView("manager"))
        view.show_filter_options(
            [],
            [{"id": "a1", "name": "קיץ"}, {"id": "a2", "name": "חורף"}],
            [
                {"id": "i1", "full_name": "מדריך א"},
                {"id": "i2", "full_name": "מדריך ב"},
            ],
        )

        emitted = []
        view.filters_requested.connect(emitted.append)

        for key in ("NEW", "CONFIRMED"):
            view.status_checks[key].setChecked(True)
        for key in ("a1", "a2"):
            view.activity_checks[key].setChecked(True)
        for key in ("i1", "i2"):
            view.instructor_checks[key].setChecked(True)

        view.unassigned_check.setChecked(True)
        view.from_filter.setText("2026-09-01")
        view._apply_popover_filters()

        self.assertEqual(emitted[-1]["status"], ["NEW", "CONFIRMED"])
        self.assertEqual(emitted[-1]["activity_id"], ["a1", "a2"])
        self.assertEqual(emitted[-1]["instructor_id"], ["i1", "i2"])
        self.assertEqual(emitted[-1]["assignment_state"], ["unassigned"])
        self.assertFalse(view.chips.isHidden())

        chips = [
            button
            for button in view.chips.findChildren(QToolButton)
            if button.property("filterChip")
        ]
        self.assertGreaterEqual(len(chips), 8)

        next(button for button in chips if "קיץ" in button.text()).click()
        self.assertEqual(emitted[-1]["activity_id"], ["a2"])
        self.assertEqual(emitted[-1]["status"], ["NEW", "CONFIRMED"])

    def test_booking_create_and_edit_dialogs_render_hebrew_form_rtl(self):
        create = self._track(
            BookingFormDialog(
                customers=[{"id": "c", "name": "לקוח"}],
                activities=[{"id": "a", "name": "פעילות"}],
                instructors=[],
            )
        )
        edit = self._track(BookingFormDialog(booking=BOOKING))

        for dialog in (create, edit):
            dialog.show()
            self.app.processEvents()

            self.assertEqual(
                dialog.layoutDirection(),
                Qt.LayoutDirection.RightToLeft,
            )
            self.assertTrue(
                dialog.heading_label.alignment()
                & Qt.AlignmentFlag.AlignRight
            )

            # BookingFormDialog now uses a QGridLayout rather than the legacy
            # QFormLayout. Verify the actual branded field labels by property.
            field_labels = [
                label
                for label in dialog.findChildren(QLabel)
                if bool(label.property("dialogFieldLabel"))
            ]
            section_labels = [
                label
                for label in dialog.findChildren(QLabel)
                if bool(label.property("dialogSectionTitle"))
            ]

            self.assertTrue(field_labels)
            self.assertTrue(section_labels)
            self.assertTrue(
                all(
                    label.alignment() & Qt.AlignmentFlag.AlignRight
                    for label in field_labels + section_labels
                )
            )

            for field in (
                dialog.city,
                dialog.venue,
                dialog.event_at,
                dialog.participants,
                dialog.price,
            ):
                self.assertTrue(
                    field.alignment() & Qt.AlignmentFlag.AlignRight
                )

            self.assertTrue(
                dialog.notes.alignment() & Qt.AlignmentFlag.AlignRight
            )

    def test_filter_popover_stays_inside_booking_page_at_supported_sizes(self):
        for width, height in ((1024, 640), (1200, 760), (1440, 900)):
            view = self._track(BookingsView("manager"))
            view.resize(width, height)
            view.show()
            self.app.processEvents()

            view.filter_button.click()
            self.app.processEvents()

            geometry = view.filter_popup.geometry()
            self.assertGreaterEqual(geometry.left(), 0)
            self.assertGreaterEqual(geometry.top(), 0)
            self.assertLess(geometry.right(), view.list_page.width())
            self.assertLess(geometry.bottom(), view.list_page.height())

            # Close immediately as well as registering cleanup because this
            # test deliberately creates several top-level views in one method.
            view.close()
            self.app.processEvents()

    def test_customer_filter_popup_hides_staffing_dimensions_and_keeps_customer_filters(self):
        view = self._track(BookingsView("customer"))
        emitted = []
        view.filters_requested.connect(emitted.append)

        self.assertFalse(view.status_section.isHidden())
        self.assertFalse(view.date_section.isHidden())
        self.assertFalse(view.activity_section.isHidden())
        self.assertTrue(view.assignment_section.isHidden())
        self.assertTrue(view.instructor_section.isHidden())

        view.unassigned_check.setChecked(True)
        view._emit_filters(search="test")
        self.assertNotIn("assignment_state", emitted[-1])
        self.assertNotIn("instructor_id", emitted[-1])
        self.assertEqual(emitted[-1]["search"], "test")

    def test_every_supported_status_and_assignment_queue_filter_emits_exact_contract(self):
        view = self._track(BookingsView("manager"))
        emitted = []
        queues = []
        view.filters_requested.connect(emitted.append)
        view.queue_requested.connect(queues.append)

        for status in ("NEW", "CONFIRMED", "CANCELLED", "COMPLETED"):
            view._clear_filter_choices()
            view.status_checks[status].setChecked(True)
            view._apply_popover_filters()
            self.assertEqual(emitted[-1]["status"], [status])

        view._clear_filter_choices()
        view.unassigned_check.setChecked(True)
        view._apply_popover_filters()
        self.assertEqual(
            emitted[-1]["assignment_state"],
            ["unassigned"],
        )
        self.assertEqual(queues, [])

    def test_customer_name_sort_emits_immediately_and_reset_restores_event_time(self):
        view = self._track(BookingsView("manager"))
        emitted = []
        view.filters_requested.connect(emitted.append)

        self.assertEqual(
            view.toolbar.sort_combo.itemData(1),
            "event_at_desc",
        )
        self.assertIn(
            "הרחוק ביותר",
            view.toolbar.sort_combo.itemText(1),
        )

        view.toolbar.sort_combo.setCurrentIndex(1)
        self.assertEqual(emitted[-1]["order_by"], "event_at_desc")

        self.assertEqual(
            view.toolbar.sort_combo.itemData(2),
            "customer_name",
        )
        self.assertIn(
            "שם לקוח",
            view.toolbar.sort_combo.itemText(2),
        )

        view.toolbar.sort_combo.setCurrentIndex(2)
        self.assertEqual(emitted[-1]["order_by"], "customer_name")

        view.toolbar.refresh_button.click()
        self.assertEqual(
            view.toolbar.sort_combo.currentData(),
            "event_at",
        )
        self.assertIn(
            "הקרוב ביותר",
            view.toolbar.sort_combo.currentText(),
        )
        self.assertEqual(emitted[-1]["order_by"], "event_at")
