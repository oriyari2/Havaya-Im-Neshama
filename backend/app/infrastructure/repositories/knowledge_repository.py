from __future__ import annotations

import json
from uuid import UUID


MANAGED_SOURCE_ID_SQL = """
jsonb_typeof(metadata -> 'source_id') = 'string'
AND (metadata ->> 'source_id') ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
"""

TASK16_DEMO_KNOWLEDGE_SQL = """
(
    source_uri LIKE 'demo://knowledge/%'
    OR source_title IN (
        'Task16 Demo Equipment',
        'Task16 Demo Preparation',
        'Task16 Demo Arrival',
        'Task16 Demo Pricing',
        'Task16 Demo Activity',
        'Task16 Demo Proposal',
        'Task16 Demo Policy',
        'Task16 Demo Instructor Internal'
    )
    OR metadata ->> 'demo_task' = 'task16'
    OR metadata ->> 'task16_demo' = 'true'
)
"""


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


def list_logical_sources(cur) -> list[dict]:
    cur.execute(
        f"""
        SELECT (metadata ->> 'source_id')::uuid AS source_id,
            max(source_title) AS title,
            max(source_uri) AS source_uri,
            max(metadata ->> 'category') AS category,
            max(metadata ->> 'activity_name') AS activity_name,
            (array_agg(metadata -> 'allowed_roles' ORDER BY chunk_index))[1] AS allowed_roles,
            count(*)::integer AS chunk_count,
            (array_agg(created_by ORDER BY chunk_index))[1] AS created_by,
            min(created_at) AS created_at,
            max(created_at) AS updated_at
        FROM knowledge_chunks
        WHERE {MANAGED_SOURCE_ID_SQL}
        GROUP BY metadata ->> 'source_id'
        ORDER BY max(created_at) DESC;
        """,
        (),
    )
    return list(cur.fetchall())


def get_logical_source(cur, *, source_id: UUID) -> dict | None:
    cur.execute(
        """
        SELECT (metadata ->> 'source_id')::uuid AS source_id,
            max(source_title) AS title,
            max(source_uri) AS source_uri,
            max(metadata ->> 'category') AS category,
            max(metadata ->> 'activity_name') AS activity_name,
            (array_agg(metadata -> 'allowed_roles' ORDER BY chunk_index))[1] AS allowed_roles,
            count(*)::integer AS chunk_count,
            (array_agg(created_by ORDER BY chunk_index))[1] AS created_by,
            min(created_at) AS created_at,
            max(created_at) AS updated_at,
            max(metadata ->> 'original_content') AS content
        FROM knowledge_chunks
        WHERE metadata ->> 'source_id' = %s
        GROUP BY metadata ->> 'source_id';
        """,
        (str(source_id),),
    )
    return cur.fetchone()


def delete_source_chunks(cur, *, source_id: UUID) -> list[dict]:
    cur.execute(
        """
        DELETE FROM knowledge_chunks
        WHERE metadata ->> 'source_id' = %s
        RETURNING id;
        """,
        (str(source_id),),
    )
    return list(cur.fetchall())


def delete_task16_demo_chunks(cur) -> list[dict]:
    cur.execute(
        f"""
        DELETE FROM knowledge_chunks
        WHERE ({MANAGED_SOURCE_ID_SQL}) IS NOT TRUE
        AND {TASK16_DEMO_KNOWLEDGE_SQL}
        RETURNING id;
        """,
        (),
    )
    return list(cur.fetchall())
