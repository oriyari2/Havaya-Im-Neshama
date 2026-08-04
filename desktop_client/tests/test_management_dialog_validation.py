import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest import TestCase

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from desktop_client.app.shared.ui.account_dialogs import ChangePasswordDialog
from desktop_client.app.features.customers.dialogs import CustomerDialog
from desktop_client.app.features.instructors.dialogs import InstructorDialog
from desktop_client.app.features.users.dialogs import CreateUserDialog, EditUserDialog


class ManagementDialogValidationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_incomplete_create_forms_keep_submit_enabled_and_do_not_submit(self):
        for dialog in (CustomerDialog(), InstructorDialog(), CreateUserDialog()):
            submitted = []
            dialog.submitted.connect(lambda values, form: submitted.append(values))
            dialog.show()
            self.app.processEvents()
            self.assertTrue(dialog.save_button.isEnabled())
            dialog.save_button.click()
            self.app.processEvents()
            self.assertEqual(submitted, [])
            self.assertFalse(dialog.error_label.isHidden())
            self.assertIs(dialog.focusWidget(), next(field for key, field in dialog.fields.items() if not str(dialog.values().get(key, "")).strip() and key in dialog.validation_errors()))
            dialog.close()

    def test_invalid_email_and_mismatched_password_have_field_feedback_and_clear(self):
        dialog = CustomerDialog()
        dialog.fields["name"].setText("לקוח")
        dialog.fields["email"].setText("bad")
        dialog.fields["password"].setText("password1")
        dialog.fields["password_confirmation"].setText("different")
        dialog.show(); self.app.processEvents(); dialog.save_button.click(); self.app.processEvents()
        self.assertIn("דוא״ל", dialog.field_errors["email"].text())
        self.assertIn("אינן תואמות", dialog.field_errors["password_confirmation"].text())
        self.assertIs(dialog.focusWidget(), dialog.fields["email"])
        self.assertTrue(dialog.fields["email"].property("invalid"))
        dialog.fields["email"].setText("customer@example.com"); self.app.processEvents()
        self.assertTrue(dialog.field_errors["email"].isHidden())
        self.assertFalse(dialog.fields["email"].property("invalid"))
        dialog.close()

    def test_password_dialog_validates_on_click_and_disables_only_during_request(self):
        dialog = ChangePasswordDialog(); submitted = []; dialog.submitted.connect(lambda values, form: submitted.append(values))
        self.assertLess(dialog.height(), 520)
        self.assertTrue(dialog.save_button.isEnabled())
        dialog.password.setText("password1"); dialog.confirmation.setText("different"); dialog.save_button.click(); self.app.processEvents()
        self.assertEqual(submitted, []); self.assertIn("אינן תואמות", dialog.field_errors["password_confirmation"].text()); self.assertIs(dialog.focusWidget(), dialog.confirmation)
        dialog.confirmation.setText("password1"); self.app.processEvents(); self.assertTrue(dialog.field_errors["password_confirmation"].isHidden()); self.assertTrue(dialog.save_button.isEnabled())
        dialog.set_submitting(True); self.assertFalse(dialog.save_button.isEnabled()); self.assertTrue(dialog.cancel_button.isEnabled())
        dialog.set_submitting(False); self.assertTrue(dialog.save_button.isEnabled()); dialog.close()

    def test_create_and_edit_dialogs_share_the_same_validation_mechanism(self):
        manager = EditUserDialog({"email": "manager@example.com", "display_name": "מנהל"}); manager.manager_name.clear()
        dialogs = (CustomerDialog({"name": "", "contact_name": "", "contact_phone": ""}), InstructorDialog({"full_name": "", "email": "guide@example.com"}), manager)
        for dialog in dialogs:
            submitted=[]; dialog.submitted.connect(lambda values, form: submitted.append(values)); dialog.save_button.click(); self.app.processEvents()
            self.assertEqual(submitted, []); self.assertTrue(any(not error.isHidden() for error in dialog.field_errors.values())); self.assertFalse(dialog.error_label.isHidden()); dialog.close()

    def test_validation_banner_fades_automatically(self):
        dialog = CreateUserDialog(); dialog.show(); self.app.processEvents(); dialog.save_button.click(); self.app.processEvents()
        self.assertFalse(dialog.error_label.isHidden()); self.assertEqual(dialog.error_label.property("feedback"), "error")
        QTest.qWait(3100)
        self.assertTrue(dialog.error_label.isHidden()); dialog.close()
