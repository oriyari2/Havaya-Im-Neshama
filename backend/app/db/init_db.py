from psycopg import Connection

from backend.app.core.security import hash_password
from backend.app.db.schema import ALTER_TABLE_SQL, CREATE_EXTENSION_SQL, CREATE_INDEX_SQL, CREATE_TABLE_SQL
from backend.app.infrastructure.repositories.user_repository import upsert_demo_user


DEMO_USERS = [
    ("manager@example.com", "manager123", "manager"),
    ("instructor@example.com", "instructor123", "instructor"),
    ("customer@example.com", "customer123", "customer"),
]


def seed_demo_users(conn: Connection, *, commit: bool = True) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM customers WHERE is_active = true ORDER BY created_at ASC, id ASC LIMIT 1;")
        customer_row = cur.fetchone()
        cur.execute("SELECT id FROM instructors WHERE is_active = true ORDER BY created_at ASC, id ASC LIMIT 1;")
        instructor_row = cur.fetchone()
        customer_id = customer_row[0] if customer_row else None
        instructor_id = instructor_row[0] if instructor_row else None
        for email, password, role in DEMO_USERS:
            password_hash = hash_password(password, salt=f"demo-{role}-salt")
            upsert_demo_user(
                cur,
                email,
                password_hash,
                role,
                customer_id=customer_id if role == "customer" else None,
                instructor_id=instructor_id if role == "instructor" else None,
            )
    if commit:
        conn.commit()


def initialize_database(conn: Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(CREATE_EXTENSION_SQL)
        for statement in CREATE_TABLE_SQL:
            cur.execute(statement)
        for statement in ALTER_TABLE_SQL:
            cur.execute(statement)
        for statement in CREATE_INDEX_SQL:
            cur.execute(statement)
    conn.commit()
    seed_demo_users(conn)
