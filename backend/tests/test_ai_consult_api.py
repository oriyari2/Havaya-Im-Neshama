from __future__ import annotations

import unittest
from dataclasses import dataclass
from unittest.mock import patch
from uuid import UUID

import httpx
from fastapi.testclient import TestClient

from backend.app.core.auth import get_current_user
from backend.app.application.services.knowledge_retrieval_service import KnowledgeRetrievalError
from backend.app.main import app
from backend.app.routers.ai import get_llm_client, _knowledge_failure_type
from backend.app.routers.knowledge import get_knowledge_retrieval_service
from rag.embedding_client import EmbeddingClientConnectionError, EmbeddingClientMalformedResponseError, EmbeddingClientTimeoutError
from rag import LLMClient, LLMClientError
from rag.llm_client import (
    LLMGeneration,
    LLMClientConnectionError,
    LLMClientHTTPError,
    LLMClientMalformedResponseError,
    LLMClientTimeoutError,
    OllamaLLMClient,
)


class _FakeLLMClient(LLMClient):
    def __init__(self, answer: str = "Grounded answer [1].", fail: bool = False, exc: Exception | None = None) -> None:
        self.answer = answer
        self.fail = fail
        self.exc = exc
        self.prompts: list[str] = []
        self.contexts: list[list[str] | None] = []

    def generate(self, prompt: str, context=None) -> str:
        self.prompts.append(prompt)
        self.contexts.append(list(context) if context is not None else None)
        if self.exc is not None:
            raise self.exc
        if self.fail:
            raise LLMClientError("offline")
        return self.answer


class _FakeMetadataLLMClient(_FakeLLMClient):
    def __init__(self, answer: str, done_reason: str) -> None:
        super().__init__(answer=answer)
        self.done_reason = done_reason

    def generate_with_metadata(self, prompt: str, context=None) -> LLMGeneration:
        self.prompts.append(prompt)
        self.contexts.append(list(context) if context is not None else None)
        return LLMGeneration(text=self.answer, metadata={"done_reason": self.done_reason})


class _FakeStreamingLLMClient(_FakeLLMClient):
    def generate_stream_with_metadata(self, prompt: str, context=None) -> LLMGeneration:
        self.prompts.append(prompt)
        self.contexts.append(list(context) if context is not None else None)
        if self.exc is not None:
            raise self.exc
        return LLMGeneration(text=self.answer, metadata={"done_reason": "stop"})


@dataclass(frozen=True)
class _SearchResult:
    chunk_id: UUID
    source_title: str
    source_uri: str | None
    chunk_index: int
    content: str
    metadata: dict
    distance: float
    score: float


@dataclass(frozen=True)
class _Search:
    query: str
    results: list[_SearchResult]


class _FakeRetrievalService:
    def __init__(self, results: list[_SearchResult] | None = None) -> None:
        self.results = results or []
        self.calls: list[dict] = []

    def search(self, *, query: str, authenticated_role: str, limit: int) -> _Search:
        self.calls.append({"query": query, "authenticated_role": authenticated_role, "limit": limit})
        return _Search(query=query.strip(), results=self.results)


CHUNK = _SearchResult(
    chunk_id=UUID("11111111-1111-1111-1111-111111111111"),
    source_title="Task17 Equipment",
    source_uri="demo://equipment",
    chunk_index=0,
    content="Check the speaker, cables, and projector before Catch the Light.",
    metadata={"allowed_roles": ["instructor"], "source_id": "source-1"},
    distance=0.2,
    score=0.8,
)

SECOND_CHUNK = _SearchResult(
    chunk_id=UUID("22222222-2222-2222-2222-222222222222"),
    source_title="Task17 Safety",
    source_uri="demo://safety",
    chunk_index=0,
    content="Confirm participants have water and the outdoor route is clear before the activity.",
    metadata={"allowed_roles": ["instructor"], "source_id": "source-2"},
    distance=0.21,
    score=0.79,
)

DUPLICATE_CHUNK = _SearchResult(
    chunk_id=UUID("33333333-3333-3333-3333-333333333333"),
    source_title="Task17 Equipment",
    source_uri="demo://equipment",
    chunk_index=1,
    content="This duplicate equipment chunk should not become a second fallback source.",
    metadata={"allowed_roles": ["instructor"], "source_id": "source-1"},
    distance=0.22,
    score=0.78,
)


