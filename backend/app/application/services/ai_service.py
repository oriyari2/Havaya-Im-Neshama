from __future__ import annotations

import re
from dataclasses import dataclass

from rag import LLMClient, LLMClientError, OllamaLLMClient

from backend.app.application.services.knowledge_retrieval_service import KnowledgeRetrievalService
from backend.app.core.environment import get_ollama_model


class AIConsultationError(RuntimeError):
    """Raised when the AI consultation flow cannot generate an answer."""


NO_APPROVED_KNOWLEDGE_ANSWER = "לא נמצא במאגר הידע המאושר מידע מספיק כדי לענות על השאלה."
INSUFFICIENT_CONTEXT_SENTINEL = "INSUFFICIENT_CONTEXT"


@dataclass(frozen=True)
class AIConsultationSource:
    chunk_id: str
    source_title: str
    source_uri: str | None


@dataclass(frozen=True)
class AIConsultationResult:
    answer: str
    answer_basis: str
    sources: list[AIConsultationSource]


def get_llm_client() -> LLMClient:
    return OllamaLLMClient(model=get_ollama_model())


class AIConsultationService:
    def __init__(self, llm_client: LLMClient, retrieval_service: KnowledgeRetrievalService) -> None:
        self.llm_client = llm_client
        self.retrieval_service = retrieval_service

    def consult(self, prompt: str, *, authenticated_role: str, limit: int) -> AIConsultationResult:
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise ValueError("Prompt must not be empty")

        search = self.retrieval_service.search(query=clean_prompt, authenticated_role=authenticated_role, limit=limit)
        if not search.results:
            return self._no_answer()

        context_chunks = [
            f"[{index}] {result.content.strip()}"
            for index, result in enumerate(search.results, start=1)
            if result.content.strip()
        ]
        if not context_chunks:
            return self._no_answer()

        try:
            answer = self.llm_client.generate(self._build_grounded_prompt(clean_prompt, context_chunks)).strip()
        except LLMClientError as exc:
            raise AIConsultationError("AI service is unavailable") from exc

        if answer == INSUFFICIENT_CONTEXT_SENTINEL:
            return self._no_answer()

        used_indexes = self._used_source_indexes(answer, max_index=len(search.results))
        if not used_indexes:
            return self._no_answer()

        sources = [
            AIConsultationSource(
                chunk_id=str(search.results[index - 1].chunk_id),
                source_title=search.results[index - 1].source_title,
                source_uri=search.results[index - 1].source_uri,
            )
            for index in used_indexes
        ]
        return AIConsultationResult(answer=answer, answer_basis="rag", sources=sources)

    @staticmethod
    def _build_grounded_prompt(question: str, context_chunks: list[str]) -> str:
        context_block = "\n\n".join(context_chunks)
        return (
            "Answer only from the numbered approved context chunks provided in this request.\n"
            "Do not use general knowledge, web knowledge, guesses, or unsupported details.\n"
            "Every factual claim must include inline citations like [1].\n"
            "If the context is insufficient, return exactly INSUFFICIENT_CONTEXT and nothing else.\n\n"
            f"Approved context:\n{context_block}\n\n"
            f"Question:\n{question}"
        )

    @staticmethod
    def _used_source_indexes(answer: str, *, max_index: int) -> list[int]:
        indexes = {int(match) for match in re.findall(r"\[(\d+)\]", answer)}
        return sorted(index for index in indexes if 1 <= index <= max_index)

    @staticmethod
    def _no_answer() -> AIConsultationResult:
        return AIConsultationResult(answer=NO_APPROVED_KNOWLEDGE_ANSWER, answer_basis="none", sources=[])
