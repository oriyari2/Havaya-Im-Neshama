from __future__ import annotations

from uuid import UUID


ACTIVITY_COLUMNS = (
    "id, name, description, target_audience, "
    "COALESCE(duration_minutes, default_duration_minutes) AS duration_minutes, "
    "COALESCE(recommended_capacity, max_participants) AS recommended_capacity, "
    "COALESCE(pricing_rule, price_notes) AS pricing_rule, "
    "required_equipment, preparation_notes, season, tags, "
    "is_active, created_at, updated_at, "
    """
    (
        SELECT jsonb_build_object(
            'id', ai.id,
            'activity_id', ai.activity_id,
            'public_id', ai.public_id,
            'secure_url', ai.secure_url,
            'original_filename', ai.original_filename,
            'content_type', ai.content_type,
            'width', ai.width,
            'height', ai.height,
            'bytes', ai.bytes,
            'is_primary', ai.is_primary,
            'created_at', ai.created_at,
            'updated_at', ai.updated_at
        )
        FROM activity_images ai
        WHERE ai.activity_id = activities.id
        ORDER BY ai.is_primary DESC, ai.created_at ASC, ai.id ASC
        LIMIT 1
    ) AS primary_image
    """
)
ACTIVITY_UPDATE_FIELDS = [
    "name",
    "description",
    "target_audience",
    "duration_minutes",
    "recommended_capacity",
    "pricing_rule",
    "required_equipment",
    "preparation_notes",
    "season",
    "tags",
    "is_active",
]


def list_activities(
    cur,
    search: str | None,
    target_audience: str | None,
    season: str | None,
    tag: str | None,
    is_active: bool | None,
    limit: int,
    offset: int,
    order_by: str = "name",
) -> list[dict]:
    clauses: list[str] = []
    params: list[object] = []

    if is_active is not None:
        clauses.append("is_active = %s")
        params.append(is_active)

    cleaned_search = search.strip() if search else None
    if cleaned_search:
        clauses.append(
            "(name ILIKE %s OR description ILIKE %s OR target_audience ILIKE %s OR "
            "pricing_rule ILIKE %s OR price_notes ILIKE %s OR required_equipment ILIKE %s OR "
            "preparation_notes ILIKE %s OR season ILIKE %s OR tags ILIKE %s)"
        )
        search_param = f"%{cleaned_search}%"
        params.extend([search_param] * 9)

    cleaned_target_audience = target_audience.strip() if target_audience else None
    if cleaned_target_audience:
        clauses.append("target_audience ILIKE %s")
        params.append(f"%{cleaned_target_audience}%")

    cleaned_season = season.strip() if season else None
    if cleaned_season:
        clauses.append("season ILIKE %s")
        params.append(f"%{cleaned_season}%")

    cleaned_tag = tag.strip() if tag else None
    if cleaned_tag:
        clauses.append("tags ILIKE %s")
        params.append(f"%{cleaned_tag}%")

    order_sql = {"name": "name ASC, id ASC", "duration_minutes": "COALESCE(duration_minutes, default_duration_minutes) ASC NULLS LAST, name ASC, id ASC"}.get(order_by)
    if order_sql is None:
        raise ValueError("unsupported activity order")
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    cur.execute(
        f"""
        SELECT {ACTIVITY_COLUMNS}
        FROM activities
        {where_sql}
        ORDER BY {order_sql}
        LIMIT %s OFFSET %s;
        """,
        [*params, limit, offset],
    )
    return list(cur.fetchall())


def get_activity(cur, activity_id: UUID) -> dict | None:
    cur.execute(f"SELECT {ACTIVITY_COLUMNS} FROM activities WHERE id = %s;", (activity_id,))
    return cur.fetchone()


def create_activity(cur, data: dict) -> dict:
    cur.execute(
        f"""
        INSERT INTO activities (
            name, description, target_audience, duration_minutes,
            recommended_capacity, pricing_rule, required_equipment,
            preparation_notes, season, tags, is_active
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING {ACTIVITY_COLUMNS};
        """,
        (
            data["name"],
            data["description"],
            data["target_audience"],
            data["duration_minutes"],
            data["recommended_capacity"],
            data["pricing_rule"],
            data["required_equipment"],
            data["preparation_notes"],
            data["season"],
            data["tags"],
            data["is_active"],
        ),
    )
    return cur.fetchone()


def update_activity(cur, activity_id: UUID, data: dict) -> dict:
    assignments = [f"{field} = %s" for field in ACTIVITY_UPDATE_FIELDS if field in data]
    params = [data[field] for field in ACTIVITY_UPDATE_FIELDS if field in data]
    cur.execute(
        f"""
        UPDATE activities
        SET {', '.join(assignments)}, updated_at = now()
        WHERE id = %s
        RETURNING {ACTIVITY_COLUMNS};
        """,
        [*params, activity_id],
    )
    return cur.fetchone()


def soft_delete_activity(cur, activity_id: UUID) -> dict:
    cur.execute(
        f"""
        UPDATE activities
        SET is_active = false, updated_at = now()
        WHERE id = %s
        RETURNING {ACTIVITY_COLUMNS};
        """,
        (activity_id,),
    )
    return cur.fetchone()