class AIConsultApiTests(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_consult_requires_authentication(self) -> None:
        response = TestClient(app).post("/api/ai/consult", json={"prompt": "hello"})
        self.assertEqual(response.status_code, 401)

    def test_no_retrieval_results_skips_llm(self) -> None:
        fake = _FakeLLMClient()
        retrieval = _FakeRetrievalService()
        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "customer"}
        app.dependency_overrides[get_llm_client] = lambda: fake
        app.dependency_overrides[get_knowledge_retrieval_service] = lambda: retrieval

        response = TestClient(app).post("/api/ai/consult", json={"prompt": "  what should I prepare?  "})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer_basis"], "none")
        self.assertEqual(response.json()["sources"], [])
        self.assertEqual(fake.prompts, [])

    def test_consult_uses_authenticated_role_and_grounded_prompt(self) -> None:
        fake = _FakeLLMClient(answer="Check the equipment before the activity [1].")
        retrieval = _FakeRetrievalService([CHUNK])
        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "instructor"}
        app.dependency_overrides[get_llm_client] = lambda: fake
        app.dependency_overrides[get_knowledge_retrieval_service] = lambda: retrieval

        response = TestClient(app).post("/api/ai/consult", json={"prompt": "  what should I prepare?  "})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(retrieval.calls[0]["authenticated_role"], "instructor")
        self.assertEqual(retrieval.calls[0]["query"], "what should I prepare?")
        self.assertIn('אתה יועץ של "חוויה עם נשמה".', fake.prompts[0])
        self.assertIn("ענה בעברית בלבד.", fake.prompts[0])
        self.assertIn("השתמש אך ורק במידע שבמקורות המצורפים.", fake.prompts[0])
        self.assertIn("לכל מידע עובדתי הוסף ציון מקור כמו [1] או [2].", fake.prompts[0])
        self.assertIn("INSUFFICIENT_CONTEXT", fake.prompts[0])
        self.assertIn(f"[1] {CHUNK.content}", fake.prompts[0])
        self.assertIsNone(fake.contexts[0])
        self.assertEqual(response.json()["answer_basis"], "rag")
        self.assertNotIn("diagnostics", response.json())
        self.assertEqual(
            response.json()["sources"],
            [{"chunk_id": str(CHUNK.chunk_id), "source_title": "Task17 Equipment", "source_uri": "demo://equipment"}],
        )

    def test_generation_receives_only_top_two_results_when_retrieval_returns_five(self) -> None:
        extra_results = [
            _SearchResult(
                chunk_id=UUID(f"44444444-4444-4444-4444-44444444444{index}"),
                source_title=f"Task17 Extra {index}",
                source_uri=f"demo://extra-{index}",
                chunk_index=0,
                content=f"Extra retrieved content {index} must not enter the prompt.",
                metadata={"source_id": f"source-extra-{index}"},
                distance=0.22 + index / 100,
                score=0.78 - index / 100,
            )
            for index in range(3)
        ]
        fake = _FakeLLMClient(answer="Use both supplied sources [1] [2].")
        retrieval = _FakeRetrievalService([CHUNK, SECOND_CHUNK, *extra_results])
        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "instructor"}
        app.dependency_overrides[get_llm_client] = lambda: fake
        app.dependency_overrides[get_knowledge_retrieval_service] = lambda: retrieval

        response = TestClient(app).post("/api/ai/consult", json={"prompt": "what should I prepare?"})

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(retrieval.calls[0]["limit"], 5)
        self.assertIn(f"[1] {CHUNK.content}", fake.prompts[0])
        self.assertIn(f"[2] {SECOND_CHUNK.content}", fake.prompts[0])
        for result in extra_results:
            self.assertNotIn(result.content, fake.prompts[0])
        self.assertEqual(body["answer_basis"], "rag")
        self.assertEqual([source["chunk_id"] for source in body["sources"]], [str(CHUNK.chunk_id), str(SECOND_CHUNK.chunk_id)])

    def test_citation_mapping_uses_only_generation_context_results(self) -> None:
        hidden = _SearchResult(
            chunk_id=UUID("55555555-5555-5555-5555-555555555555"),
            source_title="Task17 Hidden",
            source_uri="demo://hidden",
            chunk_index=0,
            content="Hidden third retrieved content must not be citeable as [3].",
            metadata={"source_id": "source-3"},
            distance=0.23,
            score=0.77,
        )
        fake = _FakeLLMClient(answer="Unsupported third citation [3].")
        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "manager"}
        app.dependency_overrides[get_llm_client] = lambda: fake
        app.dependency_overrides[get_knowledge_retrieval_service] = lambda: _FakeRetrievalService([CHUNK, SECOND_CHUNK, hidden])

        response = TestClient(app).post("/api/ai/consult", json={"prompt": "hello"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer_basis"], "none")
        self.assertEqual(response.json()["sources"], [])

    def test_done_reason_stop_returns_normal_rag_answer(self) -> None:
        fake = _FakeMetadataLLMClient(answer="Generated complete answer [1].", done_reason="stop")
        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "manager"}
        app.dependency_overrides[get_llm_client] = lambda: fake
        app.dependency_overrides[get_knowledge_retrieval_service] = lambda: _FakeRetrievalService([CHUNK])

        response = TestClient(app).post("/api/ai/consult", json={"prompt": "hello"})

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["answer_basis"], "rag")
        self.assertEqual(body["answer"], "Generated complete answer [1].")
        self.assertEqual(len(fake.prompts), 1)

    def test_done_reason_length_returns_rag_fallback_without_partial_generated_text(self) -> None:
        fake = _FakeMetadataLLMClient(answer="Partial generated text that must not leak [1].", done_reason="length")
        retrieval = _FakeRetrievalService([CHUNK])
        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "manager"}
        app.dependency_overrides[get_llm_client] = lambda: fake
        app.dependency_overrides[get_knowledge_retrieval_service] = lambda: retrieval

        response = TestClient(app).post("/api/ai/consult", json={"prompt": "hello"})

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["answer_basis"], "rag_fallback")
        self.assertNotIn("Partial generated text", body["answer"])
        self.assertIn(CHUNK.content, body["answer"])
        self.assertEqual(len(fake.prompts), 1)
        self.assertEqual(len(retrieval.calls), 1)

    def test_insufficient_context_sentinel_returns_no_answer(self) -> None:
        fake = _FakeLLMClient(answer="INSUFFICIENT_CONTEXT")
        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "manager"}
        app.dependency_overrides[get_llm_client] = lambda: fake
        app.dependency_overrides[get_knowledge_retrieval_service] = lambda: _FakeRetrievalService([CHUNK])

        response = TestClient(app).post("/api/ai/consult", json={"prompt": "what is the price?"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer_basis"], "none")
        self.assertEqual(response.json()["sources"], [])

    def test_request_role_is_ignored(self) -> None:
        fake = _FakeLLMClient(answer="Check equipment [1].")
        retrieval = _FakeRetrievalService([CHUNK])
        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "customer"}
        app.dependency_overrides[get_llm_client] = lambda: fake
        app.dependency_overrides[get_knowledge_retrieval_service] = lambda: retrieval

        response = TestClient(app).post("/api/ai/consult", json={"prompt": "what should I prepare?", "role": "manager"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(retrieval.calls[0]["authenticated_role"], "customer")

    def test_restricted_knowledge_is_not_exposed_when_retrieval_denies_role(self) -> None:
        fake = _FakeLLMClient(answer="Manager pricing [1].")
        retrieval = _FakeRetrievalService()
        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "instructor"}
        app.dependency_overrides[get_llm_client] = lambda: fake
        app.dependency_overrides[get_knowledge_retrieval_service] = lambda: retrieval

        response = TestClient(app).post("/api/ai/consult", json={"prompt": "manager pricing"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer_basis"], "none")
        self.assertEqual(fake.prompts, [])

    def test_consult_reports_generic_ollama_error_without_fallback(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "manager"}
        app.dependency_overrides[get_llm_client] = lambda: _FakeLLMClient(fail=True)
        app.dependency_overrides[get_knowledge_retrieval_service] = lambda: _FakeRetrievalService([CHUNK])

        response = TestClient(app).post("/api/ai/consult", json={"prompt": "hello"})

        self.assertEqual(response.status_code, 503)

    def test_generation_timeout_returns_rag_fallback_from_retrieved_chunks(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "manager"}
        app.dependency_overrides[get_llm_client] = lambda: _FakeLLMClient(exc=LLMClientTimeoutError("slow"))
        app.dependency_overrides[get_knowledge_retrieval_service] = lambda: _FakeRetrievalService([CHUNK])

        response = TestClient(app).post("/api/ai/consult", json={"prompt": "hello"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["answer_basis"], "rag_fallback")
        self.assertIn("נמצא מידע רלוונטי במאגר הידע המאושר", body["answer"])
        self.assertIn("Task17 Equipment", body["answer"])
        self.assertIn(CHUNK.content, body["answer"])
        self.assertEqual(body["sources"], [{"chunk_id": str(CHUNK.chunk_id), "source_title": "Task17 Equipment", "source_uri": "demo://equipment"}])

    def test_partial_stream_failure_returns_fallback_without_partial_text(self) -> None:
        fake = _FakeStreamingLLMClient(
            answer="Partial generated stream text that must not leak [1].",
            exc=LLMClientTimeoutError("idle timeout after partial stream"),
        )
        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "manager"}
        app.dependency_overrides[get_llm_client] = lambda: fake
        app.dependency_overrides[get_knowledge_retrieval_service] = lambda: _FakeRetrievalService([CHUNK])

        response = TestClient(app).post("/api/ai/consult", json={"prompt": "hello"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["answer_basis"], "rag_fallback")
        self.assertNotIn("Partial generated stream text", body["answer"])
        self.assertIn(CHUNK.content, body["answer"])
        self.assertEqual(len(fake.prompts), 1)

    def test_transport_error_after_partial_ollama_stream_returns_fallback_without_partial_text(self) -> None:
        class PartialThenProtocolErrorStream:
            request = None

            def __enter__(self):
                return self

            def __exit__(self, _exc_type, _exc, _traceback) -> None:
                return None

            def raise_for_status(self) -> None:
                return None

            def iter_lines(self):
                yield '{"response":"Partial generated stream text that must not leak ","done":false}'
                raise httpx.RemoteProtocolError("peer closed connection without complete response")

        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "manager"}
        app.dependency_overrides[get_llm_client] = lambda: OllamaLLMClient(model="demo-model", base_url="http://localhost:11434")
        app.dependency_overrides[get_knowledge_retrieval_service] = lambda: _FakeRetrievalService([CHUNK])

        with patch("rag.llm_client.httpx.stream", return_value=PartialThenProtocolErrorStream()):
            response = TestClient(app).post("/api/ai/consult", json={"prompt": "hello"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["answer_basis"], "rag_fallback")
        self.assertNotIn("Partial generated stream text", body["answer"])
        self.assertIn(CHUNK.content, body["answer"])

    def test_connection_http_and_malformed_generation_failures_return_rag_fallback(self) -> None:
        cases = (
            LLMClientConnectionError("offline"),
            LLMClientHTTPError("bad status"),
            LLMClientMalformedResponseError("bad payload"),
        )
        for exc in cases:
            with self.subTest(exc=type(exc).__name__):
                app.dependency_overrides.clear()
                app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "manager"}
                app.dependency_overrides[get_llm_client] = lambda exc=exc: _FakeLLMClient(exc=exc)
                app.dependency_overrides[get_knowledge_retrieval_service] = lambda: _FakeRetrievalService([CHUNK])

                response = TestClient(app).post("/api/ai/consult", json={"prompt": "hello"})

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["answer_basis"], "rag_fallback")

    def test_uncited_generated_answer_does_not_become_technical_fallback(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "manager"}
        app.dependency_overrides[get_llm_client] = lambda: _FakeLLMClient(answer="Unsupported answer without citations.")
        app.dependency_overrides[get_knowledge_retrieval_service] = lambda: _FakeRetrievalService([CHUNK])

        response = TestClient(app).post("/api/ai/consult", json={"prompt": "hello"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer_basis"], "none")
        self.assertEqual(response.json()["sources"], [])

    def test_fallback_uses_only_top_deduplicated_retrieved_content(self) -> None:
        hidden = _SearchResult(
            chunk_id=UUID("44444444-4444-4444-4444-444444444444"),
            source_title="Task17 Hidden",
            source_uri="demo://hidden",
            chunk_index=0,
            content="This third source must not be included.",
            metadata={"source_id": "source-3"},
            distance=0.23,
            score=0.77,
        )
        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "manager"}
        app.dependency_overrides[get_llm_client] = lambda: _FakeLLMClient(exc=LLMClientConnectionError("offline"))
        app.dependency_overrides[get_knowledge_retrieval_service] = lambda: _FakeRetrievalService([CHUNK, DUPLICATE_CHUNK, SECOND_CHUNK, hidden])

        response = TestClient(app).post("/api/ai/consult", json={"prompt": "hello"})

        body = response.json()
        self.assertEqual(body["answer_basis"], "rag_fallback")
        self.assertIn(CHUNK.content, body["answer"])
        self.assertIn(SECOND_CHUNK.content, body["answer"])
        self.assertNotIn(DUPLICATE_CHUNK.content, body["answer"])
        self.assertNotIn(hidden.content, body["answer"])
        self.assertEqual([source["source_title"] for source in body["sources"]], ["Task17 Equipment", "Task17 Safety"])

    def test_generation_failure_log_message_includes_stage_and_type(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "manager"}
        app.dependency_overrides[get_llm_client] = lambda: _FakeLLMClient(fail=True)
        app.dependency_overrides[get_knowledge_retrieval_service] = lambda: _FakeRetrievalService([CHUNK])

        with self.assertLogs("backend.app.application.services.ai_service", level="WARNING") as logs:
            TestClient(app).post("/api/ai/consult", json={"prompt": "hello"})

        self.assertIn("stage=generation failure_type=unknown", "\n".join(logs.output))

    def test_embedding_failure_type_uses_underlying_cause(self) -> None:
        cases = (
            (EmbeddingClientTimeoutError("slow"), "timeout"),
            (EmbeddingClientConnectionError("offline"), "connection error"),
            (EmbeddingClientMalformedResponseError("bad json"), "malformed response"),
        )
        for cause, expected in cases:
            with self.subTest(expected=expected):
                error = KnowledgeRetrievalError("Embedding service is unavailable")
                error.__cause__ = cause
                self.assertEqual(_knowledge_failure_type(error), expected)


if __name__ == "__main__":
    unittest.main()
