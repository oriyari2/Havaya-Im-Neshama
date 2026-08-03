from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from desktop_client.app.views.design_tokens import SPACE_2, SPACE_3, SPACE_4
from desktop_client.app.views.entity_selector import SearchableEntitySelector
from desktop_client.app.views.management_common import PaginationFooter, RetryState
from desktop_client.app.views.management_visuals import style_reference_button

_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute


class InstructorSelectorDialog(QDialog):
    def __init__(self, activity, query_handler, choose_handler, parent=None):
        super().__init__(parent)
        self.activity = activity
        self.query_handler = query_handler
        self.choose_handler = choose_handler
        self.filters = {"search": None, "city": None, "is_active": True, "order_by": "full_name", "limit": 25, "offset": 0}
        self.setWindowTitle(f"בחירת מדריך — {activity['activity_name']}")
        self.setObjectName("task20Dialog")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumWidth(640)
        self.resize(700, 460)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(SPACE_3)

        title = QLabel(self.windowTitle())
        title.setObjectName("screenTitle")
        title.setAlignment(_RIGHT)
        root.addWidget(title)
        context = QLabel("בחירת מדריך פעיל לפעילות. כללי כשירות והתנגשות נאכפים בשרת.")
        context.setProperty("dialogLead", True)
        context.setAlignment(_RIGHT)
        context.setWordWrap(True)
        root.addWidget(context)

        card = QFrame()
        card.setProperty("dialogSection", True)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_4)
        card_layout.setSpacing(SPACE_3)
        heading = QLabel("מדריכים זמינים")
        heading.setProperty("dialogSectionTitle", True)
        heading.setAlignment(_RIGHT)
        card_layout.addWidget(heading)

        self.selector = SearchableEntitySelector("חיפוש מדריך")
        card_layout.addWidget(self.selector)
        self.search = self.selector.combo
        self.search.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.search.lineEdit().setAlignment(_RIGHT)

        self.retry = RetryState()
        self.retry.hide()
        self.retry.retry_requested.connect(self._query)
        card_layout.addWidget(self.retry)

        self.footer = PaginationFooter()
        self.footer.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.footer.page_requested.connect(self._page)
        card_layout.addWidget(self.footer, alignment=Qt.AlignmentFlag.AlignHCenter)
        root.addWidget(card, 1)

        actions = QHBoxLayout()
        actions.setDirection(QHBoxLayout.Direction.LeftToRight)
        self.choose_button = QPushButton("שיבוץ מדריך")
        cancel = QPushButton("ביטול")
        style_reference_button(self.choose_button, "primary")
        style_reference_button(cancel, "secondary")
        self.choose_button.setMinimumWidth(150)
        cancel.setMinimumWidth(130)
        actions.addWidget(cancel)
        actions.addWidget(self.choose_button)
        actions.addStretch(1)
        root.addLayout(actions)
        self.choose_button.clicked.connect(self._choose)
        cancel.clicked.connect(self.reject)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(300)
        self._timer.timeout.connect(self._search)
        self.search.lineEdit().textEdited.connect(lambda _text: self._timer.start())

    def _query(self):
        self.selector.set_loading(True)
        self.query_handler(dict(self.filters))

    def _search(self):
        self.filters.update(search=self.search.currentText().strip() or None, offset=0)
        self._query()

    def _page(self, offset, limit):
        self.filters.update(offset=offset, limit=limit)
        self._query()

    def show_instructors(self, items, *, offset, count):
        self.retry.hide()
        self.selector.set_loading(False)
        allowed = [item for item in items if not item.get("_already_assigned") and item.get("is_active", True)]
        self.selector.set_items(allowed, label_key="full_name", context_keys=("city", "phone"), active_only=True)
        self.footer.set_page(offset=offset, count=count)

    def show_error(self, message, *, retriable=False):
        self.selector.set_loading(False)
        self.retry.show_message(message, retriable=retriable)
        self.selector.show_error(message)

    def _choose(self):
        value = self.selector.selected_entity()
        if value is not None:
            self.choose_handler(value)

    def close_success(self):
        self.accept()
