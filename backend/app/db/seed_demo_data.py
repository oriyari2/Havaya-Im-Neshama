from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable
from uuid import UUID

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from backend.app.db.connection import get_connection
from backend.app.db.demo_seed_catalog import (
    ACTIVITIES,
    BOOKINGS,
    CONTACTS,
    CUSTOMER_LOGIN_EMAIL,
    CUSTOMERS,
    DEMO_MARKER,
    INSTRUCTOR_LOGIN_EMAIL,
    INSTRUCTORS,
    INSTRUCTION_NOTES,
    INVENTORY_ITEMS,
    MANAGER_LOGIN_EMAIL,
    REQUIREMENTS,
    demo_id,
)
from backend.app.domain.bookings.aggregate import BookingAggregate
from backend.app.domain.bookings.events import booking_created, instructor_assigned, instructor_removed
from backend.app.domain.bookings.status import BookingStatus
from backend.app.infrastructure.repositories import booking_event_repository as events_repo
from backend.app.infrastructure.repositories import booking_projection_repository as projection_repo


CONFIRMATION_PHRASE = "אני מאשר יצירת נתוני דמו"
TEXT_COLUMNS = {
    "customers": ("name", "customer_type", "city", "address", "notes"),
    "customer_contacts": ("full_name", "role_title", "notes"),
    "instructors": ("full_name", "city", "notes"),
    "activities": ("name", "description", "target_audience", "price_notes", "pricing_rule", "required_equipment", "preparation_notes", "season", "tags"),
    "inventory_items": ("name", "category", "unit", "storage_location", "notes"),
    "bookings": ("event_title", "city", "venue", "location_name", "location_address", "audience_type", "internal_notes", "customer_notes", "vehicle_notes", "loading_notes", "notes"),
}
_ACTIVITY_ID_BY_KEY: dict[str, UUID] = {item.key: item.id for item in ACTIVITIES}
_INVENTORY_ID_BY_KEY: dict[str, UUID] = {item.key: item.id for item in INVENTORY_ITEMS}
_CUSTOMER_ID_BY_KEY: dict[str, UUID] = {item.key: item.id for item in CUSTOMERS}
_CONTACT_ID_BY_KEY: dict[str, UUID] = {item.key: item.id for item in CONTACTS}
_INSTRUCTOR_ID_BY_KEY: dict[str, UUID] = {item.key: item.id for item in INSTRUCTORS}
_INSTRUCTION_ID_BY_SEED_ID: dict[UUID, UUID] = {item.id: item.id for item in INSTRUCTION_NOTES}
_REQUIREMENT_ID_BY_SEED_ID: dict[UUID, UUID] = {item.id: item.id for item in REQUIREMENTS}


@dataclass(frozen=True)
class SeedReport:
    mode: str
    reused: dict[str, int]
    existing_seed: dict[str, int]
    to_create: dict[str, int]
    warnings: list[str]
    verification: dict[str, object] | None = None


class SeedVerificationError(RuntimeError):
    def __init__(self, failures: Iterable[object]):
        self.failures = [_safe_failure_name(failure) for failure in failures]
        super().__init__("seed verification failed: " + ", ".join(self.failures))


def _seed_ids(group: int, total: int) -> list[UUID]:
    return [demo_id(group, i) for i in range(1, total + 1)]


def _count_existing(cur, table: str, ids: Iterable[UUID]) -> int:
    cur.execute(f"SELECT COUNT(*) AS count FROM {table} WHERE id = ANY(%s);", (list(ids),))
    return int(cur.fetchone()["count"])


def _count_by_name(cur, table: str, names: Iterable[str]) -> int:
    cur.execute(f"SELECT COUNT(*) AS count FROM {table} WHERE lower(trim(name)) = ANY(%s);", ([name.strip().lower() for name in names],))
    return int(cur.fetchone()["count"])


def _get_user_id(cur, email: str) -> UUID:
    cur.execute("SELECT id FROM users WHERE email = %s;", (email,))
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"Required demo user is missing: {email}")
    return row["id"]


def _get_required_login_links(cur) -> dict[str, UUID]:
    expected = {
        CUSTOMER_LOGIN_EMAIL: "customer_id",
        INSTRUCTOR_LOGIN_EMAIL: "instructor_id",
        MANAGER_LOGIN_EMAIL: "id",
    }
    links: dict[str, UUID] = {}
    for email, column in expected.items():
        cur.execute(f"SELECT id, customer_id, instructor_id FROM users WHERE email = %s;", (email,))
        row = cur.fetchone()
        if not row:
            raise RuntimeError(f"Required demo login account is missing: {email}")
        link_id = row[column]
        if link_id is None:
            raise RuntimeError(f"Required demo login profile link is missing: {email}.{column}")
        links[email] = link_id
    return links


def _use_existing_login_profiles(links: dict[str, UUID]) -> None:
    global _CUSTOMER_ID_BY_KEY, _INSTRUCTOR_ID_BY_KEY
    _CUSTOMER_ID_BY_KEY = {item.key: item.id for item in CUSTOMERS}
    _INSTRUCTOR_ID_BY_KEY = {item.key: item.id for item in INSTRUCTORS}
    _CUSTOMER_ID_BY_KEY["customer-1"] = links[CUSTOMER_LOGIN_EMAIL]
    _INSTRUCTOR_ID_BY_KEY["instructor-1"] = links[INSTRUCTOR_LOGIN_EMAIL]


def _normalize_name(value: str) -> str:
    return " ".join(value.split()).strip().lower()


def _resolve_activity_ids(cur) -> dict[str, UUID]:
    resolved: dict[str, UUID] = {}
    for activity in ACTIVITIES:
        cur.execute("SELECT id FROM activities WHERE id = %s;", (activity.id,))
        row = cur.fetchone()
        if row:
            resolved[activity.key] = row["id"]
            continue
        cur.execute("SELECT id FROM activities WHERE lower(trim(name)) = %s ORDER BY created_at ASC LIMIT 1;", (_normalize_name(activity.name),))
        row = cur.fetchone()
        if row:
            resolved[activity.key] = row["id"]
            continue
        resolved[activity.key] = activity.id
    return resolved


