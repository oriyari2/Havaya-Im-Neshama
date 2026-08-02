from __future__ import annotations

import re
from dataclasses import dataclass
import logging
from time import perf_counter
from typing import Any

from rag import LLMClient, LLMClientError, OllamaLLMClient
from rag.llm_client import (
    LLMClientConnectionError,
    LLMClientHTTPError,
    LLMClientMalformedResponseError,
    LLMClientTimeoutError,
)

from backend.app.application.services.knowledge_retrieval_service import KnowledgeRetrievalService
from backend.app.core.environment import get_ollama_model


class AIConsultationError(RuntimeError):
    """Raised when the AI consultation flow cannot generate an answer."""


NO_APPROVED_KNOWLEDGE_ANSWER = "לא נמצא במאגר הידע המאושר מידע מספיק כדי לענות על השאלה."
INSUFFICIENT_CONTEXT_SENTINEL = "INSUFFICIENT_CONTEXT"
FALLBACK_SOURCE_LIMIT = 2
GENERATION_CONTEXT_LIMIT = 2


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


logger = logging.getLogger(__name__)


def get_llm_client() -> LLMClient:
    return OllamaLLMClient(model=get_ollama_model())


class AIConsultationService:
    def __init__(self, llm_client: LLMClient, retrieval_service: KnowledgeRetrievalService) -> None:
        self.llm_client = llm_client
        self.retrieval_service = retrieval_service

    def consult(self, prompt: str, *, authenticated_role: str, limit: int) -> AIConsultationResult:
        total_started = perf_counter()
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise ValueError("Prompt must not be empty")

        search = self.retrieval_service.search(query=clean_prompt, authenticated_role=authenticated_role, limit=limit)
        diagnostics: dict[str, Any] = {
            "embedding_ms": round(getattr(search, "embedding_ms", 0.0), 2),
            "retrieval_ms": round(getattr(search, "retrieval_ms", 0.0), 2),
            "retrieved_chunks": len(search.results),
            "generation_model": getattr(self.llm_client, "model", None),
        }
        if not search.results:
            return self._no_answer(diagnostics, total_started)

        prompt_started = perf_counter()
        generation_results = [result for result in search.results if result.content.strip()][:GENERATION_CONTEXT_LIMIT]
        context_chunks = [f"[{index}] {result.content.strip()}" for index, result in enumerate(generation_results, start=1)]
        if not context_chunks:
            return self._no_answer(diagnostics, total_started)
        diagnostics["generation_context_chunks"] = len(generation_results)
        grounded_prompt = self._build_grounded_prompt(clean_prompt, context_chunks)
        diagnostics["prompt_build_ms"] = round((perf_counter() - prompt_started) * 1000, 2)

        try:
            generation_started = perf_counter()
            answer, metadata = self._generate_once(grounded_prompt)
            diagnostics["generation_ms"] = round((perf_counter() - generation_started) * 1000, 2)
            diagnostics.update(self._safe_generation_metadata(metadata))
            if metadata.get("done_reason") == "length":
                _log_generation_rejection("length")
                logger.warning(
                    "AI consultation using deterministic fallback stage=generation failure_type=length",
                    extra={"stage": "generation", "failure_type": "length"},
                )
                return self._fallback_answer(search.results, diagnostics, total_started)
        except _TECHNICAL_FALLBACK_ERRORS as exc:
            print(f"CRITICAL RAG ERROR: {type(exc).__name__} - {exc}")
            failure_type = _failure_type(exc)
            logger.warning(
                "AI consultation using deterministic fallback stage=generation failure_type=%s",
                failure_type,
                extra={"stage": "generation", "failure_type": failure_type},
            )
            diagnostics["generation_ms"] = round((perf_counter() - generation_started) * 1000, 2)
            return self._fallback_answer(search.results, diagnostics, total_started)
        except LLMClientError as exc:
            print(f"CRITICAL RAG ERROR: {type(exc).__name__} - {exc}")
            failure_type = _failure_type(exc)
            logger.warning(
                "AI consultation failed stage=generation failure_type=%s",
                failure_type,
                extra={"stage": "generation", "failure_type": failure_type},
            )
            raise AIConsultationError("AI service is unavailable") from exc

        if answer == INSUFFICIENT_CONTEXT_SENTINEL:
            _log_generation_rejection("insufficient_context")
            return self._no_answer(diagnostics, total_started)

        used_indexes = self._used_source_indexes(answer, max_index=len(generation_results))
        if not used_indexes:
            _log_generation_rejection("no_valid_citations")
            return self._no_answer(diagnostics, total_started)

        sources = self._dedupe_sources([generation_results[index - 1] for index in used_indexes])
        diagnostics["total_ms"] = round((perf_counter() - total_started) * 1000, 2)
        _log_ai_diagnostics(diagnostics)
        return AIConsultationResult(answer=answer, answer_basis="rag", sources=sources)

    def _generate_once(self, prompt: str) -> tuple[str, dict[str, Any]]:
        if hasattr(self.llm_client, "generate_stream_with_metadata"):
            generated = self.llm_client.generate_stream_with_metadata(prompt)
            return generated.text.strip(), generated.metadata
        if hasattr(self.llm_client, "generate_with_metadata"):
            generated = self.llm_client.generate_with_metadata(prompt)
            return generated.text.strip(), generated.metadata
        return self.llm_client.generate(prompt).strip(), {}

    @staticmethod
    def _build_grounded_prompt(question: str, context_chunks: list[str]) -> str:
        context_block = "\n\n".join(context_chunks)
        return (
            'אתה יועץ של "חוויה עם נשמה".\n'
            "ענה בעברית בלבד.\n"
            "השתמש אך ורק במידע שבמקורות המצורפים.\n"
            "ענה ישירות ובקצרה על השאלה.\n"
            "העדף רשימה ברורה כאשר הדבר מתאים.\n"
            "לכל מידע עובדתי הוסף ציון מקור כמו [1] או [2].\n"
            "אל תוסיף מידע שאינו מופיע במקורות.\n"
            "אם אין במקורות מידע מספיק, החזר בדיוק:\n"
            "INSUFFICIENT_CONTEXT\n\n"
            f"מקורות:\n{context_block}\n\n"
            f"שאלה:\n{question}"
        )

    @staticmethod
    def _used_source_indexes(answer: str, *, max_index: int) -> list[int]:
        indexes = {int(match) for match in re.findall(r"\[(\d+)\]", answer)}
        return sorted(index for index in indexes if 1 <= index <= max_index)

    def _no_answer(self, diagnostics: dict[str, Any] | None = None, total_started: float | None = None) -> AIConsultationResult:
        if diagnostics is not None and total_started is not None:
            diagnostics.setdefault("prompt_build_ms", 0.0)
            diagnostics.setdefault("generation_ms", 0.0)
            diagnostics["total_ms"] = round((perf_counter() - total_started) * 1000, 2)
            _log_ai_diagnostics(diagnostics)
        return AIConsultationResult(answer=NO_APPROVED_KNOWLEDGE_ANSWER, answer_basis="none", sources=[])

    def _fallback_answer(self, results, diagnostics: dict[str, Any], total_started: float) -> AIConsultationResult:
        selected_results = self._dedupe_results(results)[:FALLBACK_SOURCE_LIMIT]
        sources = self._dedupe_sources(selected_results)
        sections = []
        for result in selected_results:
            snippet = _trim_fallback_content(result.content.strip())
            if not snippet:
                continue
            sections.append(f"מקור: {result.source_title}\n{snippet}")
        if not sections:
            return self._no_answer(diagnostics, total_started)
        diagnostics["total_ms"] = round((perf_counter() - total_started) * 1000, 2)
        _log_ai_diagnostics(diagnostics)
        answer = (
            "נמצא מידע רלוונטי במאגר הידע המאושר, אך היועץ המקומי לא הצליח להשלים את ניסוח התשובה כרגע. "
            "להלן המידע הזמין מתוך המקורות המאושרים:\n\n"
            + "\n\n".join(sections)
        )
        return AIConsultationResult(answer=answer, answer_basis="rag_fallback", sources=sources)

    @staticmethod
    def _dedupe_results(results) -> list:
        deduped = []
        seen: set[str] = set()
        for result in results:
            source_id = result.metadata.get("source_id") if isinstance(result.metadata, dict) else None
            identity = str(source_id or result.source_uri or result.source_title)
            if identity in seen:
                continue
            seen.add(identity)
            deduped.append(result)
        return deduped

    @staticmethod
    def _dedupe_sources(results) -> list[AIConsultationSource]:
        sources: list[AIConsultationSource] = []
        seen: set[str] = set()
        for result in results:
            source_id = result.metadata.get("source_id") if isinstance(result.metadata, dict) else None
            identity = str(source_id or result.source_uri or result.source_title)
            if identity in seen:
                continue
            seen.add(identity)
            sources.append(
                AIConsultationSource(
                    chunk_id=str(result.chunk_id),
                    source_title=result.source_title,
                    source_uri=result.source_uri,
                )
            )
        return sources

    @staticmethod
    def _safe_generation_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            "model_load_ms": _duration_ns_to_ms(metadata.get("load_duration")),
            "prompt_eval_ms": _duration_ns_to_ms(metadata.get("prompt_eval_duration")),
            "generation_eval_ms": _duration_ns_to_ms(metadata.get("eval_duration")),
            "prompt_tokens": metadata.get("prompt_eval_count", 0),
            "generated_tokens": metadata.get("eval_count", 0),
        }


