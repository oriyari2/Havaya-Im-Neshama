from __future__ import annotations

from uuid import UUID, uuid4
import unittest
from unittest.mock import Mock, patch

import httpx
from fastapi.testclient import TestClient

from backend.app.application.services.knowledge_ingestion_service import KnowledgeIngestionService, split_text
from backend.app.core.auth import get_current_user
from backend.app.infrastructure.repositories.knowledge_repository import insert_knowledge_chunk
from backend.app.main import app
from backend.app.routers.knowledge import get_knowledge_ingestion_service
from backend.app.schemas.knowledge import KnowledgeIngestRequest
from rag.embedding_client import EmbeddingClient, EmbeddingClientError, OllamaEmbeddingClient


class _FakeEmbeddingClient(EmbeddingClient):
    model = "fake-embed"

    def __init__(self) -> None:
        self.texts: list[str] = []

    def embed(self, text: str) -> list[float]:
        self.texts.append(text)
        return [1.0, 0.5, 0.25]


class _FakeConnection:
    def __init__(self) -> None:
        self.cursor_obj = _FakeCursor()
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def cursor(self, *args, **kwargs):
        return self.cursor_obj

    def commit(self) -> None:
        self.committed = True


class _FakeCursor:
    def __init__(self) -> None:
        self.rows = [
            {
                "id": uuid4(),
                "source_title": "Guide",
                "source_uri": None,
                "chunk_index": 0,
                "content": "content",
                "metadata": {},
                "embedding_model": "fake-embed",
                "embedding_dimensions": 3,
                "content_hash": "hash",
                "created_by": uuid4(),
                "created_at": None,
            }
        ]
        self.executed_sql = ""
        self.executed_params = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, sql, params):
        self.executed_sql = sql
        self.executed_params = params

    def fetchone(self):
        return self.rows[0]


class OllamaEmbeddingClientTests(unittest.TestCase):
    def test_embed_posts_to_ollama_embed_endpoint(self) -> None:
        client = OllamaEmbeddingClient(model="embed-model", base_url="http://localhost:11434")
        request = httpx.Request("POST", "http://localhost:11434/api/embed")
        response = httpx.Response(200, json={"embeddings": [[0.1, 0.2]]}, request=request)

        with patch("rag.embedding_client.httpx.post", return_value=response) as post:
            embedding = client.embed(" internal guide ")

        self.assertEqual(embedding, [0.1, 0.2])
        post.assert_called_once_with(
            "http://localhost:11434/api/embed",
            json={"model": "embed-model", "input": "internal guide"},
            timeout=120.0,
        )

    def test_embed_wraps_transport_errors(self) -> None:
        client = OllamaEmbeddingClient(model="embed-model", base_url="http://localhost:11434")

        with patch("rag.embedding_client.httpx.post", side_effect=httpx.ConnectError("offline")):
            with self.assertRaises(EmbeddingClientError):
                client.embed("hello")

    def test_embed_rejects_missing_embeddings(self) -> None:
        client = OllamaEmbeddingClient(model="embed-model", base_url="http://localhost:11434")
        request = httpx.Request("POST", "http://localhost:11434/api/embed")
        response = httpx.Response(200, json={}, request=request)

        with patch("rag.embedding_client.httpx.post", return_value=response):
            with self.assertRaises(EmbeddingClientError):
                client.embed("internal guide")

    def test_embed_rejects_empty_embeddings(self) -> None:
        client = OllamaEmbeddingClient(model="embed-model", base_url="http://localhost:11434")
        request = httpx.Request("POST", "http://localhost:11434/api/embed")
        response = httpx.Response(200, json={"embeddings": []}, request=request)

        with patch("rag.embedding_client.httpx.post", return_value=response):
            with self.assertRaises(EmbeddingClientError):
                client.embed("internal guide")

    def test_embed_rejects_empty_first_vector(self) -> None:
        client = OllamaEmbeddingClient(model="embed-model", base_url="http://localhost:11434")
        request = httpx.Request("POST", "http://localhost:11434/api/embed")
        response = httpx.Response(200, json={"embeddings": [[]]}, request=request)

        with patch("rag.embedding_client.httpx.post", return_value=response):
            with self.assertRaises(EmbeddingClientError):
                client.embed("internal guide")

    def test_embed_rejects_non_numeric_first_vector(self) -> None:
        client = OllamaEmbeddingClient(model="embed-model", base_url="http://localhost:11434")
        request = httpx.Request("POST", "http://localhost:11434/api/embed")
        response = httpx.Response(200, json={"embeddings": [["bad"]]}, request=request)

        with patch("rag.embedding_client.httpx.post", return_value=response):
            with self.assertRaises(EmbeddingClientError):
                client.embed("internal guide")


class KnowledgeIngestionTests(unittest.TestCase):
    def test_split_text_is_deterministic_and_overlapping(self) -> None:
        chunks = split_text("abcdefghij", chunk_size=6, overlap=2)

        self.assertEqual(chunks, ["abcdef", "efghij"])

    def test_ingestion_embeds_and_stores_chunks(self) -> None:
        fake_conn = _FakeConnection()
        fake_client = _FakeEmbeddingClient()
        service = KnowledgeIngestionService(fake_client, chunk_size=20, overlap=5)
        payload = KnowledgeIngestRequest(source_title="Guide", content="one two three four five six")
        user_id = uuid4()

        with patch(
            "backend.app.application.services.knowledge_ingestion_service.get_connection",
            return_value=fake_conn,
        ):
            result = service.ingest(payload, created_by=user_id)

        self.assertEqual(result.source_title, "Guide")
        self.assertEqual(result.chunk_count, 2)
        self.assertEqual(fake_client.texts, ["one two three four", "four five six"])
        self.assertTrue(fake_conn.committed)

    def test_repository_inserts_pgvector_embedding_parameterized(self) -> None:
        cur = _FakeCursor()
        created_by = uuid4()

        row = insert_knowledge_chunk(
            cur,
            source_title="Guide",
            source_uri=None,
            chunk_index=0,
            content="Bring mats",
            metadata={"role": "manager"},
            embedding_model="fake-embed",
            embedding=[1, 2.5],
            content_hash="abc",
            created_by=created_by,
        )

        self.assertEqual(row["id"], cur.rows[0]["id"])
        self.assertIn("%s::vector", cur.executed_sql)
        self.assertEqual(cur.executed_params[7], "[1.0,2.5]")
        self.assertEqual(cur.executed_params[9], created_by)


class KnowledgeIngestionApiTests(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_ingest_requires_manager_role(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid4()), "role": "customer"}

        response = TestClient(app).post("/api/rag/knowledge", json={"source_title": "Guide", "content": "Text"})

        self.assertEqual(response.status_code, 403)

    def test_ingest_uses_injected_service(self) -> None:
        chunk_id = uuid4()
        service = Mock()
        service.ingest.return_value = Mock(source_title="Guide", chunk_count=1, chunk_ids=[chunk_id])
        user_id = uuid4()
        app.dependency_overrides[get_current_user] = lambda: {"id": str(user_id), "role": "manager"}
        app.dependency_overrides[get_knowledge_ingestion_service] = lambda: service

        response = TestClient(app).post("/api/rag/knowledge", json={"source_title": "Guide", "content": "Text"})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"source_title": "Guide", "chunk_count": 1, "chunk_ids": [str(chunk_id)]})
        service.ingest.assert_called_once()


if __name__ == "__main__":
    unittest.main()
