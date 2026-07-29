from __future__ import annotations

from uuid import uuid4
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from backend.app.application.services.knowledge_retrieval_service import (
    KnowledgeRetrievalError,
    KnowledgeRetrievalService,
)
from backend.app.core.auth import get_current_user
from backend.app.infrastructure.repositories.knowledge_retrieval_repository import search_knowledge_chunks
from backend.app.main import app
from backend.app.routers.knowledge import get_knowledge_retrieval_service
from rag import EmbeddingClient, EmbeddingClientError


class _FakeEmbeddingClient(EmbeddingClient):
    model = "fake-embed"

    def __init__(self, embedding: list[float] | None = None, failure: Exception | None = None) -> None:
        self.embedding = [0.1, 0.2, 0.3] if embedding is None else embedding
        self.failure = failure
        self.texts: list[str] = []

    def embed(self, text: str) -> list[float]:
        self.texts.append(text)
        if self.failure:
            raise self.failure
        return self.embedding


class _FakeConnection:
    def __init__(self, rows: list[dict]) -> None:
        self.cursor_obj = _RepositoryCursor(rows)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def cursor(self, *args, **kwargs):
        return self.cursor_obj


class _RepositoryCursor:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows
        self.executed_sql = ""
        self.executed_params = None
        self.filtered_rows: list[dict] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, sql, params) -> None:
        self.executed_sql = sql
        self.executed_params = params
        role = params[3]
        model = params[1]
        dimensions = params[2]
        max_distance = params[6]
        limit = params[8]
        visible = []
        for row in self.rows:
            allowed_roles = row.get("metadata", {}).get("allowed_roles")
            is_authorized = role == "manager" or (isinstance(allowed_roles, list) and role in allowed_roles)
            if (
                is_authorized
                and row["embedding_model"] == model
                and row["embedding_dimensions"] == dimensions
                and row["distance"] <= max_distance
            ):
                visible.append(
                    {
                        "chunk_id": row["chunk_id"],
                        "source_title": row["source_title"],
                        "source_uri": row.get("source_uri"),
                        "chunk_index": row["chunk_index"],
                        "content": row["content"],
                        "metadata": row.get("metadata") or {},
                        "distance": row["distance"],
                    }
                )
        self.filtered_rows = sorted(visible, key=lambda row: row["distance"])[:limit]

    def fetchall(self):
        return self.filtered_rows


def _row(
    *,
    title: str,
    distance: float,
    metadata: dict | None,
    model: str = "fake-embed",
    dimensions: int = 3,
) -> dict:
    return {
        "chunk_id": uuid4(),
        "source_title": title,
        "source_uri": f"demo://{title}",
        "chunk_index": 0,
        "content": f"{title} content",
        "metadata": metadata or {},
        "embedding_model": model,
        "embedding_dimensions": dimensions,
        "distance": distance,
    }


