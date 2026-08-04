from __future__ import annotations

from desktop_client.app.features.contracts import FeatureContext
from desktop_client.app.features.instructors.presenter import InstructorProfilePresenter, InstructorsPresenter
from desktop_client.app.features.instructors.view import InstructorProfileView, InstructorsView


def register(context: FeatureContext) -> None:
    session = context.session
    if session.role == "manager":
        view = InstructorsView()
        presenter = InstructorsPresenter(
            view,
            context.services.instructor,
            context.services.user,
            executor=context.executor,
        )
        view.filters_requested.connect(presenter.apply_filters)
        view.page_requested.connect(presenter.page)
        view.instructor_selected.connect(presenter.select)
        view.retry_requested.connect(presenter.retry)
        view.create_requested.connect(presenter.begin_create)
        view.edit_requested.connect(presenter.begin_edit)
        view.deactivate_requested.connect(presenter.deactivate)
        view.reactivate_requested.connect(presenter.activate)
        view.change_password_requested.connect(presenter.begin_change_password)
        context.add_page("instructors", view, presenter)
        return

    if session.role == "instructor" and session.instructor_id:
        view = InstructorProfileView()
        presenter = InstructorProfilePresenter(view, context.services.instructor, executor=context.executor)
        view.retry_requested.connect(presenter.retry)
        context.add_page("my_profile", view, presenter)
