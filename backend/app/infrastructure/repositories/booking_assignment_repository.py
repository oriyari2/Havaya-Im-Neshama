from datetime import datetime
from uuid import UUID


def get_header(cur, booking_id: UUID):
    cur.execute(
        "SELECT id AS booking_id, version, requires_instructor FROM bookings WHERE id=%s;",
        (booking_id,),
    )
    return cur.fetchone()


def list_activities(cur, booking_id: UUID):
    cur.execute(
        """
        SELECT
            ba.id AS booking_activity_id,
            ba.activity_id,
            a.name AS activity_name,
            (
                b.requires_instructor
                AND b.status IN ('NEW','CONFIRMED')
                AND b.event_at >= now()
                AND NOT EXISTS (
                    SELECT 1
                    FROM booking_instructors bi
                    WHERE bi.booking_activity_id = ba.id AND bi.active = true
                )
            ) AS assignment_required
        FROM booking_activities ba
        JOIN bookings b ON b.id = ba.booking_id
        JOIN activities a ON a.id = ba.activity_id
        WHERE ba.booking_id = %s
        ORDER BY ba.sort_order, ba.created_at, ba.id;
        """,
        (booking_id,),
    )
    return list(cur.fetchall())


def list_active_assignments(cur, booking_id: UUID):
    cur.execute(
        """
        SELECT
            bi.booking_activity_id,
            bi.instructor_id,
            i.full_name AS instructor_name,
            i.city AS instructor_city,
            bi.assigned_at
        FROM booking_instructors bi
        JOIN booking_activities ba ON ba.id = bi.booking_activity_id
        JOIN instructors i ON i.id = bi.instructor_id
        WHERE ba.booking_id = %s AND bi.active=true
        ORDER BY bi.booking_activity_id, i.full_name, i.id;
        """,
        (booking_id,),
    )
    return list(cur.fetchall())


def list_pending_requests(cur, booking_id: UUID):
    cur.execute(
        """
        SELECT
            bar.id AS request_id,
            bar.booking_activity_id,
            bar.instructor_id,
            i.full_name AS instructor_name,
            i.city AS instructor_city,
            bar.status,
            bar.requested_at
        FROM booking_assignment_requests bar
        JOIN booking_activities ba ON ba.id = bar.booking_activity_id
        JOIN instructors i ON i.id = bar.instructor_id
        WHERE ba.booking_id = %s
          AND bar.status = 'PENDING'
          AND NOT EXISTS (
              SELECT 1
              FROM booking_instructors bi
              WHERE bi.booking_activity_id = bar.booking_activity_id
                AND bi.active = true
          )
        ORDER BY bar.booking_activity_id, bar.requested_at, i.full_name, i.id;
        """,
        (booking_id,),
    )
    return list(cur.fetchall())


def _customer_contact_sql() -> str:
    return """
        LEFT JOIN LATERAL (
            SELECT cc.full_name, cc.phone
            FROM customer_contacts cc
            WHERE cc.customer_id = c.id AND cc.is_active = true
            ORDER BY cc.is_primary DESC, cc.created_at ASC, cc.id ASC
            LIMIT 1
        ) contact ON true
    """


def get_open_event_header(cur, booking_id: UUID, now: datetime):
    cur.execute(
        f"""
        SELECT
            b.id AS booking_id,
            b.event_at,
            b.city,
            b.venue,
            b.status,
            b.requires_instructor,
            b.version,
            c.name AS customer_name,
            contact.full_name AS customer_contact_name,
            COALESCE(contact.phone, c.phone) AS customer_phone
        FROM bookings b
        JOIN customers c ON c.id = b.customer_id
        {_customer_contact_sql()}
        WHERE b.id = %s
          AND b.event_at >= %s
          AND b.status IN ('NEW','CONFIRMED')
          AND b.requires_instructor = true
          AND EXISTS (
              SELECT 1
              FROM booking_activities ba
              WHERE ba.booking_id = b.id
                AND NOT EXISTS (
                    SELECT 1
                    FROM booking_instructors bi
                    WHERE bi.booking_activity_id = ba.id AND bi.active = true
                )
          );
        """,
        (booking_id, now),
    )
    return cur.fetchone()


