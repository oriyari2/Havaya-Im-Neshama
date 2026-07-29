from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.app.application.services.knowledge_ingestion_service import (
    KnowledgeIngestionError,
    KnowledgeIngestionService,
    get_embedding_client,
)
from backend.app.application.services.knowledge_retrieval_service import (
    KnowledgeRetrievalError,
    KnowledgeRetrievalService,
)
from backend.app.core.environment import get_rag_retrieval_top_k
from backend.app.core.auth import require_roles
from backend.app.schemas.knowledge import (
    KnowledgeIngestRequest,
    KnowledgeIngestResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResult,
)
from rag import EmbeddingClient


router = APIRouter(prefix="/api/rag", tags=["rag"])
RequireManager = Depends(require_roles("manager"))
RequireRagSearchUser = Depends(require_roles("manager", "instructor", "customer"))


def get_knowledge_ingestion_service(
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
) -> KnowledgeIngestionService:
    return KnowledgeIngestionService(embedding_client)


def get_knowledge_retrieval_service(
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
) -> KnowledgeRetrievalService:
    return KnowledgeRetrievalService(embedding_client)


@router.post("/knowledge", response_model=KnowledgeIngestResponse, status_code=201)
def ingest_knowledge(
    payload: KnowledgeIngestRequest,
    current_user: dict = RequireManager,
    service: KnowledgeIngestionService = Depends(get_knowledge_ingestion_service),
) -> KnowledgeIngestResponse:
    try:
        result = service.ingest(payload, created_by=current_user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except KnowledgeIngestionError as exc:
        raise HTTPException(status_code=503, detail="Embedding service is unavailable. Verify Ollama is running.") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not ingest knowledge") from exc

    return KnowledgeIngestResponse(
        source_title=result.source_title,
        chunk_count=result.chunk_count,
        chunk_ids=result.chunk_ids,
    )


@router.post("/search", response_model=KnowledgeSearchResponse)
def search_knowledge(
    payload: KnowledgeSearchRequest,
    current_user: dict = RequireRagSearchUser,
    service: KnowledgeRetrievalService = Depends(get_knowledge_retrieval_service),
) -> KnowledgeSearchResponse:
    limit = payload.limit if payload.limit is not None else get_rag_retrieval_top_k()
    try:
        result = service.search(query=payload.query, authenticated_role=current_user["role"], limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except KnowledgeRetrievalError as exc:
        raise HTTPException(status_code=503, detail="Embedding service is unavailable. Verify Ollama is running.") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not search knowledge") from exc

    return KnowledgeSearchResponse(
        query=result.query,
        results=[
            KnowledgeSearchResult(
                chunk_id=item.chunk_id,
                source_title=item.source_title,
                source_uri=item.source_uri,
                chunk_index=item.chunk_index,
                content=item.content,
                metadata=item.metadata,
                distance=item.distance,
                score=item.score,
            )
            for item in result.results
        ],
    )
