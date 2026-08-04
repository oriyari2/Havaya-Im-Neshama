from __future__ import annotations

import ast
import unittest
from pathlib import Path

from desktop_client.app.features.registry import FEATURES


class MicrofrontendArchitectureTests(unittest.TestCase):
    def test_feature_registry_exposes_explicit_bounded_modules(self) -> None:
        self.assertEqual(
            [feature.name for feature in FEATURES],
            [
                "dashboard",
                "activities",
                "instructors",
                "users",
                "customers",
                "knowledge",
                "bookings",
                "ai_assistant",
            ],
        )
        for feature in FEATURES:
            self.assertTrue(feature.roles)
            self.assertTrue(feature.page_keys)
            self.assertTrue(callable(feature.register))

    def test_main_window_composes_features_through_registration_boundary(self) -> None:
        main_path = Path(__file__).parents[1] / "app" / "main.py"
        tree = ast.parse(main_path.read_text(encoding="utf-8"))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)

        self.assertIn("desktop_client.app.features.registry", imports)
        self.assertIn("desktop_client.app.features.contracts", imports)
        self.assertIn("desktop_client.app.features.auth", imports)

        forbidden_feature_internals = {
            "desktop_client.app.views.activities_view",
            "desktop_client.app.views.ai_chat_view",
            "desktop_client.app.views.bookings_view",
            "desktop_client.app.views.customer_profile_view",
            "desktop_client.app.views.customers_view",
            "desktop_client.app.views.dashboard_view",
            "desktop_client.app.views.instructors_view",
            "desktop_client.app.views.knowledge_view",
            "desktop_client.app.views.login_view",
            "desktop_client.app.views.users_view",
            "desktop_client.app.presenters.activities_presenter",
            "desktop_client.app.presenters.ai_chat_presenter",
            "desktop_client.app.presenters.booking_assignments_presenter",
            "desktop_client.app.presenters.bookings_presenter",
            "desktop_client.app.presenters.customers_presenter",
            "desktop_client.app.presenters.dashboard_presenter",
            "desktop_client.app.presenters.instructors_presenter",
            "desktop_client.app.presenters.knowledge_presenter",
            "desktop_client.app.presenters.login_presenter",
            "desktop_client.app.presenters.users_presenter",
        }
        self.assertFalse(imports & forbidden_feature_internals)

    def test_role_boundaries_are_declared_at_feature_registration_level(self) -> None:
        roles_by_feature = {feature.name: feature.roles for feature in FEATURES}
        self.assertEqual(roles_by_feature["users"], frozenset({"manager"}))
        self.assertEqual(roles_by_feature["knowledge"], frozenset({"manager"}))
        self.assertEqual(roles_by_feature["customers"], frozenset({"manager", "customer"}))
        self.assertEqual(roles_by_feature["instructors"], frozenset({"manager", "instructor"}))
        for name in ("dashboard", "activities", "bookings", "ai_assistant"):
            self.assertEqual(roles_by_feature[name], frozenset({"manager", "instructor", "customer"}))


if __name__ == "__main__":
    unittest.main()
