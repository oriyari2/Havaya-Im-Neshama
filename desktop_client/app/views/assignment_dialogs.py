from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from desktop_client.app.views.entity_selector import SearchableEntitySelector
from desktop_client.app.views.management_common import PaginationFooter, RetryState


class InstructorSelectorDialog(QDialog):
    def __init__(self, activity, query_handler, choose_handler, parent=None):
        super().__init__(parent); self.activity = activity; self.query_handler = query_handler; self.choose_handler = choose_handler; self.filters = {"search": None, "city": None, "is_active": True, "order_by": "full_name", "limit": 25, "offset": 0}
        self.setWindowTitle(f"בחירת מדריך — {activity['activity_name']}"); self.setLayoutDirection(Qt.LayoutDirection.RightToLeft); self.setMinimumWidth(620)
        root = QVBoxLayout(self); title = QLabel(self.windowTitle()); title.setObjectName("screenTitle"); title.setAlignment(Qt.AlignmentFlag.AlignRight); root.addWidget(title)
        context = QLabel("המדריכים המוצגים פעילים. כללי כשירות והתנגשות נאכפים בשרת."); context.setAlignment(Qt.AlignmentFlag.AlignRight); root.addWidget(context)
        self.selector = SearchableEntitySelector("חיפוש מדריך"); root.addWidget(self.selector); self.search = self.selector.combo
        self.retry = RetryState(); self.retry.hide(); self.retry.retry_requested.connect(self._query); root.addWidget(self.retry)
        self.footer = PaginationFooter(); self.footer.page_requested.connect(self._page); root.addWidget(self.footer)
        actions = QHBoxLayout(); actions.setDirection(QHBoxLayout.Direction.RightToLeft); self.choose_button = QPushButton("שיבוץ מדריך"); cancel = QPushButton("ביטול"); actions.addWidget(self.choose_button); actions.addWidget(cancel); actions.addStretch(); root.addLayout(actions); self.choose_button.clicked.connect(self._choose); cancel.clicked.connect(self.reject)
        self._timer = QTimer(self); self._timer.setSingleShot(True); self._timer.setInterval(300); self._timer.timeout.connect(self._search); self.search.lineEdit().textEdited.connect(lambda _text: self._timer.start())
    def _query(self): self.selector.set_loading(True); self.query_handler(dict(self.filters))
    def _search(self): self.filters.update(search=self.search.currentText().strip() or None, offset=0); self._query()
    def _page(self, offset, limit): self.filters.update(offset=offset, limit=limit); self._query()
    def show_instructors(self, items, *, offset, count):
        self.retry.hide(); self.selector.set_loading(False); allowed = [item for item in items if not item.get("_already_assigned") and item.get("is_active", True)]; self.selector.set_items(allowed, label_key="full_name", context_keys=("city", "phone"), active_only=True); self.footer.set_page(offset=offset, count=count)
    def show_error(self, message, *, retriable=False): self.selector.set_loading(False); self.retry.show_message(message, retriable=retriable); self.selector.show_error(message)
    def _choose(self):
        value = self.selector.selected_entity()
        if value is not None: self.choose_handler(value)
    def close_success(self): self.accept()
