import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from unittest import TestCase
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication,QDialog,QFormLayout,QToolButton
from desktop_client.app.views.instructor_dialogs import InstructorDialog
from desktop_client.app.views.instructors_view import InstructorProfileView,InstructorsView

ROW={"id":"i1","full_name":"מדריכה","phone":"050","email":"guide@example.com","city":"ירושלים","notes":"N","is_active":True,"created_at":"2026-01-01","updated_at":"2026-01-02"}
class InstructorViewTests(TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def test_shared_list_to_details_structure_and_semantic_table(self):
        view=InstructorsView();self.assertEqual(view.scaffold.header.title.text(),"מדריכים");self.assertEqual(view.toolbar.refresh_button.text(),"איפוס");self.assertIs(view.pages.currentWidget(),view.list_page);policies=view.table._task20_column_sizer.policies;self.assertEqual(policies[0].minimum_width,52);self.assertEqual(policies[1].minimum_width,200);self.assertEqual(policies[4].minimum_width,210)
        details=[("שם","מדריכה"),("דוא״ל","guide@example.com"),("מצב","פעיל")];view.instructor_selected.connect(lambda _id:view.show_details(details,ROW));view.show_instructors([ROW],offset=0,count=1,filtered=False);view.table.selectRow(0);self.assertEqual(view.table.item(0,1).text(),"מדריכה");self.assertIn("guide@example.com",view.table.item(0,4).toolTip());self.assertIs(view.pages.currentWidget(),view.list_page);action=view.table.cellWidget(0,0).findChild(QToolButton);action.click();self.assertIs(view.pages.currentWidget(),view.details_page);view.back_button.click();view.table.cellDoubleClicked.emit(0,1);self.assertIs(view.pages.currentWidget(),view.details_page);self.assertTrue(view.scaffold.header.isHidden());self.assertEqual(view.workspace.detail_subtitle.text(),"מידע מלא ופעולות עבור המדריך שנבחר");view.back_button.click();self.assertIs(view.pages.currentWidget(),view.list_page);self.assertFalse(view.scaffold.header.isHidden())
    def test_details_actions_are_equal_and_safe(self):
        view=InstructorsView();self.assertFalse(view.edit_button.isEnabled());view.show_details([("שם","מדריכה"),("טלפון","050"),("דוא״ל","guide@example.com"),("מצב","פעיל")],ROW);self.assertTrue(view.edit_button.isEnabled());self.assertEqual({b.width() for b in (view.edit_button,view.change_password_button,view.deactivate_button,view.reactivate_button)},{148});self.assertFalse(view.deactivate_button.isHidden());self.assertTrue(view.reactivate_button.isHidden());self.assertEqual(view.profile_details.itemAt(0,QFormLayout.ItemRole.LabelRole).widget().width(),140);self.assertTrue(view.profile_details.itemAt(0,QFormLayout.ItemRole.FieldRole).widget().alignment() & Qt.AlignmentFlag.AlignRight);rendered=" ".join(view.profile_details.itemAt(row,QFormLayout.ItemRole.FieldRole).widget().text() for row in range(view.profile_details.rowCount()));self.assertNotIn("password",rendered.lower())
    def test_instructor_lifecycle_action_matches_active_state(self):
        view=InstructorsView()
        for active,deactivate_visible,reactivate_visible in ((True,True,False),(False,False,True)):
            item={**ROW,"is_active":active};view.show_details([("שם","מדריכה"),("מצב","פעיל" if active else "לא פעיל")],item);self.assertEqual(not view.deactivate_button.isHidden(),deactivate_visible);self.assertEqual(not view.reactivate_button.isHidden(),reactivate_visible)
        self.assertFalse(hasattr(view,"delete_button"))
    def test_create_credentials_and_edit_email_read_only(self):
        create=InstructorDialog();self.assertIsNotNone(create.password);self.assertIn("password",create.values());edit=InstructorDialog(ROW);self.assertIsNone(edit.password);self.assertTrue(edit.fields["email"].isReadOnly());self.assertNotIn("password",edit.values());self.assertFalse(hasattr(InstructorProfileView(),"edit_button"))
    def test_create_and_edit_render_section_and_notes_label_in_rtl_geometry(self):
        for dialog in (InstructorDialog(),InstructorDialog(ROW)):
            dialog.show();self.app.processEvents()
            section=next(label for label in dialog.section_labels if label.text()=="פרטי מדריך")
            self.assertTrue(section.alignment() & Qt.AlignmentFlag.AlignRight);self.assertGreater(section.mapTo(dialog,section.rect().center()).x(),dialog.width()//2)
            notes=dialog.fields["notes"];notes_form=dialog.section_forms["הערות"];notes_label=notes_form.labelForField(notes)
            self.assertEqual(notes_label.text(),"הערות");self.assertTrue(notes_label.alignment() & Qt.AlignmentFlag.AlignRight)
            self.assertGreater(notes_label.mapTo(dialog,notes_label.rect().topLeft()).x(),notes.mapTo(dialog,notes.rect().topRight()).x())
            field_lefts=[field.mapTo(dialog,field.rect().topLeft()).x() for field in dialog.fields.values()]
            self.assertLessEqual(max(field_lefts)-min(field_lefts),1);dialog.close()
    def test_responsive_table_keeps_minimums(self):
        view=InstructorsView();view.resize(1024,640);view.show();self.app.processEvents();self.assertEqual(view.table.columnWidth(0),52);self.assertGreaterEqual(view.table.columnWidth(1),200);self.assertGreaterEqual(view.table.columnWidth(4),210);view.close()
    def test_status_badges_never_duplicate_wrap_clip_or_change_row_height(self):
        view=InstructorsView();view.show_instructors([ROW,{**ROW,"id":"i2","is_active":False}],offset=0,count=2,filtered=False)
        for width in (1024,1400):
            view.resize(width,700);view.show();self.app.processEvents()
            for row,text in ((0,"פעיל"),(1,"לא פעיל")):
                badge=view.table.cellWidget(row,5);self.assertIsNone(view.table.item(row,5));self.assertEqual(badge.text(),text);self.assertFalse(badge.wordWrap());self.assertEqual(view.table.rowHeight(row),40);self.assertLessEqual(badge.sizeHint().height(),view.table.rowHeight(row))
        view.close()
    def test_reference_toolbar_order_immediate_sort_and_no_loading_popup(self):
        view=InstructorsView();layout=view.toolbar.layout();self.assertEqual([layout.itemAt(i).widget() for i in range(layout.count())],[view.toolbar.search_input,view.toolbar.search_button,view.toolbar.sort_combo,view.toolbar.refresh_button]);self.assertEqual([view.toolbar.sort_combo.itemData(i) for i in range(view.toolbar.sort_combo.count())],["full_name","created_at","is_active"]);emitted=[];view.filters_requested.connect(emitted.append);view.toolbar.sort_combo.setCurrentIndex(1);self.assertEqual(emitted[-1]["order_by"],"created_at")
        view.show();self.app.processEvents();before={w for w in self.app.topLevelWidgets() if w.isVisible()};view.set_loading(True);self.app.processEvents();after={w for w in self.app.topLevelWidgets() if w.isVisible()};self.assertEqual(after,before);self.assertFalse(any(isinstance(w,QDialog) and w.isVisible() for w in after));view.close()
