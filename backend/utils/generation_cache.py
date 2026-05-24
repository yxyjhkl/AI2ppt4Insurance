"""Generation cache — avoids repeated API calls for identical inputs."""
from __future__ import annotations
import hashlib
import json
import os
import time
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

CACHE_DIR = Path.home() / ".insurdeck" / "cache"
MAX_CACHE_ENTRIES = 50
MAX_CACHE_AGE_SECONDS = 24 * 3600  # 24 hours


def _ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_key(input_text: str, scene: str, template_id: str, model: str) -> str:
    """Generate a deterministic cache key from input parameters."""
    data = f"{input_text[:500]}|{scene}|{template_id}|{model}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def get_cached_result(input_text: str, scene: str, template_id: str, model: str) -> Optional[dict]:
    """Retrieve cached generation result if available and not expired."""
    _ensure_cache_dir()
    key = _cache_key(input_text, scene, template_id, model)
    cache_file = CACHE_DIR / f"{key}.json"

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        age = time.time() - data.get("timestamp", 0)
        if age > MAX_CACHE_AGE_SECONDS:
            cache_file.unlink(missing_ok=True)
            return None
        logger.info(f"Cache hit: {key} (age: {age:.0f}s)")
        return data.get("result")
    except Exception:
        cache_file.unlink(missing_ok=True)
        return None


def set_cached_result(input_text: str, scene: str, template_id: str, model: str, result: dict):
    """Store a generation result in the cache."""
    _ensure_cache_dir()
    key = _cache_key(input_text, scene, template_id, model)
    cache_file = CACHE_DIR / f"{key}.json"

    # Prune old entries if needed
    try:
        entries = sorted(CACHE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
        while len(entries) >= MAX_CACHE_ENTRIES:
            entries.pop(0).unlink(missing_ok=True)
    except Exception:
        pass

    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"timestamp": time.time(), "result": result}, f, ensure_ascii=False)
        logger.info(f"Cache stored: {key}")
    except Exception as e:
        logger.debug(f"Failed to write cache: {e}")


def clear_cache():
    """Clear all cached results."""
    _ensure_cache_dir()
    for f in CACHE_DIR.glob("*.json"):
        f.unlink(missing_ok=True)
    logger.info("Cache cleared")
