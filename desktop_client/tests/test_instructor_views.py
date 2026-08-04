import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest import TestCase

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QFormLayout, QLabel, QToolButton

from desktop_client.app.features.instructors.dialogs import InstructorDialog
from desktop_client.app.features.instructors.view import InstructorProfileView, InstructorsView


ROW = {
    "id": "i1",
    "full_name": "מדריכה",
    "phone": "050",
    "email": "guide@example.com",
    "city": "ירושלים",
    "notes": "N",
    "is_active": True,
    "created_at": "2026-01-01",
    "updated_at": "2026-01-02",
}


class InstructorViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def _row_action_button(view, row=0):
        host = view.table.cellWidget(row, view.table.columnCount() - 1)
        if isinstance(host, QToolButton):
            return host
        return host.findChild(QToolButton) if host is not None else None

    def test_shared_list_to_details_structure_and_semantic_table(self):
        view = InstructorsView()
        self.addCleanup(view.close)

        self.assertEqual(view.scaffold.header.title.text(), "מדריכים")
        self.assertEqual(view.toolbar.refresh_button.text(), "איפוס")
        self.assertIs(view.pages.currentWidget(), view.list_page)
        self.assertEqual(
            [view.table.horizontalHeaderItem(i).text() for i in range(view.table.columnCount())],
            ["שם מדריך", "עיר", "טלפון", "דוא״ל", "מצב", ""],
        )

        policies = view.table._task20_column_sizer.policies
        self.assertEqual([p.minimum_width for p in policies[:5]], [200, 150, 140, 210, 110])

        details = [("שם", "מדריכה"), ("דוא״ל", "guide@example.com"), ("מצב", "פעיל")]
        view.instructor_selected.connect(lambda _id: view.show_details(details, ROW))
        view.show_instructors([ROW], offset=0, count=1, filtered=False)
        view.table.selectRow(0)

        self.assertEqual(view.table.item(0, 0).text(), "מדריכה")
        self.assertIn("guide@example.com", view.table.item(0, 3).toolTip())
        self.assertIs(view.pages.currentWidget(), view.list_page)

        action = self._row_action_button(view)
        self.assertIsNotNone(action)
        action.click()
        self.assertIs(view.pages.currentWidget(), view.details_page)
        self.assertIs(view.pages.currentWidget(), view.details_page)

        self.assertEqual(view.workspace.detail_subtitle.text(), "מידע מלא ופעולות עבור המדריך שנבחר")
        view.back_button.click()
        self.assertIs(view.pages.currentWidget(), view.list_page)
        self.assertIs(view.pages.currentWidget(), view.list_page)

        view.table.cellDoubleClicked.emit(0, 0)
        self.assertIs(view.pages.currentWidget(), view.details_page)

    def test_details_actions_are_equal_and_safe(self):
        view = InstructorsView()
        self.addCleanup(view.close)

        self.assertFalse(view.edit_button.isEnabled())
        view.show_details(
            [("שם", "מדריכה"), ("טלפון", "050"), ("דוא״ל", "guide@example.com"), ("מצב", "פעיל")],
            ROW,
        )
        self.assertTrue(view.edit_button.isEnabled())

        widths = {b.width() for b in (
            view.edit_button,
            view.change_password_button,
            view.deactivate_button,
            view.reactivate_button,
        )}
        self.assertEqual(len(widths), 1)
        self.assertFalse(view.deactivate_button.isHidden())
        self.assertTrue(view.reactivate_button.isHidden())

        first_label = view.profile_details.itemAt(0, QFormLayout.ItemRole.LabelRole).widget()
        first_value = view.profile_details.itemAt(0, QFormLayout.ItemRole.FieldRole).widget()
        self.assertEqual(first_label.width(), 128)
        self.assertTrue(first_value.alignment() & Qt.AlignmentFlag.AlignRight)

        rendered = " ".join(
            form.itemAt(row, QFormLayout.ItemRole.FieldRole).widget().text()
            for form in (view.profile_details, view.contact_details, view.system_details)
            for row in range(form.rowCount())
        )
        self.assertNotIn("password", rendered.lower())

    def test_instructor_lifecycle_action_matches_active_state(self):
        view = InstructorsView()
        self.addCleanup(view.close)

        for active, deactivate_visible, reactivate_visible in (
            (True, True, False),
            (False, False, True),
        ):
            item = {**ROW, "is_active": active}
            view.show_details(
                [("שם", "מדריכה"), ("מצב", "פעיל" if active else "לא פעיל")],
                item,
            )
            self.assertEqual(not view.deactivate_button.isHidden(), deactivate_visible)
            self.assertEqual(not view.reactivate_button.isHidden(), reactivate_visible)

        self.assertFalse(hasattr(view, "delete_button"))

    def test_create_credentials_and_edit_email_read_only(self):
        create = InstructorDialog()
        edit = InstructorDialog(ROW)
        profile = InstructorProfileView()
        self.addCleanup(create.close)
        self.addCleanup(edit.close)
        self.addCleanup(profile.close)

        self.assertIsNotNone(create.password)
        self.assertIn("password", create.values())
        self.assertIsNone(edit.password)
        self.assertTrue(edit.fields["email"].isReadOnly())
        self.assertNotIn("password", edit.values())
        self.assertTrue(hasattr(profile, "edit_button"))
        self.assertEqual(profile.edit_button.text(), "עריכת הפרטים שלי")
        self.assertTrue(profile.edit_button.isEnabled())

    def test_create_and_edit_render_section_and_notes_label_in_rtl_geometry(self):
        for dialog in (InstructorDialog(), InstructorDialog(ROW)):
            self.addCleanup(dialog.close)
            dialog.show()
            self.app.processEvents()

            section_labels = [
                label for label in dialog.findChildren(QLabel)
                if bool(label.property("dialogSectionTitle"))
            ]
            field_labels = [
                label for label in dialog.findChildren(QLabel)
                if bool(label.property("dialogFieldLabel"))
            ]

            section = next(label for label in section_labels if label.text() == "פרטי מדריך")
            self.assertTrue(section.alignment() & Qt.AlignmentFlag.AlignRight)

            notes = dialog.fields["notes"]
            notes_label = next(label for label in field_labels if label.text() == "הערות")
            self.assertTrue(notes_label.alignment() & Qt.AlignmentFlag.AlignRight)
            self.assertGreater(
                notes_label.mapTo(dialog, notes_label.rect().topLeft()).x(),
                notes.mapTo(dialog, notes.rect().topRight()).x(),
            )

            field_lefts = [
                field.mapTo(dialog, field.rect().topLeft()).x()
                for field in dialog.fields.values()
            ]
            self.assertLessEqual(max(field_lefts) - min(field_lefts), 2)
            dialog.close()

    def test_responsive_table_keeps_minimums(self):
        view = InstructorsView()
        self.addCleanup(view.close)
        view.resize(1024, 640)
        view.show()
        self.app.processEvents()

        minimums = [200, 150, 140, 210, 110]
        for column, minimum in enumerate(minimums):
            self.assertGreaterEqual(view.table.columnWidth(column), minimum)

        self.assertEqual(view.table.columnCount(), 6)

    def test_status_badges_never_duplicate_wrap_clip_or_change_row_height(self):
        view = InstructorsView()
        self.addCleanup(view.close)
        view.show_instructors(
            [ROW, {**ROW, "id": "i2", "is_active": False}],
            offset=0,
            count=2,
            filtered=False,
        )

        for width in (1024, 1400):
            view.resize(width, 700)
            view.show()
            self.app.processEvents()

            for row, text in ((0, "פעיל"), (1, "לא פעיל")):
                badge = view.table.cellWidget(row, 4)
                self.assertIsNone(view.table.item(row, 4))
                self.assertEqual(badge.text(), text)
                self.assertFalse(badge.wordWrap())
                self.assertEqual(view.table.rowHeight(row), 40)
                self.assertLessEqual(badge.sizeHint().height(), view.table.rowHeight(row))

        view.close()

    def test_reference_toolbar_order_immediate_sort_and_no_loading_popup(self):
        view = InstructorsView()
        self.addCleanup(view.close)

        layout = view.toolbar.layout()
        self.assertEqual(
            [layout.itemAt(i).widget() for i in range(layout.count())],
            [
                view.toolbar.search_input,
                view.toolbar.search_button,
                view.toolbar.sort_combo,
                view.toolbar.refresh_button,
            ],
        )
        self.assertEqual(
            [view.toolbar.sort_combo.itemData(i) for i in range(view.toolbar.sort_combo.count())],
            ["full_name", "created_at", "is_active"],
        )

        emitted = []
        view.filters_requested.connect(emitted.append)
        view.toolbar.sort_combo.setCurrentIndex(1)
        self.assertEqual(emitted[-1]["order_by"], "created_at")

        view.show()
        self.app.processEvents()
        before = {w for w in self.app.topLevelWidgets() if w.isVisible()}
        view.set_loading(True)
        self.app.processEvents()
        after = {w for w in self.app.topLevelWidgets() if w.isVisible()}

        new_dialogs = [w for w in after - before if isinstance(w, QDialog)]
        self.assertEqual(new_dialogs, [])
        view.close()
