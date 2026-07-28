import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from unittest import TestCase
from PySide6.QtWidgets import QApplication
from desktop_client.app.views.customer_dialogs import ContactDialog, CustomerDialog
from desktop_client.app.views.customer_profile_view import CustomerProfileView
from desktop_client.app.views.customers_view import CustomersView

class CustomerViewTests(TestCase):
    @classmethod
    def setUpClass(cls): cls.app=QApplication.instance() or QApplication([])
    def test_views_construct_and_actions_start_disabled(self):
        view=CustomersView(); self.assertFalse(view.edit_button.isEnabled()); self.assertFalse(view.delete_button.isEnabled()); self.assertFalse(view.add_contact.isEnabled()); self.assertFalse(hasattr(view,"reactivate_button")); CustomerProfileView()
    def test_dialog_values_and_failed_state_remains_open(self):
        dialog=CustomerDialog({"name":"Task 12B"}); self.assertEqual(dialog.values()["name"],"Task 12B"); self.assertNotIn("is_active",dialog.values()); dialog.show_error("bad"); self.assertFalse(dialog.error_label.isHidden()); dialog.set_submitting(True); self.assertFalse(dialog.buttons.isEnabled()); ContactDialog({"full_name":"Person"})
