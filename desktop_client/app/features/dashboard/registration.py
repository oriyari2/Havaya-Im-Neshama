from __future__ import annotations

from desktop_client.app.features.contracts import FeatureContext
from desktop_client.app.features.dashboard.presenter import DashboardPresenter
from desktop_client.app.features.dashboard.view import DashboardView


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
    view.year_changed.connect(presenter.load_chart)
    view.chart_retry_requested.connect(presenter.load_chart)
    context.add_page("dashboard", view, presenter)
