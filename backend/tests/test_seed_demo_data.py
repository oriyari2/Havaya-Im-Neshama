from __future__ import annotations

from copy import deepcopy
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from backend.app.db import init_db, seed_demo_data
from backend.app.domain.bookings.status import BookingStatus


class _Cursor:
    def __init__(self, rows: list[tuple] | None = None) -> None:
        self.rows = list(rows or [])
        self.statements: list[str] = []

    def __enter__(self) -> "_Cursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def execute(self, query: str, params=None) -> None:
        self.statements.append(query.strip())

    def fetchone(self) -> tuple:
        return self.rows.pop(0) if self.rows else (0,)


class _Connection:
    def __init__(self, cursor: _Cursor | None = None) -> None:
        self.test_cursor = cursor or _Cursor()
        self.commit = Mock()
        self.rollback = Mock()

    def cursor(self, row_factory=None) -> _Cursor:
        return self.test_cursor


class DemoSeedWorkflowTests(unittest.TestCase):
    def test_dry_run_is_read_only_and_does_not_recreate_users(self) -> None:
        conn = _Connection()

        with patch.object(seed_demo_data, "seed_demo_users") as seed_users_mock:
            report = seed_demo_data.seed_demo_data(conn, dry_run=True)

        self.assertEqual(report["mode"], "dry-run")
        self.assertTrue(conn.test_cursor.statements)
        for statement in conn.test_cursor.statements:
            first_word = statement.split(maxsplit=1)[0].upper()
            self.assertEqual(first_word, "SELECT")
        conn.commit.assert_not_called()
        conn.rollback.assert_called_once_with()
        seed_users_mock.assert_not_called()

    def test_successful_refresh_uses_one_transaction_and_existing_user_seeder(self) -> None:
        conn = _Connection()
        operation_order: list[str] = []

        with (
            patch.object(seed_demo_data, "check_external_references", return_value=[]),
            patch.object(seed_demo_data, "inspect_demo_records", return_value={}),
            patch.object(seed_demo_data, "delete_demo_data", side_effect=lambda _conn: operation_order.append("delete")),
            patch.object(seed_demo_data, "insert_demo_business_data", side_effect=lambda _conn: operation_order.append("insert")),
            patch.object(seed_demo_data, "seed_demo_users", side_effect=lambda _conn, commit: operation_order.append("users")) as seed_users_mock,
        ):
            report = seed_demo_data.seed_demo_data(conn)

        self.assertEqual(report["mode"], "refresh")
        self.assertEqual(operation_order, ["delete", "insert", "users"])
        seed_users_mock.assert_called_once_with(conn, commit=False)
        conn.commit.assert_called_once_with()
        conn.rollback.assert_not_called()

    def test_demo_user_seeder_recreates_all_three_accounts_with_existing_logic(self) -> None:
        customer_id = uuid4()
        instructor_id = uuid4()
        conn = _Connection(_Cursor([(customer_id,), (instructor_id,)]))

        with (
            patch.object(init_db, "hash_password", side_effect=lambda password, salt: f"hash:{password}:{salt}"),
            patch.object(init_db, "upsert_demo_user") as upsert_mock,
        ):
            init_db.seed_demo_users(conn, commit=False)

        self.assertEqual(
            [user_call.args[1] for user_call in upsert_mock.call_args_list],
            ["manager@example.com", "instructor@example.com", "customer@example.com"],
        )
        self.assertEqual(
            [user_call.args[2] for user_call in upsert_mock.call_args_list],
            [
                "hash:manager123:demo-manager-salt",
                "hash:instructor123:demo-instructor-salt",
                "hash:customer123:demo-customer-salt",
            ],
        )
        conn.commit.assert_not_called()

    def test_failure_rolls_back_full_refresh_without_commit(self) -> None:
        conn = _Connection()

        with (
            patch.object(seed_demo_data, "check_external_references", return_value=[]),
            patch.object(seed_demo_data, "inspect_demo_records", return_value={}),
            patch.object(seed_demo_data, "delete_demo_data"),
            patch.object(seed_demo_data, "insert_demo_business_data", side_effect=RuntimeError("insert failed")),
            patch.object(seed_demo_data, "seed_demo_users") as seed_users_mock,
        ):
            with self.assertRaisesRegex(RuntimeError, "insert failed"):
                seed_demo_data.seed_demo_data(conn)

        conn.rollback.assert_called_once_with()
        conn.commit.assert_not_called()
        seed_users_mock.assert_not_called()

    def test_external_reference_aborts_before_any_deletion(self) -> None:
        conn = _Connection()
        external = seed_demo_data.ExternalReference(
            table="bookings",
            relationship="customer_id -> customers.id",
            count=1,
        )

        with (
            patch.object(seed_demo_data, "check_external_references", return_value=[external]),
            patch.object(seed_demo_data, "inspect_demo_records") as inspect_mock,
            patch.object(seed_demo_data, "delete_demo_data") as delete_mock,
        ):
            with self.assertRaises(seed_demo_data.DemoSeedSafetyError) as raised:
                seed_demo_data.seed_demo_data(conn)

        self.assertEqual(raised.exception.references, [external])
        inspect_mock.assert_not_called()
        delete_mock.assert_not_called()
        conn.commit.assert_not_called()

    def test_deterministic_business_payload_is_identical_across_runs(self) -> None:
        first = {
            "customers": deepcopy(seed_demo_data.CUSTOMERS),
            "contacts": deepcopy(seed_demo_data.CONTACTS),
            "instructors": deepcopy(seed_demo_data.INSTRUCTORS),
            "activities": deepcopy(seed_demo_data.ACTIVITIES),
            "bookings": deepcopy(seed_demo_data.booking_seed_rows()),
            "booking_activities": deepcopy(seed_demo_data.BOOKING_ACTIVITIES),
        }
        second = {
            "customers": deepcopy(seed_demo_data.CUSTOMERS),
            "contacts": deepcopy(seed_demo_data.CONTACTS),
            "instructors": deepcopy(seed_demo_data.INSTRUCTORS),
            "activities": deepcopy(seed_demo_data.ACTIVITIES),
            "bookings": deepcopy(seed_demo_data.booking_seed_rows()),
            "booking_activities": deepcopy(seed_demo_data.BOOKING_ACTIVITIES),
        }

        self.assertEqual(first, second)

    def test_seed_booking_statuses_are_domain_values(self) -> None:
        supported = {status.value for status in BookingStatus}
        statuses = {booking[10] for booking in seed_demo_data.BOOKINGS}

        self.assertTrue(statuses <= supported)
        self.assertEqual(statuses, {BookingStatus.NEW.value, BookingStatus.CONFIRMED.value})


if __name__ == "__main__":
    unittest.main()
