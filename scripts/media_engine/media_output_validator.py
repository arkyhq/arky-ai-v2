"""
Validation-only module for Media Acquisition Results.

This module validates provider routing outputs before downstream engine use. It
does not perform networking, filesystem checks, downloads, AI generation,
routing, provider logic, logging, or asset-library updates.
"""

from __future__ import annotations

from typing import Any, Iterable

try:
    from media_constitution import (
        get_asset_categories,
        get_confidence_ranges,
        get_provider_priority,
    )
except ModuleNotFoundError:
    from scripts.media_engine.media_constitution import (
        get_asset_categories,
        get_confidence_ranges,
        get_provider_priority,
    )


REQUIRED_FIELDS = (
    "success",
    "status",
    "provider",
    "provider_type",
    "asset",
    "errors",
    "warnings",
    "metadata",
)

REQUIRED_ASSET_FIELDS = (
    "asset_id",
    "asset_type",
    "confidence",
    "local_path",
)

OPTIONAL_FIELDS = frozenset(REQUIRED_FIELDS)

OPTIONAL_ASSET_FIELDS = frozenset(
    {
        "asset_id",
        "asset_type",
        "provider",
        "provider_type",
        "source",
        "license",
        "confidence",
        "width",
        "height",
        "file_format",
        "local_path",
        "metadata_path",
        "status",
        "download_url",
        "preview_url",
        "prompt",
        "negative_prompt",
        "seed",
        "image_url",
        "hash",
    }
)

VALID_STATUSES = frozenset({"success", "warning", "failed"})
VALID_PROVIDER_TYPES = frozenset({"local", "stock", "ai", "open_repository"})
LOW_CONFIDENCE_THRESHOLD = 75


def validate_media_output(output: dict[str, Any]) -> dict[str, Any]:
    """
    Validate one Media Acquisition Result.

    Arguments:
        output: provider routing output dictionary.

    Returns:
        Structured validation result with normalized output copy.
    """
    errors: list[str] = []
    warnings: list[str] = []
    normalized: dict[str, Any] = {}

    try:
        record = _safe_mapping(output)
        normalized = _normalize_output(record)

        if not record:
            errors.append("output must be a non-empty dictionary")
            return _result(errors, warnings, normalized)

        _validate_required_fields(record, errors)
        _validate_success(record, errors)
        _validate_status(record, errors)
        _validate_provider(record, errors)
        _validate_provider_type(record, errors)
        _validate_errors_and_warnings(record, errors)
        _validate_metadata(record, errors, warnings)
        _validate_asset(record, errors, warnings)
        _validate_consistency(record, errors)
        _warn_unknown_fields(record, warnings)
    except Exception as exc:
        errors.append(f"unexpected output validation error: {exc}")

    return _result(errors, warnings, normalized)


def validate_batch(outputs: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    """
    Validate multiple Media Acquisition Results.

    Arguments:
        outputs: iterable of provider routing output dictionaries.

    Returns:
        Tuple of structured validation results.
    """
    try:
        return tuple(validate_media_output(output) for output in outputs)
    except Exception as exc:
        return (
            {
                "valid": False,
                "errors": (f"unexpected batch validation error: {exc}",),
                "warnings": (),
                "normalized": {},
            },
        )


def _validate_required_fields(record: dict[str, Any], errors: list[str]) -> None:
    """Validate top-level required fields exist."""
    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"missing required field: {field}")


def _validate_success(record: dict[str, Any], errors: list[str]) -> None:
    """Validate success is boolean."""
    if not isinstance(record.get("success"), bool):
        errors.append("success must be boolean")


def _validate_status(record: dict[str, Any], errors: list[str]) -> None:
    """Validate status exists and is allowed."""
    status = _safe_text(record.get("status"))
    if not status:
        errors.append("status must be populated")
    elif status not in VALID_STATUSES:
        errors.append(f"unsupported status: {status}")


def _validate_provider(record: dict[str, Any], errors: list[str]) -> None:
    """Validate provider exists and belongs to the constitution."""
    provider = _safe_text(record.get("provider"))
    if not provider:
        errors.append("provider must be populated")
        return

    constitution_ids = {_provider_key(item) for item in get_provider_priority()}
    if _provider_key(provider) not in constitution_ids:
        errors.append(f"unsupported provider: {provider}")


def _validate_provider_type(record: dict[str, Any], errors: list[str]) -> None:
    """Validate provider type."""
    provider_type = _safe_text(record.get("provider_type"))
    if provider_type not in VALID_PROVIDER_TYPES:
        errors.append(f"unsupported provider_type: {provider_type}")


def _validate_errors_and_warnings(
    record: dict[str, Any],
    errors: list[str],
) -> None:
    """Validate errors and warnings are lists."""
    if not isinstance(record.get("errors"), list):
        errors.append("errors must be list")
    if not isinstance(record.get("warnings"), list):
        errors.append("warnings must be list")


