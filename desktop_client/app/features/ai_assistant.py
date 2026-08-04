from __future__ import annotations

from desktop_client.app.features.contracts import FeatureContext
from desktop_client.app.presenters.ai_chat_presenter import AIChatPresenter
from desktop_client.app.views.ai_chat_view import AIChatView


def register(context: FeatureContext) -> None:
    view = AIChatView()
    presenter = AIChatPresenter(view, context.services.ai_chat, context.executor)
    view.message_submitted.connect(presenter.send_message)
    context.add_page("ai_chat", view, presenter)
