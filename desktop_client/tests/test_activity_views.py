import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from unittest import TestCase
from PySide6.QtWidgets import QApplication
from desktop_client.app.views.activities_view import ActivitiesView
from desktop_client.app.views.activity_dialogs import ActivityDialog

class ActivityViewTests(TestCase):
    @classmethod
    def setUpClass(cls): cls.app=QApplication.instance() or QApplication([])
    def test_manager_and_read_only_views(self):
        manager=ActivitiesView("manager"); customer=ActivitiesView("customer"); self.assertFalse(manager.actions.isHidden()); self.assertTrue(customer.actions.isHidden()); self.assertFalse(manager.edit_button.isEnabled())
    def test_render_empty_detail_and_retry(self):
        view=ActivitiesView("manager"); view.show_activities([],offset=0,count=0,filtered=True); self.assertFalse(view.state_label.isHidden()); view.show_error("offline",retriable=True); self.assertFalse(view.retry_state.retry_button.isHidden())
    def test_dialog_serializes_exact_textual_fields_and_has_no_media_controls(self):
        dialog=ActivityDialog({"name":"A","duration_minutes":60,"tags":"one,two"}); values=dialog.values(); self.assertEqual(values["duration_minutes"],"60"); self.assertEqual(values["tags"],"one,two"); self.assertNotIn("images",values); self.assertNotIn("upload",values)
