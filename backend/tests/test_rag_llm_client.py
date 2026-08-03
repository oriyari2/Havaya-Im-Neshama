from __future__ import annotations

import unittest
from unittest.mock import patch

import httpx

from rag.llm_client import (
    LLMClientError,
    LLMClientMalformedResponseError,
    LLMClientTimeoutError,
    OLLAMA_STREAM_CONNECT_TIMEOUT_SECONDS,
    OLLAMA_STREAM_IDLE_TIMEOUT_SECONDS,
    OllamaLLMClient,
)


class _StreamResponse:
    def __init__(self, lines: list[str], status_code: int = 200) -> None:
        self.lines = lines
        self.status_code = status_code
        self.request = httpx.Request(
            "POST",
            "http://localhost:11434/api/generate",
        )

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _traceback) -> None:
        return None

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "bad status",
                request=self.request,
                response=httpx.Response(
                    self.status_code,
                    request=self.request,
                ),
            )

    def iter_lines(self):
        yield from self.lines


class OllamaLLMClientTests(unittest.TestCase):
    def test_generate_posts_prompt_to_configured_ollama_url(self) -> None:
        client = OllamaLLMClient(
            model="demo-model",
            base_url="http://localhost:11434",
            timeout_seconds=12,
            keep_alive="test-keep-alive",
        )
        request = httpx.Request(
            "POST",
            "http://localhost:11434/api/generate",
        )
        response = httpx.Response(
            200,
            json={"response": "generated answer"},
            request=request,
        )

        with (
            patch("rag.llm_client.get_ollama_temperature", return_value=0.25),
            patch("rag.llm_client.get_ollama_num_predict", return_value=777),
            patch("rag.llm_client.httpx.post", return_value=response) as post,
        ):
            generated = client.generate("What should I prepare?")

        self.assertEqual(generated, "generated answer")
        post.assert_called_once_with(
            "http://localhost:11434/api/generate",
            json={
                "model": "demo-model",
                "prompt": "What should I prepare?",
                "stream": False,
                "keep_alive": "test-keep-alive",
                "options": {
                    "temperature": 0.25,
                    "num_predict": 777,
                },
            },
            timeout=12,
        )

    def test_generate_injects_future_rag_context_into_prompt(self) -> None:
        client = OllamaLLMClient(
            model="demo-model",
            base_url="http://localhost:11434",
        )
        request = httpx.Request(
            "POST",
            "http://localhost:11434/api/generate",
        )
        response = httpx.Response(
            200,
            json={"response": "grounded answer"},
            request=request,
        )

        with patch("rag.llm_client.httpx.post", return_value=response) as post:
            client.generate(
                "Draft a proposal",
                context=["Use drums", "Bring mats"],
            )

        payload = post.call_args.kwargs["json"]
        self.assertIn("[Source 1] Use drums", payload["prompt"])
        self.assertIn("[Source 2] Bring mats", payload["prompt"])
        self.assertIn("Question:\nDraft a proposal", payload["prompt"])

    def test_generate_rejects_empty_prompt(self) -> None:
        client = OllamaLLMClient(
            model="demo-model",
            base_url="http://localhost:11434",
        )

        with self.assertRaises(ValueError):
            client.generate("  ")

    def test_generate_wraps_ollama_transport_errors(self) -> None:
        client = OllamaLLMClient(
            model="demo-model",
            base_url="http://localhost:11434",
        )

        with patch(
            "rag.llm_client.httpx.post",
            side_effect=httpx.ConnectError("offline"),
        ):
            with self.assertRaises(LLMClientError):
                client.generate("Hello")

    def test_streaming_generation_accumulates_chunks_and_final_metadata(self) -> None:
        client = OllamaLLMClient(
            model="demo-model",
            base_url="http://localhost:11434",
        )
        stream = _StreamResponse(
            [
                '{"response":"Generated ","done":false}',
                '{"response":"answer [1].","done":true,"done_reason":"stop","eval_count":4}',
            ]
        )

        with (
            patch("rag.llm_client.get_ollama_num_predict", return_value=777),
            patch("rag.llm_client.httpx.stream", return_value=stream) as stream_call,
        ):
            generated = client.generate_stream_with_metadata("Question?")

        self.assertEqual(generated.text, "Generated answer [1].")
        self.assertEqual(generated.metadata["done_reason"], "stop")
        self.assertEqual(generated.metadata["eval_count"], 4)

        payload = stream_call.call_args.kwargs["json"]
        timeout = stream_call.call_args.kwargs["timeout"]

        self.assertTrue(payload["stream"])
        self.assertEqual(payload["options"]["num_predict"], 777)
        self.assertEqual(
            timeout.connect,
            OLLAMA_STREAM_CONNECT_TIMEOUT_SECONDS,
        )
        self.assertEqual(
            timeout.read,
            OLLAMA_STREAM_IDLE_TIMEOUT_SECONDS,
        )

    def test_streaming_progress_beyond_old_40_seconds_completes(self) -> None:
        client = OllamaLLMClient(
            model="demo-model",
            base_url="http://localhost:11434",
        )
        stream = _StreamResponse(
            [
                '{"response":"Still ","done":false}',
                '{"response":"working ","done":false}',
                '{"response":"done [1].","done":true,"done_reason":"stop"}',
            ]
        )
        times = iter([0.0, 41.0, 82.0, 123.0])

        with patch("rag.llm_client.httpx.stream", return_value=stream):
            generated = client.generate_stream_with_metadata(
                "Question?",
                total_cap_seconds=200.0,
                clock=lambda: next(times),
            )

        self.assertEqual(generated.text, "Still working done [1].")
        self.assertEqual(generated.metadata["done_reason"], "stop")

    def test_streaming_total_safety_cap_raises_timeout_without_returning_partial_text(self) -> None:
        client = OllamaLLMClient(
            model="demo-model",
            base_url="http://localhost:11434",
        )
        stream = _StreamResponse(
            [
                '{"response":"Partial text that must not return ","done":false}',
                '{"response":"late","done":false}',
            ]
        )
        times = iter([0.0, 10.0, 21.0])

        with patch("rag.llm_client.httpx.stream", return_value=stream):
            with self.assertRaises(LLMClientTimeoutError):
                client.generate_stream_with_metadata(
                    "Question?",
                    total_cap_seconds=20.0,
                    clock=lambda: next(times),
                )

    def test_streaming_timeout_and_malformed_or_broken_stream_raise_client_errors(self) -> None:
        client = OllamaLLMClient(
            model="demo-model",
            base_url="http://localhost:11434",
        )

        with patch(
            "rag.llm_client.httpx.stream",
            side_effect=httpx.ReadTimeout("idle"),
        ):
            with self.assertRaises(LLMClientTimeoutError):
                client.generate_stream_with_metadata("Question?")

        with patch(
            "rag.llm_client.httpx.stream",
            return_value=_StreamResponse(["not json"]),
        ):
            with self.assertRaises(LLMClientMalformedResponseError):
                client.generate_stream_with_metadata("Question?")

        with patch(
            "rag.llm_client.httpx.stream",
            return_value=_StreamResponse(
                ['{"response":"partial ","done":false}']
            ),
        ):
            with self.assertRaises(LLMClientMalformedResponseError):
                client.generate_stream_with_metadata("Question?")


if __name__ == "__main__":
    unittest.main()
