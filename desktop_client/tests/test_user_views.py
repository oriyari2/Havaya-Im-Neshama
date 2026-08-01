import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from unittest import TestCase
from unittest.mock import patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication,QFormLayout,QLineEdit
from desktop_client.app.views.user_dialogs import CreateUserDialog,EditUserDialog,ResetPasswordDialog
from desktop_client.app.views.users_view import UsersView

USER={"id":"u1","email":"manager@example.com","role":"manager","display_name":"מנהלת","is_active":True,"customer_id":None,"customer_name":None,"customer_email":None,"contact_name":None,"contact_phone":None,"instructor_id":None,"instructor_name":None,"instructor_email":None,"instructor_phone":None,"created_at":"2026-01-01","updated_at":"2026-01-02"}

class UserViewTests(TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def test_manager_uses_shared_list_to_details_structure(self):
        view=UsersView();self.assertEqual(view.scaffold.header.title.text(),"מנהלים");self.assertEqual(view.toolbar.refresh_button.text(),"איפוס");self.assertEqual([view.table.horizontalHeaderItem(i).text() for i in range(4)],["שם מנהל","דוא״ל","מצב","עודכן"]);self.assertIs(view.pages.currentWidget(),view.list_page)
        view.show_users([USER],offset=0,count=1,filtered=False);view.table.selectRow(0);self.assertEqual(view.table.item(0,0).text(),"מנהלת");self.assertIn('dir="ltr"',view.table.item(0,1).toolTip());view.show_details(USER,current_user_id="other");self.assertIs(view.pages.currentWidget(),view.list_page);view._open();self.assertIs(view.pages.currentWidget(),view.details_page)
    def test_manager_details_actions_and_safe_cards(self):
        view=UsersView();view.show_details(USER,current_user_id="other");self.assertTrue(view.edit_button.isEnabled());self.assertTrue(view.reset_button.isEnabled());self.assertTrue(view.deactivate_button.isEnabled());self.assertFalse(view.activate_button.isEnabled());self.assertEqual({b.width() for b in (view.edit_button,view.reset_button,view.activate_button,view.deactivate_button)},{148})
        rendered=" ".join(view.account_details.itemAt(row,QFormLayout.ItemRole.FieldRole).widget().text() for row in range(view.account_details.rowCount()));self.assertIn("מנהלת",rendered);self.assertIn(USER["email"],rendered);self.assertNotIn("password",rendered.lower());view.show_details(USER,current_user_id="u1");self.assertFalse(view.deactivate_button.isEnabled())
    def test_manager_only_rows_and_logical_delete_copy(self):
        view=UsersView();view.show_users([USER,{**USER,"id":"u2","role":"customer"}],offset=0,count=2,filtered=False);self.assertEqual(view.table.rowCount(),1)
        with patch("desktop_client.app.views.users_view.confirm_action",return_value=True) as confirm:self.assertTrue(view.confirm_deactivation(USER["email"]));self.assertIn("יושבת",confirm.call_args.args[2])
    def test_create_edit_and_password_dialogs(self):
        create=CreateUserDialog();create.email.setText("manager@example.com");create.password.setText("password1");create.confirmation.setText("password1");create.manager_name.setText("מנהלת");self.assertTrue(create.save_button.isEnabled());self.assertEqual(create.values()["role"],"manager")
        edit=EditUserDialog(USER);self.assertTrue(edit.email.isReadOnly());self.assertEqual(edit.values(),{"email":"manager@example.com","manager_name":"מנהלת"})
        reset=ResetPasswordDialog(USER);self.assertEqual(reset.password.echoMode(),QLineEdit.EchoMode.Password);self.assertEqual(set(reset.values()),{"password","password_confirmation"})
    def test_table_resizes_without_squeezing_semantic_minimums(self):
        view=UsersView();view.resize(1024,640);view.show();self.app.processEvents();policies=view.table._task20_column_sizer.policies;self.assertEqual(policies[0].minimum_width,180);self.assertGreater(view.table.columnWidth(0),view.table.columnWidth(2));view.close()
