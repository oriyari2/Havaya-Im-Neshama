from __future__ import annotations

import copy
import json
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable


MAX_CACHE_ENTRIES = 128
MAX_CACHE_BYTES = 8 * 1024 * 1024
MAX_INFLIGHT_READS = 32
MAX_BACKGROUND_REFRESHES = 2


@dataclass(frozen=True, slots=True)
class SessionScope:
    user_id: str
    role: str
    generation: int


@dataclass(frozen=True, slots=True)
class CachePolicy:
    resource: str
    ttl_seconds: float
    stale_while_revalidate: bool = False
    max_stale_seconds: float = 120.0
    max_payload_bytes: int = 1024 * 1024


@dataclass(slots=True)
class CacheStats:
    hits: int = 0
    misses: int = 0
    coalesced: int = 0
    stores: int = 0
    evictions: int = 0
    invalidations: int = 0
    rejected: int = 0
    stale_hits: int = 0
    refresh_failures: int = 0


@dataclass(slots=True)
class _Entry:
    value: Any
    resource: str
    stored_at: float
    expires_at: float
    size: int


@dataclass(slots=True)
class _Flight:
    event: threading.Event
    result: Any = None
    error: Exception | None = None


class CacheCapacityError(RuntimeError):
    pass


class CacheSessionInvalidated(RuntimeError):
    pass


def policy_for_path(path: str) -> CachePolicy | None:
    clean = path.split("?", 1)[0]
    if clean in {"/auth/login", "/api/ai/consult"}:
        return None
    if clean == "/bookings/dashboard":
        return CachePolicy("dashboard", 15, stale_while_revalidate=True)
    if clean.startswith("/api/rag/sources"):
        return CachePolicy("knowledge", 20)
    if clean.startswith("/bookings/open-events"):
        # Assignment availability and the signed-in instructor's request state
        # are operational data that can change in another user's session. Never
        # serve a stale open-event list/detail from the desktop cache.
        return None
    if clean.startswith("/bookings") and clean.endswith("/history"):
        return CachePolicy("booking_history", 15)
    if clean.startswith("/bookings") and clean.endswith("/assignments"):
        return CachePolicy("assignments", 10)
    if clean.startswith("/bookings"):
        return CachePolicy("bookings", 20, stale_while_revalidate=True)
    if clean.startswith("/customers"):
        return CachePolicy("customers", 30, stale_while_revalidate=True)
    if clean.startswith("/instructors"):
        return CachePolicy("instructors", 30, stale_while_revalidate=True)
    if clean.startswith("/users"):
        return CachePolicy("users", 20, stale_while_revalidate=True)
    if clean.startswith("/activities"):
        return CachePolicy("activities", 60, stale_while_revalidate=True)
    return None


