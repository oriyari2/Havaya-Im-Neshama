import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from unittest import TestCase
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication,QFormLayout
from desktop_client.app.views.instructor_dialogs import InstructorDialog
from desktop_client.app.views.instructors_view import InstructorProfileView,InstructorsView

ROW={"id":"i1","full_name":"מדריכה","phone":"050","email":"guide@example.com","city":"ירושלים","notes":"N","is_active":True,"created_at":"2026-01-01","updated_at":"2026-01-02"}
class InstructorViewTests(TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def test_shared_list_to_details_structure_and_semantic_table(self):
        view=InstructorsView();self.assertEqual(view.scaffold.header.title.text(),"מדריכים");self.assertEqual(view.toolbar.refresh_button.text(),"איפוס");self.assertIs(view.pages.currentWidget(),view.list_page);policies=view.table._task20_column_sizer.policies;self.assertEqual(policies[0].minimum_width,180);self.assertEqual(policies[3].minimum_width,190)
        view.show_instructors([ROW],offset=0,count=1,filtered=False);view.table.selectRow(0);self.assertEqual(view.table.item(0,0).text(),"מדריכה");self.assertIn("guide@example.com",view.table.item(0,3).toolTip());view.show_details([("שם","מדריכה"),("דוא״ל","guide@example.com"),("מצב","פעיל")],ROW);self.assertIs(view.pages.currentWidget(),view.list_page);view._open();self.assertIs(view.pages.currentWidget(),view.details_page)
    def test_details_actions_are_equal_and_safe(self):
        view=InstructorsView();self.assertFalse(view.edit_button.isEnabled());view.show_details([("שם","מדריכה"),("טלפון","050"),("דוא״ל","guide@example.com"),("מצב","פעיל")],ROW);self.assertTrue(view.edit_button.isEnabled());self.assertEqual({b.width() for b in (view.edit_button,view.change_password_button,view.delete_button)},{148});rendered=" ".join(view.profile_details.itemAt(row,QFormLayout.ItemRole.FieldRole).widget().text() for row in range(view.profile_details.rowCount()));self.assertNotIn("password",rendered.lower())
    def test_create_credentials_and_edit_email_read_only(self):
        create=InstructorDialog();self.assertIsNotNone(create.password);self.assertIn("password",create.values());edit=InstructorDialog(ROW);self.assertIsNone(edit.password);self.assertTrue(edit.fields["email"].isReadOnly());self.assertNotIn("password",edit.values());self.assertFalse(hasattr(InstructorProfileView(),"edit_button"))
    def test_responsive_table_keeps_minimums(self):
        view=InstructorsView();view.resize(1024,640);view.show();self.app.processEvents();self.assertGreaterEqual(view.table.columnWidth(0),180);self.assertGreaterEqual(view.table.columnWidth(3),190);view.close()
