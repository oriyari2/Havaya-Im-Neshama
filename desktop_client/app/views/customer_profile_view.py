from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFormLayout, QLabel, QVBoxLayout
from desktop_client.app.views.common import StatefulWidget
from desktop_client.app.views.design_tokens import SPACE_3, SPACE_4
from desktop_client.app.views.management_common import RetryState
from desktop_client.app.views.ui_foundations import DetailPanel, PageScaffold, configure_mixed_direction

class CustomerProfileView(StatefulWidget):
    retry_requested = Signal()
    def __init__(self) -> None:
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.scaffold = PageScaffold("הפרופיל שלי", "פרטי הלקוח ופרטי הקשר השמורים במערכת")
        root.addWidget(self.scaffold)
        self.retry_state = RetryState()
        self.retry_state.hide()
        self.retry_state.retry_requested.connect(self.retry_requested)
        self.scaffold.main_content.addWidget(self.retry_state)
        self.scaffold.main_content.addWidget(self.state_label)
        self.card = DetailPanel("פרטי לקוח")
        self.details = QFormLayout()
        self.details.setContentsMargins(0, 0, 0, 0)
        self.details.setHorizontalSpacing(SPACE_4)
        self.details.setVerticalSpacing(SPACE_3)
        self.details.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.details.setFormAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.details.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.card.content.addLayout(self.details)
        self.card.content.addStretch()
        self.scaffold.main_content.addWidget(self.card, 1)
    def show_profile(self, details) -> None:
        self.retry_state.hide()
        while self.details.rowCount(): self.details.removeRow(0)
        for label, value in details:
            content = QLabel(value)
            content.setWordWrap(True)
            content.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            if any(token in label for token in ("דוא", "טלפון", "מזהה")):
                configure_mixed_direction(content)
                content.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.details.addRow(label, content)
    def show_error(self, message, *, retriable=False, permission=False) -> None: self.retry_state.show_message(message, retriable=retriable)
