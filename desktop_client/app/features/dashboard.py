from __future__ import annotations

from desktop_client.app.features.contracts import FeatureContext
from desktop_client.app.presenters.dashboard_presenter import DashboardPresenter
from desktop_client.app.views.dashboard_view import DashboardView


def register(context: FeatureContext) -> None:
    view = DashboardView(context.session.role)
    presenter = DashboardPresenter(
        view,
        context.services.booking,
        context.session.role,
        context.navigate_with_filters,
        executor=context.executor,
    )
    view.drill_down_requested.connect(presenter.drill_down)
    view.shortcut_requested.connect(presenter.drill_down)
    context.add_page("dashboard", view, presenter)