class SessionPerformanceCache:
    """Session-isolated bounded GET cache and identical-read coalescer."""

    def __init__(self, *, max_entries: int = MAX_CACHE_ENTRIES, max_bytes: int = MAX_CACHE_BYTES, max_inflight: int = MAX_INFLIGHT_READS, clock: Callable[[], float] = time.monotonic) -> None:
        if min(max_entries, max_bytes, max_inflight) < 1:
            raise ValueError("Cache bounds must be positive")
        self.max_entries = max_entries
        self.max_bytes = max_bytes
        self.max_inflight = max_inflight
        self._clock = clock
        self._lock = threading.RLock()
        self._scope: SessionScope | None = None
        self._generation = 0
        self._entries: OrderedDict[str, _Entry] = OrderedDict()
        self._inflight: dict[str, _Flight] = {}
        self._bytes = 0
        self._refreshing: set[str] = set()
        self._refresh_threads: set[threading.Thread] = set()
        self._shutdown = False
        self.stats = CacheStats()
        self._refresh_failure_handler: Callable[[str], None] | None = None

    def set_refresh_failure_handler(self, handler: Callable[[str], None] | None) -> None:
        with self._lock:
            self._refresh_failure_handler = handler

    @property
    def scope(self) -> SessionScope | None:
        with self._lock:
            return self._scope

    @property
    def entry_count(self) -> int:
        with self._lock:
            return len(self._entries)

    @property
    def estimated_bytes(self) -> int:
        with self._lock:
            return self._bytes

    @property
    def inflight_count(self) -> int:
        with self._lock:
            return len(self._inflight)

    def start_session(self, user_id: str, role: str) -> SessionScope:
        if not user_id or role not in {"manager", "customer", "instructor"}:
            raise ValueError("A valid authenticated cache scope is required")
        with self._lock:
            if self._shutdown:
                raise RuntimeError("Performance cache is shut down")
            self._generation += 1
            self._clear_locked()
            self._scope = SessionScope(str(user_id), role, self._generation)
            return self._scope

    def clear_session(self) -> None:
        with self._lock:
            self._generation += 1
            self._scope = None
            self._clear_locked()

    def make_key(self, resource: str, path: str, params: dict[str, object] | None = None) -> str:
        with self._lock:
            scope = self._scope
        if scope is None:
            raise RuntimeError("Cache is unavailable without an authenticated session")
        normalized = self._normalize(params or {})
        identity = {"generation": scope.generation, "user_id": scope.user_id, "role": scope.role, "resource": resource, "path": path, "params": normalized}
        return json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def get_or_load(self, path: str, params: dict[str, object] | None, loader: Callable[[], Any]) -> Any:
        policy = policy_for_path(path)
        with self._lock:
            scope = self._scope
        if policy is None or scope is None:
            return loader()
        key = self.make_key(policy.resource, path, params)
        now = self._clock()
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None and entry.expires_at > now:
                self._entries.move_to_end(key)
                self.stats.hits += 1
                return copy.deepcopy(entry.value)
            if entry is not None and policy.stale_while_revalidate and now <= entry.expires_at + policy.max_stale_seconds:
                self._entries.move_to_end(key)
                self.stats.stale_hits += 1
                stale = copy.deepcopy(entry.value)
                if key not in self._refreshing and len(self._refreshing) < MAX_BACKGROUND_REFRESHES:
                    self._refreshing.add(key)
                    refresh_thread = threading.Thread(
                        target=self._refresh,
                        args=(key, policy, scope, loader),
                        name="desktop-cache-refresh",
                    )
                    self._refresh_threads.add(refresh_thread)
                    refresh_thread.start()
                return stale
            if entry is not None:
                self._remove_locked(key)
            flight = self._inflight.get(key)
            if flight is not None:
                self.stats.coalesced += 1
                owner = False
            else:
                if len(self._inflight) >= self.max_inflight:
                    self.stats.rejected += 1
                    raise CacheCapacityError("המערכת עסוקה כעת. נסו שוב בעוד רגע.")
                self.stats.misses += 1
                flight = _Flight(threading.Event())
                self._inflight[key] = flight
                owner = True
        if not owner:
            flight.event.wait()
            if flight.error is not None:
                raise flight.error
            return copy.deepcopy(flight.result)
        try:
            result = loader()
            stored = copy.deepcopy(result)
            size = self._estimate_size(stored)
            with self._lock:
                if self._scope == scope and not self._contains_secret(stored) and size <= min(policy.max_payload_bytes, self.max_bytes):
                    stored_at = self._clock()
                    self._store_locked(key, _Entry(stored, policy.resource, stored_at, stored_at + policy.ttl_seconds, size))
                elif self._scope == scope:
                    self.stats.rejected += 1
                flight.result = stored
            return copy.deepcopy(result)
        except Exception as exc:
            with self._lock:
                flight.error = exc
            raise
        finally:
            with self._lock:
                self._inflight.pop(key, None)
                flight.event.set()

    def invalidate_resource(self, *resources: str) -> int:
        wanted = set(resources)
        with self._lock:
            keys = [key for key, entry in self._entries.items() if entry.resource in wanted]
            for key in keys:
                self._remove_locked(key)
            self.stats.invalidations += len(keys)
            return len(keys)

    def invalidate_path(self, path: str, params: dict[str, object] | None = None) -> bool:
        policy = policy_for_path(path)
        if policy is None or self.scope is None:
            return False
        key = self.make_key(policy.resource, path, params)
        with self._lock:
            if key not in self._entries:
                return False
            self._remove_locked(key)
            self.stats.invalidations += 1
            return True

    def invalidate_for_mutation(self, path: str, payload: dict[str, object] | None = None) -> tuple[str, ...]:
        clean = path.split("?", 1)[0]
        if clean.endswith("/reset-password"):
            resources = ()
        elif clean == "/users":
            role = str((payload or {}).get("role") or "")
            resources = ("users", "customers") if role == "customer" else (("users", "instructors") if role == "instructor" else ("users",))
        elif clean.startswith("/users"):
            resources = ("users", "customers", "instructors")
        elif clean.startswith("/customers") or clean.startswith("/customer-contacts"):
            resources = ("customers", "users")
        elif clean.startswith("/instructors"):
            resources = ("instructors", "users")
        elif clean.startswith("/bookings"):
            resources = ("bookings", "booking_history", "assignments", "open_events", "dashboard")
        elif clean.startswith("/activities"):
            resources = ("activities",) if "/images" in clean else ("activities", "bookings", "open_events")
        elif clean.startswith("/api/rag/sources"):
            resources = ("knowledge",)
        else:
            resources = ()
        if resources:
            self.invalidate_resource(*resources)
        return resources

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return {
                "entries": len(self._entries),
                "estimated_bytes": self._bytes,
                "inflight": len(self._inflight),
                "refreshing": len(self._refreshing),
                "refresh_threads": len(self._refresh_threads),
                "hits": self.stats.hits,
                "misses": self.stats.misses,
                "coalesced": self.stats.coalesced,
                "stores": self.stats.stores,
                "evictions": self.stats.evictions,
                "invalidations": self.stats.invalidations,
                "rejected": self.stats.rejected,
                "stale_hits": self.stats.stale_hits,
                "refresh_failures": self.stats.refresh_failures,
            }

    def shutdown(self) -> None:
        with self._lock:
            if self._shutdown:
                return
            self._shutdown = True
            self._generation += 1
            self._scope = None
            self._refresh_failure_handler = None
            self._clear_locked()
            threads = tuple(self._refresh_threads)
        current = threading.current_thread()
        for thread in threads:
            if thread is not current:
                thread.join()

    @staticmethod
    def _normalize(value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): SessionPerformanceCache._normalize(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0])) if item not in (None, "")}
        if isinstance(value, set):
            normalized = [SessionPerformanceCache._normalize(item) for item in value]
            return sorted(normalized, key=lambda item: json.dumps(item, sort_keys=True, default=str))
        if isinstance(value, (list, tuple)):
            return [SessionPerformanceCache._normalize(item) for item in value]
        return value

    @staticmethod
    def _estimate_size(value: Any) -> int:
        try:
            return len(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8"))
        except (TypeError, ValueError):
            return MAX_CACHE_BYTES + 1

    @staticmethod
    def _contains_secret(value: Any) -> bool:
        secret_markers = ("password", "token", "secret", "credential")
        if isinstance(value, (BaseException, bytes, bytearray, memoryview)):
            return True
        if isinstance(value, dict):
            return any(any(marker in str(key).casefold() for marker in secret_markers) or SessionPerformanceCache._contains_secret(item) for key, item in value.items())
        if isinstance(value, (list, tuple)):
            return any(SessionPerformanceCache._contains_secret(item) for item in value)
        return False

    def _store_locked(self, key: str, entry: _Entry) -> None:
        if key in self._entries:
            self._remove_locked(key)
        self._entries[key] = entry
        self._bytes += entry.size
        self.stats.stores += 1
        while len(self._entries) > self.max_entries or self._bytes > self.max_bytes:
            oldest = next(iter(self._entries))
            self._remove_locked(oldest)
            self.stats.evictions += 1

    def _refresh(self, key: str, policy: CachePolicy, scope: SessionScope, loader: Callable[[], Any]) -> None:
        try:
            result = copy.deepcopy(loader())
            size = self._estimate_size(result)
            with self._lock:
                if self._scope == scope and not self._contains_secret(result) and size <= min(policy.max_payload_bytes, self.max_bytes):
                    now = self._clock()
                    self._store_locked(key, _Entry(result, policy.resource, now, now + policy.ttl_seconds, size))
                elif self._scope == scope:
                    self.stats.rejected += 1
        except Exception:
            with self._lock:
                self.stats.refresh_failures += 1
                handler = self._refresh_failure_handler if not self._shutdown and self._scope == scope else None
                if handler is not None:
                    handler(policy.resource)
        finally:
            with self._lock:
                self._refreshing.discard(key)
                self._refresh_threads.discard(threading.current_thread())

    def _remove_locked(self, key: str) -> None:
        entry = self._entries.pop(key, None)
        if entry is not None:
            self._bytes -= entry.size

    def _clear_locked(self) -> None:
        self._entries.clear()
        self._bytes = 0
        for flight in self._inflight.values():
            flight.error = CacheSessionInvalidated("The authenticated session changed while data was loading")
            flight.event.set()
        self._inflight.clear()
