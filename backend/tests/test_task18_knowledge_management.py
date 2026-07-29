from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from uuid import uuid4
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from backend.app.application.services.knowledge_management_service import (
    MAX_KNOWLEDGE_UPLOAD_CHARS,
    KnowledgeManagementService,
    normalize_allowed_roles,
)
from backend.app.core.auth import get_current_user
from backend.app.main import app
from backend.app.routers.knowledge import get_knowledge_management_service
from backend.app.schemas.knowledge import KnowledgeSourceCreateRequest, KnowledgeSourceReplaceRequest


class _FakeEmbeddingClient:
    model = "test-embedding-model"

    def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class _FakeConnection:
    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def cursor(self, *args, **kwargs):
        return _FakeKnowledgeCursor(self)

    def commit(self) -> None:
        self.commits += 1


class _FakeKnowledgeCursor:
    def __init__(self, conn: _FakeConnection) -> None:
        self.conn = conn
        self.result = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, sql, params=()) -> None:
        if "INSERT INTO knowledge_chunks" in sql:
            metadata = json.loads(params[4])
            row = {
                "id": uuid4(),
                "source_title": params[0],
                "source_uri": params[1],
                "chunk_index": params[2],
                "content": params[3],
                "metadata": metadata,
                "embedding_model": params[5],
                "embedding_dimensions": params[6],
                "content_hash": params[8],
                "created_by": params[9],
                "created_at": datetime.now(timezone.utc),
            }
            self.conn.rows.append(row)
            self.result = row
            return
        if "DELETE FROM knowledge_chunks" in sql and "metadata ->> 'source_id' = %s" in sql:
            source_id = params[0]
            deleted = [row for row in self.conn.rows if row.get("metadata", {}).get("source_id") == source_id]
            self.conn.rows = [row for row in self.conn.rows if row.get("metadata", {}).get("source_id") != source_id]
            self.result = [{"id": row["id"]} for row in deleted]
            return
        if "DELETE FROM knowledge_chunks" in sql and "RETURNING id" in sql:
            deleted = [row for row in self.conn.rows if not _has_valid_source_id(row) and _is_task16_demo_row(row)]
            self.conn.rows = [row for row in self.conn.rows if _has_valid_source_id(row) or not _is_task16_demo_row(row)]
            self.result = [{"id": row["id"]} for row in deleted]
            return
        if "SELECT (metadata ->> 'source_id')::uuid AS source_id" in sql:
            if "WHERE metadata ->> 'source_id' = %s" in sql:
                source_id = params[0]
                grouped = [row for row in self.conn.rows if row.get("metadata", {}).get("source_id") == source_id]
                self.result = _aggregate(grouped) if grouped else None
                return
            self.result = [_aggregate(rows) for rows in _managed_groups(self.conn.rows).values()]
            return
        raise AssertionError(f"Unexpected SQL: {sql}")

    def fetchone(self):
        return self.result

    def fetchall(self):
        return self.result


def _has_valid_source_id(row: dict) -> bool:
    value = row.get("metadata", {}).get("source_id")
    return isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F-]{36}", value) is not None


def _is_task16_demo_row(row: dict) -> bool:
    metadata = row.get("metadata", {})
    return (
        str(row.get("source_uri") or "").startswith("demo://knowledge/")
        or row.get("source_title")
        in {
            "Task16 Demo Equipment",
            "Task16 Demo Preparation",
            "Task16 Demo Arrival",
            "Task16 Demo Pricing",
            "Task16 Demo Activity",
            "Task16 Demo Proposal",
            "Task16 Demo Policy",
            "Task16 Demo Instructor Internal",
        }
        or metadata.get("demo_task") == "task16"
        or metadata.get("task16_demo") is True
        or metadata.get("task16_demo") == "true"
    )