def _resolve_inventory_ids(cur) -> dict[str, UUID]:
    resolved: dict[str, UUID] = {}
    for item in INVENTORY_ITEMS:
        cur.execute("SELECT id FROM inventory_items WHERE id = %s;", (item.id,))
        row = cur.fetchone()
        if row:
            resolved[item.key] = row["id"]
            continue
        cur.execute("SELECT id FROM inventory_items WHERE lower(trim(name)) = %s ORDER BY created_at ASC LIMIT 1;", (_normalize_name(item.name),))
        row = cur.fetchone()
        resolved[item.key] = row["id"] if row else item.id
    return resolved


def _resolve_instruction_ids(cur) -> dict[UUID, UUID]:
    resolved: dict[UUID, UUID] = {}
    for note in INSTRUCTION_NOTES:
        activity_id = _activity_id(note.activity_key)
        cur.execute("SELECT id FROM activity_instruction_notes WHERE id = %s;", (note.id,))
        row = cur.fetchone()
        if row:
            resolved[note.id] = row["id"]
            continue
        cur.execute(
            """
            SELECT id
            FROM activity_instruction_notes
            WHERE activity_id = %s AND lower(regexp_replace(trim(title), '\s+', ' ', 'g')) = %s
            ORDER BY created_at ASC
            LIMIT 1;
            """,
            (activity_id, _normalize_name(note.title)),
        )
        row = cur.fetchone()
        resolved[note.id] = row["id"] if row else note.id
    return resolved


def _resolve_requirement_ids(cur) -> dict[UUID, UUID]:
    resolved: dict[UUID, UUID] = {}
    for requirement in REQUIREMENTS:
        activity_id = _activity_id(requirement.activity_key)
        inventory_id = _inventory_id(requirement.inventory_key)
        cur.execute("SELECT id FROM activity_equipment_requirements WHERE id = %s;", (requirement.id,))
        row = cur.fetchone()
        if row:
            resolved[requirement.id] = row["id"]
            continue
        cur.execute(
            """
            SELECT id
            FROM activity_equipment_requirements
            WHERE activity_id = %s AND inventory_item_id = %s
            ORDER BY created_at ASC
            LIMIT 1;
            """,
            (activity_id, inventory_id),
        )
        row = cur.fetchone()
        resolved[requirement.id] = row["id"] if row else requirement.id
    return resolved


def _resolve_profile_ids_by_email(cur) -> None:
    global _CONTACT_ID_BY_KEY
    for customer in CUSTOMERS:
        if _CUSTOMER_ID_BY_KEY[customer.key] != customer.id:
            continue
        cur.execute("SELECT id FROM customers WHERE id = %s;", (customer.id,))
        if cur.fetchone():
            continue
        cur.execute("SELECT id FROM customers WHERE lower(trim(email)) = %s ORDER BY created_at ASC LIMIT 1;", (customer.email.lower(),))
        row = cur.fetchone()
        if row:
            _CUSTOMER_ID_BY_KEY[customer.key] = row["id"]
    for instructor in INSTRUCTORS:
        if _INSTRUCTOR_ID_BY_KEY[instructor.key] != instructor.id:
            continue
        cur.execute("SELECT id FROM instructors WHERE id = %s;", (instructor.id,))
        if cur.fetchone():
            continue
        cur.execute("SELECT id FROM instructors WHERE lower(trim(email)) = %s ORDER BY created_at ASC LIMIT 1;", (instructor.email.lower(),))
        row = cur.fetchone()
        if row:
            _INSTRUCTOR_ID_BY_KEY[instructor.key] = row["id"]
    _CONTACT_ID_BY_KEY = {item.key: item.id for item in CONTACTS}
    for contact in CONTACTS:
        cur.execute("SELECT id FROM customer_contacts WHERE id = %s;", (contact.id,))
        if cur.fetchone():
            continue
        cur.execute("SELECT id FROM customer_contacts WHERE lower(trim(email)) = %s ORDER BY created_at ASC LIMIT 1;", (contact.email.lower(),))
        row = cur.fetchone()
        if row:
            _CONTACT_ID_BY_KEY[contact.key] = row["id"]


