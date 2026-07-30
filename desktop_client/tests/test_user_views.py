import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")

from unittest import TestCase
from unittest.mock import patch

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication, QFormLayout, QLineEdit

from desktop_client.app.views.user_dialogs import CreateUserDialog, EditUserDialog, ResetPasswordDialog
from desktop_client.app.views.users_view import UsersView


USER={"id":"u1","email":"user@example.com","role":"customer","is_active":True,"customer_id":"c1","customer_name":"לקוח","customer_email":"user@example.com","contact_name":"איש קשר","contact_phone":"050","instructor_id":None,"instructor_name":None,"instructor_email":None,"instructor_phone":None,"created_at":"2026-01-01","updated_at":"2026-01-02"}


class UserViewTests(TestCase):
    @classmethod
    def setUpClass(cls): cls.app=QApplication.instance() or QApplication([])

    def test_page_table_filters_details_and_self_deactivation(self) -> None:
        view=UsersView(); self.assertTrue(view.table.property("task20Table")); self.assertEqual(view.table.accessibleName(),"רשימת משתמשים")
        self.assertEqual(view.table.horizontalHeaderItem(2).text(),"שם")
        self.assertEqual(view.table.horizontalHeaderItem(3).text(),"מצב חשבון")
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
        view.user_selected.connect(lambda _user_id: view.show_details(USER,current_user_id="other")); view.clear_details(); view.table.itemDoubleClicked.emit(view.table.item(0,0)); self.assertEqual(view.details.rowCount(),9)
        rendered=" ".join(view.details.itemAt(row,QFormLayout.ItemRole.FieldRole).widget().text() for row in range(view.details.rowCount()))
        self.assertIn(USER["email"],rendered); self.assertIn(USER["customer_name"],rendered); self.assertIn(USER["contact_name"],rendered); self.assertIn(USER["contact_phone"],rendered); self.assertIn(USER["created_at"],rendered); self.assertIn(USER["updated_at"],rendered)
        for secret in ("password","password_hash","token","secret"): self.assertNotIn(secret,rendered.lower())

    def test_create_dialog_role_dependent_profiles_and_secret_handling(self) -> None:
        dialog=CreateUserDialog(); self.assertEqual(dialog.role.currentIndex(),0); self.assertEqual(dialog.role.currentText(),"בחר תפקיד"); self.assertEqual(dialog.role.currentData(),""); self.assertFalse(dialog.save_button.isEnabled()); self.assertTrue(dialog.manager_name.isHidden()); self.assertTrue(dialog.customer_name.isHidden()); self.assertTrue(dialog.contact_name.isHidden()); self.assertTrue(dialog.contact_phone.isHidden()); self.assertTrue(dialog.instructor_name.isHidden()); self.assertTrue(dialog.instructor_phone.isHidden())
        self.assertEqual(dialog.email.layoutDirection(),Qt.LayoutDirection.LeftToRight); self.assertEqual(dialog.password.echoMode(),QLineEdit.EchoMode.Password); self.assertFalse(hasattr(dialog,"customer")); self.assertFalse(hasattr(dialog,"instructor")); self.assertFalse(hasattr(dialog,"customer_email")); self.assertFalse(hasattr(dialog,"instructor_email"))
        dialog.role.setCurrentIndex(dialog.role.findData("manager")); self.assertEqual(dialog.role.currentData(),"manager"); self.assertFalse(dialog.manager_name.isHidden()); self.assertTrue(dialog.customer_name.isHidden()); self.assertTrue(dialog.instructor_name.isHidden()); dialog.email.setText("manager@example.com"); dialog.password.setText("password1"); dialog.confirmation.setText("password1"); dialog.manager_name.setText("מנהלת"); self.assertTrue(dialog.save_button.isEnabled())
        dialog.role.setCurrentIndex(dialog.role.findData("customer")); self.assertEqual(dialog.role.currentData(),"customer"); self.assertFalse(dialog.customer_name.isHidden()); self.assertFalse(dialog.contact_name.isHidden()); self.assertFalse(dialog.contact_phone.isHidden()); self.assertTrue(dialog.instructor_name.isHidden())
        dialog.email.setText("c@example.com"); dialog.password.setText("password1"); dialog.confirmation.setText("password1"); dialog.customer_name.setText("לקוח"); dialog.contact_name.setText("איש קשר"); dialog.contact_phone.setText("050"); values=dialog.values(); self.assertEqual(values["email"],"c@example.com"); self.assertNotIn("customer_id",values)
        self.assertTrue(dialog.save_button.isEnabled()); dialog.role.setFocus(); dialog.email.setFocus(); self.app.processEvents(); self.assertEqual(dialog.role.currentData(),"customer")
        dialog.scroll.verticalScrollBar().setValue(dialog.scroll.verticalScrollBar().maximum()); self.assertEqual(dialog.role.currentData(),"customer")
        wheel=QWheelEvent(QPointF(2,2),QPointF(2,2),QPoint(),QPoint(0,-120),Qt.MouseButton.NoButton,Qt.KeyboardModifier.NoModifier,Qt.ScrollPhase.ScrollUpdate,False); QApplication.sendEvent(dialog.role,wheel); self.assertEqual(dialog.role.currentData(),"customer")
        dialog.role.setCurrentIndex(dialog.role.findData("instructor")); self.assertEqual(dialog.role.currentData(),"instructor"); self.assertTrue(dialog.customer_name.isHidden()); self.assertFalse(dialog.instructor_name.isHidden()); self.assertFalse(dialog.instructor_phone.isHidden()); self.assertEqual(dialog.customer_name.text(),""); dialog.instructor_name.setText("מדריך"); self.assertTrue(dialog.save_button.isEnabled())
        dialog.role.setCurrentIndex(dialog.role.findData("customer")); self.assertEqual(dialog.instructor_name.text(),""); self.assertFalse(dialog.save_button.isEnabled())
        dialog.role.setCurrentIndex(dialog.role.findData("instructor")); dialog.instructor_name.setText("מדריך"); selected=dialog.role.currentData(); dialog.show_error("שגיאה"); self.assertEqual(dialog.role.currentData(),selected); self.assertEqual(dialog.password.text(),""); self.assertEqual(dialog.confirmation.text(),""); self.assertFalse(dialog.save_button.isEnabled())

    def test_instructor_details_use_same_login_email_and_safe_phone(self) -> None:
        view=UsersView(); instructor={**USER,"role":"instructor","customer_id":None,"customer_name":None,"customer_email":None,"contact_name":None,"contact_phone":None,"instructor_id":"i1","instructor_name":"מדריך","instructor_email":"instructor@example.com","instructor_phone":"051","email":"instructor@example.com"}; view.show_details(instructor,current_user_id="other")
        rendered=" ".join(view.details.itemAt(row,QFormLayout.ItemRole.FieldRole).widget().text() for row in range(view.details.rowCount())); self.assertIn("מדריך",rendered); self.assertIn("instructor@example.com",rendered); self.assertIn("051",rendered)

    def test_manager_name_appears_in_name_column_and_details(self) -> None:
        view=UsersView(); manager={**USER,"role":"manager","display_name":"מנהלת בדיקה","customer_id":None,"customer_name":None,"customer_email":None,"contact_name":None,"contact_phone":None}; view.show_users([manager],offset=0,count=1,filtered=False); self.assertEqual(view.table.item(0,2).text(),"מנהלת בדיקה"); view.show_details(manager,current_user_id="other"); rendered=" ".join(view.details.itemAt(row,QFormLayout.ItemRole.FieldRole).widget().text() for row in range(view.details.rowCount())); self.assertIn("מנהלת בדיקה",rendered); labels=" ".join(view.details.itemAt(row,QFormLayout.ItemRole.LabelRole).widget().text() for row in range(view.details.rowCount())); self.assertIn("שם",labels); self.assertNotIn("פרופיל",labels)

    def test_edit_is_email_only_and_reset_has_no_forced_change(self) -> None:
        edit=EditUserDialog(USER); self.assertEqual(edit.values(),{"email":"user@example.com"}); self.assertFalse(hasattr(edit,"role_input"))
        reset=ResetPasswordDialog(USER); self.assertEqual(reset.password.echoMode(),QLineEdit.EchoMode.Password); self.assertEqual(set(reset.values()),{"password","password_confirmation"}); self.assertFalse(hasattr(reset,"temporary")); self.assertFalse(hasattr(reset,"must_change"))

    def test_responsive_semantic_table_uses_viewport(self) -> None:
        view=UsersView(); policies=view.table._task20_column_sizer.policies; self.assertEqual(policies[0].kind.value,"primary_text"); self.assertGreater(policies[0].stretch_weight,max(policy.stretch_weight for policy in policies[1:])); view.resize(1024,640); view.show(); self.app.processEvents(); widths=[view.table.columnWidth(i) for i in range(view.table.columnCount())]; unused=view.table.viewport().width()-1-sum(widths); self.assertTrue(abs(unused)<=1 or unused<0); self.assertGreater(widths[0],widths[3]); self.assertFalse(view.create_button.isHidden()); self.assertFalse(view.deactivate_button.isHidden()); self.assertFalse(view.toolbar.refresh_button.isHidden()); view.close()
