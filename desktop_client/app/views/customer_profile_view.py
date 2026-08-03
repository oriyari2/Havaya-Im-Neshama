from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from desktop_client.app.views.common import StatefulWidget
from desktop_client.app.views.design_tokens import SPACE_2, SPACE_3, SPACE_4
from desktop_client.app.views.management_common import RetryState
from desktop_client.app.views.management_visuals import ReadOnlyProfileCard, install_scaffold_hero
from desktop_client.app.views.ui_foundations import PageScaffold


class CustomerProfileView(StatefulWidget):
    retry_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.scaffold = PageScaffold("הפרופיל שלי", "פרטי הלקוח ופרטי הקשר השמורים במערכת")
        self.scaffold.root.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_4)
        self.scaffold.root.setSpacing(SPACE_2)
        root.addWidget(self.scaffold)
        self.hero = install_scaffold_hero(
            self.scaffold,
            "bookings-customer-hero.png",
            "תמונת פרופיל לקוח",
        )

        self.retry_state = RetryState()
        self.retry_state.hide()
        self.retry_state.retry_requested.connect(self.retry_requested)
        self.scaffold.main_content.addWidget(self.retry_state)
        self.scaffold.main_content.addWidget(self.state_label)

        # Physical layout mirrors the approved customer-detail screen:
        # a large primary card on the right and secondary/system cards stacked on the left.
        body = QWidget()
        body.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(SPACE_3)
        body_layout.setDirection(QHBoxLayout.Direction.LeftToRight)

        left_column = QWidget()
        left_column.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(SPACE_3)

        self.contact_card = ReadOnlyProfileCard("פרטי קשר", "secondary")
        self.system_card = ReadOnlyProfileCard("מידע מערכת", "system")
        left_layout.addWidget(self.contact_card)
        left_layout.addWidget(self.system_card)
        left_layout.addStretch(1)

        self.main_card = ReadOnlyProfileCard("פרטי לקוח", "primary")
        self.main_card.setMinimumWidth(430)
        self.main_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        body_layout.addWidget(left_column, 1)
        body_layout.addWidget(self.main_card, 1)
        self.scaffold.main_content.addWidget(body, 1)

        # Backward-compatible aliases used only internally by older code/tests.
        self.details = self.main_card
        self.contact_details = self.contact_card
        self.system_details = self.system_card

    def show_profile(self, details) -> None:
        self.retry_state.hide()
        for card in (self.main_card, self.contact_card, self.system_card):
            card.clear_rows()

        for label, value in details:
            mixed = any(token in label for token in ("דוא", "טלפון", "מזהה", "נוצר", "עודכן"))
            if label in {"איש קשר", "טלפון איש קשר"}:
                target = self.contact_card
            elif label in {"מצב", "נוצר", "עודכן"}:
                target = self.system_card
            else:
                target = self.main_card
            target.add_row(label, value, mixed_direction=mixed)

    def show_error(self, message, *, retriable=False, permission=False) -> None:
        self.retry_state.show_message(message, retriable=retriable)
