import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app.db import connection


class LoadLocalEnvTests(unittest.TestCase):
    def test_loads_root_env_when_backend_env_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_dir = Path(tmpdir)
            backend_dir = tmp_dir / "backend"
            backend_dir.mkdir()
            (tmp_dir / ".env").write_text("DATABASE_URL=root-value\n", encoding="utf-8")

            with patch.object(connection, "ROOT_DIR", tmp_dir), patch.object(connection, "BACKEND_DIR", backend_dir), patch.dict(os.environ, {}, clear=True):
                connection.load_local_env()
                self.assertEqual(os.environ.get("DATABASE_URL"), "root-value")

    def test_prefers_backend_env_when_both_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_dir = Path(tmpdir)
            backend_dir = tmp_dir / "backend"
            backend_dir.mkdir()
            (backend_dir / ".env").write_text("DATABASE_URL=backend-value\n", encoding="utf-8")
            (tmp_dir / ".env").write_text("DATABASE_URL=root-value\n", encoding="utf-8")

            with patch.object(connection, "ROOT_DIR", tmp_dir), patch.object(connection, "BACKEND_DIR", backend_dir), patch.dict(os.environ, {}, clear=True):
                connection.load_local_env()
                self.assertEqual(os.environ.get("DATABASE_URL"), "backend-value")
