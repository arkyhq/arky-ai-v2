"""
Purpose:
Provide reusable JSON cache helpers.

Input:
cache paths and JSON-serializable data

Output:
cached data or graceful fallback values
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


def save_cache(cache_path: Path, data: Any) -> bool:
    """
    Purpose:
    Save JSON-serializable data to a cache file.

    Arguments:
    cache_path: target cache file path
    data: JSON-serializable cache payload

    Returns:
    True when saved successfully, otherwise False
    """
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "cached_at": time.time(),
            "data": data,
        }

        with cache_path.open("w", encoding="utf-8") as cache_file:
            json.dump(payload, cache_file, indent=4, ensure_ascii=False)

        return True
    except Exception as exc:
        logger.warning("Cache save failed for %s: %s", cache_path, exc)
        return False


def load_cache(cache_path: Path, default: Any = None) -> dict[str, Any] | Any:
    """
    Purpose:
    Load a JSON cache payload.

    Arguments:
    cache_path: cache file path
    default: fallback value

    Returns:
    cache payload or fallback value
    """
    try:
        if not cache_path.exists():
            return default

        with cache_path.open("r", encoding="utf-8") as cache_file:
            return json.load(cache_file)
    except Exception as exc:
        logger.warning("Cache load failed for %s: %s", cache_path, exc)
        return default


def is_cache_valid(cache_path: Path, expiration_seconds: int) -> bool:
    """
    Purpose:
    Check whether a cache file exists and is unexpired.

    Arguments:
    cache_path: cache file path
    expiration_seconds: cache lifetime in seconds

    Returns:
    True when cache can be used, otherwise False
    """
    payload = load_cache(cache_path, default=None)

    if not isinstance(payload, dict):
        return False

    cached_at = payload.get("cached_at")

    if not isinstance(cached_at, int | float):
        return False

    return (time.time() - float(cached_at)) <= expiration_seconds


def get_cached_data(cache_path: Path, expiration_seconds: int, default: Any = None) -> Any:
    """
    Purpose:
    Return cached data when available and valid.

    Arguments:
    cache_path: cache file path
    expiration_seconds: cache lifetime in seconds
    default: fallback value

    Returns:
    cached data or fallback value
    """
    if not is_cache_valid(cache_path, expiration_seconds):
        return default

    payload = load_cache(cache_path, default=None)

    if not isinstance(payload, dict) or "data" not in payload:
        return default

    return payload["data"]


def get_stale_cached_data(cache_path: Path, default: Any = None) -> Any:
    """
    Purpose:
    Return cached data regardless of expiration.

    Arguments:
    cache_path: cache file path
    default: fallback value

    Returns:
    cached data or fallback value
    """
    payload = load_cache(cache_path, default=None)

    if not isinstance(payload, dict) or "data" not in payload:
        return default

    return payload["data"]
