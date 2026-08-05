"""
Deterministic mapper for Media Engine acquisition requests.

This module converts one Asset Planning record into one normalized media
request. It performs data shaping only and does not validate, route providers,
download, generate, read files, write files, log, or call external services.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Iterable

try:
    from media_constitution import (
        get_aspect_ratios,
        get_provider_priority,
        get_quality_targets,
    )
except ModuleNotFoundError:
    from scripts.media_engine.media_constitution import (
        get_aspect_ratios,
        get_provider_priority,
        get_quality_targets,
    )


DEFAULTS = MappingProxyType(
    {
        "candidate_limit": 5,
        "priority": "medium",
    }
)

SEARCH_ONLY_TYPES = frozenset(
    {
        "background",
        "object",
        "prop",
        "icon",
        "logo",
        "overlay",
    }
)

PROMPT_ONLY_TYPES = frozenset(
    {
        "poster",
        "illustration",
        "meme",
        "ui",
    }
)

SEARCH_AND_PROMPT_TYPES = frozenset({"character"})

REQUIRED_OUTPUT_FIELDS = (
    "request_id",
    "scene_id",
    "asset_id",
    "asset_type",
    "search_query",
    "generation_prompt",
    "preferred_style",
    "preferred_resolution",
    "preferred_aspect_ratio",
    "candidate_limit",
    "provider_preferences",
    "priority",
    "metadata",
)


def map_media_request(asset_record: dict[str, Any]) -> dict[str, Any]:
    """
    Map one Asset Planning record into one normalized Media Request.

    Arguments:
        asset_record: Asset Planning output dictionary.

    Returns:
        Normalized Media Request dictionary.
    """
    record = _safe_mapping(asset_record)
    asset_type = _safe_text(record.get("asset_type")) or "object"
    scene_id = _safe_text(record.get("scene_id")) or "scene_unknown"
    asset_id = _safe_text(record.get("asset_id")) or _build_asset_id(
        scene_id,
        asset_type,
    )
    description = _safe_text(record.get("description"))
    visual_style = _safe_text(record.get("visual_style"))
    tags = _safe_tags(record.get("tags"))
    resolution = _preferred_resolution(record)

    return {
        "request_id": _build_request_id(scene_id, asset_id),
        "scene_id": scene_id,
        "asset_id": asset_id,
        "asset_type": asset_type,
        "search_query": _build_search_query(
            asset_type,
            description,
            visual_style,
            tags,
        ),
        "generation_prompt": _build_generation_prompt(
            asset_type,
            description,
            visual_style,
            tags,
        ),
        "preferred_style": visual_style or "default",
        "preferred_resolution": resolution,
        "preferred_aspect_ratio": _preferred_aspect_ratio(record, resolution),
        "candidate_limit": _safe_int(
            record.get("candidate_limit"),
            int(DEFAULTS["candidate_limit"]),
        ),
        "provider_preferences": get_provider_priority(),
        "priority": _safe_text(record.get("priority")) or DEFAULTS["priority"],
        "metadata": _build_metadata(record),
    }


def map_batch(asset_records: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    """
    Map multiple Asset Planning records into normalized Media Requests.

    Arguments:
        asset_records: Iterable of Asset Planning output dictionaries.

    Returns:
        Tuple of normalized Media Request dictionaries.
    """
    return tuple(map_media_request(record) for record in asset_records)


def _build_search_query(
    asset_type: str,
    description: str,
    visual_style: str,
    tags: tuple[str, ...],
) -> str:
    """Build concise provider-neutral search text when search is useful."""
    normalized_type = asset_type.lower()
    if normalized_type not in SEARCH_ONLY_TYPES | SEARCH_AND_PROMPT_TYPES:
        return ""

    parts = _dedupe_text_parts((visual_style, description, *tags))
    if parts:
        return " ".join(parts)
    return asset_type.replace("_", " ")


def _build_generation_prompt(
    asset_type: str,
    description: str,
    visual_style: str,
    tags: tuple[str, ...],
) -> str:
    """Build provider-neutral generation prompt when generation is useful."""
    normalized_type = asset_type.lower()
    if normalized_type not in PROMPT_ONLY_TYPES | SEARCH_AND_PROMPT_TYPES:
        return ""

    prompt_subject = description or asset_type.replace("_", " ")
    prompt_parts = _dedupe_text_parts((prompt_subject, visual_style, *tags))
    return ", ".join(prompt_parts)


def _preferred_resolution(record: dict[str, Any]) -> tuple[int, int]:
    """Return record resolution when present, otherwise constitution default."""
    dimensions = record.get("dimensions")
    if isinstance(dimensions, dict):
        width = _safe_int(dimensions.get("width"), 0)
        height = _safe_int(dimensions.get("height"), 0)
        if width > 0 and height > 0:
            return (width, height)

    if isinstance(dimensions, (tuple, list)) and len(dimensions) >= 2:
        width = _safe_int(dimensions[0], 0)
        height = _safe_int(dimensions[1], 0)
        if width > 0 and height > 0:
            return (width, height)

    quality_targets = get_quality_targets()
    preferred = quality_targets.get("preferred_resolution")
    if isinstance(preferred, tuple) and len(preferred) == 2:
        return preferred
    return (1080, 1920)


def _preferred_aspect_ratio(
    record: dict[str, Any],
    resolution: tuple[int, int],
) -> str:
    """Return preferred aspect ratio from record or constitution defaults."""
    aspect_ratio = _safe_text(record.get("aspect_ratio"))
    if aspect_ratio:
        return aspect_ratio

    width, height = resolution
    if width == height:
        return get_aspect_ratios().get("square", "1:1")
    if width > height:
        return get_aspect_ratios().get("landscape", "16:9")
    return get_quality_targets().get("preferred_aspect_ratio", "9:16")


def _build_metadata(record: dict[str, Any]) -> dict[str, Any]:
    """Preserve existing metadata and add deterministic mapper context."""
    metadata = _safe_mapping(record.get("metadata"))
    return {
        **metadata,
        "mapper": "media_mapper",
        "source_priority": _safe_text(record.get("priority")) or DEFAULTS["priority"],
    }


def _build_request_id(scene_id: str, asset_id: str) -> str:
    """Build deterministic request id from scene and asset identifiers."""
    return f"media_request_{_slug(scene_id)}_{_slug(asset_id)}"


def _build_asset_id(scene_id: str, asset_type: str) -> str:
    """Build deterministic fallback asset id."""
    return f"asset_{_slug(scene_id)}_{_slug(asset_type)}"


def _safe_mapping(value: Any) -> dict[str, Any]:
    """Return a shallow dictionary copy for mapping inputs."""
    if isinstance(value, dict):
        return dict(value)
    return {}


def _safe_tags(value: Any) -> tuple[str, ...]:
    """Return clean tag strings."""
    if not isinstance(value, (tuple, list)):
        return ()
    return tuple(filter(None, (_safe_text(item) for item in value)))


def _safe_text(value: Any) -> str:
    """Return stripped text for scalar values."""
    if value is None:
        return ""
    return str(value).strip()


def _safe_int(value: Any, default: int) -> int:
    """Return integer value when possible, otherwise default."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _dedupe_text_parts(parts: Iterable[str]) -> tuple[str, ...]:
    """Return non-empty text parts with deterministic case-insensitive dedupe."""
    seen: set[str] = set()
    clean_parts: list[str] = []
    for part in parts:
        clean = _safe_text(part)
        key = clean.casefold()
        if clean and key not in seen:
            clean_parts.append(clean)
            seen.add(key)
    return tuple(clean_parts)


