from __future__ import annotations

import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from desktop_client.app.api.client import ApiClient, ApiError, ApiErrorKind


class _Response:
    def __init__(self, payload: object) -> None:
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return self.payload


class ApiClientTests(unittest.TestCase):
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
