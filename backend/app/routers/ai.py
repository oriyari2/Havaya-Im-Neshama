from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.app.application.services.ai_runtime import ai_readiness
from backend.app.application.services.ai_service import (
    AIConsultationError,
    AIConsultationService,
    get_llm_client,
)
from backend.app.application.services.knowledge_retrieval_service import (
    KnowledgeRetrievalError,
    KnowledgeRetrievalService,
)
from backend.app.core.auth import get_current_user, require_roles
from backend.app.core.environment import get_rag_retrieval_top_k
from backend.app.routers.knowledge import get_knowledge_retrieval_service
from backend.app.schemas.ai import AIConsultRequest, AIConsultResponse
from rag import LLMClient


router = APIRouter(prefix="/api/ai", tags=["ai"])
logger = logging.getLogger(__name__)
RequireManager = Depends(require_roles("manager"))


def get_ai_service(
    llm_client: LLMClient = Depends(get_llm_client),
    retrieval_service: KnowledgeRetrievalService = Depends(get_knowledge_retrieval_service),
) -> AIConsultationService:
    return AIConsultationService(llm_client, retrieval_service)


@router.post("/consult", response_model=AIConsultResponse)
def consult_ai(
    payload: AIConsultRequest,
    current_user: dict = Depends(get_current_user),
    service: AIConsultationService = Depends(get_ai_service),
) -> AIConsultResponse:
    try:
        result = service.consult(
            payload.prompt,
            authenticated_role=current_user["role"],
            limit=get_rag_retrieval_top_k(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except KnowledgeRetrievalError as exc:
        logger.warning("AI consultation failed stage=embedding failure_type=%s", _knowledge_failure_type(exc))
        raise HTTPException(status_code=503, detail="Embedding service is unavailable. Verify Ollama is running.") from exc
    except AIConsultationError as exc:
        raise HTTPException(status_code=503, detail="AI service is unavailable. Verify Ollama is running.") from exc

    return AIConsultResponse(
        answer=result.answer,
        answer_basis=result.answer_basis,
        sources=[
            {"chunk_id": source.chunk_id, "source_title": source.source_title, "source_uri": source.source_uri}
            for source in result.sources
        ],
    )


@router.get("/readiness")
def readiness(_current_user: dict = RequireManager) -> dict:
    return ai_readiness()


def _knowledge_failure_type(exc: KnowledgeRetrievalError) -> str:
    cause = exc.__cause__
    if cause is None:
        return "unknown"
    name = type(cause).__name__.lower()
    if "timeout" in name:
        return "timeout"
    if "connection" in name or "connect" in name:
        return "connection error"
    if "http" in name or "status" in name:
        return "Ollama HTTP error"
    if "malformed" in name or "json" in name or "response" in name:
        return "malformed response"
    return "unknown"
