from __future__ import annotations

import os
import threading
import time
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from desktop_client.app.infrastructure.qt_operations import OperationCapacityError, QtOperationExecutor
from desktop_client.app.main import MainWindow
from desktop_client.app.models.operation import OperationContext, PresenterOperations
from desktop_client.app.models.session import Session


class BackgroundOperationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def wait_until(self, predicate, timeout_ms=1500) -> None:
        loop = QEventLoop()
        timer = QTimer()
        timer.setInterval(5)
        timer.timeout.connect(lambda: loop.quit() if predicate() else None)
        timeout = QTimer()
        timeout.setSingleShot(True)
        timeout.timeout.connect(loop.quit)
        timer.start()
        timeout.start(timeout_ms)
        loop.exec()
        self.assertTrue(predicate())

    def test_submit_returns_immediately_and_ui_timer_runs_during_work(self) -> None:
        executor = QtOperationExecutor(max_workers=1)
        results = []
        ticks = []
        main_thread = threading.get_ident()
        QTimer.singleShot(20, lambda: ticks.append(time.perf_counter()))
        started = time.perf_counter()
        executor.submit(
            OperationContext(0, "test", "slow", 1),
            lambda: (time.sleep(0.20), "done")[1],
            lambda value: results.append((value, threading.get_ident())),
            lambda error: results.append(error),
        )
        submit_elapsed = time.perf_counter() - started
        self.assertLess(submit_elapsed, 0.05)
        self.wait_until(lambda: bool(results))
        self.assertTrue(ticks)
        self.assertEqual(results, [("done", main_thread)])
        executor.shutdown()

    def test_cancel_and_session_invalidation_suppress_obsolete_callbacks(self) -> None:
        executor = QtOperationExecutor(max_workers=1)
        delivered = []
        handle = executor.submit(
            OperationContext(0, "test", "cancel", 1),
            lambda: (time.sleep(0.08), "obsolete")[1],
            delivered.append,
            delivered.append,
        )
        handle.cancel()
        self.wait_until(lambda: executor.active_count == 0)
        self.assertEqual(delivered, [])

        executor.submit(
            OperationContext(0, "test", "logout", 2),
            lambda: (time.sleep(0.08), "old-session")[1],
            delivered.append,
            delivered.append,
        )
        executor.invalidate_session()
        QTimer.singleShot(120, lambda: None)
        self.wait_until(lambda: executor.active_count == 0)
        self.assertEqual(delivered, [])
        executor.shutdown()

    def test_running_cancel_retains_native_ownership_until_worker_finishes(self) -> None:
        executor = QtOperationExecutor(max_workers=1)
        entered = threading.Event()
        release = threading.Event()
        delivered = []
        handle = executor.submit(
            OperationContext(0, "test", "owned", 1),
            lambda: (entered.set(), release.wait(1), "obsolete")[2],
            delivered.append,
            delivered.append,
        )
        self.assertTrue(entered.wait(1))
        handle.cancel()
        self.assertEqual(executor.active_count, 1)
        release.set()
        self.wait_until(lambda: executor.active_count == 0)
        self.assertEqual(delivered, [])
        executor.shutdown()

    def test_shutdown_waits_for_running_work_is_idempotent_and_suppresses_callbacks(self) -> None:
        executor = QtOperationExecutor(max_workers=1)
        delivered = []
        executor.submit(
            OperationContext(0, "test", "shutdown", 1),
            lambda: (time.sleep(0.06), "late")[1],
            delivered.append,
            delivered.append,
        )
        started = time.perf_counter()
        executor.shutdown()
        self.assertGreaterEqual(time.perf_counter() - started, 0.04)
        executor.shutdown()
        self.app.processEvents()
        self.assertEqual(executor.active_count, 0)
        self.assertEqual(delivered, [])

    def test_capacity_is_bounded_and_reports_friendly_adapter_error(self) -> None:
        executor = QtOperationExecutor(max_workers=1, max_pending=1)
        errors = []
        executor.submit(OperationContext(0, "test", "first", 1), lambda: time.sleep(0.08), lambda _: None, errors.append)
        executor.submit(OperationContext(0, "test", "second", 2), lambda: None, lambda _: None, errors.append)
        self.wait_until(lambda: bool(errors))
        self.assertIsInstance(errors[0], OperationCapacityError)
        executor.shutdown()

    def test_latest_intent_removes_obsolete_callback_and_delivers_newest_result(self) -> None:
        executor = QtOperationExecutor(max_workers=1)
        operations = PresenterOperations(executor, "customers")
        delivered = []
        first = operations.replace("list")
        executor.submit(first, lambda: (time.sleep(0.10), "old")[1], delivered.append, delivered.append)
        newest = operations.replace("list")
        executor.submit(newest, lambda: "new", delivered.append, delivered.append)
        self.wait_until(lambda: delivered == ["new"], timeout_ms=2000)
        self.assertFalse(operations.is_current(first))
        self.assertTrue(operations.is_current(newest))
        executor.shutdown()

    def test_navigation_does_not_cancel_inflight_mutation(self) -> None:
        executor = QtOperationExecutor(max_workers=1)
        operations = PresenterOperations(executor, "users")
        delivered = []
        mutation = operations.begin("mutation")
        executor.submit(mutation, lambda: (time.sleep(0.06), "committed")[1], delivered.append, delivered.append)
        operations.invalidate()
        self.assertTrue(operations.is_current(mutation))
        self.wait_until(lambda: delivered == ["committed"])
        self.assertTrue(operations.finish(mutation))
        executor.shutdown()

    def test_presenter_identity_prevents_duplicates_and_stale_completion(self) -> None:
        operations = PresenterOperations(None, "customers")
        first = operations.begin("submit")
        self.assertIsNotNone(first)
        self.assertIsNone(operations.begin("submit"))
        old_list = operations.replace("list")
        new_list = operations.replace("list")
        self.assertFalse(operations.is_current(old_list))
        self.assertTrue(operations.is_current(new_list))
        operations.invalidate()
        self.assertFalse(operations.is_current(new_list))

    def test_window_navigation_and_resize_remain_live_during_slow_screen_loads(self) -> None:
        class Api:
            def set_unauthorized_handler(self, handler):
                self.handler = handler

            def set_access_token(self, token):
                self.token = token

        class SlowService:
            @staticmethod
            def _empty():
                time.sleep(0.12)
                return {"items": [], "count": 0}

            def dashboard(self):
                time.sleep(0.12)
                return {}

            def list_bookings(self, filters=None):
                return self._empty()

            def open_events(self):
                time.sleep(0.12)
                return []

            def list_customers(self, filters=None):
                return self._empty()

            def list_instructors(self, filters=None):
                return self._empty()

            def list_users(self, filters=None):
                return self._empty()

            def list_activities(self, filters=None):
                return {"items": [], "count": 0}

            def list_sources(self):
                return []

        window = MainWindow(Api())
        slow = SlowService()
        window.booking_service = slow
        window.customer_service = slow
        window.instructor_service = slow
        window.user_service = slow
        window.activity_service = slow
        window.knowledge_service = slow
        window._show_workspace(Session("token", "manager", "manager@example.com", "manager"))
        window.show()
        window.resize(1024, 640)
        ticks = []
        QTimer.singleShot(20, lambda: ticks.append(True))
        window._navigate("customers")
        window.resize(1200, 760)
        window._navigate("instructors")
        window._navigate("users")
        self.wait_until(lambda: bool(ticks))
        self.assertIs(window.shell.stack.currentWidget(), window.shell.pages["users"])
        self.assertEqual((window.width(), window.height()), (1200, 760))
        self.wait_until(lambda: window.operation_executor.active_count == 0, timeout_ms=2500)
        window.close()

    def test_real_login_view_remains_live_during_slow_authentication(self) -> None:
        class Api:
            def set_unauthorized_handler(self, handler):
                self.handler = handler

            def set_access_token(self, token):
                self.token = token

            def post(self, path, payload):
                self.login_payload = payload
                time.sleep(0.15)
                return {
                    "access_token": "test-token",
                    "user": {"id": "manager", "email": payload["email"], "role": "manager"},
                }

            def get(self, path, params=None):
                if path == "/dashboard":
                    return {}
                if "open-events" in path:
                    return []
                return {"items": [], "count": 0}

        api = Api()
        window = MainWindow(api)
        window.show()
        ticks = []
        QTimer.singleShot(20, lambda: ticks.append(True))
        window.login_presenter.login("manager@example.com", "password1")
        self.wait_until(lambda: bool(ticks))
        self.assertTrue(window.login_presenter._loading)
        self.wait_until(lambda: hasattr(window, "shell"), timeout_ms=2000)
        self.assertEqual(api.login_payload["email"], "manager@example.com")
        window.close()


if __name__ == "__main__":
    unittest.main()
