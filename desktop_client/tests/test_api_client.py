from __future__ import annotations

import io
import json
import unittest
from unittest.mock import Mock, patch
from urllib.request import Request
from urllib.error import HTTPError, URLError

from desktop_client.app.api.client import ApiClient, ApiError, ApiErrorKind, _HttpsOnlyRedirectHandler
from desktop_client.app.media_config import MAX_PREVIEW_DOWNLOAD_BYTES


class _Response:
    def __init__(self, payload: object) -> None:
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self, size=-1):
        return self.payload if size < 0 else self.payload[:size]


class _RawResponse:
    def __init__(self, payload: bytes, final_url: str = "https://cdn.example/image") -> None:
        self.payload = payload
        self.final_url = final_url

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self, size=-1):
        return self.payload if size < 0 else self.payload[:size]

    def geturl(self):
        return self.final_url


class ApiClientTests(unittest.TestCase):
    def test_successful_customer_delete_204_keeps_the_authenticated_session(self) -> None:
        client = ApiClient("http://example.test")
        client.set_access_token("manager-token")
        expired = []
        client.set_unauthorized_handler(lambda: expired.append(True))
        with patch("desktop_client.app.api.client.urlopen", return_value=_RawResponse(b"")):
            self.assertIsNone(client.delete("/customers/customer-1"))
        self.assertEqual(client.access_token, "manager-token")
        self.assertEqual(expired, [])

    def test_obsolete_request_401_cannot_expire_new_session_token(self) -> None:
        client = ApiClient("http://example.test")
        client.set_access_token("old-token")
        notified = []
        client.set_unauthorized_handler(lambda: notified.append(True))

        def fail(_request, timeout):
            client.set_access_token("new-token")
            raise HTTPError("http://example.test/customers", 401, "Unauthorized", {}, io.BytesIO(b'{"detail":"expired"}'))

        with patch("desktop_client.app.api.client.urlopen", side_effect=fail):
            with self.assertRaises(ApiError):
                client.get("/customers")
        self.assertEqual(client.access_token, "new-token")
        self.assertEqual(notified, [])

    def test_authenticated_non_401_http_errors_preserve_token_and_do_not_notify(self) -> None:
        for status_code in (403, 422, 500, 503):
            with self.subTest(status_code=status_code):
                client = ApiClient("http://example.test")
                client.set_access_token("manager-token")
                notified = []
                client.set_unauthorized_handler(lambda: notified.append(True))
                error = HTTPError(
                    "http://example.test/resource",
                    status_code,
                    "Error",
                    {},
                    io.BytesIO(b'{"detail":"backend error"}'),
                )

                with patch("desktop_client.app.api.client.urlopen", side_effect=error):
                    with self.assertRaises(ApiError) as raised:
                        client.post("/resource", {"value": "x"})

                self.assertEqual(raised.exception.status_code, status_code)
                self.assertEqual(str(raised.exception), "backend error")
                self.assertEqual(client.access_token, "manager-token")
                self.assertEqual(notified, [])

    def test_ai_timeout_has_distinct_message_and_preserves_session(self) -> None:
        client = ApiClient("http://example.test")
        client.set_access_token("manager-token")
        notified = []
        client.set_unauthorized_handler(lambda: notified.append(True))
        requests = []

        def fail(request, timeout):
            requests.append((request, timeout))
            raise TimeoutError()

        with patch("desktop_client.app.api.client.urlopen", side_effect=fail):
            with self.assertRaises(ApiError) as raised:
                client.post_ai("/api/ai/consult", {"prompt": "hello"})

        self.assertEqual(raised.exception.kind, ApiErrorKind.TIMEOUT)
        self.assertEqual(requests[0][1], 480.0)
        self.assertIn("AI", str(raised.exception))
        self.assertNotIn("להתחבר לשרת", str(raised.exception))
        self.assertEqual(client.access_token, "manager-token")
        self.assertEqual(notified, [])

    def test_ai_urlerror_wrapped_timeout_is_classified_as_timeout(self) -> None:
        client = ApiClient("http://example.test")
        client.set_access_token("manager-token")
        notified = []
        client.set_unauthorized_handler(lambda: notified.append(True))

        with patch("desktop_client.app.api.client.urlopen", side_effect=URLError(TimeoutError("timed out"))):
            with self.assertRaises(ApiError) as raised:
                client.post_ai("/api/ai/consult", {"prompt": "hello"})

        self.assertEqual(raised.exception.kind, ApiErrorKind.TIMEOUT)
        self.assertIn("AI", str(raised.exception))
        self.assertEqual(client.access_token, "manager-token")
        self.assertEqual(notified, [])

    def test_ai_503_preserves_session(self) -> None:
        client = ApiClient("http://example.test")
        client.set_access_token("manager-token")
        notified = []
        client.set_unauthorized_handler(lambda: notified.append(True))
        error = HTTPError(
            "http://example.test/api/ai/consult",
            503,
            "Service Unavailable",
            {},
            io.BytesIO(b'{"detail":"AI service is unavailable"}'),
        )

        with patch("desktop_client.app.api.client.urlopen", side_effect=error):
            with self.assertRaises(ApiError) as raised:
                client.post_ai("/api/ai/consult", {"prompt": "hello"})

        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(str(raised.exception), "שירות ה-AI אינו זמין כרגע. נסו שוב בעוד רגע.")
        self.assertNotIn("AI service is unavailable", str(raised.exception))
        self.assertEqual(client.access_token, "manager-token")
        self.assertEqual(notified, [])

    def test_ai_embedding_backend_detail_is_not_exposed(self) -> None:
        client = ApiClient("http://example.test")
        client.set_access_token("manager-token")
        error = HTTPError(
            "http://example.test/api/ai/consult",
            503,
            "Service Unavailable",
            {},
            io.BytesIO(b'{"detail":"Embedding service is unavailable. Verify Ollama is running."}'),
        )

        with patch("desktop_client.app.api.client.urlopen", side_effect=error):
            with self.assertRaises(ApiError) as raised:
                client.post_ai("/api/ai/consult", {"prompt": "hello"})

        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(str(raised.exception), "שירות ה-AI אינו זמין כרגע. נסו שוב בעוד רגע.")
        self.assertNotIn("Embedding service is unavailable", str(raised.exception))

    def test_multipart_upload_is_authenticated_and_contains_file(self) -> None:
        client = ApiClient("http://example.test")
        client.set_access_token("manager-token")
        captured = []

        def respond(request, timeout):
            captured.append(request)
            return _Response({"id": "image-1"})

        with patch("desktop_client.app.api.client.urlopen", side_effect=respond):
            result = client.post_multipart(
                "/activities/a1/images",
                field_name="file",
                filename="פלאייר.png",
                content_type="image/png",
                file_bytes=b"image-bytes",
            )

        request = captured[0]
        self.assertEqual(result, {"id": "image-1"})
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.get_header("Authorization"), "Bearer manager-token")
        self.assertIn("multipart/form-data; boundary=", request.get_header("Content-type"))
        self.assertIn("פלאייר.png".encode(), request.data)
        self.assertIn(b"Content-Type: image/png", request.data)
        self.assertIn(b"image-bytes", request.data)

    def test_public_preview_is_https_bounded_and_never_authenticated(self) -> None:
        client = ApiClient("http://example.test")
        client.set_access_token("must-not-leak")
        requests = []

        opener = Mock()
        opener.open.side_effect = lambda request, timeout: requests.append(request) or _RawResponse(b"1234")
        with patch("desktop_client.app.api.client.build_opener", return_value=opener):
            self.assertEqual(client.get_public_bytes("https://cdn.example/image", max_bytes=10), b"1234")
        self.assertIsNone(requests[0].get_header("Authorization"))
        with self.assertRaises(ApiError):
            client.get_public_bytes("http://cdn.example/image", max_bytes=10)
        opener.open.return_value = _RawResponse(b"x" * 11)
        opener.open.side_effect = None
        with patch("desktop_client.app.api.client.build_opener", return_value=opener):
            with self.assertRaises(ApiError):
                client.get_public_bytes("https://cdn.example/large", max_bytes=10)

    def test_public_preview_redirects_remain_https_and_strip_authorization(self) -> None:
        handler = _HttpsOnlyRedirectHandler()
        original = Request("https://cdn.example/start", headers={"Authorization": "Bearer forbidden"})
        redirected = handler.redirect_request(original, None, 302, "Found", {}, "https://cdn2.example/final")
        self.assertEqual(redirected.full_url, "https://cdn2.example/final")
        self.assertIsNone(redirected.get_header("Authorization"))
        with self.assertRaises(URLError):
            handler.redirect_request(original, None, 302, "Found", {}, "http://cdn2.example/final")

    def test_public_preview_rejects_http_final_url_and_handles_timeout(self) -> None:
        client = ApiClient("http://example.test")
        opener = Mock()
        opener.open.return_value = _RawResponse(b"image", "http://cdn.example/final")
        with patch("desktop_client.app.api.client.build_opener", return_value=opener):
            with self.assertRaises(ApiError):
                client.get_public_bytes("https://cdn.example/start", max_bytes=10)
        opener.open.side_effect = TimeoutError()
        with patch("desktop_client.app.api.client.build_opener", return_value=opener):
            with self.assertRaises(ApiError) as raised:
                client.get_public_bytes("https://cdn.example/start", max_bytes=10)
        self.assertEqual(raised.exception.kind, ApiErrorKind.CONNECTION)

    def test_public_preview_exact_configured_boundary(self) -> None:
        client = ApiClient("http://example.test")
        opener = Mock()
        opener.open.return_value = _RawResponse(b"x" * MAX_PREVIEW_DOWNLOAD_BYTES)
        with patch("desktop_client.app.api.client.build_opener", return_value=opener):
            self.assertEqual(len(client.get_public_bytes("https://cdn.example/image", max_bytes=MAX_PREVIEW_DOWNLOAD_BYTES)), MAX_PREVIEW_DOWNLOAD_BYTES)
        opener.open.return_value = _RawResponse(b"x" * (MAX_PREVIEW_DOWNLOAD_BYTES + 1))
        with patch("desktop_client.app.api.client.build_opener", return_value=opener):
            with self.assertRaises(ApiError):
                client.get_public_bytes("https://cdn.example/image", max_bytes=MAX_PREVIEW_DOWNLOAD_BYTES)

    def test_json_and_multipart_have_one_authorization_header(self) -> None:
        client = ApiClient("http://example.test")
        client.set_access_token("one-token")
        requests = []
        with patch("desktop_client.app.api.client.urlopen", side_effect=lambda request, timeout: requests.append(request) or _Response({"ok": True})):
            client.post("/activities", {"name": "A"})
            client.post_multipart("/activities/a/images", field_name="file", filename="a.png", content_type="image/png", file_bytes=b"x")
        for request in requests:
            authorization = [value for name, value in request.header_items() if name.lower() == "authorization"]
            self.assertEqual(authorization, ["Bearer one-token"])
    def test_validation_details_are_readable(self) -> None:
        raw = '{"detail":[{"loc":["body","participant_count"],"msg":"Input should be greater than 0"}]}'
        self.assertEqual(ApiClient._error_message(raw), "Input should be greater than 0")

    def test_http_and_connection_errors_keep_useful_categories(self) -> None:
        client = ApiClient("http://example.invalid")
        http_error = HTTPError(
            "http://example.invalid/bookings", 403, "Forbidden", {}, io.BytesIO(b'{"detail":"Not authorized"}')
        )
        with patch("desktop_client.app.api.client.urlopen", side_effect=http_error):
            with self.assertRaises(ApiError) as raised:
                client.patch("/bookings/b/status", {"status": "CONFIRMED", "expected_version": 1})
        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(str(raised.exception), "Not authorized")

        with patch("desktop_client.app.api.client.urlopen", side_effect=URLError("offline")):
            with self.assertRaises(ApiError) as raised:
                client.post("/bookings", {})
        self.assertIsNone(raised.exception.status_code)
        self.assertEqual(raised.exception.kind, ApiErrorKind.CONNECTION)
        self.assertTrue(raised.exception.retriable)

    def test_put_delete_delete_body_and_query_encoding(self) -> None:
        client = ApiClient("http://example.test")
        requests = []

        def respond(request, timeout):
            requests.append((request, timeout))
            return _Response({"ok": True})

        with patch("desktop_client.app.api.client.urlopen", side_effect=respond):
            client.get("/customers", {"search": "בית ספר", "tag": ["קיץ", "חוץ"], "empty": ""})
            client.put("/customers/c1", {"name": "לקוח"})
            client.delete("/customers/c1")
            client.delete("/bookings/b/activities/ba/instructors/i", {"expected_version": 3})

        self.assertIn("search=%D7%91%D7%99%D7%AA+%D7%A1%D7%A4%D7%A8", requests[0][0].full_url)
        self.assertIn("tag=%D7%A7%D7%99%D7%A5&tag=%D7%97%D7%95%D7%A5", requests[0][0].full_url)
        self.assertNotIn("empty=", requests[0][0].full_url)
        self.assertEqual(requests[1][0].method, "PUT")
        self.assertEqual(json.loads(requests[1][0].data), {"name": "לקוח"})
        self.assertEqual(requests[2][0].method, "DELETE")
        self.assertIsNone(requests[2][0].data)
        self.assertEqual(json.loads(requests[3][0].data), {"expected_version": 3})

    def test_authenticated_401_clears_token_and_notifies_once(self) -> None:
        client = ApiClient("http://example.invalid")
        expired = []
        client.set_access_token("expired")
        client.set_unauthorized_handler(lambda: expired.append(True))
        error = HTTPError("http://example.invalid/auth/me", 401, "Unauthorized", {}, io.BytesIO(b'{"detail":"Not authenticated"}'))
        with patch("desktop_client.app.api.client.urlopen", side_effect=error):
            with self.assertRaises(ApiError) as raised:
                client.get("/auth/me")
        self.assertEqual(raised.exception.kind, ApiErrorKind.AUTHENTICATION)
        self.assertIsNone(client.access_token)
        self.assertEqual(expired, [True])

    def test_login_401_does_not_trigger_session_expiry_without_token(self) -> None:
        client = ApiClient("http://example.invalid")
        expired = []
        client.set_unauthorized_handler(lambda: expired.append(True))
        error = HTTPError("http://example.invalid/auth/login", 401, "Unauthorized", {}, io.BytesIO(b'{"detail":"Invalid credentials"}'))
        with patch("desktop_client.app.api.client.urlopen", side_effect=error):
            with self.assertRaises(ApiError):
                client.post("/auth/login", {})
        self.assertEqual(expired, [])

    def test_statuses_are_classified_consistently(self) -> None:
        expected = {
            400: ApiErrorKind.VALIDATION,
            401: ApiErrorKind.AUTHENTICATION,
            403: ApiErrorKind.PERMISSION,
            404: ApiErrorKind.NOT_FOUND,
            409: ApiErrorKind.CONFLICT,
            422: ApiErrorKind.VALIDATION,
            500: ApiErrorKind.SERVER,
        }
        self.assertEqual({code: ApiError.kind_for_status(code) for code in expected}, expected)


if __name__ == "__main__":
    unittest.main()
