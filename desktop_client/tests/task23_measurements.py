"""Opt-in real-backend Task 23 measurement harness.

Set TASK23_DEMO_EMAIL and TASK23_DEMO_PASSWORD. The harness performs authenticated
reads only, never prints credentials or tokens, and emits one JSON measurement.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from urllib.parse import urlencode

from PySide6.QtWidgets import QApplication

from desktop_client.app.api.client import ApiClient
from desktop_client.app.main import MainWindow
from desktop_client.app.services.auth_service import AuthService


READS = (
    ("dashboard", "/bookings/dashboard", None),
    ("customers", "/customers", {"limit": 25, "offset": 0}),
    ("instructors", "/instructors", {"limit": 25, "offset": 0}),
    ("users", "/users", {"limit": 25, "offset": 0}),
    ("activities", "/activities", {"limit": 25, "offset": 0}),
    ("bookings", "/bookings", {"limit": 25, "offset": 0}),
    ("open_events", "/bookings/open-events", None),
    ("knowledge", "/api/rag/sources", None),
)


def _milliseconds(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 3)


def main() -> int:
    email = os.getenv("TASK23_DEMO_EMAIL")
    password = os.getenv("TASK23_DEMO_PASSWORD")
    if not email or not password:
        raise SystemExit("TASK23_DEMO_EMAIL and TASK23_DEMO_PASSWORD are required")

    client = ApiClient(timeout=15)
    started = time.perf_counter()
    session = AuthService(client).login(email, password)
    login_ms = _milliseconds(started)
    underlying = 0
    request = client._request

    def counted_request(*args, **kwargs):
        nonlocal underlying
        underlying += 1
        return request(*args, **kwargs)

    client._request = counted_request
    measurements = []
    for name, path, params in READS:
        query = urlencode(params or {})
        target = path + (f"?{query}" if query else "")
        try:
            started = time.perf_counter()
            request("GET", target)
            uncached_repeat_ms = _milliseconds(started)
            before = underlying
            started = time.perf_counter()
            client.get(path, params)
            first_ms = _milliseconds(started)
            after_first = underlying
            started = time.perf_counter()
            client.get(path, params)
            cached_ms = _milliseconds(started)
            measurements.append(
                {
                    "screen": name,
                    "uncached_repeat_ms": uncached_repeat_ms,
                    "first_ms": first_ms,
                    "cached_ms": cached_ms,
                    "first_http": after_first - before,
                    "cached_http": underlying - after_first,
                }
            )
        except Exception as exc:
            measurements.append({"screen": name, "unavailable": type(exc).__name__})

    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow(client)
    window._show_workspace(session)
    window.show()
    render_metrics: dict[str, dict[str, float | int]] = {}
    render_methods = {
        "dashboard": ("show_summary", "show_sections"),
        "customers": ("show_customers",),
        "instructors": ("show_instructors",),
        "users": ("show_users",),
        "activities": ("show_activities",),
        "bookings": ("show_bookings",),
        "open_events": ("show_events",),
        "knowledge": ("show_sources",),
    }
    for page, method_names in render_methods.items():
        presenter = window._presenters.get(page)
        view = getattr(presenter, "view", None)
        if view is None:
            continue
        metric = render_metrics.setdefault(page, {"calls": 0, "milliseconds": 0.0})
        for method_name in method_names:
            original = getattr(view, method_name, None)
            if original is None:
                continue

            def measured(*args, _original=original, _metric=metric, **kwargs):
                render_started = time.perf_counter()
                try:
                    return _original(*args, **kwargs)
                finally:
                    _metric["calls"] += 1
                    _metric["milliseconds"] = round(float(_metric["milliseconds"]) + (time.perf_counter() - render_started) * 1000, 3)

            setattr(view, method_name, measured)
    navigation = []
    output_path = os.getenv("TASK23_OUTPUT_PATH")
    available = set(window.shell.pages)
    sequence = [key for key in ("customers", "users", "customers", "instructors", "dashboard") if key in available]
    for width, height in ((1024, 640), (1200, 760), (1440, 900)):
        window.resize(width, height)
        app.processEvents()
    for page in sequence:
        before_requests = underlying
        started = time.perf_counter()
        window._navigate(page)
        submission_ms = _milliseconds(started)
        deadline = time.monotonic() + 15
        while window.operation_executor.active_count and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.001)
        app.processEvents()
        navigation.append({"page": page, "submission_ms": submission_ms, "useful_ms": _milliseconds(started), "http_requests": underlying - before_requests, "active_page": window._active_page, "timed_out": bool(window.operation_executor.active_count)})
        if output_path:
            Path(output_path).write_text(json.dumps({"role": session.role, "login_ms": login_ms, "reads": measurements, "navigation": navigation, "render": render_metrics, "cache": client.performance_snapshot()}, ensure_ascii=False), encoding="utf-8")
    report = json.dumps(
            {
                "role": session.role,
                "login_ms": login_ms,
                "reads": measurements,
                "navigation": navigation,
                "render": render_metrics,
                "cache": client.performance_snapshot(),
            },
            ensure_ascii=False,
        )
    if output_path:
        Path(output_path).write_text(report, encoding="utf-8")
    else:
        print(report, flush=True)
    window.close()
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
