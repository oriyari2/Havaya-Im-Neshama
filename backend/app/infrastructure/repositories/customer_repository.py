from __future__ import annotations

from uuid import UUID


CUSTOMER_COLUMNS = (
    "id, name, customer_type, city, address, phone, email, notes, "
    "is_active, created_at, updated_at"
)
CONTACT_COLUMNS = (
    "id, customer_id, full_name, role_title, phone, email, is_primary, "
    "notes, is_active, created_at, updated_at"
)
CUSTOMER_SORT_COLUMNS = {
    "name": "name",
    "created_at": "created_at",
}
CUSTOMER_UPDATE_FIELDS = [
    "name",
    "customer_type",
    "city",
    "address",
    "phone",
    "email",
    "notes",
    "is_active",
]
CONTACT_UPDATE_FIELDS = [
    "full_name",
    "role_title",
    "phone",
    "email",
    "is_primary",
    "notes",
    "is_active",
]


def list_customers(
    cur,
    search: str | None,
    city: str | None,
    customer_type: str | None,
    is_active: bool | None,
    order_by: str,
    limit: int,
    offset: int,
) -> list[dict]:
    clauses: list[str] = []
    params: list[object] = []

    if is_active is None:
        clauses.append("is_active = true")
    else:
        clauses.append("is_active = %s")
        params.append(is_active)

    cleaned_search = search.strip() if search else None
    if cleaned_search:
        clauses.append(
            "(name ILIKE %s OR phone ILIKE %s OR email ILIKE %s OR "
            "city ILIKE %s OR customer_type ILIKE %s OR notes ILIKE %s)"
        )
        search_param = f"%{cleaned_search}%"
        params.extend([search_param] * 6)

    cleaned_city = city.strip() if city else None
    if cleaned_city:
        clauses.append("city ILIKE %s")
        params.append(f"%{cleaned_city}%")

    cleaned_customer_type = customer_type.strip() if customer_type else None
    if cleaned_customer_type:
        clauses.append("customer_type ILIKE %s")
        params.append(f"%{cleaned_customer_type}%")

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sort_column = CUSTOMER_SORT_COLUMNS[order_by]
    cur.execute(
        f"""
        SELECT {CUSTOMER_COLUMNS}
        FROM customers
        {where_sql}
        ORDER BY {sort_column} ASC, id ASC
        LIMIT %s OFFSET %s;
        """,
        [*params, limit, offset],
    )
    return list(cur.fetchall())


def get_customer(cur, customer_id: UUID) -> dict | None:
    cur.execute(f"SELECT {CUSTOMER_COLUMNS} FROM customers WHERE id = %s;", (customer_id,))
    return cur.fetchone()


def lock_customer(cur, customer_id: UUID) -> dict | None:
    cur.execute(
        f"SELECT {CUSTOMER_COLUMNS} FROM customers WHERE id = %s FOR UPDATE;",
        (customer_id,),
    )
    return cur.fetchone()


def customer_delete_dependencies(cur, customer_id: UUID) -> dict:
    cur.execute(
        """
        SELECT
            EXISTS (SELECT 1 FROM users WHERE customer_id = %s) AS has_user,
            EXISTS (SELECT 1 FROM bookings WHERE customer_id = %s) AS has_booking,
            EXISTS (
                SELECT 1 FROM booking_events
                WHERE event_data ->> 'customer_id' = %s
            ) AS has_event_history;
        """,
        (customer_id, customer_id, str(customer_id)),
    )
    return cur.fetchone()


def delete_customer(cur, customer_id: UUID) -> bool:
    cur.execute("DELETE FROM customers WHERE id = %s RETURNING id;", (customer_id,))
    return cur.fetchone() is not None


def create_customer(cur, data: dict) -> dict:
    cur.execute(
        f"""
        INSERT INTO customers (
            name, customer_type, city, address, phone, email, notes, is_active
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING {CUSTOMER_COLUMNS};
        """,
        (
            data["name"],
            data["customer_type"],
            data["city"],
            data["address"],
            data["phone"],
            data["email"],
            data["notes"],
            data["is_active"],
        ),
    )
    return cur.fetchone()


def update_customer(cur, customer_id: UUID, data: dict) -> dict:
    assignments = [f"{field} = %s" for field in CUSTOMER_UPDATE_FIELDS if field in data]
    params = [data[field] for field in CUSTOMER_UPDATE_FIELDS if field in data]
    cur.execute(
        f"""
        UPDATE customers
        SET {', '.join(assignments)}, updated_at = now()
        WHERE id = %s
        RETURNING {CUSTOMER_COLUMNS};
        """,
        [*params, customer_id],
    )
    return cur.fetchone()


def list_contacts(cur, customer_id: UUID, is_active: bool | None = None) -> list[dict]:
    params: list[object] = [customer_id]
    active_filter = ""
    if is_active is not None:
        active_filter = " AND is_active = %s"
        params.append(is_active)
    cur.execute(
        f"""
        SELECT {CONTACT_COLUMNS}
        FROM customer_contacts
        WHERE customer_id = %s{active_filter}
        ORDER BY is_primary DESC, full_name ASC, created_at ASC;
        """,
        params,
    )
    return list(cur.fetchall())


def get_contact(cur, contact_id: UUID) -> dict | None:
    cur.execute(f"SELECT {CONTACT_COLUMNS} FROM customer_contacts WHERE id = %s;", (contact_id,))
    return cur.fetchone()


def clear_primary_contacts(cur, customer_id: UUID, except_contact_id: UUID | None = None) -> None:
    params: list[object] = [customer_id]
    except_filter = ""
    if except_contact_id is not None:
        except_filter = " AND id <> %s"
        params.append(except_contact_id)
    cur.execute(
        f"""
        UPDATE customer_contacts
        SET is_primary = false, updated_at = now()
        WHERE customer_id = %s{except_filter} AND is_primary = true;
        """,
        params,
    )


def create_contact(cur, customer_id: UUID, data: dict) -> dict:
    cur.execute(
        f"""
        INSERT INTO customer_contacts (
            customer_id, full_name, role_title, phone, email,
            is_primary, notes, is_active
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING {CONTACT_COLUMNS};
        """,
        (
            customer_id,
            data["full_name"],
            data["role_title"],
            data["phone"],
            data["email"],
            data["is_primary"],
            data["notes"],
            data["is_active"],
        ),
    )
    return cur.fetchone()


def update_contact(cur, contact_id: UUID, data: dict) -> dict:
    assignments = [f"{field} = %s" for field in CONTACT_UPDATE_FIELDS if field in data]
    params = [data[field] for field in CONTACT_UPDATE_FIELDS if field in data]
    cur.execute(
        f"""
        UPDATE customer_contacts
        SET {', '.join(assignments)}, updated_at = now()
        WHERE id = %s
        RETURNING {CONTACT_COLUMNS};
        """,
        [*params, contact_id],
    )
    return cur.fetchone()


def soft_delete_contact(cur, contact_id: UUID) -> dict:
    cur.execute(
        f"""
        UPDATE customer_contacts
        SET is_active = false, updated_at = now()
        WHERE id = %s
        RETURNING {CONTACT_COLUMNS};
        """,
        (contact_id,),
    )
    return cur.fetchone()
