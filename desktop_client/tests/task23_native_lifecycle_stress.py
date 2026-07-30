"""Native Qt lifecycle stress harness for the Task 23 teardown regression."""

from __future__ import annotations

import argparse
import json
import threading
import time

from PySide6.QtWidgets import QApplication

from desktop_client.app.infrastructure.performance_cache import SessionPerformanceCache
from desktop_client.app.infrastructure.qt_operations import QtOperationExecutor
from desktop_client.app.main import MainWindow
from desktop_client.app.models.operation import OperationContext
from desktop_client.app.models.session import Session


class _Clock:
    def __init__(self) -> None:
        self.value = 100.0

    def __call__(self) -> float:
        return self.value


class _StressApi:
    def __init__(self, iteration: int, role: str) -> None:
        self.iteration = iteration
        self.role = role
        self.access_token = "stress-token"
        self.performance_cache = SessionPerformanceCache()
        self.performance_cache.start_session(f"stress-{iteration}", role)
        self._unauthorized_handler = None

    def set_unauthorized_handler(self, handler) -> None:
        self._unauthorized_handler = handler

    def set_access_token(self, token) -> None:
        self.access_token = token

    def clear_performance_scope(self) -> None:
        self.performance_cache.clear_session()

    def get(self, path, params=None):
        del params
        time.sleep(0.004)
        if path == "/bookings/dashboard":
            return {}
        if path.startswith("/bookings/open-events") or path == "/api/rag/sources":
            return []
        if path == "/instructors/me":
            return {"id": "instructor", "full_name": "Stress", "is_active": True}
        if path.startswith("/customers/"):
            return {"id": "customer", "name": "Stress", "is_active": True, "contacts": []}
        return {"items": [], "count": 0}

    def post(self, path, payload):
        del path, payload
        time.sleep(0.004)
        return {}


def run_stress(iterations: int) -> dict[str, int]:
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    callbacks: list[object] = []
    scenario_counts = {
        "startup_shutdown": 0,
        "rapid_navigation": 0,
        "customers_users_transitions": 0,
        "logout_active_read": 0,
        "close_active_read": 0,
        "close_queued_completion": 0,
        "navigation_during_mutation": 0,
        "swr_shutdown": 0,
        "logout_swr_refresh": 0,
    }
    for iteration in range(iterations):
        executor = QtOperationExecutor(max_workers=2, max_pending=8)
        entered = threading.Event()
        release = threading.Event()

        def operation():
            entered.set()
            release.wait(1)
            return iteration

        executor.submit(
            OperationContext(0, "stress", "list", iteration),
            operation,
            callbacks.append,
            callbacks.append,
        )
        if not entered.wait(1):
            raise RuntimeError("stress worker did not start")
        executor.cancel_owner("stress")
        if executor.active_count != 1:
            raise RuntimeError("running operation ownership was released early")
        threading.Timer(0.002, release.set).start()
        executor.shutdown()
        executor.shutdown()
        app.processEvents()
        if executor.active_count:
            raise RuntimeError("executor retained operations after shutdown")
        scenario_counts["close_active_read"] += 1

        clock = _Clock()
        cache = SessionPerformanceCache(clock=clock)
        cache.start_session(f"stress-{iteration}", "manager")
        cache.get_or_load("/customers", {}, lambda: [iteration])
        clock.value += 31
        refresh_entered = threading.Event()
        refresh_release = threading.Event()

        def refresh():
            refresh_entered.set()
            refresh_release.wait(1)
            raise RuntimeError("expected stress refresh failure")

        cache.set_refresh_failure_handler(lambda _resource: None)
        cache.get_or_load("/customers", {}, refresh)
        if not refresh_entered.wait(1):
            raise RuntimeError("stress refresh did not start")
        if iteration % 2 == 0:
            cache.clear_session()
            scenario_counts["logout_swr_refresh"] += 1
        threading.Timer(0.002, refresh_release.set).start()
        cache.shutdown()
        cache.shutdown()
        if cache.snapshot()["refresh_threads"]:
            raise RuntimeError("cache refresh worker survived shutdown")
        scenario_counts["swr_shutdown"] += 1

        role = ("manager", "instructor", "customer")[iteration % 3]
        api = _StressApi(iteration, role)
        window = MainWindow(api)
        session = Session(
            "stress-token",
            f"user-{iteration}",
            f"{role}-{iteration}@example.test",
            role,
            customer_id="customer" if role == "customer" else None,
            instructor_id="instructor" if role == "instructor" else None,
        )
        window._show_workspace(session)
        window.show()
        scenario_counts["startup_shutdown"] += 1
        if role == "manager":
            for _repeat in range(5):
                window._navigate("customers")
                window._navigate("users")
                scenario_counts["customers_users_transitions"] += 2
        else:
            for page in tuple(window.shell.pages)[:5]:
                window._navigate(page)
        scenario_counts["rapid_navigation"] += 1

        lifecycle_case = iteration % 4
        if lifecycle_case == 0:
            window.close()
            scenario_counts["close_active_read"] += 1
        elif lifecycle_case == 1:
            window._logout()
            scenario_counts["logout_active_read"] += 1
            window.close()
        elif lifecycle_case == 2:
            window.operation_executor.submit(
                OperationContext(0, "queued", "list", iteration),
                lambda: "completed-before-dispatch",
                callbacks.append,
                callbacks.append,
            )
            time.sleep(0.01)
            window.close()
            scenario_counts["close_queued_completion"] += 1
        else:
            window.operation_executor.submit(
                OperationContext(0, "mutation", "mutation", iteration),
                lambda: (time.sleep(0.008), "committed")[1],
                callbacks.append,
                callbacks.append,
            )
            next_page = "activities" if window._active_page != "activities" else "dashboard"
            window._navigate(next_page)
            window.close()
            scenario_counts["navigation_during_mutation"] += 1
        app.processEvents()
    return {
        "iterations": iterations,
        "crashes": 0,
        "callbacks_after_shutdown": len(callbacks),
        **scenario_counts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=25)
    args = parser.parse_args()
    if args.iterations < 1:
        raise SystemExit("iterations must be positive")
    print(json.dumps(run_stress(args.iterations), sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