def _slug(value: str) -> str:
    """Return stable identifier-safe text."""
    clean = _safe_text(value).lower()
    chars = [char if char.isalnum() else "_" for char in clean]
    slug = "_".join(filter(None, "".join(chars).split("_")))
    return slug or "unknown"


def _has_required_fields(request: dict[str, Any]) -> bool:
    """Return whether request has every required output field."""
    return all(field in request for field in REQUIRED_OUTPUT_FIELDS)


def _self_test() -> bool:
    """Verify deterministic single and batch mapping behavior."""
    sample = {
        "scene_id": "scene_001",
        "asset_id": "asset_001",
        "asset_type": "character",
        "description": "curious robotics engineer in a lab",
        "visual_style": "modern futuristic",
        "tags": ["AI", "laboratory"],
        "metadata": {"source": "asset_planning"},
    }
    mapped = map_media_request(sample)
    batch = map_batch((sample, {"asset_type": "poster"}))

    checks = (
        isinstance(mapped, dict),
        isinstance(batch, tuple) and len(batch) == 2,
        _has_required_fields(mapped),
        bool(mapped["provider_preferences"]),
        isinstance(mapped["preferred_resolution"], tuple),
        bool(mapped["preferred_aspect_ratio"]),
        bool(mapped["search_query"]),
        bool(mapped["generation_prompt"]),
    )
    return all(checks)


if __name__ == "__main__":
    print("PASS" if _self_test() else "FAIL")
