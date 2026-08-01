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

    def _shown_manager_customers(self):
        shell = ShellView("manager@example.com")
        view = CustomersView()
        shell.configure_navigation((("customers", "לקוחות"),))
        shell.add_page("customers", view)
        shell.show_page("customers")
        shell.resize(1200, 760)
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
            self.assertGreater(self._center_x(heading, view), view.width() // 2)
            if view._detail_rows[key]:
                label = fields.itemAtPosition(0, 1).widget()
                value = fields.itemAtPosition(0, 0).widget()
                self.assertGreater(self._center_x(label, view), self._center_x(value, view))
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
        self.assertEqual(view.scaffold.header.description.text(), "ניהול לקוחות ופרטי קשר")
        shell.close()

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
