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


class CustomerViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

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
            form.itemAt(row, QFormLayout.ItemRole.FieldRole).widget().text()
            for form in view.detail_forms.values()
            for row in range(form.rowCount())
        )
        self.assertIn("איש קשר", rendered)
        self.assertIn("050-1", rendered)
        self.assertEqual(view.customer_details.rowCount(), 7)
        self.assertEqual(view.contact_details.rowCount(), 2)
        self.assertEqual(view.system_details.rowCount(), 3)
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
        self.assertEqual(dialog.scroll.verticalScrollBar().maximum(), 0)
        self.assertEqual(dialog.scroll.horizontalScrollBar().maximum(), 0)
        self.assertGreater(dialog.fields["name"].mapTo(dialog, dialog.fields["name"].rect().topLeft()).x(), dialog.fields["contact_name"].mapTo(dialog, dialog.fields["contact_name"].rect().topLeft()).x())
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

    def test_advanced_filters_are_progressively_disclosed_without_losing_functionality(self):
        view = CustomersView()
        emitted = []
        view.filters_requested.connect(emitted.append)
        self.assertTrue(view.advanced_filters.isHidden())
        view.advanced_filters_button.click()
        self.assertFalse(view.advanced_filters.isHidden())
        view.city.setEditText("חיפה")
        view.kind.setEditText("עסקי")
        view.active.setCurrentIndex(view.active.findData(True))
        view.order.setCurrentIndex(view.order.findData("created_at"))
        view.apply_filters_button.click()
        self.assertEqual(emitted[-1], {"city": "חיפה", "customer_type": "עסקי", "is_active": True, "order_by": "created_at"})

    def test_final_list_polish_prioritizes_search_table_and_compact_pager(self):
        view = CustomersView()
        view.resize(1200, 760)
        view.show()
        self.app.processEvents()
        self.assertEqual(view.toolbar.search_button.objectName(), "customerSearchButton")
        self.assertGreater(view.toolbar.search_input.geometry().x(), view.toolbar.search_button.geometry().x())
        self.assertTrue(view.advanced_filters.isHidden())
        self.assertLessEqual(view.footer.width(), 440)
        self.assertGreater(view.table.height(), 350)
        self.assertGreater(view.table.columnWidth(0), view.table.columnWidth(1))
        self.assertGreater(view.scaffold.header.title.geometry().x(), view.create_button.geometry().x())
        self.assertEqual(view.scaffold.header.description.text(), "ניהול לקוחות ופרטי קשר")
        view.close()

    def test_reset_clears_all_filter_state_and_returns_to_first_page(self):
        view = CustomersView()
        emitted = []
        view.filters_requested.connect(emitted.append)
        view.toolbar.search_input.setText("לקוח")
        view.order.setCurrentIndex(view.order.findData("created_at"))
        view.city.setEditText("חיפה")
        view.kind.setEditText("עסקי")
        view.active.setCurrentIndex(view.active.findData(True))
        view.advanced_filters_button.click()
        view.toolbar.refresh_button.click()
        self.assertEqual(emitted[-1], {"search": None, "city": None, "customer_type": None, "is_active": None, "order_by": "name"})
        self.assertEqual(view.toolbar.search_input.text(), "")
        self.assertEqual(view.order.currentData(), "name")
        self.assertTrue(view.advanced_filters.isHidden())

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
