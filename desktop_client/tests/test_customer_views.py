import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest import TestCase

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QBoxLayout, QFormLayout, QToolButton

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
        self.assertFalse(view.deactivate_button.isVisible())
        self.assertFalse(view.reactivate_button.isVisible())
        self.assertFalse(view.change_password_button.isEnabled())
        self.assertEqual(view.change_password_button.text(), "שינוי סיסמה")
        self.assertIs(view.scaffold.header.title.parentWidget(), view.header_identity)
        self.assertIs(view.scaffold.header.description.parentWidget(), view.header_identity)
        self.assertFalse(view.scaffold.header.description.wordWrap())
        self.assertEqual({button.minimumWidth() for button in (view.edit_button, view.change_password_button, view.deactivate_button, view.reactivate_button)}, {148})
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
            fields.itemAt(row, QFormLayout.ItemRole.FieldRole).widget().text()
            for fields in view.detail_forms.values()
            for row in range(fields.rowCount())
        )
        self.assertIn("איש קשר", rendered)
        self.assertIn("050-1", rendered)
        self.assertEqual({key: form.rowCount() for key, form in view.detail_forms.items()}, {"customer": 5, "contact": 4, "system": 3})
        profile = CustomerProfileView()
        self.assertFalse(hasattr(profile, "contacts"))
        profile.show_profile(customer_details(customer))
        profile_rendered = " ".join(
            profile.details.itemAt(row, QFormLayout.ItemRole.FieldRole).widget().text()
            for row in range(profile.details.rowCount())
        )
        self.assertIn("איש קשר", profile_rendered)
        self.assertIn("050-1", profile_rendered)

    def test_customer_lifecycle_action_matches_active_state(self):
        view = CustomersView()
        for active, deactivate_visible, reactivate_visible in ((True, True, False), (False, False, True)):
            customer = {"id": "c1", "name": "לקוח", "is_active": active, "contacts": []}
            view.show_details(customer_details(customer), customer)
            self.assertEqual(not view.deactivate_button.isHidden(), deactivate_visible)
            self.assertEqual(not view.reactivate_button.isHidden(), reactivate_visible)
            self.assertFalse(hasattr(view, "delete_button"))
    def test_dialog_exposes_single_contact_name_and_phone(self):
        dialog = CustomerDialog({"name": "Task 21 Customer", "contact_name": "Person", "contact_phone": "050"})
        values = dialog.values()
        self.assertEqual(values["name"], "Task 21 Customer")
        self.assertEqual(values["contact_name"], "Person")
        self.assertEqual(values["contact_phone"], "050")
        self.assertNotIn("role_title", values)
        self.assertNotIn("is_primary", values)
        self.assertNotIn("is_active", values)
        self.assertTrue(dialog.fields["email"].isReadOnly())
        dialog.show_error("bad")
        self.assertFalse(dialog.error_label.isHidden())
        dialog.set_submitting(True)
        self.assertFalse(dialog.save_button.isEnabled())
        self.assertTrue(dialog.cancel_button.isEnabled())
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
        self.assertGreater(
            name_label.mapTo(dialog, name_label.rect().topLeft()).x(),
            dialog.fields["name"].mapTo(dialog, dialog.fields["name"].rect().topRight()).x(),
        )
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
        customer = {"id": "c1", "name": "לקוח", "customer_type": "עסקי", "city": "חיפה", "phone": "050", "email": "a@example.com", "is_active": True}
        view.customer_selected.connect(lambda _id: view.show_details(customer_details(customer), customer))
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

        view.table.cellDoubleClicked.emit(0, 1)
        self.assertIs(view.pages.currentWidget(), view.details_page)
        view.back_button.click()
        action = view.table.cellWidget(0, 0).findChild(QToolButton)
        self.assertEqual(action.objectName(), "managementRowOpenAction")
        self.assertFalse(action.icon().isNull())
        action.click()
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
        for fields in view.detail_forms.values():
            if fields.rowCount():
                label = fields.itemAt(0, QFormLayout.ItemRole.LabelRole).widget()
                value = fields.itemAt(0, QFormLayout.ItemRole.FieldRole).widget()
                self.assertGreater(self._center_x(label, view), self._center_x(value, view))
        labels = [
            fields.itemAt(row, QFormLayout.ItemRole.LabelRole).widget()
            for fields in view.detail_forms.values()
            for row in range(fields.rowCount())
        ]
        values = [
            fields.itemAt(row, QFormLayout.ItemRole.FieldRole).widget()
            for fields in view.detail_forms.values()
            for row in range(fields.rowCount())
        ]
        self.assertEqual(len({label.width() for label in labels}), 1)
        for fields in view.detail_forms.values():
            right_edges = [
                fields.itemAt(row, QFormLayout.ItemRole.FieldRole).widget().geometry().right()
                for row in range(fields.rowCount())
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
            if expect_wide:
                self.assertEqual(view.workspace.cards.direction(), QBoxLayout.Direction.RightToLeft)
                self.assertEqual(view.details_scroll.verticalScrollBar().maximum(), 0)
            else:
                self.assertEqual(view.workspace.cards.direction(), QBoxLayout.Direction.TopToBottom)
            self.assertEqual(view.details_scroll.horizontalScrollBar().maximum(), 0)
            self.assertGreater(self._center_x(view.identity_container, view), self._center_x(view.actions_container, view))
            email = view.contact_details.itemAt(1, QFormLayout.ItemRole.FieldRole).widget()
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
        self.assertEqual(view.table.columnWidth(0), 52)
        self.assertGreater(view.table.columnWidth(1), view.table.columnWidth(2))
        self.assertGreater(self._center_x(view.scaffold.header.title, view), self._center_x(view.create_button, view))
        self.assertEqual([view.table.horizontalHeader().visualIndex(column) for column in range(5)], [0, 1, 2, 3, 4])
        for column in range(1, 4):
            alignment = view.table.item(0, column).textAlignment()
            self.assertTrue(alignment & Qt.AlignmentFlag.AlignRight)
            self.assertTrue(alignment & Qt.AlignmentFlag.AlignAbsolute)
        status = view.table.cellWidget(0, 4)
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
            widths = [view.table.columnWidth(column) for column in range(5)]
            self.assertEqual(view.table.columnCount(), 5)
            self.assertEqual(widths[0], 52)
            self.assertGreater(widths[1], max(widths[2:]))
            self.assertGreaterEqual(widths[2], 140)
            self.assertLessEqual(widths[2], 220)
            self.assertGreaterEqual(widths[3], 150)
            self.assertLessEqual(widths[3], 240)
            self.assertGreaterEqual(widths[4], 110)
            self.assertEqual(view.table.horizontalScrollBar().maximum(), 0)
            self.assertEqual(view.table.verticalScrollBar().maximum(), 0)
            for column in range(1, 5):
                required = view.table.fontMetrics().horizontalAdvance(view.table.horizontalHeaderItem(column).text()) + 24
                self.assertGreaterEqual(widths[column], required)
            self.assertIn(long_name, view.table.item(0, 1).toolTip())
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
        self.assertEqual([view.table.columnWidth(column) for column in range(5)], [52, 180, 140, 150, 110])
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
        self.assertFalse(hasattr(view, "view_details_button"))
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
