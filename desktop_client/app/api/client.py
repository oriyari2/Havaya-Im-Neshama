from __future__ import annotations

import json
import os
from enum import StrEnum
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ApiErrorKind(StrEnum):
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    SERVER = "server"
    CONNECTION = "connection"
    UNKNOWN = "unknown"


class ApiError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        kind: ApiErrorKind | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.kind = kind or self.kind_for_status(status_code)
        self.retriable = self.kind in {ApiErrorKind.SERVER, ApiErrorKind.CONNECTION}

    @staticmethod
    def kind_for_status(status_code: int | None) -> ApiErrorKind:
        if status_code is None:
            return ApiErrorKind.CONNECTION
        return {
            400: ApiErrorKind.VALIDATION,
            401: ApiErrorKind.AUTHENTICATION,
            403: ApiErrorKind.PERMISSION,
            404: ApiErrorKind.NOT_FOUND,
            409: ApiErrorKind.CONFLICT,
            422: ApiErrorKind.VALIDATION,
        }.get(status_code, ApiErrorKind.SERVER if status_code >= 500 else ApiErrorKind.UNKNOWN)


class ApiClient:
    def __init__(self, base_url: str | None = None, timeout: float = 120.0) -> None:
        self.base_url = (base_url or os.getenv("API_BASE_URL", "http://127.0.0.1:8000")).rstrip("/")
        self.timeout = timeout
        self.access_token: str | None = None
        self._unauthorized_handler: Callable[[], None] | None = None

    def set_access_token(self, token: str | None) -> None:
        self.access_token = token

    def set_unauthorized_handler(self, handler: Callable[[], None] | None) -> None:
        self._unauthorized_handler = handler

    def get(self, path: str, params: dict[str, object] | None = None) -> Any:
        query = urlencode(
            {key: value for key, value in (params or {}).items() if value not in (None, "")},
            doseq=True,
        )
        target = f"{path}?{query}" if query else path
        return self._request("GET", target)

    def post(self, path: str, payload: dict[str, object]) -> Any:
        return self._request("POST", path, payload)

    def patch(self, path: str, payload: dict[str, object]) -> Any:
        return self._request("PATCH", path, payload)

    def put(self, path: str, payload: dict[str, object]) -> Any:
        return self._request("PUT", path, payload)

    def delete(self, path: str, payload: dict[str, object] | None = None) -> Any:
        return self._request("DELETE", path, payload)

    def _request(self, method: str, path: str, payload: dict[str, object] | None = None) -> Any:
        headers = {"Accept": "application/json"}
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        request = Request(f"{self.base_url}{path}", data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else None
        except HTTPError as exc:
            message = self._error_message(exc.read().decode("utf-8", errors="replace"))
            if exc.code == 401 and self.access_token is not None:
                self.access_token = None
                if self._unauthorized_handler is not None:
                    self._unauthorized_handler()
            raise ApiError(message, status_code=exc.code) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ApiError(
                "לא ניתן להתחבר לשרת. ודאו שה־API פועל.",
                kind=ApiErrorKind.CONNECTION,
            ) from exc

    @staticmethod
    def _error_message(raw_body: str) -> str:
        try:
            detail = json.loads(raw_body).get("detail")
            if isinstance(detail, str):
                return detail
            if isinstance(detail, list):
                messages = [item.get("msg") for item in detail if isinstance(item, dict) and item.get("msg")]
                if messages:
                    return "; ".join(messages)
        except (json.JSONDecodeError, AttributeError):
            pass
        return "הבקשה לשרת נכשלה."
