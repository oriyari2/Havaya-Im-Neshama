from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from uuid import UUID

import httpx
from fastapi.testclient import TestClient

from backend.app.application.services.ai_service import AIConsultationService
from backend.app.application.services import ai_runtime
from backend.app.core.auth import get_current_user
from backend.app.core import environment
from backend.app.db import connection
from backend.app.main import app
from backend.app.routers.ai import get_llm_client
from rag import OllamaLLMClient


class AIRuntimeOptimizationTests(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        connection._pool = None

    def test_pool_opens_with_bounded_min_max_and_closes(self) -> None:
        pool = MagicMock()
        pool.closed = True
        pool.open.side_effect = lambda: setattr(pool, "closed", False)
        with (
            patch.object(connection, "get_database_url", return_value="postgresql://db"),
            patch.object(connection, "get_db_pool_min_size", return_value=1),
            patch.object(connection, "get_db_pool_max_size", return_value=5),
            patch.object(connection, "ConnectionPool", return_value=pool) as pool_cls,
        ):
            self.assertIs(connection.open_connection_pool(), pool)
            self.assertIs(connection.open_connection_pool(), pool)
            pool_cls.assert_called_once_with(conninfo="postgresql://db", min_size=1, max_size=5, open=False)
            pool.open.assert_called_once_with()
            connection.close_connection_pool()
            pool.close.assert_called_once_with()

    def test_connection_returns_safely_after_success_and_failure(self) -> None:
        conn = MagicMock()
        conn.closed = False
        pool = MagicMock()
        pool.connection.return_value.__enter__.return_value = conn
        connection._pool = pool

        with connection.get_connection() as borrowed:
            self.assertIs(borrowed, conn)
        conn.rollback.assert_not_called()

        with self.assertRaises(RuntimeError):
            with connection.get_connection():
                raise RuntimeError("boom")
        conn.rollback.assert_not_called()
        self.assertEqual(pool.connection.return_value.__exit__.call_count, 2)

    def test_pool_environment_bounds_clamp_both_values_to_five(self) -> None:
        with patch.dict("os.environ", {"DB_POOL_MIN_SIZE": "10", "DB_POOL_MAX_SIZE": "99"}, clear=False):
            self.assertEqual(environment.get_db_pool_min_size(), 5)
            self.assertEqual(environment.get_db_pool_max_size(), 5)

        with patch.dict("os.environ", {"DB_POOL_MIN_SIZE": "4", "DB_POOL_MAX_SIZE": "2"}, clear=False):
            self.assertEqual(environment.get_db_pool_min_size(), 4)
            self.assertEqual(environment.get_db_pool_max_size(), 4)

    def test_warm_up_failure_does_not_stop_startup(self) -> None:
        with patch("backend.app.application.services.ai_runtime.httpx.post", side_effect=httpx.ConnectError("offline")):
            ai_runtime.warm_generation_model()

    def test_warm_up_uses_load_only_payload_and_startup_timeout(self) -> None:
        request = httpx.Request("POST", "http://ollama/api/generate")
        response = httpx.Response(200, json={"response": ""}, request=request)

        with (
            patch("backend.app.application.services.ai_runtime.get_ollama_url", return_value="http://ollama"),
            patch("backend.app.application.services.ai_runtime.httpx.post", return_value=response) as post,
        ):
            ai_runtime.warm_generation_model()

        post.assert_called_once()
        self.assertEqual(
            post.call_args.kwargs["json"],
            {
                "model": "llama3.1",
                "prompt": "",
                "stream": False,
                "keep_alive": "30m",
            },
        )
        timeout = post.call_args.kwargs["timeout"]
        self.assertEqual(timeout.connect, 2.0)
        self.assertEqual(timeout.read, 30.0)

    def test_ollama_generation_payload_contains_bounds(self) -> None:
        captured = {}

        def respond(_url, *, json, timeout):
            captured["json"] = json
            captured["timeout"] = timeout
            request = httpx.Request("POST", "http://ollama/api/generate")
            return httpx.Response(200, json={"response": "ok", "eval_count": 3}, request=request)

        client = OllamaLLMClient(model="llama3.1", base_url="http://ollama", timeout_seconds=12, keep_alive="30m")
        with patch("rag.llm_client.httpx.post", side_effect=respond):
            self.assertEqual(client.generate("hello"), "ok")
        self.assertEqual(captured["json"]["keep_alive"], "30m")
        self.assertEqual(captured["json"]["options"]["temperature"], 0.1)
        self.assertEqual(captured["json"]["options"]["num_predict"], 400)
        self.assertEqual(captured["timeout"], 12)

    def test_duplicate_chunks_produce_one_logical_source(self) -> None:
        results = [
            _result("11111111-1111-1111-1111-111111111111", "03-code-race-equipment.md", "demo://code", "source-1"),
            _result("22222222-2222-2222-2222-222222222222", "03-code-race-equipment.md", "demo://code", "source-1"),
        ]
        sources = AIConsultationService._dedupe_sources(results)
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].source_title, "03-code-race-equipment.md")

    def test_readiness_endpoint_is_manager_only(self) -> None:
        app.dependency_overrides[get_llm_client] = lambda: None
        with patch("backend.app.routers.ai.ai_readiness", return_value={"api": "ok"}):
            response = TestClient(app).get("/api/ai/readiness")
        self.assertEqual(response.status_code, 401)

        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "customer"}
        with patch("backend.app.routers.ai.ai_readiness", return_value={"api": "ok"}):
            response = TestClient(app).get("/api/ai/readiness")
        self.assertEqual(response.status_code, 403)

        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "manager"}
        with patch("backend.app.routers.ai.ai_readiness", return_value={"api": "ok"}):
            response = TestClient(app).get("/api/ai/readiness")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"api": "ok"})


def _result(chunk_id: str, title: str, uri: str, source_id: str):
    return type(
        "SearchResult",
        (),
        {
            "chunk_id": UUID(chunk_id),
            "source_title": title,
            "source_uri": uri,
            "metadata": {"source_id": source_id},
        },
    )()


if __name__ == "__main__":
    unittest.main()
