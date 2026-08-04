from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from desktop_client.app.features.auth.presenter import LoginPresenter
from desktop_client.app.features.auth.view import LoginView


@dataclass(frozen=True)
class LoginFeature:
    view: LoginView
    presenter: LoginPresenter


def build_login_feature(auth_service: Any, on_authenticated: Callable, executor: Any) -> LoginFeature:
    """Build the authentication microfrontend behind one small public factory."""

    view = LoginView()
    presenter = LoginPresenter(view, auth_service, on_authenticated, executor)
    view.login_requested.connect(presenter.login)
    return LoginFeature(view=view, presenter=presenter)
