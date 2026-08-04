from __future__ import annotations

from desktop_client.app.features.contracts import FeatureContext
from desktop_client.app.presenters.activities_presenter import ActivitiesPresenter
from desktop_client.app.views.activities_view import ActivitiesView


def register(context: FeatureContext) -> None:
    role = context.session.role
    view = ActivitiesView(role)
    presenter = ActivitiesPresenter(view, context.services.activity, role, executor=context.executor)

    view.filters_requested.connect(presenter.apply_filters)
    view.page_requested.connect(presenter.page)
    view.activity_selected.connect(presenter.select)
    view.retry_requested.connect(presenter.retry)
    view.image_selected.connect(presenter.select_image)
    view.preview_retry_requested.connect(presenter.retry_preview)

    if role == "manager":
        view.create_requested.connect(presenter.begin_create)
        view.edit_requested.connect(presenter.begin_edit)
        view.deactivate_requested.connect(presenter.deactivate)
        view.reactivate_requested.connect(presenter.reactivate)
        view.upload_image_requested.connect(presenter.upload_image)
        view.delete_image_requested.connect(presenter.delete_image)

    context.add_page("activities", view, presenter)
