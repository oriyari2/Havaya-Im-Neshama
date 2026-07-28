from __future__ import annotations

from rag import LLMClient, LLMClientError, OllamaLLMClient

from backend.app.core.environment import get_ollama_model


class AIConsultationError(RuntimeError):
    """Raised when the AI consultation flow cannot generate an answer."""


def get_llm_client() -> LLMClient:
    return OllamaLLMClient(model=get_ollama_model())


class AIConsultationService:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def consult(self, prompt: str) -> str:
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise ValueError("Prompt must not be empty")

        try:
            return self.llm_client.generate(clean_prompt)
        except LLMClientError as exc:
            raise AIConsultationError("AI service is unavailable") from exc
