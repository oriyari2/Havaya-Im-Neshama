from __future__ import annotations


def search_knowledge_chunks(
    cur,
    *,
    query_embedding: list[float],
    authenticated_role: str,
    embedding_model: str,
    embedding_dimensions: int,
    limit: int,
    max_cosine_distance: float,
) -> list[dict]:
    embedding_literal = "[" + ",".join(str(float(value)) for value in query_embedding) + "]"
    bounded_limit = max(1, min(int(limit), 10))
    cur.execute(
        """
        SELECT id AS chunk_id,
            source_title,
            source_uri,
            chunk_index,
            content,
            metadata,
            embedding <=> %s::vector AS distance
        FROM knowledge_chunks
        WHERE embedding_model = %s
            AND embedding_dimensions = %s
            AND (
                %s = 'manager'
                OR (
                    jsonb_typeof(metadata -> 'allowed_roles') = 'array'
                    AND metadata -> 'allowed_roles' ? %s
                )
            )
            AND embedding <=> %s::vector <= %s
        ORDER BY embedding <=> %s::vector ASC
        LIMIT %s;
        """,
        (
            embedding_literal,
            embedding_model,
            embedding_dimensions,
            authenticated_role,
            authenticated_role,
            embedding_literal,
            max_cosine_distance,
            embedding_literal,
            bounded_limit,
        ),
    )
    return list(cur.fetchall())
