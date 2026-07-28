from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.app.application.services.ai_service import AIConsultationError, AIConsultationService, get_llm_client
from backend.app.core.auth import get_current_user
from backend.app.schemas.ai import AIConsultRequest, AIConsultResponse
from rag import LLMClient


router = APIRouter(prefix="/api/ai", tags=["ai"])


def get_ai_service(llm_client: LLMClient = Depends(get_llm_client)) -> AIConsultationService:
    return AIConsultationService(llm_client)


@router.post("/consult", response_model=AIConsultResponse)
def consult_ai(
    payload: AIConsultRequest,
    _current_user: dict = Depends(get_current_user),
    service: AIConsultationService = Depends(get_ai_service),
) -> AIConsultResponse:
    try:
        answer = service.consult(payload.prompt)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AIConsultationError as exc:
        raise HTTPException(status_code=503, detail="AI service is unavailable. Verify Ollama is running.") from exc

    return AIConsultResponse(answer=answer)
