from __future__ import annotations

from desktop_client.app.features.contracts import FeatureContext
from desktop_client.app.presenters.customers_presenter import CustomerProfilePresenter, CustomersPresenter
from desktop_client.app.views.customer_profile_view import CustomerProfileView
from desktop_client.app.views.customers_view import CustomersView


def register(context: FeatureContext) -> None:
    session = context.session
    if session.role == "manager":
        view = CustomersView()
        presenter = CustomersPresenter(
            view,
            context.services.customer,
            context.services.user,
            executor=context.executor,
        )
        view.filters_requested.connect(presenter.apply_filters)
        view.page_requested.connect(presenter.page)
        view.customer_selected.connect(presenter.select)
        view.retry_requested.connect(presenter.retry)
        view.create_requested.connect(presenter.begin_create)
        view.edit_requested.connect(presenter.begin_edit)
        view.deactivate_requested.connect(presenter.deactivate)
        view.reactivate_requested.connect(presenter.activate)
        view.change_password_requested.connect(presenter.begin_change_password)
        context.add_page("customers", view, presenter)
        return

    if session.role == "customer" and session.customer_id:
        view = CustomerProfileView()
        presenter = CustomerProfilePresenter(
            view,
            context.services.customer,
            session.customer_id,
            context.executor,
        )
        view.retry_requested.connect(presenter.retry)
        context.add_page("my_profile", view, presenter)