def _resolved_seed_counts(cur) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    global _ACTIVITY_ID_BY_KEY, _INVENTORY_ID_BY_KEY, _INSTRUCTION_ID_BY_SEED_ID, _REQUIREMENT_ID_BY_SEED_ID
    links = _get_required_login_links(cur)
    _use_existing_login_profiles(links)
    _resolve_profile_ids_by_email(cur)
    _ACTIVITY_ID_BY_KEY = _resolve_activity_ids(cur)
    _INVENTORY_ID_BY_KEY = _resolve_inventory_ids(cur)
    _INSTRUCTION_ID_BY_SEED_ID = _resolve_instruction_ids(cur)
    _REQUIREMENT_ID_BY_SEED_ID = _resolve_requirement_ids(cur)
    reused = {
        "regular_activities_by_name": sum(1 for item in ACTIVITIES if _ACTIVITY_ID_BY_KEY[item.key] != item.id),
        "regular_inventory_by_name": sum(1 for item in INVENTORY_ITEMS if _INVENTORY_ID_BY_KEY[item.key] != item.id),
        "existing_customers_by_email_or_login": sum(1 for item in CUSTOMERS if _CUSTOMER_ID_BY_KEY[item.key] != item.id),
        "existing_contacts_by_email": sum(1 for item in CONTACTS if _CONTACT_ID_BY_KEY[item.key] != item.id),
        "existing_instructors_by_email_or_login": sum(1 for item in INSTRUCTORS if _INSTRUCTOR_ID_BY_KEY[item.key] != item.id),
        "existing_instruction_notes_reused": sum(1 for item in INSTRUCTION_NOTES if _INSTRUCTION_ID_BY_SEED_ID[item.id] != item.id),
        "existing_equipment_requirements_reused": sum(1 for item in REQUIREMENTS if _REQUIREMENT_ID_BY_SEED_ID[item.id] != item.id),
    }
    existing_seed = {
        "customers": sum(1 for item in CUSTOMERS if _CUSTOMER_ID_BY_KEY[item.key] == item.id and _count_existing(cur, "customers", [item.id])),
        "contacts": sum(1 for item in CONTACTS if _CONTACT_ID_BY_KEY[item.key] == item.id and _count_existing(cur, "customer_contacts", [item.id])),
        "instructors": sum(1 for item in INSTRUCTORS if _INSTRUCTOR_ID_BY_KEY[item.key] == item.id and _count_existing(cur, "instructors", [item.id])),
        "activities": sum(1 for item in ACTIVITIES if _ACTIVITY_ID_BY_KEY[item.key] == item.id and _count_existing(cur, "activities", [item.id])),
        "inventory": sum(1 for item in INVENTORY_ITEMS if _INVENTORY_ID_BY_KEY[item.key] == item.id and _count_existing(cur, "inventory_items", [item.id])),
        "bookings": _count_existing(cur, "bookings", [item.id for item in BOOKINGS]),
        "instruction_notes": sum(1 for item in INSTRUCTION_NOTES if _INSTRUCTION_ID_BY_SEED_ID[item.id] == item.id and _count_existing(cur, "activity_instruction_notes", [item.id])),
        "equipment_requirements": sum(1 for item in REQUIREMENTS if _REQUIREMENT_ID_BY_SEED_ID[item.id] == item.id and _count_existing(cur, "activity_equipment_requirements", [item.id])),
    }
    to_create = {
        "customers": sum(1 for item in CUSTOMERS if _CUSTOMER_ID_BY_KEY[item.key] == item.id) - existing_seed["customers"],
        "contacts": sum(1 for item in CONTACTS if _CONTACT_ID_BY_KEY[item.key] == item.id) - existing_seed["contacts"],
        "instructors": sum(1 for item in INSTRUCTORS if _INSTRUCTOR_ID_BY_KEY[item.key] == item.id) - existing_seed["instructors"],
        "activities": sum(1 for item in ACTIVITIES if _ACTIVITY_ID_BY_KEY[item.key] == item.id) - existing_seed["activities"],
        "inventory": sum(1 for item in INVENTORY_ITEMS if _INVENTORY_ID_BY_KEY[item.key] == item.id) - existing_seed["inventory"],
        "bookings": max(0, len(BOOKINGS) - existing_seed["bookings"]),
        "instruction_notes_to_create": sum(1 for item in INSTRUCTION_NOTES if _INSTRUCTION_ID_BY_SEED_ID[item.id] == item.id) - existing_seed["instruction_notes"],
        "equipment_requirements_to_create": sum(1 for item in REQUIREMENTS if _REQUIREMENT_ID_BY_SEED_ID[item.id] == item.id) - existing_seed["equipment_requirements"],
        "events_to_complete": _missing_event_count(cur),
    }
    return reused, existing_seed, to_create


def inspect_existing_data(cur) -> dict[str, object]:
    result: dict[str, object] = {}
    for table in ("customers", "customer_contacts", "instructors", "activities", "inventory_items", "bookings"):
        cur.execute(f"SELECT COUNT(*) AS count FROM {table};")
        result[table] = cur.fetchone()["count"]
    cur.execute("SELECT customer_id FROM users WHERE email = %s;", (CUSTOMER_LOGIN_EMAIL,))
    result["customer_login_customer_id"] = (cur.fetchone() or {}).get("customer_id")
    cur.execute("SELECT instructor_id FROM users WHERE email = %s;", (INSTRUCTOR_LOGIN_EMAIL,))
    result["instructor_login_instructor_id"] = (cur.fetchone() or {}).get("instructor_id")
    return result


def build_report(cur, mode: str) -> SeedReport:
    reused, existing_seed, to_create = _resolved_seed_counts(cur)
    warnings: list[str] = []
    cur.execute(
        """
        SELECT COUNT(*) AS count
        FROM bookings b
        JOIN users u ON u.customer_id = b.customer_id
        WHERE u.email = %s AND b.id = ANY(%s);
        """,
        (CUSTOMER_LOGIN_EMAIL, [booking.id for booking in BOOKINGS]),
    )
    reused["linked_customer_bookings"] = int(cur.fetchone()["count"])
    cur.execute(
        """
        SELECT COUNT(*) AS count
        FROM booking_instructors bi
        JOIN users u ON u.instructor_id = bi.instructor_id
        JOIN booking_activities ba ON ba.id = bi.booking_activity_id
        JOIN bookings b ON b.id = ba.booking_id
        WHERE u.email = %s AND bi.active = true AND b.event_at >= now() AND b.id = ANY(%s);
        """,
        (INSTRUCTOR_LOGIN_EMAIL, [booking.id for booking in BOOKINGS]),
    )
    reused["linked_instructor_assignments"] = int(cur.fetchone()["count"])
    warnings.extend(_legacy_seed_conflict_warnings(cur))
    return SeedReport(mode=mode, reused=reused, existing_seed=existing_seed, to_create=to_create, warnings=warnings)


def _legacy_seed_conflict_warnings(cur) -> list[str]:
    warnings: list[str] = []
    checks = (
        ("booking_activities", "booking activity", sum(len(booking.activities) for booking in BOOKINGS), "booking_id"),
        ("booking_equipment_items", "booking equipment", sum(len(booking.equipment) for booking in BOOKINGS), "booking_id"),
        ("booking_price_components", "booking price component", sum(len(booking.prices) for booking in BOOKINGS), "booking_id"),
    )
    booking_ids = [booking.id for booking in BOOKINGS]
    for table, label, expected_count, booking_column in checks:
        cur.execute(f"SELECT COUNT(*) AS count FROM {table} WHERE {booking_column} = ANY(%s);", (booking_ids,))
        actual_count = int(cur.fetchone()["count"])
        if actual_count <= expected_count:
            continue
        warnings.append(
            f"legacy seed-owned {label} rows detected on deterministic demo bookings: expected {expected_count}, found {actual_count}. "
            f"Dry run only; migrate by reviewing {table} rows attached to demo booking IDs and manually removing or remapping obsolete seed rows before --apply."
        )
    return warnings


def _missing_event_count(cur) -> int:
    missing = 0
    for booking in BOOKINGS:
        cur.execute("SELECT event_type FROM booking_events WHERE aggregate_id = %s;", (booking.id,))
        existing = [row["event_type"] for row in cur.fetchall()]
        if "BookingCreated" not in existing:
            missing += 1
        missing += max(0, len(booking.assignments) - sum(1 for event in existing if event in {"BookingInstructorAssigned", "BookingInstructorRemoved"}))
        if booking.status != BookingStatus.NEW.value and "BookingStatusChanged" not in existing:
            missing += 1
    return missing


