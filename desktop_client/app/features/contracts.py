from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from desktop_client.app.models.session import Session


@dataclass(frozen=True)
class FeatureServices:
    """Application services exposed to desktop feature registrations.

    Keeping the service bundle explicit makes feature dependencies visible while
    preserving the existing service implementations and API contracts.
    """

    booking: Any
    assignment: Any
    activity: Any
    ai_chat: Any
    customer: Any
    instructor: Any
    knowledge: Any
    user: Any


@dataclass
class FeatureContext:
    """Stable composition boundary shared by desktop microfrontends."""

    shell: Any
    session: Session
    executor: Any
    services: FeatureServices
    presenters: dict[str, object]
    navigate_with_filters: Callable[[str, dict | None], None]
    refresh_booking_related: Callable[[], None]

    def add_page(self, key: str, view: Any, presenter: object) -> None:
        """Register one feature-owned page without exposing its internals to the shell."""

        self.shell.add_page(key, view)
        self.presenters[key] = presenter

    def add_presenter(self, key: str, presenter: object) -> None:
        """Register a non-page presenter owned by a mounted feature."""

        self.presenters[key] = presenter