class KnowledgeRetrievalServiceTests(unittest.TestCase):
    def test_search_passes_normalized_query_embedding_model_dimensions_role_and_limit(self) -> None:
        rows = [_row(title="Guide", distance=0.2, metadata={"allowed_roles": ["instructor"]})]
        conn = _FakeConnection(rows)
        client = _FakeEmbeddingClient()
        service = KnowledgeRetrievalService(client, max_cosine_distance=0.45)

        with patch("backend.app.application.services.knowledge_retrieval_service.get_connection", return_value=conn):
            result = service.search(query="  hello guide  ", authenticated_role="instructor", limit=4)

        self.assertEqual(client.texts, ["hello guide"])
        self.assertEqual(conn.cursor_obj.executed_params[0], "[0.1,0.2,0.3]")
        self.assertEqual(conn.cursor_obj.executed_params[1], "fake-embed")
        self.assertEqual(conn.cursor_obj.executed_params[2], 3)
        self.assertEqual(conn.cursor_obj.executed_params[3], "instructor")
        self.assertEqual(conn.cursor_obj.executed_params[8], 4)
        self.assertEqual(result.query, "hello guide")

    def test_search_preserves_distance_order_and_calculates_score(self) -> None:
        rows = [
            _row(title="Far", distance=0.4, metadata={"allowed_roles": ["customer"]}),
            _row(title="Near", distance=0.1, metadata={"allowed_roles": ["customer"]}),
        ]
        service = KnowledgeRetrievalService(_FakeEmbeddingClient(), max_cosine_distance=0.45)

        with patch(
            "backend.app.application.services.knowledge_retrieval_service.get_connection",
            return_value=_FakeConnection(rows),
        ):
            result = service.search(query="question", authenticated_role="customer", limit=5)

        self.assertEqual([item.source_title for item in result.results], ["Near", "Far"])
        self.assertAlmostEqual(result.results[0].score, 0.9)

    def test_search_filters_weak_matches_and_empty_results(self) -> None:
        service = KnowledgeRetrievalService(_FakeEmbeddingClient(), max_cosine_distance=0.2)

        with patch(
            "backend.app.application.services.knowledge_retrieval_service.get_connection",
            return_value=_FakeConnection([_row(title="Weak", distance=0.3, metadata={"allowed_roles": ["manager"]})]),
        ):
            result = service.search(query="question", authenticated_role="manager", limit=5)

        self.assertEqual(result.results, [])

    def test_empty_embedding_is_rejected(self) -> None:
        service = KnowledgeRetrievalService(_FakeEmbeddingClient(embedding=[]), max_cosine_distance=0.45)

        with self.assertRaises(KnowledgeRetrievalError):
            service.search(query="question", authenticated_role="manager", limit=5)

    def test_embedding_failure_is_wrapped(self) -> None:
        service = KnowledgeRetrievalService(
            _FakeEmbeddingClient(failure=EmbeddingClientError("offline")),
            max_cosine_distance=0.45,
        )

        with self.assertRaises(KnowledgeRetrievalError):
            service.search(query="question", authenticated_role="manager", limit=5)

    def test_embedding_model_fallback_is_lazy_when_client_provides_model(self) -> None:
        service = KnowledgeRetrievalService(_FakeEmbeddingClient(), max_cosine_distance=0.45)

        with patch(
            "backend.app.application.services.knowledge_retrieval_service.get_ollama_embedding_model",
            side_effect=AssertionError("fallback should not be evaluated"),
        ), patch(
            "backend.app.application.services.knowledge_retrieval_service.get_connection",
            return_value=_FakeConnection([]),
        ):
            result = service.search(query="question", authenticated_role="manager", limit=5)

        self.assertEqual(result.results, [])


class KnowledgeRetrievalRepositoryTests(unittest.TestCase):
    def test_sql_uses_pgvector_cosine_distance_and_parameters(self) -> None:
        cur = _RepositoryCursor([])

        search_knowledge_chunks(
            cur,
            query_embedding=[1, 0, 0],
            authenticated_role="manager",
            embedding_model="fake-embed",
            embedding_dimensions=3,
            limit=5,
            max_cosine_distance=0.45,
        )

        self.assertIn("<=>", cur.executed_sql)
        self.assertIn("jsonb_typeof(metadata -> 'allowed_roles') = 'array'", cur.executed_sql)
        self.assertIn("LIMIT %s", cur.executed_sql)
        self.assertEqual(cur.executed_params[0], "[1.0,0.0,0.0]")
        self.assertEqual(cur.executed_params[6], 0.45)

    def test_repository_filters_orders_and_bounds_results(self) -> None:
        rows = [
            _row(title="WrongModel", distance=0.01, metadata={"allowed_roles": ["manager"]}, model="other"),
            _row(title="WrongDim", distance=0.02, metadata={"allowed_roles": ["manager"]}, dimensions=2),
            _row(title="Weak", distance=0.8, metadata={"allowed_roles": ["manager"]}),
            _row(title="Second", distance=0.2, metadata={"allowed_roles": ["manager"]}),
            _row(title="First", distance=0.1, metadata={"allowed_roles": ["manager"]}),
        ]
        cur = _RepositoryCursor(rows)

        result = search_knowledge_chunks(
            cur,
            query_embedding=[1, 0, 0],
            authenticated_role="manager",
            embedding_model="fake-embed",
            embedding_dimensions=3,
            limit=1,
            max_cosine_distance=0.45,
        )

        self.assertEqual([row["source_title"] for row in result], ["First"])

    def test_role_policy_is_fail_closed(self) -> None:
        rows = [
            _row(title="ManagerOnly", distance=0.1, metadata={}),
            _row(title="NullRoles", distance=0.1, metadata={"allowed_roles": None}),
            _row(title="MalformedRoles", distance=0.1, metadata={"allowed_roles": "customer"}),
            _row(title="Instructor", distance=0.1, metadata={"allowed_roles": ["instructor"]}),
            _row(title="Customer", distance=0.1, metadata={"allowed_roles": ["customer"]}),
            _row(title="Both", distance=0.1, metadata={"allowed_roles": ["customer", "instructor"]}),
        ]

        manager_rows = self._search_titles(rows, "manager")
        instructor_rows = self._search_titles(rows, "instructor")
        customer_rows = self._search_titles(rows, "customer")

        self.assertEqual(
            manager_rows,
            ["ManagerOnly", "NullRoles", "MalformedRoles", "Instructor", "Customer", "Both"],
        )
        self.assertEqual(instructor_rows, ["Instructor", "Both"])
        self.assertEqual(customer_rows, ["Customer", "Both"])

    def _search_titles(self, rows: list[dict], role: str) -> list[str]:
        cur = _RepositoryCursor(rows)
        result = search_knowledge_chunks(
            cur,
            query_embedding=[1, 0, 0],
            authenticated_role=role,
            embedding_model="fake-embed",
            embedding_dimensions=3,
            limit=10,
            max_cosine_distance=0.45,
        )
        return [row["source_title"] for row in result]


