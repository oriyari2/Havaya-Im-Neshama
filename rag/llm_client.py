from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
import json
import time
from typing import Any

import httpx

from backend.app.core.environment import (
    get_ollama_generation_timeout_seconds,
    get_ollama_keep_alive,
    get_ollama_num_predict,
    get_ollama_temperature,
    get_ollama_url,
)


class LLMClientError(RuntimeError):
    """Raised when the configured local LLM service cannot complete a request."""


class LLMClientTimeoutError(LLMClientError):
    """Raised when local generation exceeds the configured timeout."""


class LLMClientConnectionError(LLMClientError):
    """Raised when Ollama cannot be reached."""


class LLMClientHTTPError(LLMClientError):
    """Raised when Ollama returns an unsuccessful HTTP status."""


class LLMClientMalformedResponseError(LLMClientError):
    """Raised when Ollama returns JSON without the expected shape."""


OLLAMA_STREAM_CONNECT_TIMEOUT_SECONDS = 5.0
OLLAMA_STREAM_IDLE_TIMEOUT_SECONDS = 600.0
OLLAMA_STREAM_TOTAL_CAP_SECONDS = 900.0


@dataclass(frozen=True)
class LLMGeneration:
    text: str
    metadata: dict[str, Any]


class LLMClient(ABC):
    """Interface used by future RAG services to generate grounded responses."""

    @abstractmethod
    def generate(self, prompt: str, context: Sequence[str] | None = None) -> str:
        """Generate text from a prompt and optional retrieved context snippets."""


@dataclass(frozen=True)
class OllamaLLMClient(LLMClient):
    model: str
    base_url: str | None = None
    timeout_seconds: float | None = None
    keep_alive: str | None = None
    temperature: float | None = None
    num_predict: int | None = None

    def generate(self, prompt: str, context: Sequence[str] | None = None) -> str:
        return self.generate_with_metadata(prompt, context).text

    def generate_with_metadata(self, prompt: str, context: Sequence[str] | None = None) -> LLMGeneration:
        user_prompt = self._build_prompt(prompt=prompt, context=context)
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": user_prompt,
            "stream": False,
            "keep_alive": self.keep_alive or get_ollama_keep_alive(),
            "options": {
                "temperature": get_ollama_temperature() if self.temperature is None else self.temperature,
                "num_predict": get_ollama_num_predict() if self.num_predict is None else self.num_predict,
            },
        }

        try:
            response = httpx.post(
                f"{self._resolved_base_url()}/api/generate",
                json=payload,
                timeout=self.timeout_seconds or get_ollama_generation_timeout_seconds(),
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise LLMClientTimeoutError("Ollama generation timed out") from exc
        except httpx.ConnectError as exc:
            raise LLMClientConnectionError("Ollama connection failed") from exc
        except httpx.HTTPStatusError as exc:
            raise LLMClientHTTPError("Ollama returned an HTTP error") from exc
        except httpx.HTTPError as exc:
            raise LLMClientError("Ollama request failed") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise LLMClientMalformedResponseError("Ollama response was not valid JSON") from exc
        generated = data.get("response")
        if not isinstance(generated, str):
            raise LLMClientMalformedResponseError("Ollama response did not include generated text")
        return LLMGeneration(text=generated, metadata=data)

    def generate_stream_with_metadata(
        self,
        prompt: str,
        context: Sequence[str] | None = None,
        *,
        total_cap_seconds: float = OLLAMA_STREAM_TOTAL_CAP_SECONDS,
        clock=time.monotonic,
    ) -> LLMGeneration:
        user_prompt = self._build_prompt(prompt=prompt, context=context)
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": user_prompt,
            "stream": True,
            "keep_alive": self.keep_alive or get_ollama_keep_alive(),
            "options": {
                "temperature": get_ollama_temperature() if self.temperature is None else self.temperature,
                "num_predict": get_ollama_num_predict() if self.num_predict is None else self.num_predict,
            },
        }
        timeout = httpx.Timeout(
            OLLAMA_STREAM_IDLE_TIMEOUT_SECONDS,
            connect=OLLAMA_STREAM_CONNECT_TIMEOUT_SECONDS,
            read=OLLAMA_STREAM_IDLE_TIMEOUT_SECONDS,
        )
        started = clock()
        chunks: list[str] = []
        final_metadata: dict[str, Any] | None = None

        try:
            with httpx.stream(
                "POST",
                f"{self._resolved_base_url()}/api/generate",
                json=payload,
                timeout=timeout,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if clock() - started > total_cap_seconds:
                        raise LLMClientTimeoutError("Ollama stream exceeded the generation safety cap")
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except ValueError as exc:
                        raise LLMClientMalformedResponseError("Ollama stream included malformed JSON") from exc
                    generated = data.get("response")
                    if not isinstance(generated, str):
                        raise LLMClientMalformedResponseError("Ollama stream chunk did not include generated text")
                    chunks.append(generated)
                    if data.get("done") is True:
                        final_metadata = data
                        break
        except LLMClientError:
            raise
        except httpx.TimeoutException as exc:
            raise LLMClientTimeoutError("Ollama stream timed out") from exc
        except httpx.ConnectError as exc:
            raise LLMClientConnectionError("Ollama connection failed") from exc
        except httpx.HTTPStatusError as exc:
            raise LLMClientHTTPError("Ollama returned an HTTP error") from exc
        except httpx.TransportError as exc:
            raise LLMClientConnectionError("Ollama stream transport failed") from exc
        except httpx.HTTPError as exc:
            raise LLMClientError("Ollama stream request failed") from exc

        if final_metadata is None:
            raise LLMClientMalformedResponseError("Ollama stream ended before final metadata")
        return LLMGeneration(text="".join(chunks), metadata=final_metadata)

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
