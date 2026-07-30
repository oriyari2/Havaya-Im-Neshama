import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")

from unittest import TestCase

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLineEdit

from desktop_client.app.views.user_dialogs import CreateUserDialog, EditUserDialog, ResetPasswordDialog
from desktop_client.app.views.users_view import UsersView


USER={"id":"u1","email":"user@example.com","role":"customer","is_active":True,"customer_id":"c1","customer_name":"לקוח","instructor_id":None,"instructor_name":None,"created_at":"2026-01-01","updated_at":"2026-01-02"}


class UserViewTests(TestCase):
    @classmethod
    def setUpClass(cls): cls.app=QApplication.instance() or QApplication([])

    def test_page_table_filters_details_and_self_deactivation(self) -> None:
        view=UsersView(); self.assertTrue(view.table.property("task20Table")); self.assertEqual(view.table.accessibleName(),"רשימת משתמשים")
        view.show_users([USER],offset=0,count=1,filtered=False); self.assertIn('dir="ltr"',view.table.item(0,0).toolTip()); self.assertIn("user@example.com",view.table.item(0,0).toolTip())
        view.show_details(USER,current_user_id="u1"); self.assertFalse(view.deactivate_button.isEnabled()); self.assertTrue(view.edit_button.isEnabled()); self.assertTrue(view.reset_button.isEnabled())
        view.show_details(USER,current_user_id="other"); self.assertTrue(view.deactivate_button.isEnabled()); self.assertFalse(view.activate_button.isEnabled())

    def test_create_dialog_role_dependent_profiles_and_secret_handling(self) -> None:
        dialog=CreateUserDialog([{"id":"c1","name":"לקוח"}],[{"id":"i1","full_name":"מדריך"}]); self.assertEqual(dialog.email.layoutDirection(),Qt.LayoutDirection.LeftToRight); self.assertEqual(dialog.password.echoMode(),QLineEdit.EchoMode.Password)
        dialog.role.setCurrentIndex(dialog.role.findData("customer")); self.assertFalse(dialog.customer.isHidden()); self.assertTrue(dialog.instructor.isHidden()); dialog.customer.setCurrentIndex(1)
        dialog.email.setText("c@example.com"); dialog.password.setText("password1"); dialog.confirmation.setText("password1"); self.assertEqual(dialog.values()["customer_id"],"c1")
        dialog.show_error("שגיאה"); self.assertEqual(dialog.password.text(),""); self.assertEqual(dialog.confirmation.text(),"")

    def test_edit_is_email_only_and_reset_has_no_forced_change(self) -> None:
        edit=EditUserDialog(USER); self.assertEqual(edit.values(),{"email":"user@example.com"}); self.assertFalse(hasattr(edit,"role_input"))
        reset=ResetPasswordDialog(USER); self.assertEqual(reset.password.echoMode(),QLineEdit.EchoMode.Password); self.assertEqual(set(reset.values()),{"password","password_confirmation"}); self.assertFalse(hasattr(reset,"temporary")); self.assertFalse(hasattr(reset,"must_change"))

    def test_responsive_semantic_table_uses_viewport(self) -> None:
        view=UsersView(); policies=view.table._task20_column_sizer.policies; self.assertEqual(policies[0].kind.value,"primary_text"); self.assertGreater(policies[0].stretch_weight,max(policy.stretch_weight for policy in policies[1:])); view.resize(1024,640); view.show(); self.app.processEvents(); widths=[view.table.columnWidth(i) for i in range(view.table.columnCount())]; unused=view.table.viewport().width()-1-sum(widths); self.assertTrue(abs(unused)<=1 or unused<0); self.assertGreater(widths[0],widths[3]); view.close()
