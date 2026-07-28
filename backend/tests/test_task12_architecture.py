from __future__ import annotations

from pathlib import Path
import re
import unittest
from unittest.mock import patch

from backend.app.application.services import customer_service


ROOT = Path(__file__).resolve().parents[2]


class Task12ArchitectureTests(unittest.TestCase):
    def test_customer_directory_is_manager_only_while_owned_profile_remains_separate(self) -> None:
        kwargs = dict(search=None, city=None, customer_type=None, is_active=None, order_by="name", limit=25, offset=0)
        for role in ("customer", "instructor"):
            with self.assertRaises(customer_service.CustomerAccessDeniedError):
                customer_service.list_customers(**kwargs, current_user={"role": role})

        with patch.object(customer_service.repo, "list_customers", return_value=[]) as repository:
            class Cursor:
                def __enter__(self): return self
                def __exit__(self, *_args): return False
            class Connection:
                def __enter__(self): return self
                def __exit__(self, *_args): return False
                def cursor(self, **_kwargs): return Cursor()
            with patch.object(customer_service, "get_connection", return_value=Connection()):
                customer_service.list_customers(**kwargs, current_user={"role": "manager"})
        repository.assert_called_once()

    def test_routers_do_not_contain_sql_statements(self) -> None:
        sql_pattern = re.compile(
            r"\b(?:SELECT\s+(?:\*|\d|[a-z_])|INSERT\s+INTO|UPDATE\s+[a-z_]\w*\s+SET|DELETE\s+FROM)\b",
            re.IGNORECASE,
        )
        violations: list[str] = []
        for path in (ROOT / "backend" / "app" / "routers").glob("*.py"):
            source = path.read_text(encoding="utf-8")
            if sql_pattern.search(source):
                violations.append(path.name)
        self.assertEqual(violations, [])

    def test_presenters_do_not_import_pyside_and_views_do_not_import_data_layers(self) -> None:
        presenter_violations = [
            path.name
            for path in (ROOT / "desktop_client" / "app" / "presenters").glob("*.py")
            if "PySide6" in path.read_text(encoding="utf-8")
        ]
        view_violations = []
        forbidden = ("desktop_client.app.services", "desktop_client.app.api", "psycopg", "get_connection")
        for path in (ROOT / "desktop_client" / "app" / "views").glob("*.py"):
            source = path.read_text(encoding="utf-8")
            if any(token in source for token in forbidden):
                view_violations.append(path.name)
        self.assertEqual(presenter_violations, [])
        self.assertEqual(view_violations, [])


if __name__ == "__main__":
    unittest.main()
