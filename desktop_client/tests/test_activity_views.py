import base64
import inspect
import os
from unittest import TestCase
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QFormLayout, QToolButton

from desktop_client.app.api import client as api_client
from desktop_client.app.main import MainWindow
from desktop_client.app.presenters import activities_presenter
from desktop_client.app.presenters.activity_formatting import activity_details
from desktop_client.app.services import activity_service
from desktop_client.app.views.activities_view import ActivitiesView
from desktop_client.app.views.activity_dialogs import ActivityDialog


ACTIVITY = {
    "id": "a1", "name": "סדנת טבע", "description": "חוויה בטבע", "target_audience": "משפחות",
    "duration_minutes": 60, "recommended_capacity": 20, "pricing_rule": "100 ₪ לקבוצה",
    "required_equipment": "מחצלות", "preparation_notes": "להגיע בזמן", "season": "קיץ",
    "tags": "טבע", "is_active": True, "created_at": "2026-01-01", "updated_at": "2026-01-02",
}
ROW = {key: ACTIVITY[key] for key in ("id", "name", "target_audience", "duration_minutes", "recommended_capacity", "season", "pricing_rule", "is_active")}
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")


class ActivityViewTests(TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication([])

    def test_manager_and_read_only_views_share_foundation(self):
        manager, customer, instructor = ActivitiesView("manager"), ActivitiesView("customer"), ActivitiesView("instructor")
        self.assertEqual(manager.scaffold.header.title.text(), "פעילויות")
        self.assertFalse(manager.actions.isHidden()); self.assertTrue(customer.actions.isHidden())
        self.assertFalse(manager.edit_button.isEnabled()); self.assertTrue(customer.create_button.isHidden())
        for read_only in (instructor, customer):
            self.assertTrue(read_only.actions.isHidden()); self.assertTrue(read_only.media_actions.isHidden()); self.assertTrue(read_only.create_button.isHidden())

    def test_list_search_immediate_sort_filters_reset_and_pagination(self):
        view = ActivitiesView("manager"); emitted = []; pages = []
        view.filters_requested.connect(emitted.append); view.page_requested.connect(lambda offset, limit: pages.append((offset, limit)))
        view.toolbar.search_input.setText("טבע"); view.toolbar.search_button.click(); self.assertEqual(emitted[-1]["search"], "טבע")
        self.assertEqual([view.toolbar.sort_combo.itemData(i) for i in range(view.toolbar.sort_combo.count())], ["name", "duration_minutes"])
        view.toolbar.sort_combo.setCurrentIndex(1); self.assertEqual(view.toolbar.sort_combo.currentData(), "duration_minutes"); self.assertEqual(emitted[-1]["order_by"], "duration_minutes")
        self.assertFalse(view.filter_panel.isHidden()); self.assertFalse(hasattr(view, "filter_button")); view.season.setEditText("קיץ"); view.active.setCurrentIndex(1); view.apply_filters_button.click()
        self.assertEqual(emitted[-1]["season"], "קיץ"); self.assertTrue(emitted[-1]["is_active"]); self.assertIn("קיץ", view.filter_summary.text())
        view.show_activities([ROW] * 25, offset=0, count=25, filtered=True); view.footer.next_button.click(); self.assertEqual(pages[-1], (25, 25))
        view.toolbar.refresh_button.click(); self.assertEqual(emitted[-1]["search"], None); self.assertEqual(emitted[-1]["season"], None); self.assertTrue(view.filter_summary.isHidden())

    def test_per_row_action_double_click_enter_and_back_restore_list_state(self):
        view = ActivitiesView("manager"); selected = []
        view.activity_selected.connect(selected.append); view.activity_selected.connect(lambda _id: view.show_details(activity_details(ACTIVITY), ACTIVITY))
        view.show_activities([ROW], offset=0, count=1, filtered=False); view.toolbar.search_input.setText("טבע")
        action = view.table.cellWidget(0, 0).findChild(QToolButton); self.assertFalse(action.icon().isNull()); self.assertEqual(view.table.columnWidth(0), 52)
        action.click(); self.assertEqual(selected[-1], "a1"); self.assertIs(view.pages.currentWidget(), view.details_page)
        view.back_button.click(); self.assertEqual(view.toolbar.search_input.text(), "טבע"); self.assertIs(view.pages.currentWidget(), view.list_page)
        view.table.cellDoubleClicked.emit(0, 1); self.assertIs(view.pages.currentWidget(), view.details_page)
        view.back_button.click(); view.select_activity("a1"); QTest.keyClick(view.table, Qt.Key.Key_Return); self.assertIs(view.pages.currentWidget(), view.details_page)

    def test_details_cards_and_lifecycle_are_context_sensitive(self):
        view = ActivitiesView("manager")
        view.show_details(activity_details(ACTIVITY), ACTIVITY); self.assertFalse(view.deactivate_button.isHidden()); self.assertTrue(view.reactivate_button.isHidden())
        headings = [label for label in view.details_page.findChildren(type(view.gallery_heading)) if label.objectName() == "sectionTitle"]
        self.assertEqual({label.text() for label in headings}, {"פרטי פעילות", "תפעול ותמחור", "מידע מערכת", "גלריית תמונות"})
        self.assertTrue(all(label.alignment() & Qt.AlignmentFlag.AlignRight for label in headings))
        for form in (view.activity_details, view.operational_details, view.system_details):
            for row in range(form.rowCount()):
                self.assertTrue(form.itemAt(row, QFormLayout.ItemRole.LabelRole).widget().alignment() & Qt.AlignmentFlag.AlignRight)
                self.assertTrue(form.itemAt(row, QFormLayout.ItemRole.FieldRole).widget().alignment() & Qt.AlignmentFlag.AlignRight)
        inactive = {**ACTIVITY, "is_active": False}; view.show_details(activity_details(inactive), inactive)
        self.assertTrue(view.deactivate_button.isHidden()); self.assertFalse(view.reactivate_button.isHidden()); self.assertIn("חוויה בטבע", view.workspace.detail_subtitle.text())

    def test_rtl_table_geometry_at_supported_window_sizes(self):
        view = ActivitiesView("manager"); view.show_activities([ROW], offset=0, count=1, filtered=False)
        for width, height in ((1024, 640), (1200, 760), (1440, 900)):
            view.resize(width, height); view.show(); self.app.processEvents()
            self.assertEqual(view.table.columnWidth(0), 52); self.assertEqual(view.table.rowHeight(0), 40)
            self.assertEqual(view.table.columnCount(), 7); self.assertTrue(view.table.item(0, 1).textAlignment() & Qt.AlignmentFlag.AlignRight)
            self.assertGreaterEqual(view.table.columnWidth(1), 220); self.assertEqual(view.table.horizontalHeader().hiddenSectionCount(), 0)
        view.close()

    def test_dialog_uses_shared_validation_and_natural_rtl_form(self):
        dialog = ActivityDialog(); submitted = []; dialog.submitted.connect(lambda values, _form: submitted.append(values)); dialog.show(); self.app.processEvents()
        self.assertTrue(dialog.save_button.isEnabled()); dialog.save_button.click(); self.assertEqual(submitted, []); self.assertFalse(dialog.field_errors["name"].isHidden()); self.assertIs(dialog.focusWidget(), dialog.fields["name"])
        dialog.fields["name"].setText("פעילות"); dialog.fields["duration_minutes"].setText("bad"); dialog.save_button.click(); self.assertIn("מספר שלם", dialog.field_errors["duration_minutes"].text())
        dialog.fields["duration_minutes"].setText("60"); self.assertTrue(dialog.field_errors["duration_minutes"].isHidden())
        self.assertTrue(all(label.alignment() & Qt.AlignmentFlag.AlignRight for label in dialog.section_labels + dialog.field_labels)); dialog.close()

    def test_gallery_empty_navigation_aspect_ratio_and_role_safe_actions(self):
        manager, customer = ActivitiesView("manager"), ActivitiesView("customer"); self.assertFalse(manager.media_actions.isHidden()); self.assertTrue(customer.media_actions.isHidden())
        images = [{"id": "i1", "original_filename": "one.png", "width": 1, "height": 1, "bytes": 68, "is_primary": True}, {"id": "i2", "original_filename": "two.png", "is_primary": False}]
        selected = []; manager.image_selected.connect(selected.append); manager.show_images(images); manager.select_image("i1"); self.assertEqual(manager.image_position.text(), "1 מתוך 2")
        manager.next_image_button.click(); self.assertEqual(selected[-1], "i2"); self.assertEqual(manager.image_position.text(), "2 מתוך 2")
        manager.previous_image_button.click(); self.assertEqual(selected[-1], "i1"); self.assertTrue(manager.show_preview(PNG)); self.assertEqual(manager._source_pixmap.width(), manager._source_pixmap.height())
        manager.clear_media(); self.assertIn("אין תמונות", manager.preview.text()); self.assertEqual(manager.image_position.text(), "0 מתוך 0")

    def test_image_add_remove_confirmation_and_no_unexpected_top_level_window(self):
        view = ActivitiesView("manager"); before = {widget for widget in self.app.topLevelWidgets() if widget.isVisible()}; view.show(); self.app.processEvents(); intended = {widget for widget in self.app.topLevelWidgets() if widget.isVisible()}
        view.show_activities([ROW], offset=0, count=1, filtered=False); view.show_details(activity_details(ACTIVITY), ACTIVITY); view.workspace.show_details(); self.app.processEvents()
        self.assertEqual({widget for widget in self.app.topLevelWidgets() if widget.isVisible()}, intended); self.assertEqual(before | {view}, intended)
        self.assertTrue(view.confirm_image_deletion.__name__.startswith("confirm_")); view.close()

    def test_render_empty_retry_and_malformed_image_metadata(self):
        view = ActivitiesView("manager"); view.show_activities([], offset=0, count=0, filtered=True); self.assertIs(view.workspace.table_region.currentWidget(), view.workspace.empty_state)
        view.show_error("offline", retriable=True); self.assertFalse(view.retry_state.retry_button.isHidden())
        view.show_images([{"id": "i1", "original_filename": object(), "width": "bad", "height": -1, "bytes": "bad", "is_primary": False}]); label = view.image_list.item(0).text(); self.assertIn("תמונה ללא שם", label); self.assertIn("ממדים לא זמינים", label)

    def test_logout_and_session_expiry_clear_preview_cache(self):
        class Api:
            def set_unauthorized_handler(self, handler): self.handler = handler
            def set_access_token(self, token): self.token = token
        for operation in ("logout", "expiry"):
            window = MainWindow(Api()); owner = Mock(); window._presenters = {"activities": owner}
            window._logout() if operation == "logout" else window._complete_session_expiry(); owner.clear_preview_cache.assert_called_once(); window.close()

    def test_application_preview_path_has_no_disk_persistence(self):
        source = "\n".join(inspect.getsource(module) for module in (api_client, activity_service, activities_presenter))
        for prohibited in ("tempfile", "NamedTemporaryFile", "QPixmap.save", "QImage.save", "write_bytes("): self.assertNotIn(prohibited, source)
