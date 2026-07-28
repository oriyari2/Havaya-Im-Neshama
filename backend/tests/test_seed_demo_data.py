from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from backend.app.db import demo_seed_catalog as catalog
from backend.app.db import seed_demo_data
from backend.app.domain.bookings.aggregate import BookingAggregate
from backend.app.domain.bookings.status import BookingStatus


class DemoSeedCatalogTests(unittest.TestCase):
    def test_target_demo_volume_is_realistic(self) -> None:
        self.assertGreaterEqual(len(catalog.CUSTOMERS), 15)
        self.assertGreaterEqual(len(catalog.CONTACTS), 24)
        self.assertGreaterEqual(len(catalog.INSTRUCTORS), 10)
        self.assertGreaterEqual(len(catalog.ACTIVITIES), 10)
        self.assertGreaterEqual(len(catalog.BOOKINGS), 30)

    def test_status_distribution_exercises_dashboards(self) -> None:
        statuses = [booking.status for booking in catalog.BOOKINGS]
        self.assertEqual(statuses.count(BookingStatus.NEW.value), 4)
        self.assertGreaterEqual(statuses.count(BookingStatus.CONFIRMED.value), 16)
        self.assertGreaterEqual(statuses.count(BookingStatus.COMPLETED.value), 8)
        self.assertGreaterEqual(statuses.count(BookingStatus.CANCELLED.value), 4)

    def test_planned_assignment_state_is_explicit_for_every_booking(self) -> None:
        by_state = {
            state: [booking.key for booking in catalog.BOOKINGS if booking.assignment_state == state]
            for state in ("assigned", "unassigned", "not_required")
        }

        self.assertEqual(by_state["unassigned"], ["booking-3", "booking-6", "booking-24", "booking-27", "booking-30"])
        self.assertEqual(by_state["not_required"], ["booking-10", "booking-18"])
        self.assertEqual(len(by_state["assigned"]), 25)
        self.assertEqual(sum(len(keys) for keys in by_state.values()), 32)

    def test_demo_booking_scenarios_include_multi_activity_removal_and_reassignment(self) -> None:
        multi_activity = [booking for booking in catalog.BOOKINGS if len(booking.activities) > 1]
        removals = [step for booking in catalog.BOOKINGS for step in booking.assignments if step.action == "remove"]
        reassigned = [
            booking
            for booking in catalog.BOOKINGS
            if any(step.action == "remove" for step in booking.assignments)
            and any(step.action == "assign" for step in booking.assignments[2:])
        ]

        self.assertGreaterEqual(len(multi_activity), 4)
        self.assertGreaterEqual(len(removals), 2)
        self.assertGreaterEqual(len(reassigned), 1)

    def test_booking_contacts_belong_to_booking_customer(self) -> None:
        contacts_by_key = {contact.key: contact for contact in catalog.CONTACTS}
        for booking in catalog.BOOKINGS:
            self.assertEqual(contacts_by_key[booking.contact_key].customer_key, booking.customer_key)

    def test_no_instructor_bookings_have_no_assignments(self) -> None:
        no_instructor = [booking for booking in catalog.BOOKINGS if not booking.requires_instructor]
        self.assertGreaterEqual(len(no_instructor), 2)
        for booking in no_instructor:
            self.assertFalse(booking.assignments)
            self.assertTrue(all(not activity.assignment_required for activity in booking.activities))

    def test_completed_instructor_required_bookings_have_assignment_history(self) -> None:
        for booking in catalog.BOOKINGS:
            if booking.status == BookingStatus.COMPLETED.value and booking.requires_instructor:
                self.assertTrue(booking.assignments, booking.key)

    def test_assigned_bookings_end_with_active_assignment_coverage(self) -> None:
        for booking in catalog.BOOKINGS:
            if booking.assignment_state != "assigned":
                continue
            active: set[tuple[object, str]] = set()
            for step in booking.assignments:
                pair = (step.booking_activity_id, step.instructor_key)
                if step.action == "assign":
                    active.add(pair)
                else:
                    active.discard(pair)
            for activity in booking.activities:
                if activity.assignment_required:
                    self.assertTrue(any(activity.id == activity_id for activity_id, _ in active), booking.key)

    def test_unassigned_bookings_require_instructor_without_active_assignments(self) -> None:
        unassigned = [booking for booking in catalog.BOOKINGS if booking.assignment_state == "unassigned"]
        self.assertGreaterEqual(
            len([booking for booking in unassigned if booking.days_from_now >= 0 and booking.status == BookingStatus.NEW.value]),
            2,
        )
        self.assertGreaterEqual(
            len([booking for booking in unassigned if booking.days_from_now >= 0 and booking.status == BookingStatus.CONFIRMED.value]),
            3,
        )
        for booking in unassigned:
            self.assertTrue(booking.requires_instructor, booking.key)
            self.assertTrue(all(activity.assignment_required for activity in booking.activities), booking.key)
            self.assertFalse(booking.assignments, booking.key)

    def test_not_required_bookings_have_no_instructor_requirement_or_assignments(self) -> None:
        not_required = [booking for booking in catalog.BOOKINGS if booking.assignment_state == "not_required"]
        self.assertGreaterEqual(len(not_required), 2)
        for booking in not_required:
            self.assertFalse(booking.requires_instructor, booking.key)
            self.assertTrue(all(not activity.assignment_required for activity in booking.activities), booking.key)
            self.assertFalse(booking.assignments, booking.key)

    def test_login_instructor_receives_at_least_five_planned_future_assignments(self) -> None:
        future_assignments = [
            step
            for booking in catalog.BOOKINGS
            if booking.days_from_now >= 0
            for step in booking.assignments
            if step.action == "assign" and step.instructor_key == "instructor-1"
        ]
        self.assertGreaterEqual(len(future_assignments), 5)

    def test_booking_15_and_17_remain_real_reassignment_sequences(self) -> None:
        for key in ("booking-15", "booking-17"):
            booking = next(item for item in catalog.BOOKINGS if item.key == key)
            self.assertEqual([step.action for step in booking.assignments[:3]], ["assign", "remove", "assign"])
            self.assertEqual(booking.assignments[0].booking_activity_id, booking.assignments[1].booking_activity_id)
            self.assertEqual(booking.assignments[1].booking_activity_id, booking.assignments[2].booking_activity_id)
            self.assertNotEqual(booking.assignments[0].instructor_key, booking.assignments[2].instructor_key)

    def test_multi_activity_assignments_are_coherent(self) -> None:
        multi_activity = [booking for booking in catalog.BOOKINGS if len(booking.activities) > 1]
        self.assertTrue(any(len({step.instructor_key for step in booking.assignments if step.action == "assign"}) > 1 for booking in multi_activity))
        for booking in multi_activity:
            assigned_activity_ids = {step.booking_activity_id for step in booking.assignments if step.action == "assign"}
            for activity in booking.activities:
                self.assertTrue(activity.id in assigned_activity_ids or not activity.assignment_required, booking.key)

    def test_parallel_active_instructors_are_not_reassignment_sequence(self) -> None:
        booking = next(item for item in catalog.BOOKINGS if item.key == "booking-1")
        synthetic = catalog.BookingSeed(
            **{
                **booking.__dict__,
                "assignments": (
                    catalog.AssignmentStep(booking.activities[0].id, "instructor-1", "assign"),
                    catalog.AssignmentStep(booking.activities[0].id, "instructor-2", "assign"),
                ),
            }
        )
        removed: dict[object, set[str]] = {}
        real_reassignments = 0

        for step in synthetic.assignments:
            if step.action == "assign":
                if any(removed_id != step.instructor_key for removed_id in removed.get(step.booking_activity_id, set())):
                    real_reassignments += 1
            else:
                removed.setdefault(step.booking_activity_id, set()).add(step.instructor_key)

        self.assertEqual(real_reassignments, 0)

    def test_equipment_matches_activity_requirements(self) -> None:
        requirements = {}
        for requirement in catalog.REQUIREMENTS:
            requirements.setdefault(requirement.activity_key, set()).add(requirement.inventory_key)
        for booking in catalog.BOOKINGS:
            equipment_keys = {item.inventory_key for item in booking.equipment}
            for activity in booking.activities:
                required_keys = requirements.get(activity.activity_key, set())
                self.assertTrue(required_keys.intersection(equipment_keys), booking.key)

    def test_pricing_matches_activity_scenarios(self) -> None:
        sukkah_bookings = [booking for booking in catalog.BOOKINGS if any(activity.activity_key == "activity-5" for activity in booking.activities)]
        self.assertTrue(sukkah_bookings)
        self.assertTrue(any(booking.include_sign_quiz_addon for booking in sukkah_bookings))
        self.assertTrue(any(not booking.include_sign_quiz_addon for booking in sukkah_bookings))
        for booking in sukkah_bookings:
            activity_component = next(item for item in booking.prices if item.component_type == "פעילות")
            expected = 34 if booking.participants <= 100 else 28
            self.assertEqual(activity_component.unit_price, expected)
        karmiel = [booking for booking in catalog.BOOKINGS if booking.city == "כרמיאל"]
        self.assertTrue(all(any(item.component_type == "נסיעות" and item.total_price == 450 for item in booking.prices) for booking in karmiel))

    def test_runtime_catalog_text_is_real_hebrew_not_mojibake(self) -> None:
        values = [
            catalog.DEMO_MARKER,
            catalog.CUSTOMERS[0].name,
            catalog.ACTIVITIES[0].name,
            catalog.INVENTORY_ITEMS[-1].name,
            catalog.BOOKINGS[0].title,
        ]
        for value in values:
            self.assertRegex(value, r"[\u0590-\u05ff]")
            self.assertNotIn("×", value)
            self.assertNotIn("â‚ª", value)
            self.assertNotIn("\ufffd", value)

    def test_customer_login_profile_has_six_coherent_seed_bookings(self) -> None:
        customer_bookings = [booking for booking in catalog.BOOKINGS if booking.customer_key == "customer-1"]
        statuses = {booking.status for booking in customer_bookings}

        self.assertGreaterEqual(len(customer_bookings), 6)
        self.assertTrue(any(booking.days_from_now < 0 for booking in customer_bookings))
        self.assertTrue(any(booking.days_from_now > 0 for booking in customer_bookings))
        self.assertGreaterEqual(len(statuses), 3)

    def test_event_times_use_project_timezone_convention(self) -> None:
        self.assertEqual(catalog.BOOKINGS[0].event_at.tzinfo, ZoneInfo("Asia/Jerusalem"))

    def test_booking_seed_has_no_compatibility_getitem(self) -> None:
        self.assertNotIn("__getitem__", catalog.BookingSeed.__dict__)

    def test_activity_specific_pricing_rules_do_not_leak(self) -> None:
        expected_units = {
            "activity-4": {Decimal("32"), Decimal("27")},
            "activity-7": {Decimal("38"), Decimal("33")},
            "activity-12": {Decimal("45"), Decimal("39")},
        }
        for activity_key, allowed_units in expected_units.items():
            for booking in catalog.BOOKINGS:
                if not any(activity.activity_key == activity_key for activity in booking.activities):
                    continue
                matching = [
                    component
                    for component in booking.prices
                    if component.component_type == "פעילות"
                    and catalog.ACTIVITIES[int(activity_key.split("-")[1]) - 1].name in component.description
                ]
                self.assertTrue(matching, booking.key)
                self.assertIn(matching[0].unit_price, allowed_units)
                self.assertNotIn(matching[0].unit_price, {Decimal("34"), Decimal("28")})

    def test_sign_quiz_add_on_is_not_double_charged(self) -> None:
        for booking in catalog.BOOKINGS:
            activity_keys = {activity.activity_key for activity in booking.activities}
            addon_components = [
                component
                for component in booking.prices
                if component.component_type == "תוספת" and component.unit_price == Decimal("10")
            ]
            if booking.include_sign_quiz_addon and "activity-5" in activity_keys and "activity-3" not in activity_keys:
                self.assertEqual(len(addon_components), 1, booking.key)
            else:
                self.assertFalse(addon_components, booking.key)

    def test_activity_durations_and_offsets_are_respected(self) -> None:
        activities_by_key = {activity.key: activity for activity in catalog.ACTIVITIES}
        for booking in catalog.BOOKINGS:
            for activity in booking.activities:
                self.assertEqual(activity.duration_minutes, activities_by_key[activity.activity_key].duration_minutes)
            offsets = [activity.offset_minutes for activity in booking.activities]
            self.assertEqual(offsets, sorted(offsets))
            expected_offsets = []
            cumulative = 0
            for activity in booking.activities:
                expected_offsets.append(cumulative)
                cumulative += activity.duration_minutes
            self.assertEqual(offsets, expected_offsets, booking.key)

    def test_booking_activity_participants_do_not_exceed_activity_capacity_without_round_notes(self) -> None:
        activities_by_key = {activity.key: activity for activity in catalog.ACTIVITIES}
        for booking in catalog.BOOKINGS:
            for activity in booking.activities:
                catalog_activity = activities_by_key[activity.activity_key]
                if activity.participants_count <= catalog_activity.max_participants:
                    continue
                self.assertRegex(activity.notes, r"[\u05e1][\u05d1][\u05d1][\u05d9][\u05dd]", booking.key)

    def test_multi_activity_offsets_use_previous_activity_duration(self) -> None:
        booking = next(item for item in catalog.BOOKINGS if item.key == "booking-5")

        self.assertNotEqual(booking.activities[0].duration_minutes, booking.activities[1].duration_minutes)
        self.assertEqual(booking.activities[1].offset_minutes, booking.activities[0].duration_minutes)

    def test_all_demo_facing_text_is_hebrew_or_safe_operational_value(self) -> None:
        def assert_hebrew(value: str) -> None:
            if "example.com" in value or value in {status.value for status in BookingStatus}:
                return
            self.assertNotRegex(value, r"\b(Tfos|Merotz|Beit|School|Demo)\b", value)

        for customer in catalog.CUSTOMERS:
            for value in (customer.name, customer.customer_type, customer.city, customer.address, customer.notes):
                assert_hebrew(value)
        for contact in catalog.CONTACTS:
            for value in (contact.full_name, contact.role_title):
                assert_hebrew(value)
        for instructor in catalog.INSTRUCTORS:
            for value in (instructor.full_name, instructor.city, instructor.notes):
                assert_hebrew(value)
        for activity in catalog.ACTIVITIES:
            for value in (
                activity.name,
                activity.description,
                activity.target_audience,
                activity.price_notes,
                activity.pricing_rule,
                activity.required_equipment,
                activity.preparation_notes,
                activity.season,
                activity.tags,
            ):
                assert_hebrew(value)
        for booking in catalog.BOOKINGS:
            for value in (
                booking.title,
                booking.city,
                booking.venue,
                booking.address,
                booking.audience_type,
                booking.internal_notes,
                booking.customer_notes,
                booking.vehicle_notes or "",
                booking.loading_notes or "",
            ):
                if value:
                    assert_hebrew(value)


