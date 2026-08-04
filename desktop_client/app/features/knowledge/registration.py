from __future__ import annotations

from desktop_client.app.features.contracts import FeatureContext
from desktop_client.app.features.knowledge.presenter import KnowledgeManagementPresenter
from desktop_client.app.features.knowledge.view import KnowledgeManagementView


def register(context: FeatureContext) -> None:
    if context.session.role != "manager":
        return

    view = KnowledgeManagementView()
    presenter = KnowledgeManagementPresenter(view, context.services.knowledge, context.executor)
    view.save_requested.connect(presenter.save)
    view.replace_requested.connect(presenter.replace)
    view.delete_requested.connect(presenter.delete)
    view.source_selected.connect(presenter.select_source)
    view.retry_requested.connect(presenter.retry)
    context.add_page("knowledge", view, presenter)
