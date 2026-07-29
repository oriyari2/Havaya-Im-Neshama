from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.app.application.services.ai_service import AIConsultationError, AIConsultationService, get_llm_client
from backend.app.application.services.knowledge_retrieval_service import (
    KnowledgeRetrievalError,
    KnowledgeRetrievalService,
)
from backend.app.core.auth import get_current_user
from backend.app.core.environment import get_rag_retrieval_top_k
from backend.app.routers.knowledge import get_knowledge_retrieval_service
from backend.app.schemas.ai import AIConsultRequest, AIConsultResponse
from rag import LLMClient


router = APIRouter(prefix="/api/ai", tags=["ai"])


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