class KnowledgeRetrievalApiTests(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_unauthenticated_access_is_rejected(self) -> None:
        response = TestClient(app).post("/api/rag/search", json={"query": "hello"})

        self.assertEqual(response.status_code, 401)

    def test_manager_instructor_and_customer_can_search(self) -> None:
        for role in ("manager", "instructor", "customer"):
            with self.subTest(role=role):
                service = Mock()
                service.search.return_value = Mock(query="hello", results=[])
                app.dependency_overrides[get_current_user] = lambda role=role: {"id": str(uuid4()), "role": role}
                app.dependency_overrides[get_knowledge_retrieval_service] = lambda: service

                response = TestClient(app).post("/api/rag/search", json={"query": " hello "})

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"query": "hello", "results": []})
                service.search.assert_called_once_with(query="hello", authenticated_role=role, limit=5)
                app.dependency_overrides.clear()

    def test_unexpected_request_fields_are_rejected(self) -> None:
        service = Mock()
        service.search.return_value = Mock(query="hello", results=[])
        app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid4()), "role": "customer"}
        app.dependency_overrides[get_knowledge_retrieval_service] = lambda: service

        response = TestClient(app).post("/api/rag/search", json={"query": "hello", "role": "manager"})

        self.assertEqual(response.status_code, 422)
        service.search.assert_not_called()

    def test_invalid_search_requests_are_rejected(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid4()), "role": "manager"}
        client = TestClient(app)

        self.assertEqual(client.post("/api/rag/search", json={"query": "   "}).status_code, 422)
        self.assertEqual(client.post("/api/rag/search", json={"query": "hello", "limit": 0}).status_code, 422)
        self.assertEqual(client.post("/api/rag/search", json={"query": "hello", "limit": 11}).status_code, 422)

    def test_successful_response_schema_does_not_expose_embeddings(self) -> None:
        chunk_id = uuid4()
        service = Mock()
        service.search.return_value = Mock(
            query="hello",
            results=[
                Mock(
                    chunk_id=chunk_id,
                    source_title="Guide",
                    source_uri="demo://guide",
                    chunk_index=0,
                    content="content",
                    metadata={"allowed_roles": ["manager"]},
                    distance=0.18,
                    score=0.82,
                )
            ],
        )
        app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid4()), "role": "manager"}
        app.dependency_overrides[get_knowledge_retrieval_service] = lambda: service

        response = TestClient(app).post("/api/rag/search", json={"query": "hello", "limit": 1})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["results"][0]["chunk_id"], str(chunk_id))
        self.assertEqual(body["results"][0]["score"], 0.82)
        self.assertNotIn("embedding", body["results"][0])


if __name__ == "__main__":
    unittest.main()
