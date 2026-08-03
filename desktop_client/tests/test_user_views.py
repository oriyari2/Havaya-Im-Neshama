import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest import TestCase
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFormLayout, QLabel, QLineEdit, QToolButton

from desktop_client.app.views.user_dialogs import CreateUserDialog, EditUserDialog, ResetPasswordDialog
from desktop_client.app.views.users_view import UsersView


USER = {
    "id": "u1",
    "email": "manager@example.com",
    "role": "manager",
    "display_name": "מנהלת",
    "is_active": True,
    "customer_id": None,
    "customer_name": None,
    "customer_email": None,
    "contact_name": None,
    "contact_phone": None,
    "instructor_id": None,
    "instructor_name": None,
    "instructor_email": None,
    "instructor_phone": None,
    "created_at": "2026-01-01",
    "updated_at": "2026-01-02",
}


class UserViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def _row_action_button(view, row=0):
        host = view.table.cellWidget(row, view.table.columnCount() - 1)
        if isinstance(host, QToolButton):
            return host
        return host.findChild(QToolButton) if host is not None else None

    def test_manager_uses_shared_list_to_details_structure(self):
        view = UsersView()
        self.addCleanup(view.close)

        self.assertEqual(view.scaffold.header.title.text(), "מנהלים")
        self.assertEqual(view.toolbar.refresh_button.text(), "איפוס")
        self.assertEqual(
            [view.table.horizontalHeaderItem(i).text() for i in range(view.table.columnCount())],
            ["שם מנהל", "דוא״ל", "מצב", "עודכן", ""],
        )
        self.assertIs(view.pages.currentWidget(), view.list_page)

        view.user_selected.connect(lambda _id: view.show_details(USER, current_user_id="other"))
        view.show_users([USER], offset=0, count=1, filtered=False)
        view.table.selectRow(0)

        self.assertEqual(view.table.item(0, 0).text(), "מנהלת")
        self.assertIn('dir="ltr"', view.table.item(0, 1).toolTip())
        self.assertIs(view.pages.currentWidget(), view.list_page)

        action = self._row_action_button(view)
        self.assertIsNotNone(action)
        action.click()
        self.assertIs(view.pages.currentWidget(), view.details_page)
        self.assertIs(view.pages.currentWidget(), view.details_page)
        self.assertEqual(view.workspace.detail_subtitle.text(), "מידע מלא ופעולות עבור המנהל שנבחר")

        view.back_button.click()
        self.assertIs(view.pages.currentWidget(), view.list_page)
        self.assertIs(view.pages.currentWidget(), view.list_page)

        view.table.cellDoubleClicked.emit(0, 0)
        self.assertIs(view.pages.currentWidget(), view.details_page)

    def test_manager_details_actions_and_safe_cards(self):
        view = UsersView()
        self.addCleanup(view.close)

        view.show_details(USER, current_user_id="other")
        self.assertTrue(view.edit_button.isEnabled())
        self.assertTrue(view.reset_button.isEnabled())
        self.assertTrue(view.deactivate_button.isEnabled())
        self.assertFalse(view.activate_button.isEnabled())

        widths = {
            b.width()
            for b in (view.edit_button, view.reset_button, view.activate_button, view.deactivate_button)
        }
        self.assertEqual(len(widths), 1)

        rendered = " ".join(
            form.itemAt(row, QFormLayout.ItemRole.FieldRole).widget().text()
            for form in (view.account_details, view.login_details, view.system_details)
            for row in range(form.rowCount())
        )
        self.assertIn("מנהלת", rendered)
        self.assertIn(USER["email"], rendered)
        self.assertNotIn("password", rendered.lower())

        view.show_details(USER, current_user_id="u1")
        self.assertFalse(view.deactivate_button.isEnabled())

    def test_manager_lifecycle_action_matches_active_state(self):
        view = UsersView()
        self.addCleanup(view.close)

        view.show_details(USER, current_user_id="other")
        self.assertFalse(view.deactivate_button.isHidden())
        self.assertTrue(view.activate_button.isHidden())

        view.show_details({**USER, "is_active": False}, current_user_id="other")
        self.assertTrue(view.deactivate_button.isHidden())
        self.assertFalse(view.activate_button.isHidden())

    def test_manager_only_rows_and_logical_delete_copy(self):
        view = UsersView()
        self.addCleanup(view.close)

        view.show_users(
            [USER, {**USER, "id": "u2", "role": "customer"}],
            offset=0,
            count=2,
            filtered=False,
        )
        self.assertEqual(view.table.rowCount(), 1)

        with patch("desktop_client.app.views.users_view.confirm_action", return_value=True) as confirm:
            self.assertTrue(view.confirm_deactivation(USER["email"]))
            self.assertIn("להשבית", confirm.call_args.args[2])

    def test_create_edit_and_password_dialogs(self):
        create = CreateUserDialog()
        edit = EditUserDialog(USER)
        reset = ResetPasswordDialog(USER)
        self.addCleanup(create.close)
        self.addCleanup(edit.close)
        self.addCleanup(reset.close)

        create.email.setText("manager@example.com")
        create.password.setText("password1")
        create.confirmation.setText("password1")
        create.manager_name.setText("מנהלת")
        self.assertTrue(create.save_button.isEnabled())
        self.assertEqual(create.values()["role"], "manager")

        self.assertTrue(edit.email.isReadOnly())
        self.assertEqual(edit.values(), {"email": "manager@example.com", "manager_name": "מנהלת"})

        self.assertEqual(reset.password.echoMode(), QLineEdit.EchoMode.Password)
        self.assertEqual(set(reset.values()), {"password", "password_confirmation"})

    def test_manager_create_dialog_renders_labels_to_the_right_of_aligned_fields(self):
        dialog = CreateUserDialog()
        self.addCleanup(dialog.close)
        dialog.show()
        self.app.processEvents()

        self.assertTrue(dialog.heading_label.alignment() & Qt.AlignmentFlag.AlignRight)
        self.assertTrue(dialog.heading_description.alignment() & Qt.AlignmentFlag.AlignRight)
        self.assertTrue(dialog.required_hint.alignment() & Qt.AlignmentFlag.AlignRight)

        section_labels = [
            label for label in dialog.findChildren(QLabel)
            if bool(label.property("dialogSectionTitle"))
        ]
        field_labels = [
            label for label in dialog.findChildren(QLabel)
            if bool(label.property("dialogFieldLabel"))
        ]
        self.assertTrue(section_labels)
        self.assertTrue(field_labels)
        self.assertTrue(all(label.alignment() & Qt.AlignmentFlag.AlignRight for label in section_labels))
        self.assertTrue(all(label.alignment() & Qt.AlignmentFlag.AlignRight for label in field_labels))

        field_positions = []
        for field in dialog.fields.values():
            label = next(
                label for label in field_labels
                if label.accessibleName() == field.accessibleName() or label.text().replace(" *", "") == field.accessibleName()
            )
            label_left = label.mapTo(dialog, label.rect().topLeft()).x()
            field_right = field.mapTo(dialog, field.rect().topRight()).x()
            self.assertGreater(label_left, field_right)
            field_positions.append(field.mapTo(dialog, field.rect().topLeft()).x())

        self.assertLessEqual(max(field_positions) - min(field_positions), 2)
        dialog.close()

    def test_table_resizes_without_squeezing_semantic_minimums(self):
        view = UsersView()
        self.addCleanup(view.close)
        view.resize(1024, 640)
        view.show()
        self.app.processEvents()

        policies = view.table._task20_column_sizer.policies
        self.assertEqual([p.minimum_width for p in policies[:4]], [210, 240, 110, 170])
        for column, minimum in enumerate((210, 240, 110, 170)):
            self.assertGreaterEqual(view.table.columnWidth(column), minimum)
        self.assertEqual(view.table.columnCount(), 5)

    def test_status_badges_never_duplicate_wrap_clip_or_change_row_height(self):
        view = UsersView()
        self.addCleanup(view.close)
        view.show_users(
            [USER, {**USER, "id": "u2", "is_active": False}],
            offset=0,
            count=2,
            filtered=False,
        )

        for width in (1024, 1400):
            view.resize(width, 700)
            view.show()
            self.app.processEvents()

            for row, text in ((0, "פעיל"), (1, "לא פעיל")):
                badge = view.table.cellWidget(row, 2)
                self.assertIsNone(view.table.item(row, 2))
                self.assertEqual(badge.text(), text)
                self.assertFalse(badge.wordWrap())
                self.assertEqual(view.table.rowHeight(row), 40)
                self.assertLessEqual(badge.sizeHint().height(), view.table.rowHeight(row))

        view.close()

    def test_reference_toolbar_order_sort_and_explicit_rtl_cells(self):
        view = UsersView()
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
            ["display_name", "created_at", "is_active"],
        )

        emitted = []
        view.filters_requested.connect(emitted.append)
        view.toolbar.sort_combo.setCurrentIndex(1)
        self.assertEqual(emitted[-1]["order_by"], "created_at")

        view.show_users([USER], offset=0, count=1, filtered=False)
        for column in (0, 1, 3):
            self.assertTrue(view.table.item(0, column).textAlignment() & Qt.AlignmentFlag.AlignRight)

        self.assertIsNone(view.table.item(0, 2))
        self.assertTrue(view.table.cellWidget(0, 2).alignment() & Qt.AlignmentFlag.AlignRight)
