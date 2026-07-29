from __future__ import annotations

import unittest
from dataclasses import dataclass
from uuid import UUID

from fastapi.testclient import TestClient

from backend.app.core.auth import get_current_user
from backend.app.main import app
from backend.app.routers.ai import get_llm_client
from backend.app.routers.knowledge import get_knowledge_retrieval_service
from rag import LLMClient, LLMClientError


class _FakeLLMClient(LLMClient):
    def __init__(self, answer: str = "Grounded answer [1].", fail: bool = False) -> None:
        self.answer = answer
        self.fail = fail
        self.prompts: list[str] = []
        self.contexts: list[list[str] | None] = []

    def generate(self, prompt: str, context=None) -> str:
        self.prompts.append(prompt)
        self.contexts.append(list(context) if context is not None else None)
        if self.fail:
            raise LLMClientError("offline")
        return self.answer


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
    metadata={"allowed_roles": ["instructor"]},
    distance=0.2,
    score=0.8,
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
        self.assertIn("Answer only from the numbered approved context chunks", fake.prompts[0])
        self.assertIn("Do not use general knowledge, web knowledge, guesses", fake.prompts[0])
        self.assertIn(f"[1] {CHUNK.content}", fake.prompts[0])
        self.assertIsNone(fake.contexts[0])
        self.assertEqual(response.json()["answer_basis"], "rag")
        self.assertEqual(
            response.json()["sources"],
            [{"chunk_id": str(CHUNK.chunk_id), "source_title": "Task17 Equipment", "source_uri": "demo://equipment"}],
        )

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

    def test_consult_reports_ollama_unavailable(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "manager"}
        app.dependency_overrides[get_llm_client] = lambda: _FakeLLMClient(fail=True)
        app.dependency_overrides[get_knowledge_retrieval_service] = lambda: _FakeRetrievalService([CHUNK])

        response = TestClient(app).post("/api/ai/consult", json={"prompt": "hello"})

        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
