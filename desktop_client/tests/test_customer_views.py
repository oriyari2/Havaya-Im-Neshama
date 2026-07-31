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
            view.details.itemAt(row, QFormLayout.ItemRole.FieldRole).widget().text()
            for row in range(view.details.rowCount())
        )
        self.assertIn("איש קשר", rendered)
        self.assertIn("050-1", rendered)
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
