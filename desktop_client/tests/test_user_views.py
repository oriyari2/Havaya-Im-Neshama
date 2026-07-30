import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")

from unittest import TestCase
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFormLayout, QLineEdit

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

    def test_visible_actions_and_selection_states(self) -> None:
        view=UsersView(); self.assertEqual(view.create_button.text(),"יצירת משתמש"); self.assertEqual(view.deactivate_button.text(),"מחיקת משתמש"); self.assertEqual(view.activate_button.text(),"הפעלה"); self.assertEqual(view.reset_button.text(),"איפוס סיסמה"); self.assertEqual(view.toolbar.refresh_button.text(),"רענון")
        self.assertFalse(view.create_button.isHidden()); self.assertTrue(view.create_button.isEnabled()); self.assertFalse(view.deactivate_button.isEnabled()); self.assertFalse(view.activate_button.isEnabled()); self.assertFalse(view.reset_button.isEnabled()); self.assertFalse(view.edit_button.isEnabled())
        created=[]; view.create_requested.connect(lambda: created.append(True)); view.create_button.click(); self.assertEqual(created,[True])
        view.show_details(USER,current_user_id="other"); self.assertTrue(view.deactivate_button.isEnabled()); self.assertFalse(view.activate_button.isEnabled()); self.assertTrue(view.reset_button.isEnabled()); self.assertTrue(view.edit_button.isEnabled())
        view.show_details({**USER,"is_active":False},current_user_id="other"); self.assertFalse(view.deactivate_button.isEnabled()); self.assertTrue(view.activate_button.isEnabled())

    def test_logical_delete_confirmation_and_double_click_safe_details(self) -> None:
        view=UsersView(); view.show_users([USER],offset=0,count=1,filtered=False); view.table.selectRow(0)
        with patch("desktop_client.app.views.users_view.confirm_action",return_value=True) as confirm:
            self.assertTrue(view.confirm_deactivation(USER["email"]))
        message=confirm.call_args.args[2]; self.assertIn("יושבת",message); self.assertIn("לא יוכל להתחבר",message); self.assertIn("לא יימחקו",message)
        view.user_selected.connect(lambda _user_id: view.show_details(USER,current_user_id="other")); view.clear_details(); view.table.itemDoubleClicked.emit(view.table.item(0,0)); self.assertEqual(view.details.rowCount(),6)
        rendered=" ".join(view.details.itemAt(row,QFormLayout.ItemRole.FieldRole).widget().text() for row in range(view.details.rowCount()))
        self.assertIn(USER["email"],rendered); self.assertIn(USER["created_at"],rendered); self.assertIn(USER["updated_at"],rendered)
        for secret in ("password","password_hash","token","secret"): self.assertNotIn(secret,rendered.lower())

    def test_create_dialog_role_dependent_profiles_and_secret_handling(self) -> None:
        dialog=CreateUserDialog([{"id":"c1","name":"לקוח"}],[{"id":"i1","full_name":"מדריך"}]); self.assertEqual(dialog.email.layoutDirection(),Qt.LayoutDirection.LeftToRight); self.assertEqual(dialog.password.echoMode(),QLineEdit.EchoMode.Password)
        dialog.role.setCurrentIndex(dialog.role.findData("customer")); self.assertFalse(dialog.customer.isHidden()); self.assertTrue(dialog.instructor.isHidden()); dialog.customer.setCurrentIndex(1)
        dialog.email.setText("c@example.com"); dialog.password.setText("password1"); dialog.confirmation.setText("password1"); self.assertEqual(dialog.values()["customer_id"],"c1")
        dialog.show_error("שגיאה"); self.assertEqual(dialog.password.text(),""); self.assertEqual(dialog.confirmation.text(),"")

    def test_edit_is_email_only_and_reset_has_no_forced_change(self) -> None:
        edit=EditUserDialog(USER); self.assertEqual(edit.values(),{"email":"user@example.com"}); self.assertFalse(hasattr(edit,"role_input"))
        reset=ResetPasswordDialog(USER); self.assertEqual(reset.password.echoMode(),QLineEdit.EchoMode.Password); self.assertEqual(set(reset.values()),{"password","password_confirmation"}); self.assertFalse(hasattr(reset,"temporary")); self.assertFalse(hasattr(reset,"must_change"))

    def test_responsive_semantic_table_uses_viewport(self) -> None:
        view=UsersView(); policies=view.table._task20_column_sizer.policies; self.assertEqual(policies[0].kind.value,"primary_text"); self.assertGreater(policies[0].stretch_weight,max(policy.stretch_weight for policy in policies[1:])); view.resize(1024,640); view.show(); self.app.processEvents(); widths=[view.table.columnWidth(i) for i in range(view.table.columnCount())]; unused=view.table.viewport().width()-1-sum(widths); self.assertTrue(abs(unused)<=1 or unused<0); self.assertGreater(widths[0],widths[3]); self.assertFalse(view.create_button.isHidden()); self.assertFalse(view.deactivate_button.isHidden()); self.assertFalse(view.toolbar.refresh_button.isHidden()); view.close()
