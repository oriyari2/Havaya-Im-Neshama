from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import ValidationError

from backend.app.application.services.knowledge_ingestion_service import (
    KnowledgeIngestionError,
    KnowledgeIngestionService,
    get_embedding_client,
)
from backend.app.application.services.knowledge_retrieval_service import (
    KnowledgeRetrievalError,
    KnowledgeRetrievalService,
)
from backend.app.application.services.knowledge_management_service import (
    MAX_KNOWLEDGE_UPLOAD_CHARS,
    KnowledgeManagementError,
    KnowledgeManagementService,
)
from backend.app.core.environment import get_rag_retrieval_top_k
from backend.app.core.auth import require_roles
from backend.app.schemas.knowledge import (
    KnowledgeIngestRequest,
    KnowledgeIngestResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResult,
    KnowledgeSourceCreateRequest,
    KnowledgeSourceDetail,
    KnowledgeSourceReplaceRequest,
    KnowledgeSourceSummary,
    KnowledgeSourceWriteResponse,
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


def get_knowledge_management_service(
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
) -> KnowledgeManagementService:
    return KnowledgeManagementService(embedding_client)


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


@router.post("/sources", response_model=KnowledgeSourceWriteResponse, status_code=201)
def create_source(
    payload: KnowledgeSourceCreateRequest,
    current_user: dict = RequireManager,
    service: KnowledgeManagementService = Depends(get_knowledge_management_service),
) -> KnowledgeSourceWriteResponse:
    try:
        result = service.create(payload, created_by=current_user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except KnowledgeManagementError as exc:
        raise HTTPException(status_code=503, detail="Embedding service is unavailable. Verify Ollama is running.") from exc
    return _write_response(result)


@router.post("/sources/upload", response_model=KnowledgeSourceWriteResponse, status_code=201)
async def upload_source(
    title: str = Form(...),
    category: str = Form(...),
    activity_name: str | None = Form(default=None),
    allowed_roles: list[str] = Form(default=[]),
    file: UploadFile = File(...),
    current_user: dict = RequireManager,
    service: KnowledgeManagementService = Depends(get_knowledge_management_service),
) -> KnowledgeSourceWriteResponse:
    content = await _read_supported_text_upload(file)
    try:
        payload = KnowledgeSourceCreateRequest(
            title=title,
            content=content,
            source_uri=file.filename,
            category=category,
            activity_name=activity_name,
            allowed_roles=allowed_roles,
        )
        result = service.create(payload, created_by=current_user["id"])
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except KnowledgeManagementError as exc:
        raise HTTPException(status_code=503, detail="Embedding service is unavailable. Verify Ollama is running.") from exc
    return _write_response(result)


@router.get("/sources", response_model=list[KnowledgeSourceSummary])
def list_sources(
    current_user: dict = RequireManager,
    service: KnowledgeManagementService = Depends(get_knowledge_management_service),
) -> list[KnowledgeSourceSummary]:
    return [_summary_response(source) for source in service.list_sources()]


@router.get("/sources/{source_id}", response_model=KnowledgeSourceDetail)
def get_source(
    source_id: UUID,
    current_user: dict = RequireManager,
    service: KnowledgeManagementService = Depends(get_knowledge_management_service),
) -> KnowledgeSourceDetail:
    source = service.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Knowledge source was not found")
    return _detail_response(source)


@router.put("/sources/{source_id}", response_model=KnowledgeSourceWriteResponse)
def replace_source(
    source_id: UUID,
    payload: KnowledgeSourceReplaceRequest,
    current_user: dict = RequireManager,
    service: KnowledgeManagementService = Depends(get_knowledge_management_service),
) -> KnowledgeSourceWriteResponse:
    try:
        result = service.replace(source_id, payload, created_by=current_user["id"])
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except KnowledgeManagementError as exc:
        raise HTTPException(status_code=503, detail="Embedding service is unavailable. Verify Ollama is running.") from exc
    return _write_response(result)


@router.delete("/sources/{source_id}", status_code=204, response_class=Response)
def delete_source(
    source_id: UUID,
    current_user: dict = RequireManager,
    service: KnowledgeManagementService = Depends(get_knowledge_management_service),
):
    try:
        service.delete(source_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


async def _read_supported_text_upload(file: UploadFile) -> str:
    filename = (file.filename or "").lower()
    if not (filename.endswith(".txt") or filename.endswith(".md")):
        raise HTTPException(status_code=422, detail="Only .txt and .md uploads are supported")
    content = await file.read((MAX_KNOWLEDGE_UPLOAD_CHARS * 4) + 1)
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="Uploaded file must be UTF-8 text") from exc
    if len(text) > MAX_KNOWLEDGE_UPLOAD_CHARS:
        raise HTTPException(status_code=413, detail="Uploaded file is too large")
    if not text.strip():
        raise HTTPException(status_code=422, detail="Content must not be empty")
    return text


def _summary_response(source) -> KnowledgeSourceSummary:
    return KnowledgeSourceSummary(
        source_id=source.source_id,
        title=source.title,
        source_uri=source.source_uri,
        category=source.category,
        activity_name=source.activity_name,
        allowed_roles=source.allowed_roles,
        chunk_count=source.chunk_count,
        created_by=source.created_by,
        created_at=source.created_at,
        updated_at=source.updated_at,
    )


def _detail_response(source) -> KnowledgeSourceDetail:
    return KnowledgeSourceDetail(**_summary_response(source).model_dump(), content=source.content)


def _write_response(result) -> KnowledgeSourceWriteResponse:
    return KnowledgeSourceWriteResponse(source=_detail_response(result.source), chunk_ids=result.chunk_ids)
