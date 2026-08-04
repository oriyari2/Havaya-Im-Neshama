from __future__ import annotations

from desktop_client.app.features.contracts import FeatureContext
from desktop_client.app.features.bookings.assignments_presenter import BookingAssignmentsPresenter
from desktop_client.app.features.bookings.presenter import BookingsPresenter
from desktop_client.app.features.bookings.view import BookingsView


def register(context: FeatureContext) -> None:
    role = context.session.role
    page_key = "my_bookings" if role == "customer" else "bookings"
    view = BookingsView(role)
    presenter = BookingsPresenter(
        view,
        context.services.booking,
        role,
        on_changed=context.refresh_booking_related,
        customer_service=context.services.customer,
        activity_service=context.services.activity,
        instructor_service=context.services.instructor,
        executor=context.executor,
    )

    view.filters_requested.connect(presenter.load)
    view.booking_selected.connect(presenter.select_booking)
    view.page_requested.connect(presenter.page)
    view.queue_requested.connect(presenter.load_queue)
    if role in {"manager", "customer"}:
        view.create_requested.connect(presenter.begin_create)
    if role == "manager":
        view.edit_requested.connect(presenter.begin_edit)
        view.confirm_requested.connect(presenter.confirm)
        view.cancel_requested.connect(presenter.cancel)
        view.complete_requested.connect(presenter.complete)

        dashboard_presenter = context.presenters["dashboard"]
        dashboard_presenter.create_booking = presenter.begin_create
        dashboard_presenter.view.create_booking_requested.connect(dashboard_presenter.create_booking)

    context.add_page(page_key, view, presenter)

    if role == "manager":
        assignments_presenter = BookingAssignmentsPresenter(
            view,
            context.services.assignment,
            context.services.instructor,
            refresh_booking=presenter.select_booking,
            refresh_related=context.refresh_booking_related,
            confirm_after_assignment=presenter.confirm_after_assignment,
            executor=context.executor,
        )
        presenter.assign_after_creation = assignments_presenter.assign_after_creation
        view.booking_selected.connect(assignments_presenter.select_booking)
        view.assignment_add_requested.connect(assignments_presenter.begin_assign)
        view.assignment_add_and_confirm_requested.connect(assignments_presenter.begin_assign_and_confirm)
        view.assignment_replace_requested.connect(assignments_presenter.begin_replace)
        view.assignment_remove_requested.connect(assignments_presenter.remove)
        context.add_presenter("booking_assignments", assignments_presenter)