def _failure_type(exc: LLMClientError) -> str:
    name = type(exc).__name__.lower()
    if "timeout" in name:
        return "timeout"
    if "connection" in name:
        return "connection error"
    if "http" in name:
        return "Ollama HTTP error"
    if "malformed" in name:
        return "malformed response"
    return "unknown"


_TECHNICAL_FALLBACK_ERRORS = (
    LLMClientTimeoutError,
    LLMClientConnectionError,
    LLMClientHTTPError,
    LLMClientMalformedResponseError,
)


def _trim_fallback_content(content: str, *, max_chars: int = 420) -> str:
    clean = re.sub(r"\s+\n", "\n", content).strip()
    clean = re.sub(r"[ \t]+", " ", clean)
    if len(clean) <= max_chars:
        return clean
    boundary = max(
        clean.rfind("\n\n", 0, max_chars),
        clean.rfind(". ", 0, max_chars),
        clean.rfind("! ", 0, max_chars),
        clean.rfind("? ", 0, max_chars),
        clean.rfind("׃ ", 0, max_chars),
    )
    if boundary < max_chars // 2:
        boundary = clean.rfind(" ", 0, max_chars)
    trimmed = clean[: boundary if boundary > 0 else max_chars].strip()
    return f"{trimmed}..."


def _duration_ns_to_ms(value: Any) -> float:
    if isinstance(value, int | float):
        return round(float(value) / 1_000_000, 2)
    return 0.0


