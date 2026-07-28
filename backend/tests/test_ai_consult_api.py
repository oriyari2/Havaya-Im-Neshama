from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from backend.app.core.auth import get_current_user
from backend.app.main import app
from backend.app.routers.ai import get_llm_client
from rag import LLMClient, LLMClientError


class _FakeLLMClient(LLMClient):
    def __init__(self, answer: str = "שלום, זו תשובה.", fail: bool = False) -> None:
        self.answer = answer
        self.fail = fail
        self.prompts: list[str] = []

    def generate(self, prompt: str, context=None) -> str:
        self.prompts.append(prompt)
        if self.fail:
            raise LLMClientError("offline")
        return self.answer


class AIConsultApiTests(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_consult_requires_authentication(self) -> None:
        response = TestClient(app).post("/api/ai/consult", json={"prompt": "שלום"})
        self.assertEqual(response.status_code, 401)

    def test_consult_uses_injected_llm_client(self) -> None:
        fake = _FakeLLMClient()
        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "customer"}
        app.dependency_overrides[get_llm_client] = lambda: fake

        response = TestClient(app).post("/api/ai/consult", json={"prompt": "  מה להכין?  "})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"answer": "שלום, זו תשובה."})
        self.assertEqual(fake.prompts, ["מה להכין?"])

    def test_consult_reports_ollama_unavailable(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "role": "manager"}
        app.dependency_overrides[get_llm_client] = lambda: _FakeLLMClient(fail=True)

        response = TestClient(app).post("/api/ai/consult", json={"prompt": "שלום"})

        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