def _upsert_business_data(cur) -> None:
    _resolve_profile_ids_by_email(cur)
    for customer in CUSTOMERS:
        if _CUSTOMER_ID_BY_KEY[customer.key] != customer.id:
            continue
        cur.execute(
            """
            INSERT INTO customers (id, name, customer_type, city, address, phone, email, notes, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name, customer_type = EXCLUDED.customer_type, city = EXCLUDED.city,
                address = EXCLUDED.address, phone = EXCLUDED.phone, email = EXCLUDED.email,
                notes = EXCLUDED.notes, is_active = true, updated_at = now();
            """,
            (customer.id, customer.name, customer.customer_type, customer.city, customer.address, customer.phone, customer.email, customer.notes),
        )
    customer_ids = _CUSTOMER_ID_BY_KEY
    for contact in CONTACTS:
        if _CONTACT_ID_BY_KEY[contact.key] != contact.id:
            continue
        cur.execute(
            """
            INSERT INTO customer_contacts (id, customer_id, full_name, role_title, phone, email, is_primary, notes, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true)
            ON CONFLICT (id) DO UPDATE SET
                customer_id = EXCLUDED.customer_id, full_name = EXCLUDED.full_name,
                role_title = EXCLUDED.role_title, phone = EXCLUDED.phone, email = EXCLUDED.email,
                is_primary = EXCLUDED.is_primary, notes = EXCLUDED.notes, is_active = true,
                updated_at = now();
            """,
            (contact.id, customer_ids[contact.customer_key], contact.full_name, contact.role_title, contact.phone, contact.email, contact.is_primary, DEMO_MARKER),
        )
    for instructor in INSTRUCTORS:
        if _INSTRUCTOR_ID_BY_KEY[instructor.key] != instructor.id:
            continue
        cur.execute(
            """
            INSERT INTO instructors (id, full_name, phone, email, city, notes, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, true)
            ON CONFLICT (id) DO UPDATE SET
                full_name = EXCLUDED.full_name, phone = EXCLUDED.phone, email = EXCLUDED.email,
                city = EXCLUDED.city, notes = EXCLUDED.notes, is_active = true, updated_at = now();
            """,
            (instructor.id, instructor.full_name, instructor.phone, instructor.email, instructor.city, instructor.notes),
        )
    global _ACTIVITY_ID_BY_KEY, _INVENTORY_ID_BY_KEY, _INSTRUCTION_ID_BY_SEED_ID, _REQUIREMENT_ID_BY_SEED_ID
    _ACTIVITY_ID_BY_KEY = _resolve_activity_ids(cur)
    _INVENTORY_ID_BY_KEY = _resolve_inventory_ids(cur)
    for activity in ACTIVITIES:
        if _ACTIVITY_ID_BY_KEY[activity.key] != activity.id:
            continue
        cur.execute(
            """
            INSERT INTO activities (
                id, name, description, target_audience, duration_minutes, recommended_capacity,
                pricing_rule, required_equipment, preparation_notes, season, tags,
                default_duration_minutes, min_participants, max_participants, base_price,
                price_notes, default_setup_minutes, default_cleanup_minutes, is_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name, description = EXCLUDED.description,
                target_audience = EXCLUDED.target_audience, duration_minutes = EXCLUDED.duration_minutes,
                recommended_capacity = EXCLUDED.recommended_capacity, pricing_rule = EXCLUDED.pricing_rule,
                required_equipment = EXCLUDED.required_equipment, preparation_notes = EXCLUDED.preparation_notes,
                season = EXCLUDED.season, tags = EXCLUDED.tags,
                default_duration_minutes = EXCLUDED.default_duration_minutes,
                min_participants = EXCLUDED.min_participants, max_participants = EXCLUDED.max_participants,
                base_price = EXCLUDED.base_price, price_notes = EXCLUDED.price_notes,
                default_setup_minutes = EXCLUDED.default_setup_minutes,
                default_cleanup_minutes = EXCLUDED.default_cleanup_minutes,
                is_active = true, updated_at = now();
            """,
            (
                activity.id,
                activity.name,
                activity.description,
                activity.target_audience,
                activity.duration_minutes,
                activity.recommended_capacity,
                activity.pricing_rule,
                activity.required_equipment,
                activity.preparation_notes,
                activity.season,
                activity.tags,
                activity.duration_minutes,
                activity.min_participants,
                activity.max_participants,
                activity.base_price,
                activity.price_notes,
                activity.setup_minutes,
                activity.cleanup_minutes,
            ),
        )
    for item in INVENTORY_ITEMS:
        if _INVENTORY_ID_BY_KEY[item.key] != item.id:
            continue
        cur.execute(
            """
            INSERT INTO inventory_items (id, name, category, unit, quantity_total, quantity_available, storage_location, needs_charging, notes, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, true)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name, category = EXCLUDED.category, unit = EXCLUDED.unit,
                quantity_total = EXCLUDED.quantity_total, quantity_available = EXCLUDED.quantity_available,
                storage_location = EXCLUDED.storage_location, needs_charging = EXCLUDED.needs_charging,
                notes = EXCLUDED.notes, is_active = true, updated_at = now();
            """,
            (item.id, item.name, item.category, item.unit, item.quantity_total, item.quantity_available, item.storage_location, item.needs_charging, DEMO_MARKER),
        )
    _INSTRUCTION_ID_BY_SEED_ID = _resolve_instruction_ids(cur)
    for note in INSTRUCTION_NOTES:
        if _INSTRUCTION_ID_BY_SEED_ID[note.id] != note.id:
            continue
        cur.execute(
            """
            INSERT INTO activity_instruction_notes (id, activity_id, title, body, sort_order)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                activity_id = EXCLUDED.activity_id, title = EXCLUDED.title, body = EXCLUDED.body,
                sort_order = EXCLUDED.sort_order, updated_at = now();
            """,
            (note.id, _activity_id(note.activity_key), note.title, note.body, note.sort_order),
        )
    _REQUIREMENT_ID_BY_SEED_ID = _resolve_requirement_ids(cur)
    for requirement in REQUIREMENTS:
        if _REQUIREMENT_ID_BY_SEED_ID[requirement.id] != requirement.id:
            continue
        cur.execute(
            """
            INSERT INTO activity_equipment_requirements (id, activity_id, inventory_item_id, quantity_required, quantity_per_participant, is_optional, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                activity_id = EXCLUDED.activity_id, inventory_item_id = EXCLUDED.inventory_item_id,
                quantity_required = EXCLUDED.quantity_required,
                quantity_per_participant = EXCLUDED.quantity_per_participant,
                is_optional = EXCLUDED.is_optional, notes = EXCLUDED.notes, updated_at = now();
            """,
            (requirement.id, _activity_id(requirement.activity_key), _inventory_id(requirement.inventory_key), requirement.quantity_required, requirement.quantity_per_participant, requirement.is_optional, requirement.notes),
        )

