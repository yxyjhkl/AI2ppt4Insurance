"""Server-side secure API key store (never logged, never sent to frontend)."""
from __future__ import annotations

_api_key_store: dict[str, dict[str, str]] = {}


def set_api_key(model_id: str, api_key: str, base_url: str | None = None):
    _api_key_store[model_id] = {"api_key": api_key, "base_url": base_url or ""}


def get_api_key(model_id: str) -> dict[str, str]:
    return _api_key_store.get(model_id, {"api_key": "", "base_url": ""})
