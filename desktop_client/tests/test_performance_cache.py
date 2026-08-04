from __future__ import annotations

import threading
import time
import unittest

from desktop_client.app.api.client import ApiClient
from desktop_client.app.infrastructure.performance_cache import CacheCapacityError, SessionPerformanceCache, policy_for_path
from desktop_client.app.features.auth.service import AuthService


class _Clock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now


class PerformanceCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = _Clock()
        self.cache = SessionPerformanceCache(max_entries=3, max_bytes=2048, max_inflight=2, clock=self.clock)
        self.cache.start_session("user-1", "manager")

    def tearDown(self) -> None:
        self.cache.shutdown()

    def test_hit_uses_all_query_dimensions_and_returns_defensive_copies(self) -> None:
        calls = 0

        def load():
            nonlocal calls
            calls += 1
            return [{"id": calls}]

        dimensions = {"page": 1, "page_size": 20, "search": "north", "status": "active", "sort": "name", "customer_id": "owned"}
        first = self.cache.get_or_load("/customers", dimensions, load)
        first[0]["id"] = 999
        self.assertEqual(self.cache.get_or_load("/customers", dict(reversed(list(dimensions.items()))), load), [{"id": 1}])
        self.cache.get_or_load("/customers", {**dimensions, "page": 2}, load)
        self.cache.get_or_load("/customers", {**dimensions, "search": "south"}, load)
        self.cache.get_or_load("/customers", {**dimensions, "page_size": 50}, load)
        self.cache.get_or_load("/customers", {**dimensions, "status": "inactive"}, load)
        self.cache.get_or_load("/customers", {**dimensions, "sort": "created_at"}, load)
        self.cache.get_or_load("/customers", {**dimensions, "customer_id": "other-owner"}, load)
        self.cache.get_or_load("/customers", {**dimensions, "city": "Haifa"}, load)
        self.assertEqual(calls, 8)
        self.assertEqual(self.cache.snapshot()["hits"], 1)

    def test_identical_concurrent_reads_are_coalesced(self) -> None:
        entered = threading.Event()
        release = threading.Event()
        calls = 0
        results: list[object] = []

        def load():
            nonlocal calls
            calls += 1
            entered.set()
            release.wait(2)
            return {"value": 7}

        threads = [threading.Thread(target=lambda: results.append(self.cache.get_or_load("/instructors", {}, load))) for _ in range(2)]
        threads[0].start()
        self.assertTrue(entered.wait(1))
        threads[1].start()
        release.set()
        for thread in threads:
            thread.join(2)
        self.assertEqual(calls, 1)
        self.assertEqual(results, [{"value": 7}, {"value": 7}])
        self.assertEqual(self.cache.snapshot()["coalesced"], 1)

    def test_travel_estimate_is_never_served_from_session_cache(self) -> None:
        self.assertIsNone(policy_for_path("/bookings/booking-1/travel-estimate"))

    def test_open_event_availability_is_never_served_from_session_cache(self) -> None:
        calls = 0

        def load():
            nonlocal calls
            calls += 1
            return [{"id": calls}]

        self.assertEqual(self.cache.get_or_load("/bookings/open-events", {}, load), [{"id": 1}])
        self.assertEqual(self.cache.get_or_load("/bookings/open-events", {}, load), [{"id": 2}])
        self.assertEqual(calls, 2)

    def test_failed_read_is_not_cached_and_does_not_poison_retry(self) -> None:
        calls = 0

        def load():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise RuntimeError("offline")
            return ["recovered"]

        with self.assertRaisesRegex(RuntimeError, "offline"):
            self.cache.get_or_load("/api/rag/sources", {}, load)
        self.assertEqual(self.cache.inflight_count, 0)
        self.assertEqual(self.cache.get_or_load("/api/rag/sources", {}, load), ["recovered"])
        self.assertEqual(calls, 2)

    def test_hard_ttl_refetches_and_swr_returns_stale_then_refreshes(self) -> None:
        hard_calls = 0

        def hard_load():
            nonlocal hard_calls
            hard_calls += 1
            return hard_calls

        self.assertEqual(self.cache.get_or_load("/api/rag/sources", {}, hard_load), 1)
        self.clock.now += 21
        self.assertEqual(self.cache.get_or_load("/api/rag/sources", {}, hard_load), 2)

        refreshed = threading.Event()
        soft_calls = 0

        def soft_load():
            nonlocal soft_calls
            soft_calls += 1
            if soft_calls > 1:
                refreshed.set()
            return soft_calls

        self.assertEqual(self.cache.get_or_load("/customers", {}, soft_load), 1)
        self.clock.now += 31
        self.assertEqual(self.cache.get_or_load("/customers", {}, soft_load), 1)
        self.assertTrue(refreshed.wait(1))
        current = 1
        deadline = time.monotonic() + 1
        while current == 1 and time.monotonic() < deadline:
            current = self.cache.get_or_load("/customers", {}, soft_load)
            time.sleep(0.005)
        self.assertEqual(current, 2)

    def test_bounds_evict_lru_and_reject_secret_or_oversize_payloads(self) -> None:
        for index in range(4):
            self.cache.get_or_load("/customers", {"page": index}, lambda index=index: {"id": index})
        self.assertEqual(self.cache.entry_count, 3)
        self.assertEqual(self.cache.snapshot()["evictions"], 1)
        self.cache.get_or_load("/users", {"kind": "secret"}, lambda: {"access_token": "never-cache"})
        self.cache.get_or_load("/users", {"kind": "hash"}, lambda: {"password_hash": "never-cache"})
        self.cache.get_or_load("/users", {"kind": "bytes"}, lambda: {"preview": b"never-cache"})
        self.cache.get_or_load("/users", {"kind": "large"}, lambda: {"data": "x" * 3000})
        self.assertEqual(self.cache.entry_count, 3)

    def test_set_parameters_have_a_deterministic_key(self) -> None:
        first = self.cache.make_key("customers", "/customers", {"status": {"active", "pending"}})
        second = self.cache.make_key("customers", "/customers", {"status": {"pending", "active"}})
        self.assertEqual(first, second)

    def test_session_and_role_changes_clear_all_cached_data(self) -> None:
        self.cache.get_or_load("/customers", {}, lambda: ["manager"])
        self.cache.start_session("user-1", "customer")
        self.assertEqual(self.cache.entry_count, 0)
        self.assertEqual(self.cache.get_or_load("/customers", {}, lambda: ["customer"]), ["customer"])
        self.cache.start_session("user-2", "manager")
        self.assertEqual(self.cache.entry_count, 0)
        self.cache.start_session("user-3", "instructor")
        self.assertEqual(self.cache.entry_count, 0)
        self.cache.clear_session()
        self.assertEqual(self.cache.entry_count, 0)

    def test_logout_and_session_expiry_clear_cache_and_token(self) -> None:
        client = ApiClient("http://example.test", performance_cache=self.cache)
        client.set_access_token("opaque-test-token")
        self.cache.get_or_load("/customers", {}, lambda: ["private"])
        AuthService(client).logout()
        self.assertIsNone(client.access_token)
        self.assertEqual(self.cache.entry_count, 0)
        client.set_access_token("another-opaque-token")
        client.set_performance_scope("user-2", "customer")
        self.cache.get_or_load("/customers", {}, lambda: ["owned"])
        AuthService(client).expire_session()
        self.assertIsNone(client.access_token)
        self.assertEqual(self.cache.entry_count, 0)

    def test_mutation_invalidation_is_targeted(self) -> None:
        self.cache.get_or_load("/customers", {}, lambda: ["customer"])
        self.cache.get_or_load("/activities", {}, lambda: ["activity"])
        self.assertEqual(self.cache.invalidate_for_mutation("/customers/new"), ("customers", "users"))
        self.assertEqual(self.cache.entry_count, 1)
        self.assertEqual(self.cache.get_or_load("/activities", {}, lambda: ["changed"]), ["activity"])

    def test_related_invalidation_matrix_and_capacity_are_bounded(self) -> None:
        self.cache.get_or_load("/users", {}, lambda: ["user"])
        self.cache.get_or_load("/instructors", {}, lambda: ["instructor"])
        self.cache.get_or_load("/activities", {}, lambda: ["activity"])
        self.assertEqual(self.cache.invalidate_for_mutation("/instructors/i1"), ("instructors", "users"))
        self.assertEqual(self.cache.entry_count, 1)
        self.assertEqual(self.cache.invalidate_for_mutation("/users/u1/reset-password", {"new_password": "never-cache"}), ())
        self.assertEqual(self.cache.invalidate_for_mutation("/users", {"role": "manager"}), ("users",))
        self.assertEqual(self.cache.invalidate_for_mutation("/users", {"role": "customer"}), ("users", "customers"))
        self.assertEqual(self.cache.invalidate_for_mutation("/activities/a1/images"), ("activities",))

        entered = [threading.Event(), threading.Event()]
        release = threading.Event()
        errors: list[Exception] = []

        def blocking(index):
            entered[index].set()
            release.wait(2)
            return index

        threads = [threading.Thread(target=lambda index=index: self.cache.get_or_load("/customers", {"page": index}, lambda: blocking(index))) for index in range(2)]
        for thread in threads:
            thread.start()
        self.assertTrue(all(event.wait(1) for event in entered))
        try:
            self.cache.get_or_load("/customers", {"page": 3}, lambda: 3)
        except Exception as exc:
            errors.append(exc)
        release.set()
        for thread in threads:
            thread.join(2)
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], CacheCapacityError)
        self.assertEqual(self.cache.inflight_count, 0)

    def test_failed_background_refresh_retains_stale_data_and_reports_freshness(self) -> None:
        warnings = []
        self.cache.set_refresh_failure_handler(warnings.append)
        self.assertEqual(self.cache.get_or_load("/customers", {}, lambda: ["safe-stale"]), ["safe-stale"])
        self.clock.now += 31
        failed = threading.Event()

        def fail():
            failed.set()
            raise RuntimeError("offline")

        self.assertEqual(self.cache.get_or_load("/customers", {}, fail), ["safe-stale"])
        self.assertTrue(failed.wait(1))
        deadline = time.monotonic() + 1
        while not warnings and time.monotonic() < deadline:
            time.sleep(0.005)
        self.assertEqual(warnings, ["customers"])
        self.assertEqual(self.cache.entry_count, 1)
        self.clock.now += 121
        with self.assertRaisesRegex(RuntimeError, "offline"):
            self.cache.get_or_load("/customers", {}, fail)
        self.assertEqual(self.cache.entry_count, 0)

    def test_session_change_does_not_expand_background_refresh_worker_bound(self) -> None:
        releases = threading.Event()
        entered = [threading.Event(), threading.Event()]
        resources = (("/customers", "customers"), ("/instructors", "instructors"))
        for path, value in resources:
            self.cache.get_or_load(path, {}, lambda value=value: [value])
        self.clock.now += 61

        def blocking(index):
            entered[index].set()
            releases.wait(2)
            return ["fresh"]

        for index, (path, _value) in enumerate(resources):
            self.cache.get_or_load(path, {}, lambda index=index: blocking(index))
        self.assertTrue(all(event.wait(1) for event in entered))
        self.assertEqual(self.cache.snapshot()["refreshing"], 2)
        self.cache.start_session("new-user", "customer")
        self.assertEqual(self.cache.snapshot()["refreshing"], 2)
        releases.set()
        deadline = time.monotonic() + 1
        while self.cache.snapshot()["refreshing"] and time.monotonic() < deadline:
            time.sleep(0.005)
        self.assertEqual(self.cache.snapshot()["refreshing"], 0)

    def test_shutdown_joins_refresh_worker_and_detaches_failure_handler(self) -> None:
        warnings = []
        self.cache.set_refresh_failure_handler(warnings.append)
        self.cache.get_or_load("/customers", {}, lambda: ["stale"])
        self.clock.now += 31
        entered = threading.Event()
        release = threading.Event()

        def fail_after_release():
            entered.set()
            release.wait(1)
            raise RuntimeError("offline")

        self.cache.get_or_load("/customers", {}, fail_after_release)
        self.assertTrue(entered.wait(1))
        threading.Timer(0.05, release.set).start()
        started = time.perf_counter()
        self.cache.shutdown()
        self.assertGreaterEqual(time.perf_counter() - started, 0.03)
        self.assertEqual(self.cache.snapshot()["refresh_threads"], 0)
        self.assertEqual(warnings, [])
        self.cache.shutdown()

    def test_api_client_reuses_reads_and_invalidates_after_successful_mutation(self) -> None:
        client = ApiClient("http://example.test", performance_cache=self.cache)
        calls: list[tuple[str, str]] = []

        def request(method, path, payload=None):
            calls.append((method, path))
            return {"items": [len(calls)]}

        client._request = request
        first = client.get("/customers", {"page": 1})
        self.assertEqual(client.get("/customers", {"page": 1}), first)
        client.post("/customers", {"name": "new"})
        client.get("/customers", {"page": 1})
        self.assertEqual([method for method, _path in calls], ["GET", "POST", "GET"])


if __name__ == "__main__":
    unittest.main()