def _activity_id(key: str) -> UUID:
    return _ACTIVITY_ID_BY_KEY.get(key, next(item.id for item in ACTIVITIES if item.key == key))


def _inventory_id(key: str) -> UUID:
    return _INVENTORY_ID_BY_KEY.get(key, next(item.id for item in INVENTORY_ITEMS if item.key == key))


def _instructor_id(key: str) -> UUID:
    return _INSTRUCTOR_ID_BY_KEY[key]


def _customer_id(key: str) -> UUID:
    return _CUSTOMER_ID_BY_KEY[key]


def _contact_id(key: str) -> UUID:
    return _CONTACT_ID_BY_KEY[key]


def _append_seed_event(cur, *, aggregate: BookingAggregate, event, actor_user_id: UUID, event_id: UUID) -> None:
    next_version = aggregate.version + 1
    cur.execute(
        """
        INSERT INTO booking_events (
            event_id, aggregate_id, aggregate_version, event_type, event_data, actor_user_id, correlation_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_id) DO NOTHING
        RETURNING event_id;
        """,
        (event_id, aggregate.id, next_version, event.event_type, Jsonb(event.payload()), actor_user_id, demo_id(13, next_version)),
    )
    if cur.fetchone() is None:
        return
    aggregate.apply(event.event_type, event.payload())
    aggregate.version = next_version
    projection_repo.upsert_projection(cur, aggregate.to_projection())
    if aggregate.booking_activity_id is not None:
        projection_repo.upsert_default_booking_activity(cur, aggregate.booking_activity_id, aggregate.id, aggregate.activity_id, aggregate.event_at, aggregate.participant_count)
    projection_repo.sync_instructor_projection(cur, aggregate.id, aggregate.active_instructor_assignments)


def _load_or_new_aggregate(cur, booking_id: UUID) -> BookingAggregate:
    events = events_repo.list_events(cur, booking_id)
    return BookingAggregate.replay(booking_id, events) if events else BookingAggregate(id=booking_id)


def _ensure_booking_event_history(cur, actor_user_id: UUID) -> None:
    for index, booking in enumerate(BOOKINGS, start=1):
        aggregate = _load_or_new_aggregate(cur, booking.id)
        if aggregate.version == 0:
            first_activity = booking.activities[0]
            event = booking_created(
                customer_id=_customer_id(booking.customer_key),
                activity_id=_activity_id(first_activity.activity_key),
                booking_activity_id=first_activity.id,
                event_at=booking.event_at,
                city=booking.city,
                venue=booking.venue,
                participant_count=booking.participants,
                agreed_price=booking.agreed_price,
                status=BookingStatus.NEW.value,
                requires_instructor=booking.requires_instructor,
                notes=booking.internal_notes,
            )
            _append_seed_event(cur, aggregate=aggregate, event=event, actor_user_id=actor_user_id, event_id=demo_id(14, index * 10 + 1))
        for activity in booking.activities:
            activity_event_at = aggregate.event_at or booking.event_at
            cur.execute(
                """
                INSERT INTO booking_activities (id, booking_id, activity_id, start_time, duration_minutes, participants_count, location_detail, sort_order, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    activity_id = EXCLUDED.activity_id,
                    start_time = EXCLUDED.start_time,
                    duration_minutes = EXCLUDED.duration_minutes,
                    participants_count = EXCLUDED.participants_count,
                    location_detail = EXCLUDED.location_detail,
                    sort_order = EXCLUDED.sort_order,
                    notes = EXCLUDED.notes,
                    updated_at = now();
                """,
                (activity.id, booking.id, _activity_id(activity.activity_key), activity_event_at + timedelta(minutes=activity.offset_minutes), activity.duration_minutes, activity.participants_count, activity.location_detail, activity.sort_order, activity.notes),
            )
        for step_number, step in enumerate(booking.assignments, start=2):
            aggregate = _load_or_new_aggregate(cur, booking.id)
            active_pair = (step.booking_activity_id, _instructor_id(step.instructor_key))
            if step.action == "assign" and active_pair not in aggregate.active_instructor_assignments:
                _append_seed_event(cur, aggregate=aggregate, event=instructor_assigned(booking_activity_id=step.booking_activity_id, instructor_id=active_pair[1]), actor_user_id=actor_user_id, event_id=demo_id(14, index * 10 + step_number))
            elif step.action == "remove" and active_pair in aggregate.active_instructor_assignments:
                _append_seed_event(cur, aggregate=aggregate, event=instructor_removed(booking_activity_id=step.booking_activity_id, instructor_id=active_pair[1]), actor_user_id=actor_user_id, event_id=demo_id(14, index * 10 + step_number))
        aggregate = _load_or_new_aggregate(cur, booking.id)
        if booking.status != BookingStatus.NEW.value and aggregate.status and aggregate.status.value != booking.status:
            from backend.app.domain.bookings.events import field_changed

            _append_seed_event(cur, aggregate=aggregate, event=field_changed("BookingStatusChanged", aggregate.status.value, booking.status), actor_user_id=actor_user_id, event_id=demo_id(14, index * 10 + 8))
        _update_rich_booking_projection(cur, booking, aggregate)


