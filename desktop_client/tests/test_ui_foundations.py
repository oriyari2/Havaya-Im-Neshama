from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QFormLayout, QFrame, QPushButton, QTableWidget, QWidget

from desktop_client.app.main import APP_STYLE, MainWindow
from desktop_client.app.models.request_state import RequestIdentity, RequestPhase, RequestState
from desktop_client.app.views.customer_dialogs import CustomerDialog
from desktop_client.app.views.instructor_dialogs import InstructorDialog
from desktop_client.app.views.user_dialogs import CreateUserDialog, EditUserDialog
from desktop_client.app.views.customers_view import CustomersView
from desktop_client.app.views.activities_view import ActivitiesView
from desktop_client.app.views.ai_chat_view import AIChatView
from desktop_client.app.views.bookings_view import BookingsView
from desktop_client.app.views.dashboard_view import DashboardView
from desktop_client.app.views.instructors_view import InstructorProfileView, InstructorsView
from desktop_client.app.views.knowledge_view import KnowledgeManagementView
from desktop_client.app.views.open_events_view import OpenEventsView
from desktop_client.app.views.design_tokens import (
    COLOR_BACKGROUND, COLOR_FOCUS, CONTROL_HEIGHT, DIALOG_WIDTH_DEFAULT,
    DURATION_STANDARD, ELEVATION_LOW, FONT_SIZE_BODY, ICON_SIZE, RADIUS_MEDIUM,
    SPACE_4, TABLE_ROW_HEIGHT,
)
from desktop_client.app.views.login_view import LoginView
from desktop_client.app.views.shell_view import ShellView
from desktop_client.app.views.users_view import UsersView
from desktop_client.app.views.ui_foundations import (
    ColumnKind, ColumnPolicy, FeedbackBanner, PageScaffold, StatePanel,
    configure_data_table, set_item_text,
)


class UiFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_tokens_and_neutral_theme_are_centralized(self) -> None:
        self.assertEqual((SPACE_4, CONTROL_HEIGHT, ICON_SIZE, DURATION_STANDARD, DIALOG_WIDTH_DEFAULT, TABLE_ROW_HEIGHT), (16, 40, 20, 200, 520, 40))
        self.assertEqual((COLOR_BACKGROUND, COLOR_FOCUS, FONT_SIZE_BODY, RADIUS_MEDIUM, ELEVATION_LOW), ("#F5F6F8", "#1F6FEB", 14, 8, (0, 1, 3, 12)))

    def test_neutral_text_and_semantic_colors_meet_contrast_target(self) -> None:
        def luminance(value: str) -> float:
            channels = [int(value[index:index + 2], 16) / 255 for index in (1, 3, 5)]
            linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
        def contrast(first: str, second: str) -> float:
            high, low = sorted((luminance(first), luminance(second)), reverse=True)
            return (high + 0.05) / (low + 0.05)
        pairs = (("#1F2933", "#F5F6F8"), ("#5F6B76", "#FFFFFF"), ("#FFFFFF", "#1F6FEB"), ("#176B45", "#E7F5ED"), ("#7A4D00", "#FFF4D6"), ("#A61B1B", "#FDECEC"))
        self.assertTrue(all(contrast(foreground, background) >= 4.5 for foreground, background in pairs))

    def test_request_state_and_identity_are_plain_and_deterministic(self) -> None:
        phases = {phase for phase in RequestPhase}
        self.assertEqual(len(phases), 10)
        state = RequestState(RequestPhase.LOADING, "טוען", "list", blocks_primary_action=True)
        self.assertTrue(state.blocks_primary_action)
        first = RequestIdentity(2, "customers", "detail", 4, "c1")
        self.assertTrue(first.is_current(RequestIdentity(2, "customers", "detail", 4, "c1")))
        self.assertFalse(first.is_current(RequestIdentity(2, "customers", "detail", 5, "c1")))
        with self.assertRaises(ValueError): RequestIdentity(0, "", "detail", 1)
        with self.assertRaises(ValueError): RequestIdentity(-1, "customers", "detail", 1)

    def test_page_scaffold_has_authoritative_slots(self) -> None:
        page = PageScaffold("כותרת")
        self.assertEqual(page.layout().contentsMargins().left(), 24)
        self.assertTrue(page.header.title.accessibleName())
        self.assertIsNotNone(page.action_bar)
        self.assertIsNotNone(page.filter_panel)
        self.assertIsNotNone(page.main_content)
        self.assertIsNotNone(page.footer_slot)
        self.assertTrue(page.action_bar.isHidden()); self.assertTrue(page.filter_panel.isHidden()); self.assertTrue(page.footer_region.isHidden()); self.assertTrue(page.header.description.isHidden())

    def test_feedback_and_state_panels_render_distinct_mechanisms(self) -> None:
        banner = FeedbackBanner(); banner.render(RequestState(RequestPhase.SUCCESS, "נשמר", "save")); self.assertFalse(banner.isHidden()); self.assertEqual(banner.property("feedback"), "success")
        self.assertEqual(banner._dismiss_timer.interval() + banner._fade.duration(), 2500); self.assertTrue(banner._dismiss_timer.isActive()); banner._fade_success(); QTest.qWait(300); self.assertTrue(banner.isHidden())
        panel = StatePanel(); panel.render(RequestState(RequestPhase.CONNECTION_ERROR, "אין חיבור", "list", retryable=True)); self.assertFalse(panel.isHidden()); self.assertFalse(panel.retry_button.isHidden())
        panel.render(RequestState(RequestPhase.STALE, "ישן", "list")); self.assertTrue(panel.isHidden())
        for phase in RequestPhase:
            panel.render(RequestState(phase, "מצב", "test", retryable=phase == RequestPhase.CONNECTION_ERROR))
            expected = phase in {RequestPhase.LOADING, RequestPhase.EMPTY, RequestPhase.CONNECTION_ERROR, RequestPhase.SERVER_ERROR, RequestPhase.AUTHORIZATION_ERROR}
            self.assertEqual(not panel.isHidden(), expected, phase)

    def test_entity_dialogs_share_customer_geometry_hierarchy_and_actions(self) -> None:
        dialogs = (CustomerDialog(), InstructorDialog(), CreateUserDialog(), EditUserDialog({"email": "m@example.com", "display_name": "מנהל"}))
        for dialog in dialogs:
            self.assertEqual(dialog.minimumSize().width(), 760); self.assertEqual(dialog.minimumSize().height(), 600); self.assertEqual(dialog.maximumWidth(), 860)
            self.assertEqual(dialog.heading_label.objectName(), "screenTitle"); self.assertEqual(dialog.form.rowWrapPolicy(), QFormLayout.RowWrapPolicy.WrapAllRows)
            self.assertGreaterEqual(dialog.save_button.minimumHeight(), 44); self.assertEqual(dialog.save_button.minimumWidth(), 120); self.assertEqual(dialog.cancel_button.minimumWidth(), 120)

    def test_management_modules_share_exact_customer_foundation_values(self) -> None:
        customer, instructor, manager = CustomersView(), InstructorsView(), UsersView()
        modules = (customer, instructor, manager)
        reference_header = customer.scaffold.header.layout()
        reference_toolbar = customer.toolbar.layout()
        for view in modules:
            header = view.scaffold.header.layout(); toolbar = view.toolbar.layout()
            self.assertEqual(header.contentsMargins(), reference_header.contentsMargins()); self.assertEqual(header.spacing(), reference_header.spacing())
            self.assertEqual(view.scaffold.header.title.objectName(), "screenTitle"); self.assertEqual(view.scaffold.header.description.alignment(), customer.scaffold.header.description.alignment())
            self.assertEqual(toolbar.contentsMargins(), reference_toolbar.contentsMargins()); self.assertEqual(toolbar.spacing(), reference_toolbar.spacing()); self.assertEqual(toolbar.direction(), reference_toolbar.direction())
            self.assertEqual([toolbar.itemAt(i).widget() for i in range(toolbar.count())],[view.toolbar.search_input,view.toolbar.search_button,view.toolbar.sort_combo,view.toolbar.refresh_button])
            self.assertEqual(view.toolbar.parentWidget().objectName(), "filterPanel"); self.assertIsInstance(view.toolbar.parentWidget(), QFrame)
            self.assertEqual(view.table.verticalHeader().defaultSectionSize(), customer.table.verticalHeader().defaultSectionSize()); self.assertEqual(view.table.horizontalHeader().minimumHeight(), customer.table.horizontalHeader().minimumHeight()); self.assertEqual(view.table.alternatingRowColors(), customer.table.alternatingRowColors())
            self.assertEqual(view.footer.maximumWidth(), customer.footer.maximumWidth()); self.assertEqual(view.back_button.minimumHeight(), customer.back_button.minimumHeight())

    def test_table_policy_sets_accessibility_density_and_elision(self) -> None:
        table = QTableWidget(0, 3); configure_data_table(table, "בדיקה", (
            ColumnPolicy(ColumnKind.PRIMARY_TEXT),
            ColumnPolicy(ColumnKind.SECONDARY_TEXT),
            ColumnPolicy(ColumnKind.COMPACT),
        ))
        self.assertEqual(table.accessibleName(), "בדיקה")
        self.assertEqual(table.verticalHeader().defaultSectionSize(), TABLE_ROW_HEIGHT)
        self.assertEqual(table.textElideMode(), Qt.TextElideMode.ElideRight)

    def test_login_accessibility_focus_rtl_and_duplicate_guard(self) -> None:
        view = LoginView(); emitted = []; view.login_requested.connect(lambda email, password: emitted.append((email, password)))
        self.assertEqual(view.layoutDirection(), Qt.LayoutDirection.RightToLeft)
        self.assertEqual(view.email_input.layoutDirection(), Qt.LayoutDirection.LeftToRight)
        self.assertTrue(view.email_input.accessibleName()); self.assertTrue(view.password_input.accessibleName())
        view.email_input.setText("user@example.com"); view.password_input.setText("secret"); view.set_loading(True); view._emit_login(); self.assertEqual(emitted, [])
        view.set_loading(False); view._emit_login(); self.assertEqual(len(emitted), 1)

    def test_login_layout_is_wide_stacked_and_centered(self) -> None:
        view = LoginView(); view.resize(1200, 760); view.show(); self.app.processEvents()
        self.assertGreaterEqual(view.panel.width(), 520)
        self.assertGreaterEqual(view.email_input.width(), 440); self.assertEqual(view.email_input.width(), view.password_input.width())
        self.assertEqual(view.login_button.width(), view.email_input.width())
        self.assertLess(view.email_label.geometry().bottom(), view.email_input.geometry().top())
        self.assertLess(view.password_label.geometry().bottom(), view.password_input.geometry().top())
        view.show_error("פרטי ההתחברות אינם תקינים"); self.app.processEvents()
        self.assertLess(view.password_input.geometry().bottom(), view.feedback.geometry().top())
        self.assertLess(view.feedback.geometry().bottom(), view.login_button.geometry().top())
        self.assertLessEqual(abs(view.panel.geometry().center().x() - view.rect().center().x()), 1)
        self.assertEqual(
            [view.welcome_label.text(), view.application_name_label.text(), view.description_label.text(), view.instruction_label.text()],
            ["ברוכים הבאים", "חוויה עם נשמה", "מערכת לניהול חוויות, לקוחות והזמנות", "התחברו כדי להמשיך למערכת הניהול"],
        )
        view.close()

    def test_semantic_table_policy_fills_viewport_and_expands_primary_column(self) -> None:
        table = QTableWidget(0, 3); configure_data_table(table, "table", (
            ColumnPolicy(ColumnKind.PRIMARY_TEXT),
            ColumnPolicy(ColumnKind.SECONDARY_TEXT),
            ColumnPolicy(ColumnKind.COMPACT),
        )); table.resize(420, 240); table.show(); self.app.processEvents()
        small = tuple(table.columnWidth(index) for index in range(3))
        self.assertLessEqual(abs(table.viewport().width() - 1 - sum(small)), 1)
        self.assertGreater(small[0], small[1]); self.assertGreater(small[1], small[2])
        table.resize(700, 240); self.app.processEvents()
        large = tuple(table.columnWidth(index) for index in range(3))
        self.assertLessEqual(abs(table.viewport().width() - 1 - sum(large)), 1)
        self.assertGreater(large[0], small[0]); self.assertEqual(large[2], small[2]); table.close()

    def test_semantic_table_policy_caps_bounded_columns_and_preserves_minimums(self) -> None:
        table = QTableWidget(0, 4); configure_data_table(table, "table", (
            ColumnPolicy(ColumnKind.PRIMARY_TEXT, 180),
            ColumnPolicy(ColumnKind.SECONDARY_TEXT, 140, 220),
            ColumnPolicy(ColumnKind.SECONDARY_TEXT, 150, 240),
            ColumnPolicy(ColumnKind.COMPACT, 110),
        ))
        table.resize(1100, 240); table.show(); self.app.processEvents()
        widths = tuple(table.columnWidth(index) for index in range(4))
        self.assertGreater(widths[0], widths[1])
        self.assertEqual(widths[1:], (220, 240, 110))
        self.assertLessEqual(abs(table.viewport().width() - 1 - sum(widths)), 1)
        with self.assertRaises(ValueError):
            ColumnPolicy(ColumnKind.COMPACT, 100, 90)
        table.close()

    def test_elided_tooltips_preserve_full_directional_values(self) -> None:
        from PySide6.QtWidgets import QTableWidgetItem
        table = QTableWidget(1, 2); configure_data_table(table, "table")
        set_item_text(table, 0, 0, QTableWidgetItem("שם עברי ארוך"), tooltip_direction=Qt.LayoutDirection.RightToLeft)
        set_item_text(table, 0, 1, QTableWidgetItem("user@example.com"), tooltip_direction=Qt.LayoutDirection.LeftToRight)
        self.assertIn('dir="rtl"', table.item(0, 0).toolTip()); self.assertIn("שם עברי ארוך", table.item(0, 0).toolTip())
        self.assertIn('dir="ltr"', table.item(0, 1).toolTip()); self.assertIn("user@example.com", table.item(0, 1).toolTip())

    def test_shell_bounds_sidebar_and_marks_current_navigation(self) -> None:
        shell = ShellView("manager@example.com"); shell.configure_navigation((("dashboard", "לוח בקרה"), ("customers", "לקוחות")))
        page = PageScaffold("לקוחות"); shell.add_page("customers", page); shell.show_page("customers")
        self.assertEqual(shell.layoutDirection(), Qt.LayoutDirection.RightToLeft)
        self.assertEqual(shell.navigation_buttons["customers"].accessibleDescription(), "העמוד הנוכחי")
        self.assertTrue(shell.logout_button.accessibleName())

    def test_customers_accessibility_disabled_help_and_tooltips(self) -> None:
        view = CustomersView(); self.assertEqual(view.table.accessibleName(), "רשימת לקוחות"); self.assertTrue(view.edit_button.accessibleDescription())
        view.show_customers([{"id": "c1", "name": "שם ארוך", "customer_type": "עסקי", "city": "חיפה", "phone": "050", "email": "a@example.com", "is_active": True}], offset=0, count=1, filtered=False)
        self.assertIn('dir="rtl"', view.table.item(0, 0).toolTip())
        self.assertEqual(view.table.columnCount(), 4)
        self.assertNotIn("דוא״ל", [view.table.horizontalHeaderItem(column).text() for column in range(view.table.columnCount())])

    def test_customers_uses_one_feedback_mechanism_for_current_context(self) -> None:
        view = CustomersView(); view.show_error("אין חיבור", retriable=True)
        self.assertFalse(view.retry.isHidden()); self.assertTrue(view.scaffold.feedback.isHidden())
        view.show_customers([{"id": "c1", "name": "לקוח", "customer_type": "—", "city": "—", "phone": "—", "email": "—", "is_active": True}], offset=0, count=1, filtered=False)
        view.show_error("אין חיבור", retriable=True)
        self.assertTrue(view.retry.isHidden()); self.assertFalse(view.scaffold.feedback.isHidden())

    def test_dialog_standard_preserves_values_focuses_validation_and_cancel(self) -> None:
        dialog = CustomerDialog({"name": "נשמר", "email": "bad"}); self.assertGreaterEqual(dialog.width(), DIALOG_WIDTH_DEFAULT); self.assertTrue(dialog.save_button.isDefault())
        dialog.show_error("כתובת הדוא״ל אינה תקינה."); self.app.processEvents(); self.assertEqual(dialog.focusWidget(), dialog.fields["email"]); self.assertEqual(dialog.values()["name"], "נשמר")
        dialog.reject(); self.assertEqual(dialog.result(), QDialog.DialogCode.Rejected)
        self.assertEqual(dialog.fields["contact_phone"].layoutDirection(), Qt.LayoutDirection.LeftToRight)

    def test_dialog_labels_keyboard_scrolling_and_focus_restoration(self) -> None:
        parent = QWidget(); opener = QPushButton("פתיחה", parent); parent.show(); opener.setFocus(); self.app.processEvents()
        dialog = CustomerDialog(parent=parent); submitted = []; dialog.submitted.connect(lambda values, form: submitted.append(values)); dialog.show(); self.app.processEvents()
        self.assertIs(dialog.form.labelForField(dialog.fields["name"]).buddy(), dialog.fields["name"]); self.assertIs(dialog.focusWidget(), dialog.fields["name"])
        dialog.fields["name"].setText("לקוח"); dialog.fields["contact_name"].setText("איש קשר"); dialog.fields["contact_phone"].setText("050"); QTest.keyClick(dialog.fields["name"], Qt.Key.Key_Return); self.assertEqual(len(submitted), 1)
        submitted.clear(); dialog.notes.setFocus(); QTest.keyClick(dialog.notes, Qt.Key.Key_Return); self.assertEqual(submitted, [])
        self.assertGreaterEqual(dialog.width(), 760); self.assertLessEqual(dialog.width(), 860); self.assertTrue(dialog.scroll.widgetResizable())
        QTest.keyClick(dialog, Qt.Key.Key_Escape); self.app.processEvents(); self.assertEqual(dialog.result(), QDialog.DialogCode.Rejected); self.assertIs(parent.focusWidget(), opener); parent.close()

    def test_supported_minimum_keeps_pilot_regions_meaningfully_sized(self) -> None:
        shell = ShellView("manager@example.com"); customers = CustomersView(); shell.configure_navigation((("customers", "לקוחות"),)); shell.add_page("customers", customers); shell.show_page("customers"); shell.resize(1024, 640); shell.show(); self.app.processEvents()
        self.assertGreaterEqual(customers.table.width(), 500)
        for widget in (customers.create_button, customers.toolbar, customers.table, customers.footer): self.assertTrue(widget.isVisibleTo(customers), widget)
        self.assertEqual(customers.sort_by.currentData(), "name"); self.assertGreater(customers.table.height(), 180); shell.close()

    def test_customer_table_and_dedicated_details_page_use_supported_sizes(self) -> None:
        shell = ShellView("manager@example.com"); customers = CustomersView()
        shell.configure_navigation((("customers", "לקוחות"),)); shell.add_page("customers", customers); shell.show_page("customers"); shell.show()
        measurements = []
        for width, height in ((1024, 640), (1200, 760), (1440, 900)):
            shell.resize(width, height); self.app.processEvents()
            customer_widths = tuple(customers.table.columnWidth(index) for index in range(customers.table.columnCount()))
            measurements.append(customer_widths)
            unused = customers.table.viewport().width() - 1 - sum(customer_widths)
            self.assertTrue(abs(unused) <= 1 or unused < 0)
            self.assertGreater(customer_widths[0], customer_widths[3])
        self.assertGreater(measurements[2][0], measurements[1][0])
        self.assertEqual(measurements[2][3], measurements[1][3])
        customers.show_customers([{"id": "c1", "name": "לקוח", "customer_type": "עסקי", "city": "חיפה", "phone": "050", "email": "a@example.com", "is_active": True}], offset=0, count=1, filtered=False)
        customers.select_customer("c1"); customers._open_selected_customer(); self.app.processEvents()
        self.assertIs(customers.pages.currentWidget(), customers.details_page); self.assertTrue(customers.back_button.isVisibleTo(customers)); shell.close()

    def test_global_theme_does_not_force_pilot_geometry_on_excluded_modules(self) -> None:
        self.app.setStyleSheet(APP_STYLE)
        excluded = (DashboardView(), ActivitiesView("manager"), InstructorsView(), InstructorProfileView(), BookingsView("manager"), OpenEventsView(), KnowledgeManagementView(), AIChatView())
        for view in excluded:
            view.show(); self.app.processEvents(); self.assertTrue(view.isVisible()); view.close()
        activity = excluded[1]
        self.assertIsNone(activity.table.property("task20Table")); self.assertEqual(activity.upload_image_button.minimumHeight(), 0)
        pilot = CustomersView(); pilot.show(); self.app.processEvents(); self.assertTrue(pilot.table.property("task20Table")); self.assertGreaterEqual(pilot.create_button.sizeHint().height(), 32); pilot.close()

    def test_main_window_enforces_supported_minimum(self) -> None:
        class Api:
            def set_unauthorized_handler(self, handler): self.handler = handler
            def set_access_token(self, token): pass
        window = MainWindow(Api()); self.assertEqual((window.minimumWidth(), window.minimumHeight()), (1024, 640)); window.close()


if __name__ == "__main__":
    unittest.main()
