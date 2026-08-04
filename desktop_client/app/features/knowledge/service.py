from __future__ import annotations

from pathlib import Path

from desktop_client.app.api.client import ApiClient

MAX_KNOWLEDGE_SOURCE_CONTENT_CHARS = 50000
SUPPORTED_KNOWLEDGE_SUFFIXES = {".txt", ".md"}


class KnowledgeService:
    def __init__(self, api_client: ApiClient) -> None:
        self.api_client = api_client

    def list_sources(self) -> list[dict]:
        response = self.api_client.get("/api/rag/sources")
        return response if isinstance(response, list) else []

    def invalidate_list(self) -> None:
        self.api_client.invalidate_cached_get("/api/rag/sources")

    def get_source(self, source_id: str) -> dict:
        response = self.api_client.get(f"/api/rag/sources/{source_id}")
        return response if isinstance(response, dict) else {}

    def create_text_source(self, payload: dict) -> dict:
        response = self.api_client.post("/api/rag/sources", payload)
        return response if isinstance(response, dict) else {}

    def replace_source(self, source_id: str, payload: dict) -> dict:
        response = self.api_client.put(f"/api/rag/sources/{source_id}", payload)
        return response if isinstance(response, dict) else {}

    def delete_source(self, source_id: str) -> None:
        self.api_client.delete(f"/api/rag/sources/{source_id}")

    def upload_source(self, *, title: str, category: str, activity_name: str | None, allowed_roles: list[str], path: str) -> dict:
        file_path, content = read_supported_knowledge_file(path)
        return self.create_text_source(
            {
                "title": title,
                "category": category,
                "activity_name": activity_name,
                "source_uri": file_path.name,
                "allowed_roles": allowed_roles,
                "content": content,
            }
        )

    def replace_with_file(
        self,
        source_id: str,
        *,
        title: str,
        category: str,
        activity_name: str | None,
        allowed_roles: list[str],
        path: str,
    ) -> dict:
        file_path, content = read_supported_knowledge_file(path)
        return self.replace_source(
            source_id,
            {
                "title": title,
                "category": category,
                "activity_name": activity_name,
                "source_uri": file_path.name,
                "allowed_roles": allowed_roles,
                "content": content,
            },
        )


def read_supported_knowledge_file(path: str) -> tuple[Path, str]:
    file_path = Path(path)
    if file_path.suffix.lower() not in SUPPORTED_KNOWLEDGE_SUFFIXES:
        raise ValueError("Only .txt and .md files are supported")
    content = file_path.read_text(encoding="utf-8-sig")
    if len(content) > MAX_KNOWLEDGE_SOURCE_CONTENT_CHARS:
        raise ValueError("Knowledge content must be 50,000 characters or fewer")
    if not content.strip():
        raise ValueError("Content must not be empty")
    return file_path, content
