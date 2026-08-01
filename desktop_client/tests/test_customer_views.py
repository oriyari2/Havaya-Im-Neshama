import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest import TestCase

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFormLayout

from desktop_client.app.presenters.customer_formatting import customer_details
from desktop_client.app.views.customer_dialogs import CustomerDialog
from desktop_client.app.views.customer_profile_view import CustomerProfileView
from desktop_client.app.views.customers_view import CustomersView
from desktop_client.app.views.shell_view import ShellView


class CustomerViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def _center_x(widget, ancestor) -> int:
        return widget.mapTo(ancestor, widget.rect().center()).x()

    def _shown_manager_customers(self, width=1200, height=760):
        shell = ShellView("manager@example.com")
        view = CustomersView()
        shell.configure_navigation((("customers", "לקוחות"),))
        shell.add_page("customers", view)
        shell.show_page("customers")
        shell.resize(width, height)
        shell.show()
        self.app.processEvents()
        return shell, view

    def test_view_has_single_contact_details_and_no_multi_contact_controls(self):
        view = CustomersView()
        self.assertFalse(view.edit_button.isEnabled())
        self.assertFalse(view.delete_button.isEnabled())
        for obsolete in (
            "contacts",
            "add_contact",
            "edit_contact",
            "deactivate_contact",
            "reactivate_contact",
        ):
            self.assertFalse(hasattr(view, obsolete))
        customer = {"name": "לקוח", "is_active": True}
        contact = {"id": "ct1", "full_name": "איש קשר", "phone": "050-1", "is_primary": True, "is_active": True}
        customer["contacts"] = [contact]
        view.show_details(customer_details(customer), customer)
        rendered = " ".join(
            fields.itemAtPosition(row, 0).widget().text()
            for key, fields in view.detail_forms.items()
            for row in range(view._detail_rows[key])
        )
        self.assertIn("איש קשר", rendered)
        self.assertIn("050-1", rendered)
        self.assertEqual(view._detail_rows, {"customer": 7, "contact": 2, "system": 3})
        profile = CustomerProfileView()
        self.assertFalse(hasattr(profile, "contacts"))
        profile.show_profile(customer_details(customer))
        profile_rendered = " ".join(
            profile.details.itemAt(row, QFormLayout.ItemRole.FieldRole).widget().text()
            for row in range(profile.details.rowCount())
        )
        self.assertIn("איש קשר", profile_rendered)
        self.assertIn("050-1", profile_rendered)

    def test_dialog_exposes_single_contact_name_and_phone(self):
        dialog = CustomerDialog({"name": "Task 21 Customer", "contact_name": "Person", "contact_phone": "050"})
        values = dialog.values()
        self.assertEqual(values["name"], "Task 21 Customer")
        self.assertEqual(values["contact_name"], "Person")
        self.assertEqual(values["contact_phone"], "050")
        self.assertNotIn("role_title", values)
        self.assertNotIn("is_primary", values)
        self.assertNotIn("is_active", values)
        dialog.show_error("bad")
        self.assertFalse(dialog.error_label.isHidden())
        dialog.set_submitting(True)
        self.assertFalse(dialog.buttons.isEnabled())
        self.assertGreaterEqual(dialog.minimumWidth(), 760)
        self.assertEqual(dialog.save_button.text(), "שמירת שינויים")
        self.assertEqual(dialog.save_button.minimumWidth(), dialog.cancel_button.minimumWidth())
        section_titles = [label.text() for label in dialog.findChildren(type(dialog.heading_label)) if label.objectName() == "sectionTitle"]
        self.assertCountEqual(section_titles, ["פרטי לקוח", "פרטי איש קשר", "הערות"])

    def test_create_dialog_has_specific_primary_action_and_required_field_guidance(self):
        dialog = CustomerDialog()
        dialog.show()
        self.app.processEvents()
        self.assertEqual(dialog.heading_label.text(), "לקוח חדש")
        self.assertEqual(dialog.required_hint.text(), "* שדה חובה")
        self.assertEqual(dialog.save_button.text(), "יצירת לקוח")
        self.assertEqual(dialog.save_button.objectName(), "customerDialogPrimary")
        self.assertIsNotNone(dialog.password)
        self.assertIsNotNone(dialog.password_confirmation)
        self.assertEqual(dialog.password.echoMode(), dialog.password.EchoMode.Password)
        self.assertIn("password", dialog.values())
        self.assertGreaterEqual(dialog.notes.minimumHeight(), 88)
        self.assertEqual(dialog.scroll.horizontalScrollBar().maximum(), 0)
        self.assertLess(dialog.fields["name"].mapTo(dialog, dialog.fields["name"].rect().topLeft()).y(), dialog.fields["contact_name"].mapTo(dialog, dialog.fields["contact_name"].rect().topLeft()).y())
        self.assertLess(dialog.fields["contact_name"].mapTo(dialog, dialog.fields["contact_name"].rect().topLeft()).y(), dialog.notes.mapTo(dialog, dialog.notes.rect().topLeft()).y())
        self.assertGreater(self._center_x(dialog.heading_label, dialog), dialog.width() // 2)
        self.assertGreater(self._center_x(dialog.save_button, dialog), self._center_x(dialog.cancel_button, dialog))
        name_label = dialog.form.labelForField(dialog.fields["name"])
        self.assertGreater(self._center_x(name_label, dialog), dialog.width() // 2)
        self.assertLess(name_label.geometry().bottom(), dialog.fields["name"].geometry().top())
        dialog.close()

    def test_edit_dialog_does_not_expose_account_creation_secrets(self):
        dialog = CustomerDialog({"name": "לקוח", "contact_name": "איש", "contact_phone": "050"})
        self.assertIsNone(dialog.password)
        self.assertNotIn("password", dialog.values())
        self.assertNotIn("password_confirmation", dialog.values())

    def test_edit_dialog_reuses_the_same_rendered_rtl_form_geometry(self):
        dialog = CustomerDialog({"name": "לקוח", "contact_name": "איש קשר", "contact_phone": "050"})
        dialog.show()
        self.app.processEvents()
        self.assertEqual(dialog.heading_label.text(), "עריכת לקוח")
        self.assertEqual(dialog.save_button.text(), "שמירת שינויים")
        self.assertGreater(self._center_x(dialog.heading_label, dialog), dialog.width() // 2)
        self.assertGreater(self._center_x(dialog.save_button, dialog), self._center_x(dialog.cancel_button, dialog))
        self.assertEqual(dialog.scroll.horizontalScrollBar().maximum(), 0)
        dialog.close()

    def test_list_selection_open_paths_and_return_preserve_list_state(self):
        view = CustomersView()
        selected = []
        view.customer_selected.connect(selected.append)
        view.show_customers([
            {"id": "c1", "name": "לקוח", "customer_type": "עסקי", "city": "חיפה", "phone": "050", "email": "a@example.com", "is_active": True}
        ], offset=0, count=1, filtered=False)
        view.toolbar.search_input.setText("לקוח")
        view.select_customer("c1")
        self.assertEqual(selected, ["c1"])
        self.assertIs(view.pages.currentWidget(), view.list_page)

        QTest.keyClick(view.table, Qt.Key.Key_Return)
        self.assertIs(view.pages.currentWidget(), view.details_page)
        self.assertTrue(view.scaffold.header.isHidden())
        view.back_button.click()
        self.assertIs(view.pages.currentWidget(), view.list_page)
        self.assertFalse(view.scaffold.header.isHidden())
        self.assertEqual(view.toolbar.search_input.text(), "לקוח")
        self.assertEqual(view.table.currentRow(), 0)

        view.table.cellDoubleClicked.emit(0, 0)
        self.assertIs(view.pages.currentWidget(), view.details_page)

    def test_details_header_and_actions_keep_rtl_regions(self):
        shell, view = self._shown_manager_customers()
        customer = {"id": "c1", "name": "לקוח", "is_active": True, "contacts": []}
        view.show_customers([{**customer, "customer_type": "עסקי", "city": "חיפה", "phone": "050", "email": "a@example.com"}], offset=0, count=1, filtered=False)
        view.show_details(customer_details(customer), customer)
        view.select_customer("c1")
        view._open_selected_customer()
        self.app.processEvents()
        self.assertGreater(self._center_x(view.identity_container, view), self._center_x(view.actions_container, view))
        self.assertLess(self._center_x(view.back_button, view), view.width() // 2)
        for key, fields in view.detail_forms.items():
            heading = view.detail_groups[key].section_heading
            group = view.detail_groups[key]
            self.assertGreater(self._center_x(heading, group), group.width() // 2)
            if view._detail_rows[key]:
                label = fields.itemAtPosition(0, 1).widget()
                value = fields.itemAtPosition(0, 0).widget()
                self.assertGreater(self._center_x(label, view), self._center_x(value, view))
        labels = [
            fields.itemAtPosition(row, 1).widget()
            for key, fields in view.detail_forms.items()
            for row in range(view._detail_rows[key])
        ]
        values = [
            fields.itemAtPosition(row, 0).widget()
            for key, fields in view.detail_forms.items()
            for row in range(view._detail_rows[key])
        ]
        self.assertEqual(len({label.width() for label in labels}), 1)
        for key, fields in view.detail_forms.items():
            right_edges = [
                fields.itemAtPosition(row, 0).widget().geometry().right()
                for row in range(view._detail_rows[key])
            ]
            self.assertLessEqual(max(right_edges) - min(right_edges), 1)
        for widget in labels + values:
            self.assertTrue(widget.alignment() & Qt.AlignmentFlag.AlignRight)
            self.assertTrue(widget.alignment() & Qt.AlignmentFlag.AlignAbsolute)
        shell.close()

    def test_details_switches_between_wide_rtl_composition_and_narrow_stack(self):
        customer = {
            "id": "c1", "name": "לקוח", "customer_type": "עסקי", "city": "חיפה",
            "email": "a-very-long-customer-address@example-domain.test", "is_active": True,
            "contacts": [{"full_name": "איש קשר", "phone": "050-1234567", "is_primary": True, "is_active": True}],
        }
        for size, expect_wide in (((1024, 640), False), ((1200, 760), True), ((1440, 900), True)):
            shell, view = self._shown_manager_customers(*size)
            view.show_customers([customer], offset=0, count=1, filtered=False)
            view.show_details(customer_details(customer), customer)
            view.select_customer("c1")
            view._open_selected_customer()
            self.app.processEvents()
            groups = view.detail_groups
            if expect_wide:
                self.assertGreater(groups["customer"].geometry().x(), groups["contact"].mapTo(view.details_widget, groups["contact"].rect().topLeft()).x())
                ratio = groups["customer"].width() / view.details_scroll.viewport().width()
                self.assertGreaterEqual(ratio, 0.58)
                self.assertLessEqual(ratio, 0.66)
                self.assertEqual(view.details_scroll.verticalScrollBar().maximum(), 0)
            else:
                tops = [groups[key].mapTo(view.details_widget, groups[key].rect().topLeft()).y() for key in ("customer", "contact", "system")]
                self.assertEqual(tops, sorted(tops))
                self.assertEqual(len(set(tops)), 3)
            self.assertEqual(view.details_scroll.horizontalScrollBar().maximum(), 0)
            self.assertGreater(self._center_x(view.identity_container, view), self._center_x(view.actions_container, view))
            email = view.customer_details.itemAtPosition(5, 0).widget()
            self.assertIn("example-domain.test", email.toolTip())
            shell.close()

    def test_sort_by_is_a_single_immediate_selection_without_extra_editors(self):
        view = CustomersView()
        emitted = []
        view.filters_requested.connect(emitted.append)
        self.assertEqual(view.sort_by.count(), 2)
        self.assertFalse(hasattr(view, "filter_panel"))
        self.assertFalse(hasattr(view, "apply_filters_button"))
        view.sort_by.setCurrentIndex(view.sort_by.findData("created_at"))
        self.assertEqual(emitted[-1], {"order_by": "created_at"})
        self.assertEqual(emitted[-1]["order_by"], "created_at")

    def test_final_list_polish_prioritizes_search_table_and_compact_pager(self):
        shell, view = self._shown_manager_customers()
        view.show_customers([{
            "id": "c1", "name": "לקוח", "customer_type": "עסקי", "city": "חיפה",
            "phone": "050", "email": "a@example.com", "is_active": True,
        }], offset=0, count=1, filtered=False)
        self.app.processEvents()
        self.assertEqual(view.toolbar.search_button.objectName(), "customerSearchButton")
        positions = [
            self._center_x(control, view)
            for control in (view.toolbar.search_input, view.toolbar.search_button, view.sort_by, view.toolbar.refresh_button)
        ]
        self.assertEqual(positions, sorted(positions, reverse=True))
        self.assertEqual(view.sort_by.currentData(), "name")
        self.assertLessEqual(view.footer.width(), 440)
        self.assertGreater(view.table.height(), 350)
        self.assertGreater(view.table.columnWidth(0), view.table.columnWidth(1))
        self.assertGreater(self._center_x(view.scaffold.header.title, view), self._center_x(view.create_button, view))
        self.assertEqual([view.table.horizontalHeader().visualIndex(column) for column in range(4)], [0, 1, 2, 3])
        for column in range(3):
            alignment = view.table.item(0, column).textAlignment()
            self.assertTrue(alignment & Qt.AlignmentFlag.AlignRight)
            self.assertTrue(alignment & Qt.AlignmentFlag.AlignAbsolute)
        status = view.table.cellWidget(0, 3)
        self.assertTrue(status.alignment() & Qt.AlignmentFlag.AlignRight)
        self.assertTrue(status.alignment() & Qt.AlignmentFlag.AlignAbsolute)
        self.assertEqual(view.scaffold.header.description.text(), "ניהול לקוחות ופרטי קשר")
        shell.close()

    def test_customer_table_semantic_widths_and_scrollbars_at_supported_sizes(self):
        long_name = "שם לקוח ארוך במיוחד שנועד להיחתך בצורה תקינה"
        for width, height in ((1024, 640), (1200, 760), (1440, 900)):
            shell, view = self._shown_manager_customers(width, height)
            view.show_customers([{
                "id": "c1", "name": long_name, "customer_type": "לקוח עסקי",
                "city": "ירושלים", "phone": "050", "email": "a@example.com", "is_active": False,
            }], offset=0, count=1, filtered=False)
            self.app.processEvents()
            widths = [view.table.columnWidth(column) for column in range(4)]
            self.assertEqual(view.table.columnCount(), 4)
            self.assertGreater(widths[0], max(widths[1:]))
            self.assertGreaterEqual(widths[1], 140)
            self.assertLessEqual(widths[1], 220)
            self.assertGreaterEqual(widths[2], 150)
            self.assertLessEqual(widths[2], 240)
            self.assertGreaterEqual(widths[3], 110)
            self.assertEqual(view.table.horizontalScrollBar().maximum(), 0)
            self.assertEqual(view.table.verticalScrollBar().maximum(), 0)
            for column in range(4):
                required = view.table.fontMetrics().horizontalAdvance(view.table.horizontalHeaderItem(column).text()) + 24
                self.assertGreaterEqual(widths[column], required)
            self.assertIn(long_name, view.table.item(0, 0).toolTip())
            if width == 1024:
                rows = [{
                    "id": f"c{index}", "name": f"לקוח {index}", "customer_type": "עסקי",
                    "city": "חיפה", "phone": "050", "email": "a@example.com", "is_active": True,
                } for index in range(40)]
                view.show_customers(rows, offset=0, count=len(rows), filtered=False)
                self.app.processEvents()
                self.assertGreater(view.table.verticalScrollBar().maximum(), 0)
            shell.close()

        view = CustomersView()
        view.resize(900, 640)
        view.table.setFixedWidth(500)
        view.show()
        self.app.processEvents()
        self.assertGreater(view.table.horizontalScrollBar().maximum(), 0)
        self.assertEqual([view.table.columnWidth(column) for column in range(4)], [180, 140, 150, 110])
        view.close()

    def test_reset_clears_search_sort_and_selection_and_returns_to_first_page(self):
        view = CustomersView()
        emitted = []
        view.filters_requested.connect(emitted.append)
        view.toolbar.search_input.setText("לקוח")
        view.sort_by.setCurrentIndex(view.sort_by.findData("created_at"))
        view.show_customers([{"id": "c1", "name": "לקוח", "customer_type": "עסקי", "city": "חיפה", "phone": "050", "email": "a@example.com", "is_active": True}], offset=0, count=1, filtered=False)
        view.select_customer("c1")
        view.toolbar.refresh_button.click()
        self.assertEqual(emitted[-1], {"search": None, "order_by": "name", "_clear_selection": True})
        self.assertEqual(view.toolbar.search_input.text(), "")
        self.assertEqual(view.sort_by.currentData(), "name")
        self.assertIsNone(view._selected_customer_id)

    def test_empty_states_offer_create_or_filter_reset_without_empty_table(self):
        view = CustomersView()
        created = []
        filters = []
        view.create_requested.connect(lambda: created.append(True))
        view.filters_requested.connect(filters.append)
        view.show_customers([], offset=0, count=0, filtered=False)
        self.assertIs(view.table_region.currentWidget(), view.empty_state)
        self.assertEqual(view.empty_title.text(), "אין עדיין לקוחות")
        self.assertTrue(view.footer.isHidden())
        self.assertTrue(view.view_details_button.isHidden())
        view.empty_action_button.click()
        self.assertEqual(created, [True])
        view.toolbar.search_input.setText("missing")
        view.show_customers([], offset=0, count=0, filtered=True)
        self.assertEqual(view.empty_title.text(), "לא נמצאו לקוחות")
        view.empty_action_button.click()
        self.assertEqual(filters[-1]["search"], None)

    def test_empty_nonfirst_page_returns_to_previous_valid_page(self):
        view = CustomersView()
        requested = []
        view.page_requested.connect(lambda offset, limit: requested.append((offset, limit)))
        view.show_customers([], offset=25, count=0, filtered=False)
        self.assertEqual(requested, [(0, 25)])
        self.assertIs(view.pages.currentWidget(), view.list_page)