class DemoSeedCliTests(unittest.TestCase):
    def test_default_main_runs_read_only_dry_run(self) -> None:
        report = seed_demo_data.SeedReport("dry-run", {}, {}, {}, [])
        with (
            patch.object(seed_demo_data, "dry_run", return_value=report) as dry_run_mock,
            patch.object(seed_demo_data, "_print_report"),
        ):
            result = seed_demo_data.main([])

        self.assertEqual(result, 0)
        dry_run_mock.assert_called_once_with()

    def test_apply_requires_explicit_confirmation_phrase(self) -> None:
        with (
            patch.object(seed_demo_data, "apply_seed") as apply_mock,
            patch("builtins.print"),
        ):
            result = seed_demo_data.main(["--apply"])

        self.assertEqual(result, 2)
        apply_mock.assert_not_called()

    def test_apply_with_confirmation_calls_apply_seed(self) -> None:
        report = seed_demo_data.SeedReport("apply", {}, {}, {}, [])
        with (
            patch.object(seed_demo_data, "apply_seed", return_value=report) as apply_mock,
            patch.object(seed_demo_data, "_print_report"),
        ):
            result = seed_demo_data.main(["--apply", "--confirm", seed_demo_data.CONFIRMATION_PHRASE])

        self.assertEqual(result, 0)
        apply_mock.assert_called_once_with()

    def test_exception_output_is_sanitized(self) -> None:
        message = seed_demo_data._sanitize_error(RuntimeError("postgresql://secret@example"))

        self.assertNotIn("postgresql://secret@example", message)
        self.assertIn("connection details were hidden", message)


