import os
import base64
import inspect
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from unittest import TestCase
from PySide6.QtWidgets import QApplication
from desktop_client.app.views.activities_view import ActivitiesView
from desktop_client.app.views.activity_dialogs import ActivityDialog
from desktop_client.app.main import MainWindow
from desktop_client.app.presenters import activities_presenter
from desktop_client.app.services import activity_service
from desktop_client.app.api import client as api_client
from unittest.mock import Mock

class ActivityViewTests(TestCase):
    @classmethod
    def setUpClass(cls): cls.app=QApplication.instance() or QApplication([])
    def test_manager_and_read_only_views(self):
        manager=ActivitiesView("manager"); customer=ActivitiesView("customer"); self.assertFalse(manager.actions.isHidden()); self.assertTrue(customer.actions.isHidden()); self.assertFalse(manager.edit_button.isEnabled())
    def test_render_empty_detail_and_retry(self):
        view=ActivitiesView("manager"); view.show_activities([],offset=0,count=0,filtered=True); self.assertFalse(view.state_label.isHidden()); view.show_error("offline",retriable=True); self.assertFalse(view.retry_state.retry_button.isHidden())
    def test_dialog_serializes_exact_textual_fields_and_has_no_media_controls(self):
        dialog=ActivityDialog({"name":"A","duration_minutes":60,"tags":"one,two"}); values=dialog.values(); self.assertEqual(values["duration_minutes"],"60"); self.assertEqual(values["tags"],"one,two"); self.assertNotIn("images",values); self.assertNotIn("upload",values)
    def test_media_controls_are_role_safe_and_preview_renders_in_view(self):
        manager=ActivitiesView("manager"); customer=ActivitiesView("customer"); self.assertFalse(manager.media_actions.isHidden()); self.assertTrue(customer.media_actions.isHidden())
        images=[{"id":"i1","original_filename":"one.png","width":1,"height":1,"bytes":68,"is_primary":True}]; manager.show_images(images); manager.select_image("i1"); self.assertTrue(manager.delete_image_button.isEnabled())
        png=base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")
        self.assertTrue(manager.show_preview(png)); self.assertIsNotNone(manager.preview.pixmap()); self.assertFalse(manager.show_preview(b"not-an-image")); self.assertFalse(manager.preview_retry.isHidden())
    def test_empty_media_state_and_selection_signal(self):
        view=ActivitiesView("manager"); selected=[]; view.image_selected.connect(selected.append); view.show_images([{"id":"i1","original_filename":None,"is_primary":False}]); view.image_list.setCurrentRow(0); self.assertEqual(selected,["i1"]); view.clear_media(); self.assertEqual(view.image_list.count(),0); self.assertIn("אין תמונות",view.preview.text())
    def test_malformed_optional_metadata_uses_fallbacks(self):
        view=ActivitiesView("manager"); view.show_images([{"id":"i1","original_filename":object(),"width":"bad","height":-1,"bytes":"not-a-number","is_primary":False}]); label=view.image_list.item(0).text(); self.assertIn("תמונה ללא שם",label); self.assertIn("ממדים לא זמינים",label); self.assertIn("גודל לא זמין",label)
    def test_logout_and_session_expiry_clear_preview_cache(self):
        class Api:
            def set_unauthorized_handler(self,handler): self.handler=handler
            def set_access_token(self,token): self.token=token
        for operation in ("logout","expiry"):
            window=MainWindow(Api()); owner=Mock(); window._presenters={"activities":owner}
            window._logout() if operation=="logout" else window._complete_session_expiry(); owner.clear_preview_cache.assert_called_once(); window.close()
    def test_application_preview_path_has_no_disk_persistence(self):
        source="\n".join(inspect.getsource(module) for module in (api_client,activity_service,activities_presenter))
        for prohibited in ("tempfile","NamedTemporaryFile","QPixmap.save","QImage.save","write_bytes("):
            self.assertNotIn(prohibited,source)
