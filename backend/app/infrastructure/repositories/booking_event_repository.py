from __future__ import annotations

from uuid import UUID

from psycopg.types.json import Jsonb


EVENT_COLUMNS = (
    "event_id, aggregate_id, aggregate_version, event_type, event_data, "
    "actor_user_id, occurred_at, correlation_id"
)


def append_event(
    cur,
    *,
    aggregate_id: UUID,
    aggregate_version: int,
    event_type: str,
    event_data: dict,
    actor_user_id: UUID,
    correlation_id: UUID | None,
) -> dict:
    cur.execute(
        f"""
        INSERT INTO booking_events (
            aggregate_id, aggregate_version, event_type, event_data,
            actor_user_id, correlation_id
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING {EVENT_COLUMNS};
        """,
        (
            aggregate_id,
            aggregate_version,
            event_type,
            Jsonb(event_data),
            actor_user_id,
            correlation_id,
        ),
    )
    return cur.fetchone()


def list_events(cur, aggregate_id: UUID) -> list[dict]:
    cur.execute(
        f"""
        SELECT {EVENT_COLUMNS}
        FROM booking_events
        WHERE aggregate_id = %s
        ORDER BY aggregate_version ASC;
        """,
        (aggregate_id,),
    )
    return list(cur.fetchall())


def get_current_version(cur, aggregate_id: UUID) -> int:
    cur.execute(
        """
        SELECT COALESCE(MAX(aggregate_version), 0)
        FROM booking_events
        WHERE aggregate_id = %s;
        """,
        (aggregate_id,),
    )
    return cur.fetchone()["coalesce"]
