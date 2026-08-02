from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import httpx

from backend.app.core.environment import get_ollama_url


class EmbeddingClientError(RuntimeError):
    """Raised when the configured embedding service cannot complete a request."""


class EmbeddingClientTimeoutError(EmbeddingClientError):
    """Raised when embedding generation exceeds the configured timeout."""


class EmbeddingClientConnectionError(EmbeddingClientError):
    """Raised when Ollama cannot be reached for embeddings."""


class EmbeddingClientHTTPError(EmbeddingClientError):
    """Raised when Ollama returns an unsuccessful HTTP status for embeddings."""


class EmbeddingClientMalformedResponseError(EmbeddingClientError):
    """Raised when Ollama returns JSON without the expected embedding shape."""


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
        except httpx.TimeoutException as exc:
            raise EmbeddingClientTimeoutError("Ollama embedding request timed out") from exc
        except httpx.ConnectError as exc:
            raise EmbeddingClientConnectionError("Ollama embedding connection failed") from exc
        except httpx.HTTPStatusError as exc:
            raise EmbeddingClientHTTPError("Ollama embedding returned an HTTP error") from exc
        except httpx.HTTPError as exc:
            raise EmbeddingClientError("Ollama embedding request failed") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise EmbeddingClientMalformedResponseError("Ollama embedding response was not valid JSON") from exc
        embeddings = data.get("embeddings")
        if not isinstance(embeddings, list) or not embeddings:
            raise EmbeddingClientMalformedResponseError("Ollama response did not include embeddings")

        embedding = embeddings[0]
        if not embedding or not _is_numeric_sequence(embedding):
            raise EmbeddingClientMalformedResponseError("Ollama response did not include a numeric embedding")
        return [float(value) for value in embedding]

    def _resolved_base_url(self) -> str:
        return (self.base_url or get_ollama_url()).rstrip("/")


def _is_numeric_sequence(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and all(
        isinstance(item, int | float) for item in value
    )
