import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from unittest import TestCase
from unittest.mock import Mock
from PySide6.QtWidgets import QApplication
from desktop_client.app.views.bookings_view import BookingsView
from desktop_client.app.views.assignment_dialogs import InstructorSelectorDialog
class AssignmentViewTests(TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def test_controls_manager_only_and_names_render(self):
        m=BookingsView("manager");i=BookingsView("instructor");c=BookingsView("customer");self.assertFalse(m.assignment_group.isHidden());self.assertTrue(i.assignment_group.isHidden());self.assertTrue(c.assignment_group.isHidden());m.show_assignments([{"booking_activity_id":"ba","activity_id":"a","activity_name":"Activity","assignment_required":False,"assignments":[{"instructor_id":"i","instructor_name":"Instructor","instructor_city":"C"}]}]);self.assertEqual(m.assignment_tree.topLevelItem(0).child(0).text(0),"Instructor")
    def test_selector_is_passive_and_paged(self):
        q=Mock();choose=Mock();d=InstructorSelectorDialog({"activity_name":"A","booking_activity_id":"ba"},q,choose);d.show_instructors([{"id":"i","full_name":"I","city":"C","phone":"1"}],offset=0,count=1);self.assertEqual(d.table.rowCount(),1)
