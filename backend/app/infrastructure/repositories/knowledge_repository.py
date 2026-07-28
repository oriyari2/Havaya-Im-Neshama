from __future__ import annotations

import json
from uuid import UUID


def insert_knowledge_chunk(
    cur,
    *,
    source_title: str,
    source_uri: str | None,
    chunk_index: int,
    content: str,
    metadata: dict,
    embedding_model: str,
    embedding: list[float],
    content_hash: str,
    created_by: UUID | str,
) -> dict:
    embedding_literal = "[" + ",".join(str(float(value)) for value in embedding) + "]"
    cur.execute(
        """
        INSERT INTO knowledge_chunks (
            source_title, source_uri, chunk_index, content, metadata,
            embedding_model, embedding_dimensions, embedding, content_hash, created_by
        )
        VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s::vector, %s, %s)
        ON CONFLICT (source_title, chunk_index, content_hash) DO UPDATE
        SET source_uri = EXCLUDED.source_uri,
            content = EXCLUDED.content,
            metadata = EXCLUDED.metadata,
            embedding_model = EXCLUDED.embedding_model,
            embedding_dimensions = EXCLUDED.embedding_dimensions,
            embedding = EXCLUDED.embedding
        RETURNING id, source_title, source_uri, chunk_index, content,
            metadata, embedding_model, embedding_dimensions, content_hash,
            created_by, created_at;
        """,
        (
            source_title,
            source_uri,
            chunk_index,
            content,
            json.dumps(metadata, ensure_ascii=False),
            embedding_model,
            len(embedding),
            embedding_literal,
            content_hash,
            created_by,
        ),
    )
    return cur.fetchone()
