from __future__ import annotations

from dataclasses import dataclass


NOMIC_DOCUMENT_PREFIX = "search_document: "
NOMIC_QUERY_PREFIX = "search_query: "


def normalize_embedding_text(text: str) -> str:
    return " ".join(text.split())


def is_nomic_model(model: str) -> bool:
    return model.strip().lower().startswith("nomic-embed-text")


@dataclass(frozen=True)
class KnowledgeDocumentText:
    source_title: str
    content: str
    metadata: dict


def format_document_embedding_input(*, model: str, document: KnowledgeDocumentText) -> str:
    parts: list[str] = []
    title = normalize_embedding_text(document.source_title)
    if title:
        parts.append(f"כותרת: {title}")

    category = _metadata_string(document.metadata, "category")
    if category:
        parts.append(f"קטגוריה: {category}")

    activity = _metadata_string(document.metadata, "activity")
    if activity:
        parts.append(f"פעילות: {activity}")

    content = normalize_embedding_text(document.content)
    if content:
        parts.append(f"תוכן מקורי: {content}")

    enriched_text = "\n".join(parts)
    if is_nomic_model(model):
        return f"{NOMIC_DOCUMENT_PREFIX}{enriched_text}"
    return enriched_text


def format_query_embedding_input(*, model: str, query: str) -> str:
    normalized_query = normalize_embedding_text(query)
    if is_nomic_model(model):
        return f"{NOMIC_QUERY_PREFIX}{normalized_query}"
    return normalized_query


def _metadata_string(metadata: dict, key: str) -> str:
    value = metadata.get(key)
    if not isinstance(value, str):
        return ""
    return normalize_embedding_text(value)