def _update_rich_booking_projection(cur, booking, aggregate: BookingAggregate) -> None:
    event_at = aggregate.event_at or booking.event_at
    city = aggregate.city or booking.city
    venue = aggregate.venue or booking.venue
    participant_count = aggregate.participant_count if aggregate.participant_count is not None else booking.participants
    agreed_price = aggregate.agreed_price if aggregate.agreed_price is not None else booking.agreed_price
    cur.execute(
        """
        UPDATE bookings
        SET event_title = %s, event_date = %s, location_name = %s, location_address = %s,
            city = %s, participants_count = %s, audience_type = %s, internal_notes = %s,
            customer_notes = %s, requires_vehicle = %s, vehicle_notes = %s, loading_notes = %s,
            event_at = %s, venue = %s, participant_count = %s, agreed_price = %s,
            primary_contact_id = %s, updated_at = now()
        WHERE id = %s;
        """,
        (booking.title, event_at, venue, booking.address, city, participant_count, booking.audience_type, aggregate.notes or booking.internal_notes, booking.customer_notes, booking.requires_vehicle, booking.vehicle_notes, booking.loading_notes, event_at, venue, participant_count, agreed_price, _contact_id(booking.contact_key), booking.id),
    )
    for item in booking.equipment:
        cur.execute(
            """
            INSERT INTO booking_equipment_items (id, booking_id, inventory_item_id, quantity_planned, status, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                inventory_item_id = EXCLUDED.inventory_item_id,
                quantity_planned = EXCLUDED.quantity_planned,
                status = EXCLUDED.status, notes = EXCLUDED.notes, updated_at = now();
            """,
            (item.id, booking.id, _inventory_id(item.inventory_key), item.quantity, item.status, item.notes),
        )
    for item in booking.prices:
        cur.execute(
            """
            INSERT INTO booking_price_components (id, booking_id, component_type, description, quantity, unit_price, total_price, sort_order)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                component_type = EXCLUDED.component_type, description = EXCLUDED.description,
                quantity = EXCLUDED.quantity, unit_price = EXCLUDED.unit_price,
                total_price = EXCLUDED.total_price, sort_order = EXCLUDED.sort_order,
                updated_at = now();
            """,
            (item.id, booking.id, item.component_type, item.description, item.quantity, item.unit_price, item.total_price, item.sort_order),
        )


def apply_seed() -> SeedReport:
    with get_connection() as conn:
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                before = build_report(cur, "apply")
                links = _get_required_login_links(cur)
                _use_existing_login_profiles(links)
                _upsert_business_data(cur)
                actor_user_id = _get_user_id(cur, MANAGER_LOGIN_EMAIL)
                _ensure_booking_event_history(cur, actor_user_id)
                verification = verify_with_cursor(cur)
                if _verification_failed(verification):
                    raise SeedVerificationError(verification.get("failures", []))
            conn.commit()
            return SeedReport("apply", before.reused, before.existing_seed, before.to_create, before.warnings, verification)
        except Exception as exc:
            conn.rollback()
            if isinstance(exc, SeedVerificationError):
                raise
            raise RuntimeError(_sanitize_error(exc)) from exc


def dry_run() -> SeedReport:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            report = build_report(cur, "dry-run")
        conn.rollback()
        return report


