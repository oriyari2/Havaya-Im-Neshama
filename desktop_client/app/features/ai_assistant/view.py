from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from desktop_client.app.resource_paths import asset_path
from desktop_client.app.shared.ui.common import StatefulWidget
from desktop_client.app.shared.ui.design_tokens import (
    COLOR_BORDER,
    COLOR_BRAND,
    COLOR_BRAND_HOVER,
    COLOR_BRAND_PRESSED,
    COLOR_DISABLED_BACKGROUND,
    COLOR_DISABLED_TEXT,
    COLOR_SURFACE,
    COLOR_TEXT,
    COLOR_TEXT_MUTED,
    SPACE_1,
    SPACE_2,
    SPACE_3,
    SPACE_4,
)
from desktop_client.app.shared.ui.management_visuals import ManagementHero

_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute


class AIChatView(StatefulWidget):
    """Branded RTL chat view matching the approved AI reference without changing presenter behavior."""

    message_submitted = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("aiChatPage")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        root = QVBoxLayout(self)
        root.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_4)
        root.setSpacing(SPACE_3)

        hero_path = asset_path("heroes", "ai-agent-hero.png")
        self.hero = ManagementHero(hero_path, "תמונת פעילות למסך יועץ AI")
        hero_title = QLabel("יועץ AI")
        hero_title.setObjectName("screenTitle")
        hero_subtitle = QLabel("שאלו על פעילויות, ציוד, נהלים והידע המאושר של העסק")
        self.hero.attach_header(hero_title, hero_subtitle, None)
        root.addWidget(self.hero)

        self.state_label.setObjectName("aiStateLabel")
        self.state_label.setAlignment(_RIGHT)
        self.state_label.setWordWrap(True)
        root.addWidget(self.state_label)

        conversation_card = QFrame()
        conversation_card.setObjectName("aiConversationCard")
        conversation_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        conversation_layout = QVBoxLayout(conversation_card)
        conversation_layout.setContentsMargins(SPACE_3, SPACE_3, SPACE_3, SPACE_3)
        conversation_layout.setSpacing(SPACE_2)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("aiConversationScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.messages_host = QWidget()
        self.messages_host.setObjectName("aiMessagesHost")
        self.messages_host.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.messages_layout = QVBoxLayout(self.messages_host)
        self.messages_layout.setContentsMargins(SPACE_2, SPACE_2, SPACE_2, SPACE_2)
        self.messages_layout.setSpacing(SPACE_3)
        self.messages_layout.addStretch(1)
        self.scroll.setWidget(self.messages_host)
        conversation_layout.addWidget(self.scroll, 1)
        root.addWidget(conversation_card, 1)

        # Keep the legacy history attribute for compatibility with any tests/tools that inspect it.
        self.history = QTextEdit()
        self.history.setReadOnly(True)
        self.history.hide()

        composer_card = QFrame()
        composer_card.setObjectName("aiComposerCard")
        composer = QHBoxLayout(composer_card)
        composer.setContentsMargins(SPACE_2, SPACE_2, SPACE_2, SPACE_2)
        composer.setSpacing(SPACE_2)
        composer.setDirection(QHBoxLayout.Direction.LeftToRight)

        self.submit_button = QPushButton("שליחה")
        self.submit_button.setObjectName("aiSendButton")
        self.submit_button.setMinimumWidth(126)
        self.submit_button.setMinimumHeight(44)
        self.submit_button.clicked.connect(self._submit)
        self._apply_send_style()

        self.prompt_input = QLineEdit()
        self.prompt_input.setObjectName("aiPromptInput")
        self.prompt_input.setPlaceholderText("כתבו שאלה ליועץ...")
        self.prompt_input.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.prompt_input.setAlignment(_RIGHT)
        self.prompt_input.setMinimumHeight(44)
        self.prompt_input.returnPressed.connect(self._submit)

        composer.addWidget(self.submit_button)
        composer.addWidget(self.prompt_input, 1)
        root.addWidget(composer_card)

    def _apply_send_style(self) -> None:
        self.submit_button.setStyleSheet(
            f"""
            QPushButton {{
                color: #FFFFFF;
                background: {COLOR_BRAND};
                border: 1px solid {COLOR_BRAND};
                border-radius: 10px;
                padding: 0 20px;
                font-weight: 700;
            }}
            QPushButton:hover {{ color: #FFFFFF; background: {COLOR_BRAND_HOVER}; border-color: {COLOR_BRAND_HOVER}; }}
            QPushButton:pressed {{ color: #FFFFFF; background: {COLOR_BRAND_PRESSED}; border-color: {COLOR_BRAND_PRESSED}; }}
            QPushButton:disabled {{ color: {COLOR_DISABLED_TEXT}; background: {COLOR_DISABLED_BACKGROUND}; border-color: {COLOR_BORDER}; }}
            """
        )

    def _submit(self) -> None:
        self.message_submitted.emit(self.prompt_input.text())

    def append_message(self, sender: str, message: str) -> None:
        is_user = sender.strip() in {"את/ה", "את", "אתה", "user", "User"}
        self._append_visual_message(sender, message, is_user=is_user)

        # Legacy hidden history mirror.
        safe_sender = self._escape_html(sender)
        safe_message = self._escape_html(message).replace("\n", "<br>")
        self.history.append(f"<p dir='rtl' align='right'><b>{safe_sender}:</b><br>{safe_message}</p>")
        self.state_label.hide()
        QTimer.singleShot(0, self._scroll_to_bottom)

    def _append_visual_message(self, sender: str, message: str, *, is_user: bool) -> None:
        # Insert before the trailing stretch.
        insert_at = max(0, self.messages_layout.count() - 1)

        row = QWidget()
        # Use physical LTR layout so user and assistant can occupy opposite sides
        # regardless of the application's global RTL direction.
        row.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        row_layout = QHBoxLayout(row)
        row_layout.setDirection(QHBoxLayout.Direction.LeftToRight)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(SPACE_2)

        avatar = QLabel()
        avatar.setObjectName("aiAvatarUser" if is_user else "aiAvatarAssistant")
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if is_user:
            # A clear user avatar instead of the previous empty circle.
            avatar.setText("👤")
            avatar.setAccessibleName("משתמש")
        else:
            logo_path = asset_path("branding", "logo-sidebar.png")
            pixmap = QPixmap(str(logo_path))
            if not pixmap.isNull():
                avatar.setPixmap(
                    pixmap.scaled(
                        34,
                        34,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
            avatar.setAccessibleName("יועץ AI")

        bubble = QFrame()
        bubble.setProperty("aiMessage", "user" if is_user else "assistant")
        bubble.setMaximumWidth(820 if is_user else 900)
        bubble.setMinimumWidth(300)
        bubble.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_3)
        bubble_layout.setSpacing(SPACE_2)

        sender_label = QLabel(sender)
        sender_label.setObjectName("aiMessageSender")
        sender_label.setAlignment(_RIGHT)
        sender_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        sender_label.setTextFormat(Qt.TextFormat.PlainText)
        bubble_layout.addWidget(sender_label)

        answer_text, source_lines = self._split_sources(message)
        body = QLabel(answer_text or " ")
        body.setObjectName("aiMessageBody")
        body.setTextFormat(Qt.TextFormat.PlainText)
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        body.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        body.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignAbsolute)
        bubble_layout.addWidget(body)

        if source_lines:
            source_card = QFrame()
            source_card.setProperty("aiSource", True)
            source_layout = QVBoxLayout(source_card)
            source_layout.setContentsMargins(SPACE_3, SPACE_2, SPACE_3, SPACE_2)
            source_layout.setSpacing(SPACE_1)
            source_title = QLabel("מקורות")
            source_title.setObjectName("aiSourceTitle")
            source_title.setAlignment(_RIGHT)
            source_layout.addWidget(source_title)
            for line in source_lines:
                source = QLabel(line.lstrip("- ").strip())
                source.setTextFormat(Qt.TextFormat.PlainText)
                source.setWordWrap(True)
                source.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                source.setAlignment(_RIGHT)
                source.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                source_layout.addWidget(source)
            bubble_layout.addWidget(source_card)

        if is_user:
            # User message sits on the physical right side.
            row_layout.addStretch(1)
            row_layout.addWidget(bubble, 0, Qt.AlignmentFlag.AlignTop)
            row_layout.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)
        else:
            # Assistant response sits on the physical left side.
            row_layout.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)
            row_layout.addWidget(bubble, 0, Qt.AlignmentFlag.AlignTop)
            row_layout.addStretch(1)

        self.messages_layout.insertWidget(insert_at, row)

    @staticmethod
    def _split_sources(message: str) -> tuple[str, list[str]]:
        marker = "\n\nמקורות:\n"
        if marker not in message:
            return message, []
        answer, raw_sources = message.split(marker, 1)
        lines = [line.strip() for line in raw_sources.splitlines() if line.strip()]
        return answer, lines

    def _scroll_to_bottom(self) -> None:
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def clear_input(self) -> None:
        self.prompt_input.clear()

    def clear_error(self) -> None:
        self.state_label.hide()

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