class DemoSeedSqlContractTests(unittest.TestCase):
    def test_no_destructive_sql_in_seed_module(self) -> None:
        source = seed_demo_data.__loader__.get_source(seed_demo_data.__name__)

        self.assertIsNotNone(source)
        assert source is not None
        self.assertNotIn("DELETE FROM", source.upper())
        self.assertNotIn("TRUNCATE", source.upper())
        self.assertNotIn("DROP TABLE", source.upper())

    def test_event_sourcing_path_uses_booking_events_and_projection_sync(self) -> None:
        source = seed_demo_data.__loader__.get_source(seed_demo_data.__name__)

        self.assertIsNotNone(source)
        assert source is not None
        self.assertIn("INSERT INTO booking_events", source)
        self.assertIn("BookingAggregate", source)
        self.assertIn("projection_repo.upsert_projection", source)
        self.assertIn("projection_repo.sync_instructor_projection", source)

    def test_apply_never_calls_upsert_demo_user(self) -> None:
        source = seed_demo_data.__loader__.get_source(seed_demo_data.__name__)

        self.assertIsNotNone(source)
        assert source is not None
        self.assertNotIn("upsert_demo_user", source)
        self.assertNotIn("hash_password", source)

    def test_activity_resolution_is_used_for_relationships(self) -> None:
        seed_demo_data._ACTIVITY_ID_BY_KEY = {"activity-1": catalog.demo_id(99, 1)}

        self.assertEqual(seed_demo_data._activity_id("activity-1"), catalog.demo_id(99, 1))

    def test_relationship_reuse_resolution_avoids_duplicate_instruction_notes(self) -> None:
        note = catalog.INSTRUCTION_NOTES[0]
        reused_id = catalog.demo_id(99, 11)
        cursor = Mock()
        cursor.fetchone.side_effect = [None, {"id": reused_id}]
        seed_demo_data._ACTIVITY_ID_BY_KEY = {note.activity_key: catalog.demo_id(99, 1)}

        with patch.object(seed_demo_data, "INSTRUCTION_NOTES", (note,)):
            resolved = seed_demo_data._resolve_instruction_ids(cursor)

        self.assertEqual(resolved[note.id], reused_id)
        matching_sql = cursor.execute.call_args_list[1].args[0]
        matching_params = cursor.execute.call_args_list[1].args[1]
        self.assertIn("activity_id = %s", matching_sql)
        self.assertEqual(matching_params[1], seed_demo_data._normalize_name(note.title))

    def test_relationship_reuse_resolution_avoids_duplicate_equipment_requirements(self) -> None:
        requirement = catalog.REQUIREMENTS[0]
        reused_id = catalog.demo_id(99, 12)
        cursor = Mock()
        cursor.fetchone.side_effect = [None, {"id": reused_id}]
        seed_demo_data._ACTIVITY_ID_BY_KEY = {requirement.activity_key: catalog.demo_id(99, 1)}
        seed_demo_data._INVENTORY_ID_BY_KEY = {requirement.inventory_key: catalog.demo_id(99, 2)}

        with patch.object(seed_demo_data, "REQUIREMENTS", (requirement,)):
            resolved = seed_demo_data._resolve_requirement_ids(cursor)

        self.assertEqual(resolved[requirement.id], reused_id)
        matching_sql = cursor.execute.call_args_list[1].args[0]
        matching_params = cursor.execute.call_args_list[1].args[1]
        self.assertIn("activity_id = %s", matching_sql)
        self.assertIn("inventory_item_id = %s", matching_sql)
        self.assertEqual(matching_params, (seed_demo_data._activity_id(requirement.activity_key), seed_demo_data._inventory_id(requirement.inventory_key)))

    def test_no_startup_coupling_to_demo_seed(self) -> None:
        import backend.app.main as backend_main

        source = backend_main.__loader__.get_source(backend_main.__name__) or ""
        self.assertNotIn("seed_demo_data", source)


