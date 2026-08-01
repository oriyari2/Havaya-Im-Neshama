import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest import TestCase

from PySide6.QtWidgets import QApplication, QFormLayout

from desktop_client.app.views.instructor_dialogs import InstructorDialog
from desktop_client.app.views.instructors_view import InstructorProfileView, InstructorsView


class InstructorViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_construct_and_no_password(self):
        view = InstructorsView()
        profile = InstructorProfileView()
        dialog = InstructorDialog({"full_name": "A"})
        self.assertFalse(view.edit_button.isEnabled())
        self.assertFalse(view.delete_button.isEnabled())
        self.assertFalse(view.change_password_button.isEnabled())
        self.assertEqual(view.change_password_button.text(), "שינוי סיסמה")
        self.assertFalse(hasattr(view, "reactivate_button"))
        self.assertNotIn("password", dialog.values())
        self.assertNotIn("is_active", dialog.values())
        self.assertFalse(hasattr(profile, "edit_button"))

    def test_create_collects_login_credentials_but_edit_does_not(self):
        create = InstructorDialog()
        self.assertIsNotNone(create.password)
        self.assertIsNotNone(create.password_confirmation)
        self.assertIn("password", create.values())
        edit = InstructorDialog({"full_name": "A"})
        self.assertIsNone(edit.password)
        self.assertNotIn("password", edit.values())

    def test_semantic_table_and_responsive_splitter(self):
        view = InstructorsView()
        self.assertTrue(view.table.property("task20Table"))
        policies = view.table._task20_column_sizer.policies
        self.assertEqual(policies[0].kind.value, "primary_text")
        self.assertEqual(policies[1].minimum_width, 115)
        self.assertEqual(policies[2].minimum_width, 150)
        self.assertEqual(policies[3].minimum_width, 80)
        view.show()
        previous_name_width = 0
        for width, height in ((1024, 640), (1200, 760), (1440, 900)):
            view.resize(width, height)
            self.app.processEvents()
            widths = [view.table.columnWidth(index) for index in range(view.table.columnCount())]
            unused = view.table.viewport().width() - 1 - sum(widths)
            self.assertTrue(abs(unused) <= 1 or unused < 0)
            self.assertGreater(widths[0], widths[4])
            self.assertGreaterEqual(view.splitter.widget(1).width(), 300)
            self.assertGreaterEqual(widths[2], 150)
            self.assertGreaterEqual(widths[1], 115)
            self.assertGreaterEqual(widths[0], previous_name_width)
            previous_name_width = widths[0]
            for widget in (view.toolbar.search_input, view.apply_filters_button, view.create_button, view.table, view.footer):
                self.assertTrue(widget.isVisibleTo(view), widget)
        view.close()

    def test_safe_details_and_tooltips(self):
        view = InstructorsView()
        row = {"id": "i1", "full_name": "מדריך ארוך", "phone": "050", "email": "guide@example.com", "city": "ירושלים", "is_active": True}
        view.show_instructors([row], offset=0, count=1, filtered=False)
        self.assertIn("guide@example.com", view.table.item(0, 2).toolTip())
        self.assertIn('dir="ltr"', view.table.item(0, 2).toolTip())
        view.show_details([("שם", "מדריך ארוך"), ("טלפון", "050"), ("דוא״ל", "guide@example.com")], row)
        rendered = " ".join(
            view.details.itemAt(index, QFormLayout.ItemRole.FieldRole).widget().text()
            for index in range(view.details.rowCount())
        )
        self.assertIn("guide@example.com", rendered)
        self.assertNotIn("password", rendered.lower())
