from __future__ import annotations

import itertools
import logging
import threading
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Qt, Signal, Slot

from desktop_client.app.models.operation import OperationContext


logger = logging.getLogger(__name__)
MAX_BACKGROUND_OPERATIONS = 4
MAX_PENDING_OPERATIONS = 32


class OperationCapacityError(RuntimeError):
    pass


class _Bridge(QObject):
    succeeded = Signal(object)
    failed = Signal(object)
    completed = Signal()

    def __init__(self, success, error, finished) -> None:
        super().__init__()
        self._success = success
        self._error = error
        self._finished = finished
        self.succeeded.connect(self._deliver_success, Qt.ConnectionType.QueuedConnection)
        self.failed.connect(self._deliver_error, Qt.ConnectionType.QueuedConnection)
        self.completed.connect(self._deliver_finished, Qt.ConnectionType.QueuedConnection)

    @Slot(object)
    def _deliver_success(self, value: object) -> None:
        self._success(value)

    @Slot(object)
    def _deliver_error(self, error: object) -> None:
        if isinstance(error, Exception):
            self._error(error)
        else:
            self._error(RuntimeError("Background operation failed"))

    @Slot()
    def _deliver_finished(self) -> None:
        if self._finished is not None:
            self._finished()


class _Work(QRunnable):
    def __init__(self, operation: Callable[[], Any], bridge: _Bridge) -> None:
        super().__init__()
        self.operation = operation
        self.bridge = bridge

    @Slot()
    def run(self) -> None:
        try:
            self.bridge.succeeded.emit(self.operation())
        except Exception as exc:
            self.bridge.failed.emit(exc)
        finally:
            self.bridge.completed.emit()


class QtOperationHandle:
    def __init__(self, executor: "QtOperationExecutor", operation_id: int) -> None:
        self._executor = executor
        self._operation_id = operation_id

    def cancel(self) -> None:
        self._executor.cancel(self._operation_id)


class QtOperationExecutor(QObject):
    """Bounded Qt adapter; callbacks are always dispatched on the UI thread."""

    def __init__(self, *, max_workers: int = MAX_BACKGROUND_OPERATIONS, max_pending: int = MAX_PENDING_OPERATIONS, parent=None) -> None:
        super().__init__(parent)
        if max_workers < 1:
            raise ValueError("max_workers must be positive")
        if max_pending < max_workers:
            raise ValueError("max_pending must be at least max_workers")
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(max_workers)
        self._ids = itertools.count(1)
        self._max_pending = max_pending
        self._epoch = 0
        self._lock = threading.Lock()
        self._active: dict[int, tuple[int, _Bridge]] = {}

    @property
    def active_count(self) -> int:
        with self._lock:
            return len(self._active)

    def submit(self, context, operation, on_success, on_error, on_finished=None):
        with self._lock:
            at_capacity = len(self._active) >= self._max_pending
        if at_capacity:
            QTimer.singleShot(0, lambda: on_error(OperationCapacityError("המערכת עסוקה כעת. נסו שוב בעוד רגע.")))
            if on_finished is not None:
                QTimer.singleShot(0, on_finished)
            return QtOperationHandle(self, 0)
        operation_id = next(self._ids)
        epoch = self._epoch

        def current() -> bool:
            with self._lock:
                return operation_id in self._active and epoch == self._epoch

        def success(value: object) -> None:
            if current():
                on_success(value)

        def error(exc: Exception) -> None:
            if current():
                on_error(exc)

        def finished() -> None:
            callback = None
            with self._lock:
                entry = self._active.pop(operation_id, None)
                if entry is not None and epoch == self._epoch:
                    callback = on_finished
            if callback is not None:
                callback()

        bridge = _Bridge(success, error, finished)
        with self._lock:
            self._active[operation_id] = (epoch, bridge)
        self._pool.start(_Work(operation, bridge))
        return QtOperationHandle(self, operation_id)

    def cancel(self, operation_id: int) -> None:
        with self._lock:
            self._active.pop(operation_id, None)

    def invalidate_session(self) -> None:
        with self._lock:
            self._epoch += 1
            self._active.clear()
        self._pool.clear()

    def shutdown(self, timeout_ms: int = 3000) -> None:
        self.invalidate_session()
        if not self._pool.waitForDone(timeout_ms):
            logger.warning("Desktop background operations exceeded shutdown timeout")