class DemoSeedWorkflowTests(unittest.TestCase):
    def test_existing_aggregate_event_date_does_not_drift_on_rerun_projection_update(self) -> None:
        booking = catalog.BOOKINGS[0]
        original_event_at = datetime(2026, 8, 10, 9, tzinfo=ZoneInfo("Asia/Jerusalem"))
        aggregate = BookingAggregate(
            id=booking.id,
            customer_id=seed_demo_data._customer_id(booking.customer_key),
            activity_id=seed_demo_data._activity_id(booking.activities[0].activity_key),
            event_at=original_event_at,
            city=booking.city,
            venue=booking.venue,
            participant_count=booking.participants,
            agreed_price=booking.agreed_price,
            status=BookingStatus.CONFIRMED,
            requires_instructor=booking.requires_instructor,
            notes=booking.internal_notes,
            version=3,
        )
        later_catalog_booking = catalog.BookingSeed(**{**booking.__dict__, "days_from_now": booking.days_from_now + 30})
        cursor = Mock()

        seed_demo_data._update_rich_booking_projection(cursor, later_catalog_booking, aggregate)

        update_params = cursor.execute.call_args_list[0].args[1]
        self.assertEqual(update_params[1], original_event_at)
        self.assertEqual(update_params[12], original_event_at)
        self.assertNotEqual(later_catalog_booking.event_at, original_event_at)

    def test_apply_rolls_back_on_failure(self) -> None:
        conn = Mock()
        cursor_cm = Mock()
        cursor = Mock()
        cursor_cm.__enter__ = Mock(return_value=cursor)
        cursor_cm.__exit__ = Mock(return_value=False)
        conn.cursor.return_value = cursor_cm

        with (
            patch.object(seed_demo_data, "get_connection") as get_connection,
            patch.object(seed_demo_data, "build_report", side_effect=RuntimeError("boom")),
        ):
            get_connection.return_value.__enter__.return_value = conn
            with self.assertRaises(RuntimeError):
                seed_demo_data.apply_seed()

        conn.rollback.assert_called_once_with()
        conn.commit.assert_not_called()

    def test_apply_rolls_back_when_post_apply_verification_fails(self) -> None:
        conn = Mock()
        cursor_cm = Mock()
        cursor = Mock()
        cursor_cm.__enter__ = Mock(return_value=cursor)
        cursor_cm.__exit__ = Mock(return_value=False)
        conn.cursor.return_value = cursor_cm
        report = seed_demo_data.SeedReport("apply", {}, {}, {}, [])
        verification = {"failures": ["postgresql://secret@example missing required assignment rows"]}

        with (
            patch.object(seed_demo_data, "get_connection") as get_connection,
            patch.object(seed_demo_data, "build_report", return_value=report),
            patch.object(seed_demo_data, "_get_required_login_links", return_value={}),
            patch.object(seed_demo_data, "_use_existing_login_profiles"),
            patch.object(seed_demo_data, "_upsert_business_data"),
            patch.object(seed_demo_data, "_get_user_id", return_value=catalog.demo_id(99, 1)),
            patch.object(seed_demo_data, "_ensure_booking_event_history"),
            patch.object(seed_demo_data, "verify_with_cursor", return_value=verification),
        ):
            get_connection.return_value.__enter__.return_value = conn
            with self.assertRaises(seed_demo_data.SeedVerificationError) as raised:
                seed_demo_data.apply_seed()

        conn.rollback.assert_called_once_with()
        conn.commit.assert_not_called()
        message = seed_demo_data._sanitize_error(raised.exception)
        self.assertNotIn("postgresql://secret@example", message)
        self.assertIn("missing required assignment rows", message)


if __name__ == "__main__":
    unittest.main()
