from __future__ import annotations

from uuid import UUID

from backend.app.domain.bookings.status import BookingStatus


BOOKING_COLUMNS = (
    "id, customer_id, activity_id, event_at, city, venue, participant_count, "
    "agreed_price, status, requires_instructor, notes, version, created_at, updated_at"
)

BOOKING_QUERY_COLUMNS = (
    "b.id, b.customer_id, b.activity_id, b.event_at, b.city, b.venue, "
    "b.participant_count, b.agreed_price, b.status, b.requires_instructor, "
    "b.notes, b.version, b.created_at, b.updated_at, "
    "c.name AS customer_name, "
    "(SELECT cc.full_name FROM customer_contacts cc "
    " WHERE cc.customer_id = c.id AND cc.is_active = true "
    " ORDER BY cc.is_primary DESC, cc.created_at ASC, cc.id ASC LIMIT 1) AS customer_contact_name, "
    "COALESCE((SELECT cc.phone FROM customer_contacts cc "
    " WHERE cc.customer_id = c.id AND cc.is_active = true "
    " ORDER BY cc.is_primary DESC, cc.created_at ASC, cc.id ASC LIMIT 1), c.phone) AS customer_phone, "
    "a.name AS activity_name"
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

def upsert_default_booking_activity(cur,booking_activity_id,booking_id,activity_id,event_at,participant_count)->None:
    cur.execute("""INSERT INTO booking_activities (id,booking_id,activity_id,start_time,participants_count,sort_order) VALUES (%s,%s,%s,%s,%s,1) ON CONFLICT (id) DO UPDATE SET activity_id=EXCLUDED.activity_id,start_time=EXCLUDED.start_time,participants_count=EXCLUDED.participants_count,updated_at=now();""",(booking_activity_id,booking_id,activity_id,event_at,participant_count))


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


def booking_exists(cur, booking_id: UUID) -> bool:
    cur.execute("SELECT 1 FROM bookings WHERE id = %s;", (booking_id,))
    return cur.fetchone() is not None


def _visibility_filter(
    role: str,
    customer_id: UUID | None,
    instructor_id: UUID | None,
    *,
    booking_alias: str,
) -> tuple[str, list[object]]:
    if role == "manager":
        return "", []
    if role == "customer":
        return f"AND {booking_alias}.customer_id = %s", [customer_id]
    if role == "instructor":
        return (
            f"""
            AND EXISTS (
                SELECT 1
                FROM booking_activities ba
                JOIN booking_instructors bi ON bi.booking_activity_id = ba.id
                WHERE ba.booking_id = {booking_alias}.id
                  AND bi.instructor_id = %s
                  AND bi.active = true
            )
            """,
            [instructor_id],
        )
    return "AND FALSE", []


def get_booking(
    cur,
    booking_id: UUID,
    *,
    role: str | None = None,
    customer_id: UUID | None = None,
    instructor_id: UUID | None = None,
) -> dict | None:
    role_name = role or "manager"
    visibility_sql, visibility_params = _visibility_filter(
        role_name,
        customer_id,
        instructor_id,
        booking_alias="b",
    )
    params: list[object] = [booking_id, *visibility_params]
    cur.execute(
        f"""
        SELECT {BOOKING_QUERY_COLUMNS}
        FROM bookings b
        JOIN customers c ON c.id = b.customer_id
        JOIN activities a ON a.id = b.activity_id
        WHERE b.id = %s
        {visibility_sql}
        ;
        """,
        params,
    )
    return cur.fetchone()


def list_bookings(
    cur,
    *,
    role: str | None = None,
    customer_id: UUID | None = None,
    instructor_id: UUID | None = None,
    customer_filter_id: UUID | None = None,
    instructor_filter_id: UUID | list[UUID] | None = None,
    activity_id: UUID | list[UUID] | None = None,
    status: str | list[str] | None = None,
    assignment_state: str | list[str] | None = None,
    from_date: object | None = None,
    to_date: object | None = None,
    order_by: str = "event_at",
    limit: int,
    offset: int,
) -> list[dict]:
    role_name = role or "manager"
    visibility_sql, visibility_params = _visibility_filter(
        role_name,
        customer_id,
        instructor_id,
        booking_alias="b",
    )
    params: list[object] = [*visibility_params]
    filters: list[str] = []

    if customer_filter_id is not None:
        filters.append("AND b.customer_id = %s")
        params.append(customer_filter_id)
    if instructor_filter_id is not None:
        instructor_ids = instructor_filter_id if isinstance(instructor_filter_id, list) else [instructor_filter_id]
        filters.append("AND EXISTS (SELECT 1 FROM booking_activities ba JOIN booking_instructors bi ON bi.booking_activity_id = ba.id WHERE ba.booking_id = b.id AND bi.instructor_id = ANY(%s) AND bi.active = true)")
        params.append(instructor_ids)
    if activity_id is not None:
        activity_ids = activity_id if isinstance(activity_id, list) else [activity_id]
        filters.append("AND b.activity_id = ANY(%s)")
        params.append(activity_ids)
    if status is not None:
        statuses = status if isinstance(status, list) else [status]
        filters.append("AND b.status = ANY(%s)")
        params.append(statuses)
    if assignment_state is not None:
        states = assignment_state if isinstance(assignment_state, list) else [assignment_state]
        assignment_clauses = []
        if "assigned" in states:
            # Match the dashboard's assigned bucket exactly: every activity in
            # an instructor-required booking must have an active instructor.
            assignment_clauses.append(
                "(b.requires_instructor = true "
                "AND EXISTS (SELECT 1 FROM booking_activities ba WHERE ba.booking_id = b.id) "
                "AND NOT EXISTS ("
                "SELECT 1 FROM booking_activities ba "
                "WHERE ba.booking_id = b.id "
                "AND NOT EXISTS (SELECT 1 FROM booking_instructors bi WHERE bi.booking_activity_id = ba.id AND bi.active = true)"
                "))"
            )
        if "unassigned" in states:
            # A booking belongs to the unassigned bucket when at least one of
            # its activities is still missing an active instructor, including
            # partially staffed multi-activity bookings.
            assignment_clauses.append(
                "(b.requires_instructor = true AND EXISTS ("
                "SELECT 1 FROM booking_activities ba "
                "WHERE ba.booking_id = b.id "
                "AND NOT EXISTS (SELECT 1 FROM booking_instructors bi WHERE bi.booking_activity_id = ba.id AND bi.active = true)"
                "))"
            )
        if assignment_clauses:
            filters.append("AND (" + " OR ".join(assignment_clauses) + ")")
    if from_date is not None:
        filters.append("AND b.event_at >= %s")
        params.append(from_date)
    if to_date is not None:
        filters.append("AND b.event_at <= %s")
        params.append(to_date)

    order_sql = {
        "event_at": "b.event_at ASC, b.created_at ASC",
        "event_at_desc": "b.event_at DESC, b.created_at DESC",
        "customer_name": "c.name ASC, b.event_at ASC, b.created_at ASC",
    }.get(order_by)
    if order_sql is None:
        raise ValueError("unsupported booking order")
    filter_sql = "\n".join(filters)
    cur.execute(
        f"""
        SELECT {BOOKING_QUERY_COLUMNS}
        FROM bookings b
        JOIN customers c ON c.id = b.customer_id
        JOIN activities a ON a.id = b.activity_id
        WHERE 1 = 1
        {visibility_sql}
        {filter_sql}
        ORDER BY {order_sql}
        LIMIT %s OFFSET %s;
        """,
        [*params, limit, offset],
    )
    return list(cur.fetchall())


def get_dashboard_summary(cur, *, role: str, customer_id: UUID | None, instructor_id: UUID | None, now: object) -> dict:
    visibility_sql, visibility_params = _visibility_filter(
        role,
        customer_id,
        instructor_id,
        booking_alias="b",
    )
    params: list[object] = [
        BookingStatus.CONFIRMED.value,
        now,
        BookingStatus.NEW.value,
        now,
        BookingStatus.CANCELLED.value,
        now,
        now,
        now,
        now,
        *visibility_params,
    ]
    cur.execute(
        f"""
        SELECT
            COUNT(*) FILTER (WHERE status = %s AND event_at >= %s) AS confirmed_count,
            COUNT(*) FILTER (WHERE status = %s AND event_at >= %s) AS pending_count,
            COUNT(*) FILTER (WHERE status = %s AND event_at >= %s) AS cancelled_count,
            COUNT(*) FILTER (WHERE event_at >= %s) AS upcoming_count,
            COUNT(*) FILTER (
                WHERE event_at >= %s
                  AND requires_instructor = true
                  AND EXISTS (SELECT 1 FROM booking_activities ba WHERE ba.booking_id = b.id)
                  AND NOT EXISTS (
                      SELECT 1
                      FROM booking_activities ba
                      WHERE ba.booking_id = b.id
                        AND NOT EXISTS (
                            SELECT 1 FROM booking_instructors bi
                            WHERE bi.booking_activity_id = ba.id AND bi.active = true
                        )
                  )
            ) AS assigned_count,
            COUNT(*) FILTER (
                WHERE event_at >= %s
                  AND requires_instructor = true
                  AND EXISTS (
                      SELECT 1
                      FROM booking_activities ba
                      WHERE ba.booking_id = b.id
                        AND NOT EXISTS (
                            SELECT 1 FROM booking_instructors bi
                            WHERE bi.booking_activity_id = ba.id AND bi.active = true
                        )
                  )
            ) AS unassigned_count
        FROM bookings b
        WHERE 1 = 1
        {visibility_sql};
        """,
        params,
    )
    return dict(cur.fetchone() or {})


def get_yearly_event_trend(
    cur,
    *,
    role: str,
    customer_id: UUID | None,
    instructor_id: UUID | None,
    year: int,
    current_year: int,
) -> dict:
    """Return a complete 12-month projection and scoped selectable years."""
    visibility_sql, visibility_params = _visibility_filter(
        role,
        customer_id,
        instructor_id,
        booking_alias="b",
    )
    cur.execute(
        f"""
        WITH visible_bookings AS (
            SELECT b.event_at
            FROM bookings b
            WHERE 1 = 1
            {visibility_sql}
        ),
        requested_months AS (
            SELECT generate_series(1, 12) AS month
        ),
        monthly_counts AS (
            SELECT EXTRACT(MONTH FROM event_at)::integer AS month, COUNT(*)::integer AS count
            FROM visible_bookings
            WHERE EXTRACT(YEAR FROM event_at)::integer = %s
            GROUP BY EXTRACT(MONTH FROM event_at)::integer
        ),
        available_years AS (
            SELECT DISTINCT EXTRACT(YEAR FROM event_at)::integer AS year
            FROM visible_bookings
            UNION SELECT %s
        )
        SELECT
            (SELECT json_agg(json_build_object('month', m.month, 'count', COALESCE(c.count, 0)) ORDER BY m.month)
             FROM requested_months m LEFT JOIN monthly_counts c ON c.month = m.month) AS months,
            (SELECT array_agg(y.year ORDER BY y.year) FROM available_years y) AS available_years;
        """,
        [*visibility_params, year, current_year],
    )
    row = dict(cur.fetchone() or {})
    return {
        "year": year,
        "available_years": list(row.get("available_years") or [current_year]),
        "months": list(row.get("months") or [{"month": month, "count": 0} for month in range(1, 13)]),
    }


def get_open_events(cur, *, role: str, customer_id: UUID | None, instructor_id: UUID | None, now: object) -> list[dict]:
    if role not in {"manager", "instructor"}:
        return []
    params: list[object] = [instructor_id, now]
    cur.execute(
        f"""
        SELECT
            b.id,
            c.name AS customer_name,
            open_activity.activity_id,
            open_activity.booking_activity_id,
            open_activity.my_request_status,
            open_activity.activity_name,
            b.event_at,
            b.city,
            b.venue,
            b.status,
            b.requires_instructor,
            b.version,
            b.created_at,
            b.updated_at
        FROM bookings b
        JOIN customers c ON c.id = b.customer_id
        JOIN LATERAL (
            SELECT
                ba.id AS booking_activity_id,
                ba.activity_id,
                a.name AS activity_name,
                bar.status AS my_request_status
            FROM booking_activities ba
            JOIN activities a ON a.id = ba.activity_id
            LEFT JOIN booking_assignment_requests bar
              ON bar.booking_activity_id = ba.id
             AND bar.instructor_id = %s
            WHERE ba.booking_id = b.id
              AND NOT EXISTS (
                  SELECT 1
                  FROM booking_instructors bi
                  WHERE bi.booking_activity_id = ba.id
                    AND bi.active = true
              )
            ORDER BY ba.sort_order, ba.created_at, ba.id
            LIMIT 1
        ) open_activity ON true
        WHERE 1 = 1
        AND b.event_at >= %s
        AND b.status IN ('NEW', 'CONFIRMED')
        AND b.requires_instructor = true
        ORDER BY b.event_at ASC, b.created_at ASC;
        """,
        params,
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
