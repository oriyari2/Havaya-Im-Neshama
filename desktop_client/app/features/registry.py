from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from desktop_client.app.features import activities, ai_assistant, bookings, customers, dashboard, instructors, knowledge, users
from desktop_client.app.features.contracts import FeatureContext


ALL_ROLES = frozenset({"manager", "instructor", "customer"})


@dataclass(frozen=True)
class FeatureDescriptor:
    """Public descriptor used by the shell composition root."""

    name: str
    roles: frozenset[str]
    page_keys: tuple[str, ...]
    register: Callable[[FeatureContext], None]


FEATURES: tuple[FeatureDescriptor, ...] = (
    FeatureDescriptor("dashboard", frozenset({"manager"}), ("dashboard",), dashboard.register),
    FeatureDescriptor("activities", ALL_ROLES, ("activities",), activities.register),
    FeatureDescriptor("instructors", frozenset({"manager", "instructor"}), ("instructors", "my_profile"), instructors.register),
    FeatureDescriptor("users", frozenset({"manager"}), ("users",), users.register),
    FeatureDescriptor("customers", frozenset({"manager", "customer"}), ("customers", "my_profile"), customers.register),
    FeatureDescriptor("knowledge", frozenset({"manager"}), ("knowledge",), knowledge.register),
    FeatureDescriptor("bookings", ALL_ROLES, ("bookings", "my_bookings"), bookings.register),
    FeatureDescriptor("ai_assistant", ALL_ROLES, ("ai_chat",), ai_assistant.register),
)


def mount_role_features(context: FeatureContext) -> None:
    """Mount only feature registrations allowed for the authenticated role."""

    for feature in FEATURES:
        if context.session.role in feature.roles:
            feature.register(context)
