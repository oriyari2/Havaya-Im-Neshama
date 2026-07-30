from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RequestPhase(str, Enum):
    IDLE = "idle"
    LOADING = "loading"
    SUCCESS = "success"
    EMPTY = "empty"
    VALIDATION_ERROR = "validation_error"
    AUTHORIZATION_ERROR = "authorization_error"
    CONNECTION_ERROR = "connection_error"
    SERVER_ERROR = "server_error"
    STALE = "stale"
    SESSION_EXPIRED = "session_expired"


@dataclass(frozen=True, slots=True)
class RequestState:
    phase: RequestPhase
    message: str = ""
    operation_key: str = ""
    retryable: bool = False
    blocks_primary_action: bool = False
    diagnostic_id: str | None = None


@dataclass(frozen=True, slots=True)
class RequestIdentity:
    session_epoch: int
    module_key: str
    operation_key: str
    generation: int
    resource_id: str | None = None

    def __post_init__(self) -> None:
        if self.session_epoch < 0 or self.generation < 0:
            raise ValueError("Request identity counters must be non-negative")
        if not self.module_key or not self.operation_key:
            raise ValueError("Request identity keys must be non-empty")

    def is_current(self, current: "RequestIdentity") -> bool:
        return self == current
