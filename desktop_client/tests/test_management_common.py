from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from desktop_client.app.shared.ui.management_common import ActiveBadge, PaginationFooter, RetryState, SearchToolbar


class ManagementCommonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_search_toolbar_emits_trimmed_search_and_sort(self) -> None:
        toolbar = SearchToolbar(placeholder="חיפוש", sort_options=(("name", "שם"), ("created_at", "נוצר")))
        emitted = []
        toolbar.search_requested.connect(lambda search, sort: emitted.append((search, sort)))
        toolbar.search_input.setText("  לקוח  ")
        toolbar.sort_combo.setCurrentIndex(1)
        toolbar.search_button.click()
        self.assertEqual(emitted, [("לקוח", "created_at")])

    def test_pagination_emits_real_offsets(self) -> None:
        footer = PaginationFooter(limit=25)
        emitted = []
        footer.page_requested.connect(lambda offset, limit: emitted.append((offset, limit)))
        footer.set_page(offset=25, count=25)
        footer.previous_button.click()
        footer.next_button.click()
        self.assertEqual(emitted, [(0, 25), (50, 25)])
        footer.set_page(offset=50, count=4)
        self.assertFalse(footer.next_button.isEnabled())

    def test_active_badge_and_retry_state_render_functional_state(self) -> None:
        badge = ActiveBadge()
        badge.set_active(False)
        self.assertEqual(badge.text(), "לא פעיל")
        retry = RetryState()
        retried = []
        retry.retry_requested.connect(lambda: retried.append(True))
        retry.show_message("תקלה", retriable=True)
        retry.retry_button.click()
        self.assertEqual(retried, [True])
        retry.show_message("אין הרשאה", retriable=False)
        self.assertTrue(retry.retry_button.isHidden())


if __name__ == "__main__":
    unittest.main()
