from __future__ import annotations

import logging
from typing import Any

import httpx

from backend.app.core.environment import (
    get_ollama_embedding_model,
    get_ollama_keep_alive,
    get_ollama_model,
    get_ollama_startup_timeout_seconds,
    get_ollama_url,
)
from backend.app.db.connection import get_connection_pool


logger = logging.getLogger(__name__)


def _startup_timeout() -> httpx.Timeout:
    return httpx.Timeout(get_ollama_startup_timeout_seconds(), connect=2.0)


def warm_generation_model() -> None:
    payload = {
        "model": get_ollama_model(),
        "prompt": "",
        "stream": False,
        "keep_alive": get_ollama_keep_alive(),
    }
    try:
        response = httpx.post(
            f"{get_ollama_url()}/api/generate",
            json=payload,
            timeout=_startup_timeout(),
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("Ollama generation model warm-up failed: %s", type(exc).__name__)


def ai_readiness() -> dict[str, Any]:
    ollama = _ollama_status()
    return {
        "api": "ok",
        "database_pool": _database_pool_status(),
        "ollama_reachable": ollama["reachable"],
        "generation_model_available": _model_present(get_ollama_model(), ollama["models"]),
        "embedding_model_available": _model_present(get_ollama_embedding_model(), ollama["models"]),
        "generation_model_warm": _model_present(get_ollama_model(), ollama["running_models"]),
    }


def _database_pool_status() -> str:
    try:
        get_connection_pool().get_stats()
    except Exception:
        return "unavailable"
    return "ok"


def _ollama_status() -> dict[str, Any]:
    status: dict[str, Any] = {"reachable": False, "models": set(), "running_models": set()}
    try:
        with httpx.Client(base_url=get_ollama_url(), timeout=_startup_timeout()) as client:
            tags = client.get("/api/tags")
            tags.raise_for_status()
            status["reachable"] = True
            status["models"] = _model_names(tags.json())
            try:
                ps = client.get("/api/ps")
                ps.raise_for_status()
                status["running_models"] = _model_names(ps.json())
            except httpx.HTTPError:
                pass
    except httpx.HTTPError:
        pass
    return status


def _model_names(payload: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for item in payload.get("models", []):
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            names.add(item["name"])
            names.add(item["name"].split(":", 1)[0])
    return names


def _model_present(model: str, names: set[str]) -> bool:
    return model in names or model.split(":", 1)[0] in names
