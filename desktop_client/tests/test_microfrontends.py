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

    def test_business_code_is_physically_feature_first(self) -> None:
        app_dir = Path(__file__).parents[1] / "app"
        features_dir = app_dir / "features"
        expected = {
            "auth": {"registration.py", "view.py", "presenter.py", "service.py"},
            "dashboard": {"registration.py", "view.py", "presenter.py"},
            "activities": {"registration.py", "view.py", "dialogs.py", "presenter.py", "service.py"},
            "customers": {"registration.py", "view.py", "profile_view.py", "dialogs.py", "presenter.py", "service.py"},
            "instructors": {"registration.py", "view.py", "dialogs.py", "presenter.py", "service.py"},
            "users": {"registration.py", "view.py", "dialogs.py", "presenter.py", "service.py"},
            "bookings": {
                "registration.py",
                "view.py",
                "dialogs.py",
                "assignment_dialogs.py",
                "presenter.py",
                "assignments_presenter.py",
                "service.py",
                "assignment_service.py",
            },
            "knowledge": {"registration.py", "view.py", "presenter.py", "service.py"},
            "ai_assistant": {"registration.py", "view.py", "presenter.py", "service.py"},
        }
        for feature_name, required_files in expected.items():
            package = features_dir / feature_name
            self.assertTrue(package.is_dir(), feature_name)
            self.assertTrue((package / "__init__.py").is_file(), feature_name)
            self.assertTrue(required_files.issubset({path.name for path in package.iterdir()}), feature_name)

        # Business implementations no longer live in parallel layer-first trees.
        self.assertFalse((app_dir / "views").exists())
        self.assertFalse((app_dir / "presenters").exists())
        self.assertFalse((app_dir / "services").exists())
        self.assertTrue((app_dir / "shared" / "ui").is_dir())

    def test_main_window_composes_features_through_public_boundaries(self) -> None:
        main_path = Path(__file__).parents[1] / "app" / "main.py"
        tree = ast.parse(main_path.read_text(encoding="utf-8"))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)

        self.assertIn("desktop_client.app.features.registry", imports)
        self.assertIn("desktop_client.app.features.contracts", imports)
        self.assertIn("desktop_client.app.features.auth", imports)
        self.assertIn("desktop_client.app.features.service_factory", imports)

        forbidden_suffixes = (".view", ".presenter", ".service", ".dialogs", ".assignment_service")
        leaked_feature_internals = {
            module
            for module in imports
            if module.startswith("desktop_client.app.features.") and module.endswith(forbidden_suffixes)
        }
        self.assertFalse(leaked_feature_internals)

    def test_role_boundaries_are_declared_at_feature_registration_level(self) -> None:
        roles_by_feature = {feature.name: feature.roles for feature in FEATURES}
        self.assertEqual(roles_by_feature["users"], frozenset({"manager"}))
        self.assertEqual(roles_by_feature["knowledge"], frozenset({"manager"}))
        self.assertEqual(roles_by_feature["customers"], frozenset({"manager", "customer"}))
        self.assertEqual(roles_by_feature["instructors"], frozenset({"manager", "instructor"}))
        self.assertEqual(roles_by_feature["dashboard"], frozenset({"manager"}))
        for name in ("activities", "bookings", "ai_assistant"):
            self.assertEqual(roles_by_feature[name], frozenset({"manager", "instructor", "customer"}))

    def test_runtime_assets_are_packaged_and_not_design_reference_dependent(self) -> None:
        app_dir = Path(__file__).parents[1] / "app"
        required_assets = (
            app_dir / "assets" / "branding" / "logo.png",
            app_dir / "assets" / "branding" / "logo-sidebar.png",
            app_dir / "assets" / "branding" / "sidebar-leaf.png",
            app_dir / "assets" / "heroes" / "customers-hero.png",
            app_dir / "assets" / "heroes" / "dashboard-hero.png",
            app_dir / "assets" / "heroes" / "ai-agent-hero.png",
            app_dir / "assets" / "heroes" / "activities-manager-hero.png",
            app_dir / "assets" / "heroes" / "bookings-manager-hero.png",
            app_dir / "assets" / "heroes" / "instructors-hero.png",
            app_dir / "assets" / "heroes" / "managers-hero.png",
        )
        for asset in required_assets:
            self.assertTrue(asset.is_file(), str(asset))

        runtime_sources = [
            path
            for path in app_dir.rglob("*.py")
            if "__pycache__" not in path.parts
        ]
        design_reference_users = [
            str(path.relative_to(app_dir))
            for path in runtime_sources
            if "design_reference" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(design_reference_users, [])


if __name__ == "__main__":
    unittest.main()