def list_my_request_states(cur, booking_id: UUID, instructor_id: UUID) -> dict[UUID, dict]:
    cur.execute(
        """
        SELECT bar.id AS request_id, bar.booking_activity_id, bar.status, bar.requested_at
        FROM booking_assignment_requests bar
        JOIN booking_activities ba ON ba.id = bar.booking_activity_id
        WHERE ba.booking_id = %s AND bar.instructor_id = %s;
        """,
        (booking_id, instructor_id),
    )
    return {row["booking_activity_id"]: row for row in cur.fetchall()}


def get_requestable_activity(cur, booking_id: UUID, booking_activity_id: UUID, now: datetime):
    cur.execute(
        """
        SELECT ba.id AS booking_activity_id
        FROM booking_activities ba
        JOIN bookings b ON b.id = ba.booking_id
        WHERE ba.id = %s
          AND ba.booking_id = %s
          AND b.event_at >= %s
          AND b.status IN ('NEW','CONFIRMED')
          AND b.requires_instructor = true
          AND NOT EXISTS (
              SELECT 1
              FROM booking_instructors bi
              WHERE bi.booking_activity_id = ba.id AND bi.active = true
          );
        """,
        (booking_activity_id, booking_id, now),
    )
    return cur.fetchone()


def instructor_is_active(cur, instructor_id: UUID) -> bool:
    cur.execute("SELECT is_active FROM instructors WHERE id = %s;", (instructor_id,))
    row = cur.fetchone()
    return bool(row and row["is_active"])


def upsert_assignment_request(cur, booking_activity_id: UUID, instructor_id: UUID):
    cur.execute(
        """
        INSERT INTO booking_assignment_requests (
            booking_activity_id, instructor_id, status, requested_at, decided_at, decided_by
        )
        VALUES (%s, %s, 'PENDING', now(), NULL, NULL)
        ON CONFLICT (booking_activity_id, instructor_id) DO UPDATE SET
            status = 'PENDING',
            requested_at = CASE
                WHEN booking_assignment_requests.status = 'PENDING'
                    THEN booking_assignment_requests.requested_at
                ELSE now()
            END,
            decided_at = NULL,
            decided_by = NULL,
            updated_at = now()
        RETURNING id AS request_id, booking_activity_id, instructor_id, status, requested_at;
        """,
        (booking_activity_id, instructor_id),
    )
    return cur.fetchone()


def get_request_for_manager(cur, booking_id: UUID, request_id: UUID):
    cur.execute(
        """
        SELECT
            bar.id AS request_id,
            bar.booking_activity_id,
            bar.instructor_id,
            bar.status,
            b.version
        FROM booking_assignment_requests bar
        JOIN booking_activities ba ON ba.id = bar.booking_activity_id
        JOIN bookings b ON b.id = ba.booking_id
        WHERE bar.id = %s AND ba.booking_id = %s;
        """,
        (request_id, booking_id),
    )
    return cur.fetchone()


def resolve_approved_request(cur, booking_activity_id: UUID, instructor_id: UUID, decided_by: UUID) -> None:
    cur.execute(
        """
        UPDATE booking_assignment_requests
        SET
            status = CASE WHEN instructor_id = %s THEN 'APPROVED' ELSE 'REJECTED' END,
            decided_at = now(),
            decided_by = %s,
            updated_at = now()
        WHERE booking_activity_id = %s AND status = 'PENDING';
        """,
        (instructor_id, decided_by, booking_activity_id),
    )


def reject_request(cur, booking_id: UUID, request_id: UUID, decided_by: UUID):
    cur.execute(
        """
        UPDATE booking_assignment_requests bar
        SET status = 'REJECTED', decided_at = now(), decided_by = %s, updated_at = now()
        FROM booking_activities ba
        WHERE bar.id = %s
          AND bar.booking_activity_id = ba.id
          AND ba.booking_id = %s
          AND bar.status = 'PENDING'
        RETURNING bar.id AS request_id, bar.booking_activity_id, bar.instructor_id,
                  bar.status, bar.requested_at;
        """,
        (decided_by, request_id, booking_id),
    )
    return cur.fetchone()
