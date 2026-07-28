from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import httpx

from backend.app.core.environment import get_ollama_url


class LLMClientError(RuntimeError):
    """Raised when the configured local LLM service cannot complete a request."""


class LLMClient(ABC):
    """Interface used by future RAG services to generate grounded responses."""

    @abstractmethod
    def generate(self, prompt: str, context: Sequence[str] | None = None) -> str:
        """Generate text from a prompt and optional retrieved context snippets."""


@dataclass(frozen=True)
class OllamaLLMClient(LLMClient):
    model: str
    base_url: str | None = None
    timeout_seconds: float = 60.0

    def generate(self, prompt: str, context: Sequence[str] | None = None) -> str:
        user_prompt = self._build_prompt(prompt=prompt, context=context)
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": user_prompt,
            "stream": False,
        }

        try:
            response = httpx.post(
                f"{self._resolved_base_url()}/api/generate",
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMClientError("Ollama request failed") from exc

        data = response.json()
        generated = data.get("response")
        if not isinstance(generated, str):
            raise LLMClientError("Ollama response did not include generated text")
        return generated

    def _resolved_base_url(self) -> str:
        return (self.base_url or get_ollama_url()).rstrip("/")

    @staticmethod
    def _build_prompt(prompt: str, context: Sequence[str] | None = None) -> str:
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise ValueError("prompt must not be empty")

        snippets = [item.strip() for item in context or () if item and item.strip()]
        if not snippets:
            return clean_prompt

        context_block = "\n\n".join(f"[Source {index}] {snippet}" for index, snippet in enumerate(snippets, start=1))
        return (
            "Use only the approved context below when it is relevant.\n\n"
            f"{context_block}\n\n"
            f"Question:\n{clean_prompt}"
        )
