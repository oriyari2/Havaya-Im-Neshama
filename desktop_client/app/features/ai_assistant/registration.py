from __future__ import annotations

from desktop_client.app.features.contracts import FeatureContext
from desktop_client.app.features.ai_assistant.presenter import AIChatPresenter
from desktop_client.app.features.ai_assistant.view import AIChatView


def register(context: FeatureContext) -> None:
    view = AIChatView()
    presenter = AIChatPresenter(view, context.services.ai_chat, context.executor)
    view.message_submitted.connect(presenter.send_message)
    context.add_page("ai_chat", view, presenter)
