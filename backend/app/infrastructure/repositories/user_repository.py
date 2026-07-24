from __future__ import annotations

from uuid import UUID


USER_COLUMNS = (
    "id, email, password_hash, role, is_active, customer_id, instructor_id, "
    "created_at, updated_at"
)


def get_user_by_email(cur, email: str) -> dict | None:
    cur.execute(f"SELECT {USER_COLUMNS} FROM users WHERE email = %s;", (email,))
    return cur.fetchone()


def get_user_by_id(cur, user_id: UUID) -> dict | None:
    cur.execute(f"SELECT {USER_COLUMNS} FROM users WHERE id = %s;", (user_id,))
    return cur.fetchone()


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