def _managed_groups(rows: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        if _has_valid_source_id(row):
            groups.setdefault(row["metadata"]["source_id"], []).append(row)
    return groups


def _aggregate(rows: list[dict]) -> dict:
    first = rows[0]
    metadata = first["metadata"]
    return {
        "source_id": metadata["source_id"],
        "title": first["source_title"],
        "source_uri": first["source_uri"],
        "category": metadata.get("category"),
        "activity_name": metadata.get("activity_name"),
        "allowed_roles": metadata.get("allowed_roles"),
        "chunk_count": len(rows),
        "created_by": first["created_by"],
        "created_at": first["created_at"],
        "updated_at": rows[-1]["created_at"],
        "content": metadata.get("original_content", ""),
    }


class KnowledgeManagementServiceRepositoryTests(unittest.TestCase):
    def test_replacement_deletes_selected_source_chunks_and_keeps_other_sources(self) -> None:
        conn = _FakeConnection()
        service = KnowledgeManagementService(_FakeEmbeddingClient(), chunk_size=5, overlap=0)
        creator = uuid4()
        with patch("backend.app.application.services.knowledge_management_service.get_connection", return_value=conn):
            first = service.create(
                KnowledgeSourceCreateRequest(title="First", category="general", content="alpha beta gamma", allowed_roles=["customer"]),
                created_by=creator,
            )
            other = service.create(
                KnowledgeSourceCreateRequest(title="Other", category="general", content="other content", allowed_roles=["instructor"]),
                created_by=creator,
            )
            replaced = service.replace(
                first.source.source_id,
                KnowledgeSourceReplaceRequest(content="new chunks only", allowed_roles=["customer"]),
                created_by=creator,
            )

        first_rows = [row for row in conn.rows if row["metadata"].get("source_id") == str(first.source.source_id)]
        other_rows = [row for row in conn.rows if row["metadata"].get("source_id") == str(other.source.source_id)]
        self.assertEqual({row["content"] for row in first_rows}, {row["content"] for row in conn.rows if row["id"] in replaced.chunk_ids})
        self.assertTrue(all("alpha" not in row["content"] and "beta" not in row["content"] for row in first_rows))
        self.assertEqual(len(first_rows), len(replaced.chunk_ids))
        self.assertEqual(len(other_rows), other.source.chunk_count)

    def test_deletion_removes_every_selected_source_chunk(self) -> None:
        conn = _FakeConnection()
        service = KnowledgeManagementService(_FakeEmbeddingClient(), chunk_size=5, overlap=0)
        with patch("backend.app.application.services.knowledge_management_service.get_connection", return_value=conn):
            source = service.create(
                KnowledgeSourceCreateRequest(title="Delete Me", category="general", content="one two three", allowed_roles=[]),
                created_by=uuid4(),
            )
            deleted = service.delete(source.source.source_id)

        self.assertEqual(deleted, source.source.chunk_count)
        self.assertFalse(any(row["metadata"].get("source_id") == str(source.source.source_id) for row in conn.rows))

    def test_task16_demo_cleanup_preserves_managed_and_non_demo_legacy_sources(self) -> None:
        conn = _FakeConnection()
        managed_id = str(uuid4())
        conn.rows = [
            _stored_row("Managed", "visible", {"source_id": managed_id, "allowed_roles": ["manager", "customer"]}, source_uri="demo://knowledge/managed"),
            _stored_row("Legacy", "legacy content", {"allowed_roles": ["manager", "customer"]}, source_uri="manual://knowledge/customer-guide"),
            _stored_row("Task16 Demo Equipment", "demo content", {"allowed_roles": ["manager"]}, source_uri="demo://knowledge/equipment-guide"),
            _stored_row("Task16 Marker", "marker content", {"allowed_roles": ["manager"], "demo_task": "task16"}),
        ]
        service = KnowledgeManagementService(_FakeEmbeddingClient())

        with patch("backend.app.application.services.knowledge_management_service.get_connection", return_value=conn):
            deleted = service.cleanup_task16_demo_chunks()
            sources = service.list_sources()

        self.assertEqual(deleted, 2)
        self.assertEqual([str(source.source_id) for source in sources], [managed_id])
        self.assertEqual([row["source_title"] for row in conn.rows], ["Managed", "Legacy"])

    def test_customer_and_instructor_retrieval_follows_allowed_roles(self) -> None:
        from backend.tests.test_task16_rag_retrieval import _RepositoryCursor, _row
        from backend.app.infrastructure.repositories.knowledge_retrieval_repository import search_knowledge_chunks

        rows = [
            _row(title="Customer", distance=0.1, metadata={"source_id": str(uuid4()), "allowed_roles": ["manager", "customer"]}),
            _row(title="Instructor", distance=0.1, metadata={"source_id": str(uuid4()), "allowed_roles": ["manager", "instructor"]}),
        ]

        customer = search_knowledge_chunks(
            _RepositoryCursor(rows),
            query_embedding=[0.1, 0.2, 0.3],
            authenticated_role="customer",
            embedding_model="nomic-embed-text",
            embedding_dimensions=3,
            limit=10,
            max_cosine_distance=0.45,
        )
        instructor = search_knowledge_chunks(
            _RepositoryCursor(rows),
            query_embedding=[0.1, 0.2, 0.3],
            authenticated_role="instructor",
            embedding_model="nomic-embed-text",
            embedding_dimensions=3,
            limit=10,
            max_cosine_distance=0.45,
        )

        self.assertEqual([row["source_title"] for row in customer], ["Customer"])
        self.assertEqual([row["source_title"] for row in instructor], ["Instructor"])

    def test_activity_name_is_included_in_document_embedding_input(self) -> None:
        conn = _FakeConnection()
        embedding_client = Mock()
        embedding_client.model = "test-embedding-model"
        embedding_client.embed.return_value = [0.1, 0.2, 0.3]
        service = KnowledgeManagementService(embedding_client, chunk_size=100, overlap=0)

        with patch("backend.app.application.services.knowledge_management_service.get_connection", return_value=conn):
            service.create(
                KnowledgeSourceCreateRequest(
                    title="Activity Guide",
                    category="activity",
                    activity_name="Drumming Workshop",
                    content="Bring equipment.",
                    allowed_roles=["customer"],
                ),
                created_by=uuid4(),
            )

        embedded_text = embedding_client.embed.call_args.args[0]
        self.assertIn("Drumming Workshop", embedded_text)
        self.assertEqual(conn.rows[0]["metadata"]["activity"], "Drumming Workshop")
        self.assertEqual(conn.rows[0]["metadata"]["activity_name"], "Drumming Workshop")


def _stored_row(title: str, content: str, metadata: dict, *, source_uri: str | None = None) -> dict:
    return {
        "id": uuid4(),
        "source_title": title,
        "source_uri": source_uri,
        "chunk_index": 0,
        "content": content,
        "metadata": metadata,
        "embedding_model": "test-embedding-model",
        "embedding_dimensions": 3,
        "content_hash": title,
        "created_by": uuid4(),
        "created_at": datetime.now(timezone.utc),
    }


class KnowledgeManagementApiTests(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_non_manager_source_management_is_denied(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid4()), "role": "instructor"}

        response = TestClient(app).get("/api/rag/sources")

        self.assertEqual(response.status_code, 403)

    def test_manager_can_create_pasted_text_source(self) -> None:
        source_id = uuid4()
        chunk_id = uuid4()
        service = Mock()
        service.create.return_value = _write_result(source_id, chunk_id, roles=["manager", "customer"], chunks=2)
        app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid4()), "role": "manager"}
        app.dependency_overrides[get_knowledge_management_service] = lambda: service

        response = TestClient(app).post(
            "/api/rag/sources",
            json={
                "title": "Activity",
                "category": "activity",
                "content": "new approved text",
                "allowed_roles": ["customer"],
            },
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["source"]["source_id"], str(source_id))
        self.assertEqual(body["source"]["chunk_count"], 2)
        self.assertNotIn("embedding", body["source"])
        service.create.assert_called_once()

    def test_manager_can_upload_supported_file(self) -> None:
        source_id = uuid4()
        service = Mock()
        service.create.return_value = _write_result(source_id, uuid4(), roles=["manager", "instructor"])
        app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid4()), "role": "manager"}
        app.dependency_overrides[get_knowledge_management_service] = lambda: service

        response = TestClient(app).post(
            "/api/rag/sources/upload",
            data={"title": "Equipment", "category": "equipment", "allowed_roles": ["instructor"]},
            files={"file": ("equipment.md", b"# gear\ncharge lights", "text/markdown")},
        )

        self.assertEqual(response.status_code, 201)
        payload = service.create.call_args.args[0]
        self.assertEqual(payload.source_uri, "equipment.md")
        self.assertEqual(payload.content, "# gear\ncharge lights")

    def test_empty_and_unsupported_uploads_are_rejected(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid4()), "role": "manager"}
        client = TestClient(app)

        unsupported = client.post(
            "/api/rag/sources/upload",
            data={"title": "Doc", "category": "general"},
            files={"file": ("doc.pdf", b"text", "application/pdf")},
        )
        empty = client.post(
            "/api/rag/sources/upload",
            data={"title": "Doc", "category": "general"},
            files={"file": ("doc.txt", b"   ", "text/plain")},
        )

        self.assertEqual(unsupported.status_code, 422)
        self.assertEqual(empty.status_code, 422)

    def test_upload_size_limit_is_enforced(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid4()), "role": "manager"}

        response = TestClient(app).post(
            "/api/rag/sources/upload",
            data={"title": "Large", "category": "general"},
            files={"file": ("large.txt", b"x" * (MAX_KNOWLEDGE_UPLOAD_CHARS + 1), "text/plain")},
        )

        self.assertEqual(response.status_code, 413)

    def test_upload_over_schema_content_limit_is_rejected_before_service(self) -> None:
        service = Mock()
        app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid4()), "role": "manager"}
        app.dependency_overrides[get_knowledge_management_service] = lambda: service

        response = TestClient(app).post(
            "/api/rag/sources/upload",
            data={"title": "Large", "category": "general"},
            files={"file": ("large.txt", ("x" * 50001).encode("utf-8"), "text/plain")},
        )

        self.assertEqual(response.status_code, 413)
        service.create.assert_not_called()

    def test_upload_manual_payload_validation_returns_422(self) -> None:
        service = Mock()
        app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid4()), "role": "manager"}
        app.dependency_overrides[get_knowledge_management_service] = lambda: service

        response = TestClient(app).post(
            "/api/rag/sources/upload",
            data={"title": "x" * 201, "category": "general"},
            files={"file": ("valid.txt", b"valid content", "text/plain")},
        )

        self.assertEqual(response.status_code, 422)
        service.create.assert_not_called()

    def test_list_returns_logical_sources_not_embeddings(self) -> None:
        source_id = uuid4()
        service = Mock()
        service.list_sources.return_value = [_source(source_id, roles=["manager", "customer"], chunks=3)]
        app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid4()), "role": "manager"}
        app.dependency_overrides[get_knowledge_management_service] = lambda: service

        response = TestClient(app).get("/api/rag/sources")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["chunk_count"], 3)
        self.assertNotIn("embedding", response.json()[0])

    def test_replace_and_delete_call_grouped_source_operations(self) -> None:
        source_id = uuid4()
        service = Mock()
        service.replace.return_value = _write_result(source_id, uuid4(), roles=["manager"])
        app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid4()), "role": "manager"}
        app.dependency_overrides[get_knowledge_management_service] = lambda: service
        client = TestClient(app)

        replaced = client.put(
            f"/api/rag/sources/{source_id}",
            json={"content": "replacement", "allowed_roles": [], "activity_name": None},
        )
        deleted = client.delete(f"/api/rag/sources/{source_id}")

        self.assertEqual(replaced.status_code, 200)
        self.assertEqual(deleted.status_code, 204)
        service.replace.assert_called_once()
        service.delete.assert_called_once_with(source_id)

    def test_invalid_roles_are_rejected_and_manager_is_retained(self) -> None:
        self.assertEqual(normalize_allowed_roles(["customer"]), ["customer", "manager"])
        with self.assertRaises(ValueError):
            normalize_allowed_roles(["admin"])


def _source(source_id, *, roles: list[str], chunks: int = 1):
    return Mock(
        source_id=source_id,
        title="Guide",
        source_uri="guide.md",
        category="general",
        activity_name=None,
        allowed_roles=roles,
        chunk_count=chunks,
        created_by=uuid4(),
        created_at=None,
        updated_at=None,
        content="original",
    )


def _write_result(source_id, chunk_id, *, roles: list[str], chunks: int = 1):
    return Mock(source=_source(source_id, roles=roles, chunks=chunks), chunk_ids=[chunk_id])


if __name__ == "__main__":
    unittest.main()
