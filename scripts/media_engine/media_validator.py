"""
Validation-only module for Media Acquisition Requests.

This module checks the structure and constitution alignment of normalized media
requests before they reach provider routing. It performs no provider selection,
file access, networking, downloading, generation, logging, or routing.
"""

from __future__ import annotations

from typing import Any, Iterable

try:
    from media_constitution import (
        get_aspect_ratios,
        get_asset_categories,
        get_provider_priority,
        get_supported_resolutions,
    )
except ModuleNotFoundError:
    from scripts.media_engine.media_constitution import (
        get_aspect_ratios,
        get_asset_categories,
        get_provider_priority,
        get_supported_resolutions,
    )


REQUIRED_FIELDS = (
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

OPTIONAL_FIELDS = frozenset(REQUIRED_FIELDS)

AI_CAPABLE_ASSET_TYPES = frozenset(
    {
        "character",
        "illustration",
        "poster",
        "meme",
        "ui",
    }
)

ALLOWED_PRIORITIES = frozenset(
    {
        "low",
        "medium",
        "high",
        "critical",
    }
)

VERY_SHORT_QUERY_LENGTH = 3
VERY_LONG_QUERY_LENGTH = 120


def validate_media_request(request: dict[str, Any]) -> dict[str, Any]:
    """
    Validate one normalized Media Acquisition Request.

    Arguments:
        request: normalized media request dictionary.

    Returns:
        Structured validation result with valid, errors, and warnings fields.
    """
    errors: list[str] = []
    warnings: list[str] = []

    try:
        record = _safe_mapping(request)
        if not record:
            errors.append("request must be a non-empty dictionary")
            return _result(errors, warnings)

        _validate_required_fields(record, errors)
        _validate_asset_type(record, errors)
        _validate_resolution(record, errors)
        _validate_aspect_ratio(record, errors)
        _validate_provider_preferences(record, errors)
        _validate_candidate_limit(record, errors)
        _validate_priority(record, errors)
        _validate_search_query(record, errors, warnings)
        _validate_generation_prompt(record, errors)
        _validate_metadata(record, errors, warnings)
        _warn_unknown_fields(record, warnings)
    except Exception as exc:
        errors.append(f"unexpected validation error: {exc}")

    return _result(errors, warnings)


def validate_batch(requests: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    """
    Validate multiple normalized Media Acquisition Requests.

    Arguments:
        requests: iterable of normalized media request dictionaries.

    Returns:
        Tuple of structured validation results.
    """
    try:
        return tuple(validate_media_request(request) for request in requests)
    except Exception as exc:
        return (
            {
                "valid": False,
                "errors": [f"unexpected batch validation error: {exc}"],
                "warnings": [],
            },
        )


def _validate_required_fields(record: dict[str, Any], errors: list[str]) -> None:
    """Validate required fields exist and identifiers are populated."""
    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"missing required field: {field}")

    for field in ("request_id", "scene_id", "asset_id", "asset_type"):
        if field in record and not _safe_text(record.get(field)):
            errors.append(f"{field} must be populated")


def _validate_asset_type(record: dict[str, Any], errors: list[str]) -> None:
    """Validate asset type is allowed by the constitution."""
    asset_type = _safe_text(record.get("asset_type"))
    if asset_type and asset_type not in get_asset_categories():
        errors.append(f"unsupported asset_type: {asset_type}")


def _validate_resolution(record: dict[str, Any], errors: list[str]) -> None:
    """Validate preferred resolution is constitution-supported."""
    resolution = _resolution_tuple(record.get("preferred_resolution"))
    supported = {
        resolution
        for group in get_supported_resolutions().values()
        for resolution in group
    }
    if resolution is None:
        errors.append("preferred_resolution must be a width-height pair")
    elif resolution not in supported:
        errors.append(f"unsupported preferred_resolution: {resolution}")


def _validate_aspect_ratio(record: dict[str, Any], errors: list[str]) -> None:
    """Validate preferred aspect ratio is constitution-supported."""
    aspect_ratio = _safe_text(record.get("preferred_aspect_ratio"))
    if aspect_ratio and aspect_ratio not in set(get_aspect_ratios().values()):
        errors.append(f"unsupported preferred_aspect_ratio: {aspect_ratio}")
    elif not aspect_ratio:
        errors.append("preferred_aspect_ratio must be populated")


def _validate_provider_preferences(
    record: dict[str, Any],
    errors: list[str],
) -> None:
    """Validate provider preferences preserve constitution priority order."""
    preferences = record.get("provider_preferences")
    constitution_order = get_provider_priority()

    if not isinstance(preferences, (tuple, list)) or not preferences:
        errors.append("provider_preferences must be a non-empty sequence")
        return

    preference_tuple = tuple(preferences)
    if preference_tuple != constitution_order[: len(preference_tuple)]:
        errors.append("provider_preferences must preserve constitution order")


def _validate_candidate_limit(record: dict[str, Any], errors: list[str]) -> None:
    """Validate candidate limit is positive."""
    candidate_limit = record.get("candidate_limit")
    if not isinstance(candidate_limit, int) or candidate_limit <= 0:
        errors.append("candidate_limit must be greater than 0")


def _validate_priority(record: dict[str, Any], errors: list[str]) -> None:
    """Validate priority is in the allowed range."""
    priority = _safe_text(record.get("priority"))
    if priority not in ALLOWED_PRIORITIES:
        errors.append(f"unsupported priority: {priority}")


def _validate_search_query(
    record: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    """Validate search query exists and warn on suspicious length."""
    search_query = _safe_text(record.get("search_query"))
    if not search_query:
        errors.append("search_query must be populated")
        return

    if len(search_query) <= VERY_SHORT_QUERY_LENGTH:
        warnings.append("search_query is very short")
    elif len(search_query) > VERY_LONG_QUERY_LENGTH:
        warnings.append("search_query is very long")


def _validate_generation_prompt(
    record: dict[str, Any],
    errors: list[str],
) -> None:
    """Validate AI-capable asset types include generation prompts."""
    asset_type = _safe_text(record.get("asset_type"))
    generation_prompt = _safe_text(record.get("generation_prompt"))
    if asset_type in AI_CAPABLE_ASSET_TYPES and not generation_prompt:
        errors.append("generation_prompt must be populated for AI-capable asset types")


def _validate_metadata(
    record: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    """Validate metadata is a dictionary and warn when empty."""
    metadata = record.get("metadata")
    if not isinstance(metadata, dict):
        errors.append("metadata must be a dictionary")
    elif not metadata:
        warnings.append("metadata is empty")


def _warn_unknown_fields(record: dict[str, Any], warnings: list[str]) -> None:
    """Warn when request includes fields outside the expected contract."""
    unknown_fields = tuple(field for field in record if field not in OPTIONAL_FIELDS)
    if unknown_fields:
        warnings.append(f"unknown optional fields: {', '.join(unknown_fields)}")


def _safe_mapping(value: Any) -> dict[str, Any]:
    """Return a shallow dictionary copy for validation."""
    if isinstance(value, dict):
        return dict(value)
    return {}


def _safe_text(value: Any) -> str:
    """Return stripped text for scalar values."""
    if value is None:
        return ""
    return str(value).strip()


def _resolution_tuple(value: Any) -> tuple[int, int] | None:
    """Normalize a resolution value into a width-height tuple."""
    if isinstance(value, dict):
        width = value.get("width")
        height = value.get("height")
        return _int_pair(width, height)

    if isinstance(value, (tuple, list)) and len(value) >= 2:
        return _int_pair(value[0], value[1])

    return None


def _int_pair(first: Any, second: Any) -> tuple[int, int] | None:
    """Return a positive integer pair when possible."""
    try:
        first_int = int(first)
        second_int = int(second)
    except (TypeError, ValueError):
        return None

    if first_int <= 0 or second_int <= 0:
        return None
    return (first_int, second_int)


def _result(errors: list[str], warnings: list[str]) -> dict[str, Any]:
    """Build a structured validation result."""
    return {
        "valid": not errors,
        "errors": tuple(errors),
        "warnings": tuple(warnings),
    }


def _valid_request() -> dict[str, Any]:
    """Build a valid request sample for self-test."""
    return {
        "request_id": "media_request_scene_001_asset_001",
        "scene_id": "scene_001",
        "asset_id": "asset_001",
        "asset_type": "character",
        "search_query": "modern futuristic AI laboratory engineer",
        "generation_prompt": "curious robotics engineer in a laboratory",
        "preferred_style": "modern futuristic",
        "preferred_resolution": (1080, 1920),
        "preferred_aspect_ratio": "9:16",
        "candidate_limit": 5,
        "provider_preferences": get_provider_priority(),
        "priority": "medium",
        "metadata": {"source": "media_mapper"},
    }


def _self_test() -> bool:
    """Verify validation success, failure cases, and batch validation."""
    valid_request = _valid_request()
    missing_asset = {**valid_request, "asset_id": ""}
    invalid_type = {**valid_request, "asset_type": "unsupported"}
    invalid_resolution = {**valid_request, "preferred_resolution": (123, 456)}
    invalid_aspect = {**valid_request, "preferred_aspect_ratio": "4:3"}
    empty_providers = {**valid_request, "provider_preferences": ()}

    checks = (
        validate_media_request(valid_request)["valid"] is True,
        validate_media_request(missing_asset)["valid"] is False,
        validate_media_request(invalid_type)["valid"] is False,
        validate_media_request(invalid_resolution)["valid"] is False,
        validate_media_request(invalid_aspect)["valid"] is False,
        validate_media_request(empty_providers)["valid"] is False,
        len(validate_batch((valid_request, invalid_type))) == 2,
    )
    return all(checks)


if __name__ == "__main__":
    print("PASS" if _self_test() else "FAIL")