def verify_with_cursor(cur) -> dict[str, object]:
    checks: dict[str, object] = {}
    failures: list[str] = []
    _resolved_seed_counts(cur)
    cur.execute("SELECT status, COUNT(*) AS count FROM bookings WHERE id = ANY(%s) GROUP BY status;", ([booking.id for booking in BOOKINGS],))
    checks["status_distribution"] = {row["status"]: row["count"] for row in cur.fetchall()}
    expected_status_distribution: dict[str, int] = {}
    for booking in BOOKINGS:
        expected_status_distribution[booking.status] = expected_status_distribution.get(booking.status, 0) + 1
    if checks["status_distribution"] != expected_status_distribution:
        failures.append("status distribution does not match catalog")
    checks["seed_bookings"] = sum(checks["status_distribution"].values())
    if checks["seed_bookings"] != len(BOOKINGS):
        failures.append("missing deterministic seed bookings")
    cur.execute("SELECT COUNT(*) AS count FROM booking_events WHERE aggregate_id = ANY(%s) AND event_type = 'BookingCreated';", ([booking.id for booking in BOOKINGS],))
    checks["booking_created_events"] = int(cur.fetchone()["count"])
    if checks["booking_created_events"] != len(BOOKINGS):
        failures.append("missing BookingCreated events")
    cur.execute("SELECT COUNT(*) AS count FROM booking_activities WHERE booking_id = ANY(%s);", ([booking.id for booking in BOOKINGS],))
    checks["booking_activities"] = int(cur.fetchone()["count"])
    expected_booking_activities = sum(len(booking.activities) for booking in BOOKINGS)
    if checks["booking_activities"] != expected_booking_activities:
        failures.append("missing booking activity rows")
    cur.execute(
        """
        SELECT lower(regexp_replace(trim(name), '\s+', ' ', 'g')) AS normalized_name, COUNT(*) AS count
        FROM activities
        WHERE lower(regexp_replace(trim(name), '\s+', ' ', 'g')) = ANY(%s)
        GROUP BY normalized_name
        HAVING COUNT(*) > 1;
        """,
        ([_normalize_name(item.name) for item in ACTIVITIES],),
    )
    checks["duplicate_activity_names"] = {row["normalized_name"]: row["count"] for row in cur.fetchall()}
    if checks["duplicate_activity_names"]:
        failures.append("duplicate normalized Hebrew activity names")
    assignment_mismatches = 0
    assignment_event_mismatches = 0
    real_reassignments = 0
    future_new_unassigned = sum(1 for booking in BOOKINGS if booking.days_from_now >= 0 and booking.status == BookingStatus.NEW.value and booking.assignment_state == "unassigned")
    future_confirmed_unassigned = sum(1 for booking in BOOKINGS if booking.days_from_now >= 0 and booking.status == BookingStatus.CONFIRMED.value and booking.assignment_state == "unassigned")
    future_assigned = sum(1 for booking in BOOKINGS if booking.days_from_now >= 0 and booking.assignment_state == "assigned")
    not_required_bookings = sum(1 for booking in BOOKINGS if booking.assignment_state == "not_required")
    checks["future_new_unassigned"] = future_new_unassigned
    checks["future_confirmed_unassigned"] = future_confirmed_unassigned
    checks["future_assigned"] = future_assigned
    checks["not_required_bookings"] = not_required_bookings
    if future_new_unassigned < 2:
        failures.append("future NEW unassigned count is below 2")
    if future_confirmed_unassigned < 3:
        failures.append("future CONFIRMED unassigned count is below 3")
    for booking in BOOKINGS:
        expected_active: set[tuple[UUID, UUID]] = set()
        removed_instructors: dict[UUID, set[UUID]] = {}
        cur.execute(
            """
            SELECT event_type, event_data
            FROM booking_events
            WHERE aggregate_id = %s
            ORDER BY aggregate_version ASC;
            """,
            (booking.id,),
        )
        ordered_events = cur.fetchall()
        next_event_index = 0
        for step in booking.assignments:
            instructor_id = _instructor_id(step.instructor_key)
            event_type = "BookingInstructorAssigned" if step.action == "assign" else "BookingInstructorRemoved"
            matching_index = next(
                (
                    index
                    for index, row in enumerate(ordered_events[next_event_index:], start=next_event_index)
                    if row["event_type"] == event_type
                    and row["event_data"].get("booking_activity_id") == str(step.booking_activity_id)
                    and row["event_data"].get("instructor_id") == str(instructor_id)
                ),
                None,
            )
            if matching_index is None:
                assignment_event_mismatches += 1
            else:
                next_event_index = matching_index + 1
            if step.action == "assign":
                removed_for_activity = removed_instructors.get(step.booking_activity_id, set())
                if any(removed_id != instructor_id for removed_id in removed_for_activity):
                    real_reassignments += 1
                expected_active.add((step.booking_activity_id, instructor_id))
            else:
                expected_active.discard((step.booking_activity_id, instructor_id))
                removed_instructors.setdefault(step.booking_activity_id, set()).add(instructor_id)
        for booking_activity_id, instructor_id in expected_active:
            cur.execute(
                """
                SELECT COUNT(*) AS count
                FROM booking_instructors bi
                JOIN instructors i ON i.id = bi.instructor_id
                WHERE bi.booking_activity_id = %s AND bi.instructor_id = %s
                  AND bi.active = true AND i.is_active = true;
                """,
                (booking_activity_id, instructor_id),
            )
            if int(cur.fetchone()["count"]) != 1:
                assignment_mismatches += 1
        for activity in booking.activities:
            cur.execute("SELECT COUNT(*) AS count FROM booking_instructors WHERE booking_activity_id = %s AND active = true;", (activity.id,))
            active_count = int(cur.fetchone()["count"])
            if booking.assignment_state == "assigned" and activity.assignment_required and active_count < 1:
                assignment_mismatches += 1
            if booking.assignment_state == "unassigned" and active_count:
                assignment_mismatches += 1
            if booking.assignment_state == "not_required" and active_count:
                assignment_mismatches += 1
    checks["assignment_mismatches"] = assignment_mismatches
    checks["assignment_event_mismatches"] = assignment_event_mismatches
    checks["real_reassignments"] = real_reassignments
    if assignment_mismatches:
        failures.append("assignment projection rows do not match expected active state")
    if assignment_event_mismatches:
        failures.append("assignment event history does not match expected ordered steps")
    if real_reassignments < 1:
        failures.append("missing real reassignment sequence")
    cur.execute(
        """
        SELECT COUNT(*) AS count
        FROM booking_instructors bi
        JOIN booking_activities ba ON ba.id = bi.booking_activity_id
        JOIN instructors i ON i.id = bi.instructor_id
        WHERE ba.booking_id = ANY(%s) AND bi.active = true AND i.is_active = false;
        """,
        ([booking.id for booking in BOOKINGS],),
    )
    checks["active_assignments_to_inactive_instructors"] = int(cur.fetchone()["count"])
    if checks["active_assignments_to_inactive_instructors"]:
        failures.append("active assignments reference inactive instructors")
    no_instructor_activity_ids = [activity.id for booking in BOOKINGS if not booking.requires_instructor for activity in booking.activities]
    cur.execute("SELECT COUNT(*) AS count FROM booking_instructors WHERE booking_activity_id = ANY(%s);", (no_instructor_activity_ids,))
    checks["no_instructor_assignment_rows"] = int(cur.fetchone()["count"])
    if checks["no_instructor_assignment_rows"]:
        failures.append("no-instructor booking has assignments")
    cur.execute("SELECT COUNT(*) AS count FROM booking_events WHERE aggregate_id = ANY(%s) AND event_type = 'BookingInstructorRemoved';", ([booking.id for booking in BOOKINGS],))
    checks["removal_events"] = int(cur.fetchone()["count"])
    if checks["removal_events"] < 2:
        failures.append("missing removal events")
    cur.execute("SELECT COUNT(*) AS count FROM bookings b JOIN users u ON u.customer_id = b.customer_id WHERE u.email = %s AND b.id = ANY(%s);", (CUSTOMER_LOGIN_EMAIL, [booking.id for booking in BOOKINGS]))
    checks["linked_customer_bookings"] = int(cur.fetchone()["count"])
    if checks["linked_customer_bookings"] < 6:
        failures.append("customer@example.com has fewer than 6 seed bookings")
    cur.execute(
        """
        SELECT COUNT(*) AS count
        FROM booking_instructors bi
        JOIN users u ON u.instructor_id = bi.instructor_id
        JOIN booking_activities ba ON ba.id = bi.booking_activity_id
        JOIN bookings b ON b.id = ba.booking_id
        WHERE u.email = %s AND bi.active = true AND b.event_at >= now() AND b.id = ANY(%s);
        """,
        (INSTRUCTOR_LOGIN_EMAIL, [booking.id for booking in BOOKINGS]),
    )
    checks["linked_instructor_future_assignments"] = int(cur.fetchone()["count"])
    if checks["linked_instructor_future_assignments"] < 5:
        failures.append("instructor@example.com has fewer than 5 future active seed assignments")
    expected_equipment = sum(len(booking.equipment) for booking in BOOKINGS)
    cur.execute("SELECT COUNT(*) AS count FROM booking_equipment_items WHERE booking_id = ANY(%s);", ([booking.id for booking in BOOKINGS],))
    checks["booking_equipment_rows"] = int(cur.fetchone()["count"])
    if checks["booking_equipment_rows"] != expected_equipment:
        failures.append("equipment rows do not match catalog")
    expected_prices = sum(len(booking.prices) for booking in BOOKINGS)
    cur.execute("SELECT COUNT(*) AS count FROM booking_price_components WHERE booking_id = ANY(%s);", ([booking.id for booking in BOOKINGS],))
    checks["booking_price_rows"] = int(cur.fetchone()["count"])
    if checks["booking_price_rows"] != expected_prices:
        failures.append("price rows do not match catalog")
    catalog_row_mismatches = 0
    for booking in BOOKINGS:
        cur.execute(
            """
            SELECT b.customer_id, b.primary_contact_id, c.customer_id AS contact_customer_id
            FROM bookings b
            LEFT JOIN customer_contacts c ON c.id = b.primary_contact_id
            WHERE b.id = %s;
            """,
            (booking.id,),
        )
        contact_row = cur.fetchone()
        if not contact_row or contact_row["customer_id"] != _customer_id(booking.customer_key) or contact_row["primary_contact_id"] != _contact_id(booking.contact_key) or contact_row["contact_customer_id"] != contact_row["customer_id"]:
            catalog_row_mismatches += 1
        for item in booking.equipment:
            cur.execute(
                """
                SELECT COUNT(*) AS count
                FROM booking_equipment_items
                WHERE id = %s AND booking_id = %s AND inventory_item_id = %s AND quantity_planned = %s;
                """,
                (item.id, booking.id, _inventory_id(item.inventory_key), item.quantity),
            )
            if int(cur.fetchone()["count"]) != 1:
                catalog_row_mismatches += 1
        for item in booking.prices:
            cur.execute(
                """
                SELECT COUNT(*) AS count
                FROM booking_price_components
                WHERE id = %s AND booking_id = %s AND component_type = %s
                  AND quantity = %s AND unit_price = %s AND total_price = %s;
                """,
                (item.id, booking.id, item.component_type, item.quantity, item.unit_price, item.total_price),
            )
            if int(cur.fetchone()["count"]) != 1:
                catalog_row_mismatches += 1
    checks["catalog_row_mismatches"] = catalog_row_mismatches
    if catalog_row_mismatches:
        failures.append("catalog detail rows do not match expected seed rows")
    cur.execute(
        """
        SELECT COUNT(*) AS count
        FROM (
            SELECT aggregate_id, aggregate_version,
                   row_number() OVER (PARTITION BY aggregate_id ORDER BY aggregate_version) AS expected_version
            FROM booking_events
            WHERE aggregate_id = ANY(%s)
        ) versions
        WHERE aggregate_version <> expected_version;
        """,
        ([booking.id for booking in BOOKINGS],),
    )
    checks["invalid_event_versions"] = int(cur.fetchone()["count"])
    if checks["invalid_event_versions"]:
        failures.append("event versions are not contiguous")
    projection_mismatches = 0
    for booking in BOOKINGS:
        aggregate = _load_or_new_aggregate(cur, booking.id)
        cur.execute("SELECT status, version, customer_id, activity_id, event_at, city, venue, requires_instructor, notes, participant_count, agreed_price FROM bookings WHERE id = %s;", (booking.id,))
        row = cur.fetchone()
        if not row or row["version"] != aggregate.version or row["status"] != (aggregate.status.value if aggregate.status else None) or row["customer_id"] != aggregate.customer_id or row["activity_id"] != aggregate.activity_id or row["event_at"] != aggregate.event_at or row["city"] != aggregate.city or row["venue"] != aggregate.venue or row["requires_instructor"] != aggregate.requires_instructor or row["notes"] != aggregate.notes or row["participant_count"] != aggregate.participant_count or row["agreed_price"] != aggregate.agreed_price:
            projection_mismatches += 1
    checks["projection_mismatches"] = projection_mismatches
    if projection_mismatches:
        failures.append("projections do not match aggregate state")
    if failures:
        checks["failures"] = failures
    return checks


