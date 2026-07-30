from __future__ import annotations

import itertools
import threading
from dataclasses import dataclass
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QRunnable, QThreadPool, QThread, Qt, Signal, Slot

from desktop_client.app.models.operation import NON_CANCELLABLE_OPERATION_KEYS, OperationContext


MAX_BACKGROUND_OPERATIONS = 4
MAX_PENDING_OPERATIONS = 32


class OperationCapacityError(RuntimeError):
    pass


@dataclass(slots=True)
class _OperationRecord:
    epoch: int
    context: OperationContext
    work: "_Work"
    success: Callable[[object], None]
    error: Callable[[Exception], None]
    finished: Callable[[], None] | None
    cancelled: bool = False


class _Work(QRunnable):
    def __init__(self, operation_id: int, operation: Callable[[], Any], deliver: Callable[[int, bool, object], None]) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.operation_id = operation_id
        self.operation = operation
        self.deliver = deliver

    @Slot()
    def run(self) -> None:
        try:
            self.deliver(self.operation_id, True, self.operation())
        except Exception as exc:
            self.deliver(self.operation_id, False, exc)


class QtOperationHandle:
    def __init__(self, executor: "QtOperationExecutor", operation_id: int) -> None:
        self._executor = executor
        self._operation_id = operation_id

    def cancel(self) -> None:
        self._executor.cancel(self._operation_id)


class QtOperationExecutor(QObject):
    """Bounded Qt adapter; callbacks are always dispatched on the UI thread."""

    operation_completed = Signal(int, bool, object)

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
        self._active: dict[int, _OperationRecord] = {}
        self._shutdown = False
        self.operation_completed.connect(self._deliver_completion, Qt.ConnectionType.QueuedConnection)

    @property
    def active_count(self) -> int:
        with self._lock:
            return len(self._active)

    def submit(self, context, operation, on_success, on_error, on_finished=None):
        with self._lock:
            if self._shutdown:
                raise RuntimeError("Desktop operation executor is shut down")
            at_capacity = len(self._active) >= self._max_pending
        if at_capacity:
            on_error(OperationCapacityError("המערכת עסוקה כעת. נסו שוב בעוד רגע."))
            if on_finished is not None:
                on_finished()
            return QtOperationHandle(self, 0)
        operation_id = next(self._ids)
        epoch = self._epoch
        work = _Work(operation_id, operation, self.operation_completed.emit)
        with self._lock:
            self._active[operation_id] = _OperationRecord(epoch, context, work, on_success, on_error, on_finished)
        self._pool.start(work)
        return QtOperationHandle(self, operation_id)

    @Slot(int, bool, object)
    def _deliver_completion(self, operation_id: int, succeeded: bool, payload: object) -> None:
        with self._lock:
            record = self._active.pop(operation_id, None)
            current = record is not None and not record.cancelled and record.epoch == self._epoch
        if record is None or not current:
            return
        try:
            if succeeded:
                record.success(payload)
            elif isinstance(payload, Exception):
                record.error(payload)
            else:
                record.error(RuntimeError("Background operation failed"))
        finally:
            if record.finished is not None:
                record.finished()

    def cancel(self, operation_id: int) -> None:
        with self._lock:
            record = self._active.get(operation_id)
            if record is not None:
                record.cancelled = True
        if record is not None:
            self._remove_if_queued(operation_id, record)

    def cancel_owner(self, owner: str) -> int:
        with self._lock:
            matches = [operation_id for operation_id, record in self._active.items() if self._context_owner(record.context) == owner and self._context_key(record.context) not in NON_CANCELLABLE_OPERATION_KEYS]
            records = [(operation_id, self._active[operation_id]) for operation_id in matches]
            for _operation_id, record in records:
                record.cancelled = True
        for operation_id, record in records:
            self._remove_if_queued(operation_id, record)
        return len(records)

    def cancel_operation(self, owner: str, key: str) -> int:
        with self._lock:
            matches = [operation_id for operation_id, record in self._active.items() if self._context_owner(record.context) == owner and self._context_key(record.context) == key and key not in NON_CANCELLABLE_OPERATION_KEYS]
            records = [(operation_id, self._active[operation_id]) for operation_id in matches]
            for _operation_id, record in records:
                record.cancelled = True
        for operation_id, record in records:
            self._remove_if_queued(operation_id, record)
        return len(records)

    def _remove_if_queued(self, operation_id: int, record: _OperationRecord) -> None:
        if not self._try_remove_queued(record.work):
            return
        with self._lock:
            if self._active.get(operation_id) is record:
                self._active.pop(operation_id, None)

    def _try_remove_queued(self, work: "_Work") -> bool:
        try:
            return self._pool.tryTake(work)
        except RuntimeError:
            # QRunnable may finish before its queued Qt completion reaches Python.
            return False

    @staticmethod
    def _context_owner(context) -> str | None:
        return getattr(context, "owner", getattr(context, "screen", None))

    @staticmethod
    def _context_key(context) -> str | None:
        return getattr(context, "key", getattr(context, "operation_key", None))

    def invalidate_session(self) -> None:
        with self._lock:
            self._epoch += 1
            records = list(self._active.items())
            for _operation_id, record in records:
                record.cancelled = True
        for operation_id, record in records:
            self._remove_if_queued(operation_id, record)

    def shutdown(self, timeout_ms: int = 3000) -> None:
        del timeout_ms
        if QThread.currentThread() is not self.thread():
            raise RuntimeError("Desktop operation executor must be shut down on its owning Qt thread")
        with self._lock:
            if self._shutdown:
                return
            self._shutdown = True
        self.invalidate_session()
        self._pool.waitForDone(-1)
        QCoreApplication.sendPostedEvents(self, QEvent.Type.MetaCall)
        with self._lock:
            self._active.clear()
        QCoreApplication.removePostedEvents(self)