def _validate_metadata(
    record: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    """Validate metadata exists and warn when empty."""
    metadata = record.get("metadata")
    if not isinstance(metadata, dict):
        errors.append("metadata must be dictionary")
    elif not metadata:
        warnings.append("metadata is empty")


def _validate_asset(
    record: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    """Validate asset payload and asset-level consistency."""
    asset = record.get("asset")
    if not isinstance(asset, dict):
        errors.append("asset must be dictionary")
        return

    if record.get("success") is True and not asset:
        errors.append("asset is required when success is true")
        return

    if not asset:
        return

    for field in REQUIRED_ASSET_FIELDS:
        if field not in asset:
            errors.append(f"missing asset field: {field}")

    asset_id = _safe_text(asset.get("asset_id"))
    if not asset_id:
        errors.append("asset_id must be populated")

    asset_type = _safe_text(asset.get("asset_type"))
    if not asset_type:
        errors.append("asset_type must be populated")
    elif asset_type not in get_asset_categories():
        errors.append(f"unsupported asset_type: {asset_type}")

    confidence = _confidence_value(asset.get("confidence"))
    if confidence is None:
        errors.append("confidence must be numeric")
    elif not _confidence_in_constitution_range(confidence):
        errors.append(f"confidence out of constitution range: {confidence}")
    elif confidence < LOW_CONFIDENCE_THRESHOLD:
        warnings.append("low confidence")

    if "local_path" not in asset:
        errors.append("local_path field must exist")

    _warn_unknown_asset_fields(asset, warnings)


def _validate_consistency(record: dict[str, Any], errors: list[str]) -> None:
    """Validate success/failure internal consistency."""
    success = record.get("success")
    output_errors = record.get("errors")
    asset = record.get("asset")
    provider = _safe_text(record.get("provider"))

    if success is True:
        if isinstance(output_errors, list) and output_errors:
            errors.append("errors must be empty when success is true")
        if not isinstance(asset, dict) or not asset:
            errors.append("asset required when success is true")
        if not provider:
            errors.append("provider required when success is true")

    if success is False and isinstance(output_errors, list) and not output_errors:
        errors.append("errors required when success is false")


def _warn_unknown_fields(record: dict[str, Any], warnings: list[str]) -> None:
    """Warn for unknown top-level optional keys."""
    unknown_fields = tuple(field for field in record if field not in OPTIONAL_FIELDS)
    if unknown_fields:
        warnings.append(f"unknown optional keys: {', '.join(unknown_fields)}")


def _warn_unknown_asset_fields(asset: dict[str, Any], warnings: list[str]) -> None:
    """Warn for unknown asset optional keys."""
    unknown_fields = tuple(field for field in asset if field not in OPTIONAL_ASSET_FIELDS)
    if unknown_fields:
        warnings.append(f"unknown asset optional keys: {', '.join(unknown_fields)}")


def _normalize_output(record: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow normalized output copy."""
    normalized = dict(record)
    if isinstance(normalized.get("asset"), dict):
        normalized["asset"] = dict(normalized["asset"])
    if isinstance(normalized.get("metadata"), dict):
        normalized["metadata"] = dict(normalized["metadata"])
    return normalized


def _confidence_value(value: Any) -> int | float | None:
    """Return numeric confidence when possible."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return value
    return None


def _confidence_in_constitution_range(confidence: int | float) -> bool:
    """Return whether confidence falls within any constitution confidence range."""
    return any(
        low <= confidence <= high
        for low, high in get_confidence_ranges().values()
    )


def _provider_key(value: str) -> str:
    """Normalize provider names for constitution membership checks."""
    return _safe_text(value).casefold().replace(" ", "_")


def _safe_mapping(value: Any) -> dict[str, Any]:
    """Return a shallow dictionary copy when possible."""
    if isinstance(value, dict):
        return dict(value)
    return {}


def _safe_text(value: Any) -> str:
    """Return stripped text for scalar values."""
    if value is None:
        return ""
    return str(value).strip()


def _result(
    errors: list[str],
    warnings: list[str],
    normalized: dict[str, Any],
) -> dict[str, Any]:
    """Build a structured validation result."""
    return {
        "valid": not errors,
        "errors": tuple(errors),
        "warnings": tuple(warnings),
        "normalized": normalized,
    }


def _valid_output() -> dict[str, Any]:
    """Build a valid output sample for self-test."""
    return {
        "success": True,
        "status": "success",
        "provider": "Pexels",
        "provider_type": "stock",
        "asset": {
            "asset_id": "asset_001",
            "asset_type": "background",
            "confidence": 92,
            "local_path": "",
        },
        "errors": [],
        "warnings": [],
        "metadata": {"request_id": "media_request_001"},
    }


def _self_test() -> bool:
    """Verify output validation success, failure cases, and batch behavior."""
    valid_output = _valid_output()
    invalid_provider = {**valid_output, "provider": "Unknown Provider"}
    invalid_type = {
        **valid_output,
        "asset": {**valid_output["asset"], "asset_type": "unsupported"},
    }
    missing_asset_id = {
        **valid_output,
        "asset": {**valid_output["asset"], "asset_id": ""},
    }
    failed_without_errors = {
        **valid_output,
        "success": False,
        "status": "failed",
        "asset": {},
        "errors": [],
    }

    checks = (
        validate_media_output(valid_output)["valid"] is True,
        validate_media_output(invalid_provider)["valid"] is False,
        validate_media_output(invalid_type)["valid"] is False,
        validate_media_output(missing_asset_id)["valid"] is False,
        validate_media_output(failed_without_errors)["valid"] is False,
        len(validate_batch((valid_output, invalid_provider))) == 2,
    )
    return all(checks)


if __name__ == "__main__":
    print("PASS" if _self_test() else "FAIL")
