import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app.core import environment
from backend.app.db import connection


class LoadBackendEnvTests(unittest.TestCase):
    def test_ignores_root_env_when_backend_env_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_dir = Path(tmpdir)
            backend_dir = tmp_dir / "backend"
            backend_dir.mkdir()
            (tmp_dir / ".env").write_text("DATABASE_URL=root-value\n", encoding="utf-8")

            with (
                patch.object(environment, "BACKEND_DIR", backend_dir),
                patch.object(environment, "BACKEND_ENV_PATH", backend_dir / ".env"),
                patch.dict(os.environ, {}, clear=True),
            ):
                environment.load_backend_env()
                self.assertIsNone(os.environ.get("DATABASE_URL"))

    def test_loads_backend_env_when_root_env_also_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_dir = Path(tmpdir)
            backend_dir = tmp_dir / "backend"
            backend_dir.mkdir()
            (backend_dir / ".env").write_text("DATABASE_URL=backend-value\n", encoding="utf-8")
            (tmp_dir / ".env").write_text("DATABASE_URL=root-value\n", encoding="utf-8")

            with (
                patch.object(environment, "BACKEND_DIR", backend_dir),
                patch.object(environment, "BACKEND_ENV_PATH", backend_dir / ".env"),
                patch.dict(os.environ, {}, clear=True),
            ):
                environment.load_backend_env()
                self.assertEqual(os.environ.get("DATABASE_URL"), "backend-value")

    def test_database_url_uses_shared_backend_env_loader(self) -> None:
        with (
            patch.object(connection, "load_backend_env") as load_backend_env,
            patch.dict(
                os.environ,
                {"DATABASE_URL": "postgresql+psycopg://user:pass@host/db"},
                clear=True,
            ),
        ):
            self.assertEqual(connection.get_database_url(), "postgresql://user:pass@host/db")
            load_backend_env.assert_called_once_with()
