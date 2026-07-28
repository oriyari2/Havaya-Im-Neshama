from __future__ import annotations

import unittest
from unittest.mock import patch

import httpx

from rag.llm_client import LLMClientError, OllamaLLMClient


class OllamaLLMClientTests(unittest.TestCase):
    def test_generate_posts_prompt_to_configured_ollama_url(self) -> None:
        client = OllamaLLMClient(model="demo-model", base_url="http://localhost:11434")
        request = httpx.Request("POST", "http://localhost:11434/api/generate")
        response = httpx.Response(200, json={"response": "generated answer"}, request=request)

        with patch("rag.llm_client.httpx.post", return_value=response) as post:
            generated = client.generate("What should I prepare?")

        self.assertEqual(generated, "generated answer")
        post.assert_called_once_with(
            "http://localhost:11434/api/generate",
            json={
                "model": "demo-model",
                "prompt": "What should I prepare?",
                "stream": False,
            },
            timeout=120.0,
        )

    def test_generate_injects_future_rag_context_into_prompt(self) -> None:
        client = OllamaLLMClient(model="demo-model", base_url="http://localhost:11434")
        request = httpx.Request("POST", "http://localhost:11434/api/generate")
        response = httpx.Response(200, json={"response": "grounded answer"}, request=request)

        with patch("rag.llm_client.httpx.post", return_value=response) as post:
            client.generate("Draft a proposal", context=["Use drums", "Bring mats"])

        payload = post.call_args.kwargs["json"]
        self.assertIn("[Source 1] Use drums", payload["prompt"])
        self.assertIn("[Source 2] Bring mats", payload["prompt"])
        self.assertIn("Question:\nDraft a proposal", payload["prompt"])

    def test_generate_rejects_empty_prompt(self) -> None:
        client = OllamaLLMClient(model="demo-model", base_url="http://localhost:11434")

        with self.assertRaises(ValueError):
            client.generate("  ")

    def test_generate_wraps_ollama_transport_errors(self) -> None:
        client = OllamaLLMClient(model="demo-model", base_url="http://localhost:11434")

        with patch("rag.llm_client.httpx.post", side_effect=httpx.ConnectError("offline")):
            with self.assertRaises(LLMClientError):
                client.generate("Hello")


if __name__ == "__main__":
    unittest.main()
