from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import httpx

from backend.app.core.environment import get_ollama_url


class EmbeddingClientError(RuntimeError):
    """Raised when the configured embedding service cannot complete a request."""


class EmbeddingClient(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Return a vector embedding for a single text snippet."""


@dataclass(frozen=True)
class OllamaEmbeddingClient(EmbeddingClient):
    model: str
    base_url: str | None = None
    timeout_seconds: float = 120.0

    def embed(self, text: str) -> list[float]:
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("text must not be empty")

        payload: dict[str, Any] = {"model": self.model, "input": clean_text}
        try:
            response = httpx.post(
                f"{self._resolved_base_url()}/api/embed",
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise EmbeddingClientError("Ollama embedding request failed") from exc

        data = response.json()
        embeddings = data.get("embeddings")
        if not isinstance(embeddings, list) or not embeddings:
            raise EmbeddingClientError("Ollama response did not include embeddings")

        embedding = embeddings[0]
        if not embedding or not _is_numeric_sequence(embedding):
            raise EmbeddingClientError("Ollama response did not include a numeric embedding")
        return [float(value) for value in embedding]

    def _resolved_base_url(self) -> str:
        return (self.base_url or get_ollama_url()).rstrip("/")


def _is_numeric_sequence(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and all(
        isinstance(item, int | float) for item in value
    )
