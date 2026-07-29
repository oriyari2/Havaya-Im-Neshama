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
from rag.embedding_formatting import (
    KnowledgeDocumentText,
    format_document_embedding_input,
    format_query_embedding_input,
)
from rag.evaluation import (
    EvaluationCase,
    RetrievalHit,
    calculate_failure_report,
    calculate_raw_metrics,
    calculate_threshold_metrics,
    generate_candidate_thresholds,
    load_evaluation_cases,
)


class _FakeEmbeddingClient(EmbeddingClient):
    model = "nomic-embed-text"

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
        model = params[1]
        dimensions = params[2]
        source_uri_prefix = params[3]
        role = params[5]
        max_distance = params[7]
        limit = params[11]
        visible = []
        for row in self.rows:
            allowed_roles = row.get("metadata", {}).get("allowed_roles")
            is_authorized = role == "manager" or (isinstance(allowed_roles, list) and role in allowed_roles)
            in_source_scope = source_uri_prefix is None or str(row.get("source_uri", "")).startswith(source_uri_prefix)
            in_threshold = max_distance is None or row["distance"] <= max_distance
            if (
                is_authorized
                and in_source_scope
                and row["embedding_model"] == model
                and row["embedding_dimensions"] == dimensions
                and in_threshold
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
    model: str = "nomic-embed-text",
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
        self.assertEqual(conn.cursor_obj.executed_params[1], "nomic-embed-text")
        self.assertEqual(conn.cursor_obj.executed_params[2], 3)
        self.assertEqual(conn.cursor_obj.executed_params[5], "instructor")
        self.assertEqual(conn.cursor_obj.executed_params[11], 4)
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


class EmbeddingFormattingTests(unittest.TestCase):
    def test_nomic_document_input_is_enriched_without_changing_visible_content(self) -> None:
        document = KnowledgeDocumentText(
            source_title=" מדריך ציוד ",
            content="  טען יחידות אור  ",
            metadata={"category": "equipment", "activity": "תפוס את האור"},
        )

        formatted = format_document_embedding_input(model="nomic-embed-text-v2-moe", document=document)

        self.assertEqual(
            formatted,
            "search_document: כותרת: מדריך ציוד\nקטגוריה: equipment\nפעילות: תפוס את האור\nתוכן מקורי: טען יחידות אור",
        )
        self.assertEqual(document.content, "  טען יחידות אור  ")

    def test_bge_m3_uses_plain_normalized_text_without_prefix(self) -> None:
        document = KnowledgeDocumentText(
            source_title="כותרת",
            content="תוכן   מקורי",
            metadata={"category": "preparation"},
        )

        self.assertEqual(format_query_embedding_input(model="bge-m3", query="  שלום   עולם "), "שלום עולם")
        self.assertEqual(
            format_document_embedding_input(model="bge-m3", document=document),
            "כותרת: כותרת\nקטגוריה: preparation\nתוכן מקורי: תוכן מקורי",
        )

    def test_document_enrichment_omits_empty_metadata_values(self) -> None:
        cases = [
            ({}, "קטגוריה:"),
            ({"category": None}, "קטגוריה: None"),
            ({"category": ""}, "קטגוריה:"),
            ({"category": "   "}, "קטגוריה:"),
            ({"activity": None}, "פעילות: None"),
            ({"activity": ""}, "פעילות:"),
            ({"activity": "   "}, "פעילות:"),
        ]

        for metadata, forbidden in cases:
            with self.subTest(metadata=metadata):
                formatted = format_document_embedding_input(
                    model="bge-m3",
                    document=KnowledgeDocumentText(source_title="Guide", content="Body", metadata=metadata),
                )
                self.assertNotIn(forbidden, formatted)

        formatted = format_document_embedding_input(
            model="bge-m3",
            document=KnowledgeDocumentText(
                source_title="Guide",
                content="Body",
                metadata={"category": " equipment ", "activity": " Catch the Light "},
            ),
        )
        self.assertIn("קטגוריה: equipment", formatted)
        self.assertIn("פעילות: Catch the Light", formatted)


class KnowledgeRetrievalRepositoryTests(unittest.TestCase):
    def test_sql_uses_pgvector_cosine_distance_and_parameters(self) -> None:
        cur = _RepositoryCursor([])

        search_knowledge_chunks(
            cur,
            query_embedding=[1, 0, 0],
            authenticated_role="manager",
            embedding_model="nomic-embed-text",
            embedding_dimensions=3,
            limit=5,
            max_cosine_distance=0.45,
        )

        self.assertIn("<=>", cur.executed_sql)
        self.assertIn("jsonb_typeof(metadata -> 'allowed_roles') = 'array'", cur.executed_sql)
        self.assertIn("LIMIT %s", cur.executed_sql)
        self.assertEqual(cur.executed_params[0], "[1.0,0.0,0.0]")
        self.assertEqual(cur.executed_params[7], 0.45)

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
            embedding_model="nomic-embed-text",
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
            embedding_model="nomic-embed-text",
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


class Task16EvaluationTests(unittest.TestCase):
    def test_fixture_parses_required_hebrew_cases(self) -> None:
        cases = load_evaluation_cases("rag/evaluation_fixture_task16_he.json")

        self.assertGreaterEqual(len(cases), 30)
        self.assertLessEqual(len(cases), 50)
        self.assertTrue(any(case.authenticated_role == "manager" for case in cases))
        self.assertTrue(any(case.authenticated_role == "instructor" for case in cases))
        self.assertTrue(any(case.authenticated_role == "customer" for case in cases))
        self.assertTrue(any(not case.should_retrieve for case in cases))

    def test_metrics_include_accuracy_rejection_margins_and_unauthorized_count(self) -> None:
        cases = [
            EvaluationCase("ציוד", "instructor", True, expected_category="equipment"),
            EvaluationCase("חללית", "customer", False),
            EvaluationCase("מחיר פנימי", "customer", False),
        ]
        results = [
            (
                cases[0],
                [
                    RetrievalHit("Guide", "equipment", 0.1, authorized=True),
                    RetrievalHit("Other", "arrival", 0.3, authorized=True),
                ],
            ),
            (cases[1], []),
            (cases[2], [RetrievalHit("Internal", "pricing", 0.2, authorized=False)]),
        ]
        raw_metrics = calculate_raw_metrics(results)
        threshold_metrics = calculate_threshold_metrics(results, 0.15)

        self.assertEqual(raw_metrics.top_1_accuracy, 1.0)
        self.assertEqual(raw_metrics.top_3_recall, 1.0)
        self.assertEqual(raw_metrics.relevant_distance_range, (0.1, 0.1))
        self.assertEqual(raw_metrics.unrelated_first_result_distance_range, (0.2, 0.2))
        self.assertEqual(raw_metrics.first_to_second_margin_range, (0.19999999999999998, 0.19999999999999998))
        self.assertEqual(raw_metrics.unauthorized_retrieval_count, 1)
        self.assertEqual(threshold_metrics.relevant_queries_accepted, 1)
        self.assertEqual(threshold_metrics.unrelated_queries_accepted, 0)
        self.assertEqual(threshold_metrics.unrelated_rejection_rate, 1.0)
        self.assertEqual(threshold_metrics.accepted_top_1_accuracy, 1.0)
        self.assertEqual(threshold_metrics.wrong_top_1_accepted_count, 0)

    def test_authorization_metric_detects_unauthorized_hit(self) -> None:
        case = EvaluationCase("מחיר פנימי", "customer", False, forbidden_sources=("Internal",))
        metrics = calculate_raw_metrics(
            [
                (case, [RetrievalHit("Internal", "pricing", 0.2, authorized=False)]),
            ]
        )

        self.assertEqual(metrics.unauthorized_retrieval_count, 1)
        self.assertEqual(metrics.forbidden_retrieval_count, 1)

    def test_threshold_metrics_require_expected_source_for_relevant_acceptance(self) -> None:
        case = EvaluationCase("ציוד", "instructor", True, expected_sources=("Expected",))
        results = [
            (
                case,
                [
                    RetrievalHit("Wrong", "equipment", 0.1, authorized=True),
                    RetrievalHit("Expected", "equipment", 0.2, authorized=True),
                ],
            )
        ]

        low_threshold = calculate_threshold_metrics(results, 0.15)
        high_threshold = calculate_threshold_metrics(results, 0.25)

        self.assertEqual(low_threshold.relevant_queries_accepted, 0)
        self.assertEqual(low_threshold.relevant_queries_rejected, 1)
        self.assertEqual(high_threshold.relevant_queries_accepted, 1)
        self.assertEqual(high_threshold.accepted_top_1_accuracy, 0.0)
        self.assertEqual(high_threshold.wrong_top_1_accepted_count, 1)

    def test_candidate_thresholds_include_expected_source_distances_and_midpoints(self) -> None:
        relevant = EvaluationCase("ציוד", "instructor", True, expected_sources=("Expected",))
        unrelated = EvaluationCase("חללית", "customer", False)
        thresholds = generate_candidate_thresholds(
            [
                (
                    relevant,
                    [
                        RetrievalHit("Wrong", "equipment", 0.1, authorized=True),
                        RetrievalHit("Expected", "equipment", 0.3, authorized=True),
                    ],
                ),
                (unrelated, [RetrievalHit("Other", "arrival", 0.5, authorized=True)]),
            ]
        )

        self.assertIn(0.1, thresholds)
        self.assertIn(0.3, thresholds)
        self.assertIn(0.4, thresholds)
        self.assertIn(0.5, thresholds)

    def test_failure_report_lists_exact_threshold_failures(self) -> None:
        relevant = EvaluationCase("ציוד", "instructor", True, expected_sources=("Expected",))
        unrelated = EvaluationCase("חללית", "customer", False, forbidden_sources=("Forbidden",))
        failures = calculate_failure_report(
            [
                (relevant, [RetrievalHit("Wrong", "equipment", 0.1, authorized=True)]),
                (unrelated, [RetrievalHit("Forbidden", "pricing", 0.1, authorized=False)]),
            ],
            0.2,
        )

        self.assertEqual(len(failures), 2)
        self.assertIn("expected source did not pass threshold", failures[0].failure_reason)
        self.assertIn("unrelated query had accepted retrieval", failures[1].failure_reason)
        self.assertIn("forbidden source passed threshold", failures[1].failure_reason)
        self.assertIn("unauthorized result passed threshold", failures[1].failure_reason)


if __name__ == "__main__":
    unittest.main()
