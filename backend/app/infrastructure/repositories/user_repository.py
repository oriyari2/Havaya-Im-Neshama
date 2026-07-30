from __future__ import annotations

from uuid import UUID


USER_COLUMNS = (
    "id, email, password_hash, role, display_name, is_active, customer_id, instructor_id, "
    "created_at, updated_at"
)

SAFE_USER_COLUMNS = (
    "u.id, u.email, u.role, u.display_name, u.is_active, u.customer_id, c.name AS customer_name, "
    "c.email AS customer_email, cc.full_name AS contact_name, cc.phone AS contact_phone, "
    "u.instructor_id, i.full_name AS instructor_name, i.email AS instructor_email, "
    "i.phone AS instructor_phone, u.created_at, u.updated_at"
)

SAFE_USER_JOINS = """
LEFT JOIN customers c ON c.id = u.customer_id
LEFT JOIN LATERAL (
    SELECT full_name, phone FROM customer_contacts
    WHERE customer_id = c.id AND is_active = true
    ORDER BY is_primary DESC, created_at ASC LIMIT 1
) cc ON true
LEFT JOIN instructors i ON i.id = u.instructor_id
"""


def get_user_by_email(cur, email: str) -> dict | None:
    cur.execute(f"SELECT {USER_COLUMNS} FROM users WHERE email = %s;", (email,))
    return cur.fetchone()


def get_user_by_id(cur, user_id: UUID) -> dict | None:
    cur.execute(f"SELECT {USER_COLUMNS} FROM users WHERE id = %s;", (user_id,))
    return cur.fetchone()


def list_users(cur, *, search: str | None, role: str | None, is_active: bool | None, limit: int, offset: int) -> list[dict]:
    clauses: list[str] = []
    params: list[object] = []
    if search:
        clauses.append("(u.email ILIKE %s OR u.display_name ILIKE %s OR c.name ILIKE %s OR i.full_name ILIKE %s)")
        term = f"%{search.strip()}%"
        params.extend((term, term, term, term))
    if role:
        clauses.append("u.role = %s")
        params.append(role)
    if is_active is not None:
        clauses.append("u.is_active = %s")
        params.append(is_active)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    cur.execute(
        f"""
        SELECT {SAFE_USER_COLUMNS}
        FROM users u
        {SAFE_USER_JOINS}
        {where}
        ORDER BY lower(u.email) ASC, u.id ASC
        LIMIT %s OFFSET %s;
        """,
        [*params, limit, offset],
    )
    return list(cur.fetchall())


def get_safe_user(cur, user_id: UUID) -> dict | None:
    cur.execute(
        f"""
        SELECT {SAFE_USER_COLUMNS}
        FROM users u
        {SAFE_USER_JOINS}
        WHERE u.id = %s;
        """,
        (user_id,),
    )
    return cur.fetchone()


def get_customer_profile(cur, customer_id: UUID) -> dict | None:
    cur.execute("SELECT id, name, is_active FROM customers WHERE id = %s;", (customer_id,))
    return cur.fetchone()


def get_instructor_profile(cur, instructor_id: UUID) -> dict | None:
    cur.execute("SELECT id, full_name, is_active FROM instructors WHERE id = %s;", (instructor_id,))
    return cur.fetchone()


def create_user(cur, *, email: str, password_hash: str, role: str, display_name: str | None, customer_id: UUID | None, instructor_id: UUID | None) -> dict:
    cur.execute(
        f"""
        INSERT INTO users (email, password_hash, role, display_name, is_active, customer_id, instructor_id)
        VALUES (%s, %s, %s, %s, true, %s, %s)
        RETURNING {USER_COLUMNS};
        """,
        (email, password_hash, role, display_name, customer_id, instructor_id),
    )
    return cur.fetchone()


def update_user_email(cur, user_id: UUID, email: str) -> bool:
    cur.execute(
        "UPDATE users SET email = %s, updated_at = now() WHERE id = %s RETURNING id;",
        (email, user_id),
    )
    return cur.fetchone() is not None


def set_user_active(cur, user_id: UUID, is_active: bool) -> bool:
    cur.execute(
        "UPDATE users SET is_active = %s, updated_at = now() WHERE id = %s RETURNING id;",
        (is_active, user_id),
    )
    return cur.fetchone() is not None


def set_password_hash(cur, user_id: UUID, password_hash: str) -> bool:
    cur.execute(
        "UPDATE users SET password_hash = %s, updated_at = now() WHERE id = %s RETURNING id;",
        (password_hash, user_id),
    )
    return cur.fetchone() is not None


def upsert_demo_user(
    cur,
    email: str,
    password_hash: str,
    role: str,
    customer_id: str | None = None,
    instructor_id: str | None = None,
) -> None:
    cur.execute(
        """
        INSERT INTO users (email, password_hash, role, is_active, customer_id, instructor_id)
        VALUES (%s, %s, %s, true, %s, %s)
        ON CONFLICT (email) DO UPDATE
        SET password_hash = EXCLUDED.password_hash,
            role = EXCLUDED.role,
            is_active = true,
            customer_id = EXCLUDED.customer_id,
            instructor_id = EXCLUDED.instructor_id,
            updated_at = now();
        """,
        (email, password_hash, role, customer_id, instructor_id),
    )
