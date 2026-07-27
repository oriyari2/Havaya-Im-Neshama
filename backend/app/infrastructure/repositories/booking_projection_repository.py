from __future__ import annotations

from uuid import UUID


BOOKING_COLUMNS = (
    "id, customer_id, activity_id, event_at, city, venue, participant_count, "
    "agreed_price, status, requires_instructor, notes, version, created_at, updated_at"
)


def customer_is_active(cur, customer_id: UUID) -> bool:
    cur.execute("SELECT is_active FROM customers WHERE id = %s;", (customer_id,))
    row = cur.fetchone()
    return bool(row and row["is_active"])


def activity_is_active(cur, activity_id: UUID) -> bool:
    cur.execute("SELECT is_active FROM activities WHERE id = %s;", (activity_id,))
    row = cur.fetchone()
    return bool(row and row["is_active"])


def instructor_is_active(cur, instructor_id: UUID) -> bool:
    cur.execute("SELECT is_active FROM instructors WHERE id = %s;", (instructor_id,))
    row = cur.fetchone()
    return bool(row and row["is_active"])


def booking_activity_belongs_to_booking(cur, booking_activity_id: UUID, booking_id: UUID) -> bool:
    cur.execute(
        "SELECT 1 FROM booking_activities WHERE id = %s AND booking_id = %s;",
        (booking_activity_id, booking_id),
    )
    return cur.fetchone() is not None


def upsert_projection(cur, data: dict) -> dict:
    cur.execute(
        f"""
        INSERT INTO bookings (
            id, customer_id, activity_id, event_at, city, venue, participant_count,
            agreed_price, status, requires_instructor, notes, version
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            customer_id = EXCLUDED.customer_id,
            activity_id = EXCLUDED.activity_id,
            event_at = EXCLUDED.event_at,
            city = EXCLUDED.city,
            venue = EXCLUDED.venue,
            participant_count = EXCLUDED.participant_count,
            agreed_price = EXCLUDED.agreed_price,
            status = EXCLUDED.status,
            requires_instructor = EXCLUDED.requires_instructor,
            notes = EXCLUDED.notes,
            version = EXCLUDED.version,
            updated_at = now()
        RETURNING {BOOKING_COLUMNS};
        """,
        (
            data["id"],
            data["customer_id"],
            data["activity_id"],
            data["event_at"],
            data["city"],
            data["venue"],
            data["participant_count"],
            data["agreed_price"],
            data["status"],
            data["requires_instructor"],
            data["notes"],
            data["version"],
        ),
    )
    return cur.fetchone()


def get_booking(cur, booking_id: UUID) -> dict | None:
    cur.execute(f"SELECT {BOOKING_COLUMNS} FROM bookings WHERE id = %s;", (booking_id,))
    return cur.fetchone()


def list_bookings(cur, customer_id: UUID | None, status: str | None, limit: int, offset: int) -> list[dict]:
    clauses: list[str] = []
    params: list[object] = []
    if customer_id is not None:
        clauses.append("customer_id = %s")
        params.append(customer_id)
    if status is not None:
        clauses.append("status = %s")
        params.append(status)
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    cur.execute(
        f"""
        SELECT {BOOKING_COLUMNS}
        FROM bookings
        {where_sql}
        ORDER BY event_at ASC, created_at ASC
        LIMIT %s OFFSET %s;
        """,
        [*params, limit, offset],
    )
    return list(cur.fetchall())


def sync_instructor_projection(cur, booking_id: UUID, active_assignments: set[tuple[UUID, UUID]]) -> None:
    active_activity_ids = [assignment[0] for assignment in active_assignments]
    active_instructor_ids = [assignment[1] for assignment in active_assignments]
    cur.execute(
        """
        UPDATE booking_instructors
        SET active = false, removed_at = COALESCE(removed_at, now()), updated_at = now()
        WHERE booking_activity_id IN (
            SELECT id FROM booking_activities WHERE booking_id = %s
        )
        AND active = true
        AND NOT EXISTS (
            SELECT 1
            FROM unnest(%s::uuid[], %s::uuid[]) AS active_pair(activity_id, instructor_id)
            WHERE active_pair.activity_id = booking_instructors.booking_activity_id
            AND active_pair.instructor_id = booking_instructors.instructor_id
        );
        """,
        (booking_id, active_activity_ids, active_instructor_ids),
    )
    for booking_activity_id, instructor_id in active_assignments:
        cur.execute(
            """
            INSERT INTO booking_instructors (booking_activity_id, instructor_id, assigned_at, active)
            VALUES (%s, %s, now(), true)
            ON CONFLICT (booking_activity_id, instructor_id) DO UPDATE SET
                assigned_at = now(),
                active = true,
                removed_at = NULL,
                updated_at = now();
            """,
            (booking_activity_id, instructor_id),
        )
