from __future__ import annotations

from desktop_client.app.features.contracts import FeatureContext
from desktop_client.app.presenters.users_presenter import UsersPresenter
from desktop_client.app.views.users_view import UsersView


def register(context: FeatureContext) -> None:
    if context.session.role != "manager":
        return

    view = UsersView()
    presenter = UsersPresenter(
        view,
        context.services.user,
        current_user_id=context.session.user_id,
        session_role=context.session.role,
        executor=context.executor,
    )
    view.filters_requested.connect(presenter.apply_filters)
    view.page_requested.connect(presenter.page)
    view.user_selected.connect(presenter.select)
    view.retry_requested.connect(presenter.retry)
    view.create_requested.connect(presenter.begin_create)
    view.edit_requested.connect(presenter.begin_edit)
    view.activate_requested.connect(presenter.activate)
    view.deactivate_requested.connect(presenter.deactivate)
    view.reset_password_requested.connect(presenter.begin_reset_password)
    context.add_page("users", view, presenter)