def _verification_failed(verification: dict[str, object]) -> bool:
    return bool(verification.get("failures"))


def _safe_failure_name(value: object) -> str:
    text = re.sub(r"\b\w+://\S+", "[hidden-url]", str(value))
    text = re.sub(r"\S+@\S+", "[hidden-email]", text)
    return "".join(ch for ch in text if ch.isalnum() or ch in {" ", "_", "-", ".", "[", "]"}).strip()[:120] or "verification failure"


def verify() -> SeedReport:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            report = build_report(cur, "verify")
            verification = verify_with_cursor(cur)
        conn.rollback()
        return SeedReport("verify", report.reused, report.existing_seed, report.to_create, report.warnings, verification)


def _sanitize_error(exc: Exception) -> str:
    if isinstance(exc, SeedVerificationError):
        return f"SeedVerificationError: {', '.join(exc.failures)}"
    name = exc.__class__.__name__
    return f"{name}: seed operation failed; database connection details were hidden"


def _print_report(report: SeedReport) -> None:
    print(f"מצב הרצה: {report.mode}")
    print("רשומות קיימות לשימוש חוזר:")
    for key, value in report.reused.items():
        print(f"  {key}: {value}")
    print("רשומות דמו קיימות:")
    for key, value in report.existing_seed.items():
        print(f"  {key}: {value}")
    print("רשומות או אירועים שיידרשו להשלמה:")
    for key, value in report.to_create.items():
        print(f"  {key}: {value}")
    if report.warnings:
        print("אזהרות:")
        for warning in report.warnings:
            print(f"  {warning}")
    if report.verification:
        print("אימות:")
        for key, value in report.verification.items():
            print(f"  {key}: {value}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create or verify deterministic Hebrew demo seed data.")
    parser.add_argument("--apply", action="store_true", help="Write missing demo data. Requires explicit confirmation phrase.")
    parser.add_argument("--verify", action="store_true", help="Run read-only verification checks.")
    parser.add_argument("--confirm", default="", help="Required with --apply: אני מאשר יצירת נתוני דמו")
    args = parser.parse_args(argv)
    try:
        if args.apply:
            if args.confirm != CONFIRMATION_PHRASE:
                print(f"--apply requires --confirm \"{CONFIRMATION_PHRASE}\"")
                return 2
            _print_report(apply_seed())
            return 0
        if args.verify:
            report = verify()
            _print_report(report)
            return 1 if report.verification and _verification_failed(report.verification) else 0
        _print_report(dry_run())
        return 0
    except Exception as exc:
        print(_sanitize_error(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