def _log_ai_diagnostics(diagnostics: dict[str, Any]) -> None:
    fields = {
        "embedding_ms": diagnostics.get("embedding_ms", 0.0),
        "retrieval_ms": diagnostics.get("retrieval_ms", 0.0),
        "prompt_build_ms": diagnostics.get("prompt_build_ms", 0.0),
        "generation_ms": diagnostics.get("generation_ms", 0.0),
        "total_ms": diagnostics.get("total_ms", 0.0),
        "model_load_ms": diagnostics.get("model_load_ms", 0.0),
        "prompt_eval_ms": diagnostics.get("prompt_eval_ms", 0.0),
        "generation_eval_ms": diagnostics.get("generation_eval_ms", 0.0),
        "prompt_tokens": diagnostics.get("prompt_tokens", 0),
        "generated_tokens": diagnostics.get("generated_tokens", 0),
        "retrieved_chunks": diagnostics.get("retrieved_chunks", 0),
    }
    logger.info(
        "AI diagnostics %s",
        " ".join(f"{key}={value}" for key, value in fields.items()),
    )


def _log_generation_rejection(reason: str) -> None:
    logger.warning(
        "AI consultation rejected completed generation reason=%s",
        reason,
        extra={"stage": "generation", "rejection_reason": reason},
    )
