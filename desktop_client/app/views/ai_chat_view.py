from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout

from desktop_client.app.views.common import StatefulWidget


class AIChatView(StatefulWidget):
    message_submitted = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QVBoxLayout(self)
        title = QLabel("יועץ AI")
        title.setObjectName("screenTitle")
        layout.addWidget(title)
        layout.addWidget(self.state_label)

        self.history = QTextEdit()
        self.history.setReadOnly(True)
        self.history.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.history.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.history, 1)

        composer = QHBoxLayout()
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("כתבו שאלה ליועץ...")
        self.prompt_input.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.prompt_input.returnPressed.connect(self._submit)
        self.submit_button = QPushButton("שליחה")
        self.submit_button.clicked.connect(self._submit)
        composer.addWidget(self.prompt_input, 1)
        composer.addWidget(self.submit_button)
        layout.addLayout(composer)

    def _submit(self) -> None:
        self.message_submitted.emit(self.prompt_input.text())

    def append_message(self, sender: str, message: str) -> None:
        safe_sender = self._escape_html(sender)
        safe_message = self._escape_html(message).replace("\n", "<br>")
        self.history.append(f"<p dir='rtl' align='right'><b>{safe_sender}:</b><br>{safe_message}</p>")
        self.history.moveCursor(QTextCursor.MoveOperation.End)
        self.state_label.hide()

    def clear_input(self) -> None:
        self.prompt_input.clear()

    def set_loading(self, loading: bool) -> None:
        self.prompt_input.setEnabled(not loading)
        self.submit_button.setDisabled(loading)
        self.submit_button.setText("חושב..." if loading else "שליחה")
        if loading:
            self.state_label.setText("ממתין לתשובת היועץ...")
            self.state_label.show()
        elif self.state_label.text() == "ממתין לתשובת היועץ...":
            self.state_label.hide()

    @staticmethod
    def _escape_html(value: str) -> str:
        return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
