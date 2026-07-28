import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from unittest import TestCase
from PySide6.QtWidgets import QApplication
from desktop_client.app.views.instructors_view import InstructorProfileView,InstructorsView
from desktop_client.app.views.instructor_dialogs import InstructorDialog
class InstructorViewTests(TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def test_construct_and_no_password(self):
        v=InstructorsView();p=InstructorProfileView();d=InstructorDialog({"full_name":"A"});self.assertFalse(v.edit_button.isEnabled());self.assertFalse(v.delete_button.isEnabled());self.assertFalse(hasattr(v,"reactivate_button"));self.assertNotIn("password",d.values());self.assertNotIn("is_active",d.values());self.assertFalse(hasattr(p,"edit_button"))
