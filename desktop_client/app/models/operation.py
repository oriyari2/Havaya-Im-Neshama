from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class OperationContext:
    """Plain lifecycle identity shared by presenters and execution adapters."""

    session_epoch: int
    owner: str
    key: str
    generation: int


class OperationHandle(Protocol):
    def cancel(self) -> None: ...


class OperationExecutor(Protocol):
    def submit(
        self,
        context: OperationContext,
        operation: Callable[[], T],
        on_success: Callable[[T], None],
        on_error: Callable[[Exception], None],
        on_finished: Callable[[], None] | None = None,
    ) -> OperationHandle: ...

    def invalidate_session(self) -> None: ...

    def shutdown(self, timeout_ms: int = 3000) -> None: ...


class _CompletedHandle:
    def cancel(self) -> None:
        return None


class ImmediateOperationExecutor:
    """Deterministic non-Qt adapter used by presenter unit tests."""

    def submit(self, context, operation, on_success, on_error, on_finished=None):
        del context
        try:
            on_success(operation())
        except Exception as exc:
            on_error(exc)
        finally:
            if on_finished is not None:
                on_finished()
        return _CompletedHandle()

    def invalidate_session(self) -> None:
        return None

    def shutdown(self, timeout_ms: int = 3000) -> None:
        del timeout_ms


class PresenterOperations:
    """Qt-free request identity, duplicate guard, and stale-result helper."""

    def __init__(self, executor: OperationExecutor | None, owner: str) -> None:
        self.executor = executor or ImmediateOperationExecutor()
        self.owner = owner
        self.session_epoch = 0
        self.generation = 0
        self.current: dict[str, OperationContext] = {}

    def begin(self, key: str) -> OperationContext | None:
        if key in self.current:
            return None
        self.generation += 1
        context = OperationContext(self.session_epoch, self.owner, key, self.generation)
        self.current[key] = context
        return context

    def replace(self, key: str) -> OperationContext:
        self.generation += 1
        context = OperationContext(self.session_epoch, self.owner, key, self.generation)
        self.current[key] = context
        return context

    def is_current(self, context: OperationContext) -> bool:
        return self.current.get(context.key) == context

    def finish(self, context: OperationContext) -> bool:
        if not self.is_current(context):
            return False
        self.current.pop(context.key, None)
        return True

    def invalidate(self) -> None:
        self.session_epoch += 1
        self.current.clear()
