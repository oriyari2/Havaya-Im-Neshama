from __future__ import annotations

import json
import os
import socket
import secrets
from enum import StrEnum
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

from desktop_client.app.infrastructure.performance_cache import SessionPerformanceCache


class ApiErrorKind(StrEnum):
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    SERVER = "server"
    CONNECTION = "connection"
    TIMEOUT = "timeout"
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
        self.retriable = self.kind in {ApiErrorKind.SERVER, ApiErrorKind.CONNECTION, ApiErrorKind.TIMEOUT}

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


def _is_timeout_error(exc: BaseException) -> bool:
    if isinstance(exc, TimeoutError | socket.timeout):
        return True
    reason = getattr(exc, "reason", None)
    if isinstance(reason, BaseException):
        return _is_timeout_error(reason)
    return isinstance(reason, str) and "timed out" in reason.lower()


class _HttpsOnlyRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        parsed = urlparse(new_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise URLError("Insecure image redirect blocked")
        redirected = super().redirect_request(request, file_pointer, code, message, headers, new_url)
        if redirected is not None:
            redirected.remove_header("Authorization")
        return redirected


class ApiClient:
    def __init__(self, base_url: str | None = None, timeout: float = 120.0, performance_cache: SessionPerformanceCache | None = None) -> None:
        self.base_url = (base_url or os.getenv("API_BASE_URL", "http://127.0.0.1:8000")).rstrip("/")
        self.timeout = timeout
        self.ai_timeout = float(os.getenv("API_AI_TIMEOUT_SECONDS", "480"))
        self.access_token: str | None = None
        self._unauthorized_handler: Callable[[], None] | None = None
        self.performance_cache = performance_cache or SessionPerformanceCache()

    def set_access_token(self, token: str | None) -> None:
        self.access_token = token

    def set_performance_scope(self, user_id: str, role: str) -> None:
        self.performance_cache.start_session(user_id, role)

    def clear_performance_scope(self) -> None:
        self.performance_cache.clear_session()

    def invalidate_cached_get(self, path: str, params: dict[str, object] | None = None) -> bool:
        return self.performance_cache.invalidate_path(path, params)

    def performance_snapshot(self) -> dict[str, int]:
        return self.performance_cache.snapshot()

    def set_unauthorized_handler(self, handler: Callable[[], None] | None) -> None:
        self._unauthorized_handler = handler

    def get(self, path: str, params: dict[str, object] | None = None) -> Any:
        query = urlencode(
            {key: value for key, value in (params or {}).items() if value not in (None, "")},
            doseq=True,
        )
        target = f"{path}?{query}" if query else path
        return self.performance_cache.get_or_load(path, params, lambda: self._request("GET", target))

    def post(self, path: str, payload: dict[str, object]) -> Any:
        result = self._request("POST", path, payload)
        if path != "/auth/login":
            self.performance_cache.invalidate_for_mutation(path, payload)
        return result

    def post_ai(self, path: str, payload: dict[str, object]) -> Any:
        return self._request("POST", path, payload, timeout=self.ai_timeout, ai_request=True)

    def patch(self, path: str, payload: dict[str, object]) -> Any:
        result = self._request("PATCH", path, payload)
        self.performance_cache.invalidate_for_mutation(path, payload)
        return result

    def put(self, path: str, payload: dict[str, object]) -> Any:
        result = self._request("PUT", path, payload)
        self.performance_cache.invalidate_for_mutation(path, payload)
        return result

    def delete(self, path: str, payload: dict[str, object] | None = None) -> Any:
        result = self._request("DELETE", path, payload)
        self.performance_cache.invalidate_for_mutation(path, payload)
        return result

    def post_multipart(
        self,
        path: str,
        *,
        field_name: str,
        filename: str,
        content_type: str,
        file_bytes: bytes,
    ) -> Any:
        boundary = f"codex-{secrets.token_hex(16)}"
        disposition = (
            f'Content-Disposition: form-data; name="{field_name}"; '
            f'filename="{filename.replace(chr(34), "_")}"\r\n'
        ).encode("utf-8")
        body = b"".join(
            (
                f"--{boundary}\r\n".encode("ascii"),
                disposition,
                f"Content-Type: {content_type}\r\n\r\n".encode("ascii"),
                file_bytes,
                f"\r\n--{boundary}--\r\n".encode("ascii"),
            )
        )
        headers = {
            "Accept": "application/json",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
        result = self._send("POST", f"{self.base_url}{path}", data=body, headers=headers, authenticated=True)
        self.performance_cache.invalidate_for_mutation(path)
        return result

    def get_public_bytes(self, url: str, *, max_bytes: int) -> bytes:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ApiError("Invalid secure image URL", kind=ApiErrorKind.VALIDATION)
        request = Request(url, headers={"Accept": "image/*"}, method="GET")
        try:
            with build_opener(_HttpsOnlyRedirectHandler()).open(request, timeout=self.timeout) as response:
                final_url = response.geturl()
                final = urlparse(final_url)
                if final.scheme != "https" or not final.netloc:
                    raise ApiError("Image preview is unavailable", kind=ApiErrorKind.CONNECTION)
                data = response.read(max_bytes + 1)
        except HTTPError as exc:
            raise ApiError("Image preview is unavailable", status_code=exc.code) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ApiError("Image preview is unavailable", kind=ApiErrorKind.CONNECTION) from exc
        if len(data) > max_bytes:
            raise ApiError("Image preview exceeds the allowed size", kind=ApiErrorKind.VALIDATION)
        return data

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, object] | None = None,
        *,
        timeout: float | None = None,
        ai_request: bool = False,
    ) -> Any:
        headers = {"Accept": "application/json"}
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")
        return self._send(
            method,
            f"{self.base_url}{path}",
            data=data,
            headers=headers,
            authenticated=True,
            timeout=timeout,
            ai_request=ai_request,
        )

    def _send(
        self,
        method: str,
        url: str,
        *,
        data: bytes | None,
        headers: dict[str, str],
        authenticated: bool,
        timeout: float | None = None,
        ai_request: bool = False,
    ) -> Any:
        request_token = self.access_token if authenticated else None
        if request_token:
            headers = {**headers, "Authorization": f"Bearer {request_token}"}
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=timeout or self.timeout) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else None
        except HTTPError as exc:
            raw_body = exc.read().decode("utf-8", errors="replace")
            message = (
                self._ai_error_message(exc.code)
                if ai_request and exc.code != 401
                else self._error_message(raw_body)
            )
            if exc.code == 401 and request_token is not None and self.access_token == request_token:
                self.access_token = None
                if self._unauthorized_handler is not None:
                    self._unauthorized_handler()
            raise ApiError(message, status_code=exc.code) from exc
        except (TimeoutError, socket.timeout) as exc:
            raise ApiError(
                "בקשת ה-AI ארכה יותר מדי זמן. נסו שוב בעוד רגע." if ai_request else "הבקשה לשרת ארכה יותר מדי זמן.",
                kind=ApiErrorKind.TIMEOUT,
            ) from exc
        except (URLError, OSError) as exc:
            if _is_timeout_error(exc):
                raise ApiError(
                    "בקשת ה-AI ארכה יותר מדי זמן. נסו שוב בעוד רגע." if ai_request else "הבקשה לשרת ארכה יותר מדי זמן.",
                    kind=ApiErrorKind.TIMEOUT,
                ) from exc
            raise ApiError(
                "שירות ה-AI אינו זמין כרגע. נסו שוב בעוד רגע." if ai_request else "לא ניתן להתחבר לשרת. ודאו שה־API פועל.",
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

    @staticmethod
    def _ai_error_message(status_code: int) -> str:
        if status_code in {400, 422}:
            return "לא ניתן לשלוח את בקשת ה-AI כפי שהיא."
        return "שירות ה-AI אינו זמין כרגע. נסו שוב בעוד רגע."
