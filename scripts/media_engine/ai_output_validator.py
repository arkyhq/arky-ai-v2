"""Validation-only utilities for normalized AI provider outputs."""

from __future__ import annotations

from typing import Any


REQUIRED_FIELDS = (
    "success",
    "provider",
    "provider_type",
    "asset_type",
    "download_url",
    "preview_url",
    "prompt",
    "asset_id",
    "license",
    "generation_cost",
)


def validate_ai_output(result: dict) -> dict:
    """
    Validate one normalized AI provider asset response.

    Arguments:
        result: normalized AI provider asset dictionary.

    Returns:
        Structured validation result.
    """
    errors: list[str] = []
    warnings: list[str] = []
    validated = _safe_mapping(result)

    try:
        if not validated:
            errors.append("result must be a non-empty dictionary")
            return _validation_result(False, None, errors, warnings)

        _validate_required_fields(validated, errors)
        _validate_success(validated, errors)
        _validate_provider(validated, errors)
        _validate_provider_type(validated, errors)
        _validate_asset_type(validated, errors)
        _validate_download_url(validated, errors)
        _validate_preview_url(validated, errors)
        _validate_prompt(validated, errors)
        _validate_asset_id(validated, errors)
        _validate_license(validated, errors)
        _validate_generation_cost(validated, errors)
    except Exception as exc:
        errors.append(f"unexpected AI output validation error: {exc}")

    return _validation_result(
        not errors,
        validated if not errors else None,
        errors,
        warnings,
    )


def validate_batch(results: list[dict]) -> dict:
    """
    Validate multiple normalized AI provider asset responses.

    Arguments:
        results: list of normalized AI provider asset dictionaries.

    Returns:
        Structured batch validation result.
    """
    errors: list[str] = []
    warnings: list[str] = []

    try:
        if not isinstance(results, list):
            errors.append("results must be a list")
            return _validation_result(False, None, errors, warnings)

        validated_results = []
        for index, result in enumerate(results):
            validation = validate_ai_output(result)
            if validation.get("success") is True:
                validated_results.append(validation.get("validated"))
            else:
                errors.extend(
                    f"result[{index}]: {error}"
                    for error in validation.get("errors", [])
                )
            warnings.extend(validation.get("warnings", []))

        return _validation_result(
            not errors,
            validated_results if not errors else None,
            errors,
            warnings,
        )
    except Exception as exc:
        errors.append(f"unexpected AI output batch validation error: {exc}")
        return _validation_result(False, None, errors, warnings)


def _validate_required_fields(result: dict[str, Any], errors: list[str]) -> None:
    """Validate all required fields exist."""
    for field in REQUIRED_FIELDS:
        if field not in result:
            errors.append(f"missing required field: {field}")


def _validate_success(result: dict[str, Any], errors: list[str]) -> None:
    """Validate success field exists and is boolean."""
    if "success" in result and not isinstance(result.get("success"), bool):
        errors.append("success must be boolean")


def _validate_provider(result: dict[str, Any], errors: list[str]) -> None:
    """Validate provider is populated."""
    if "provider" in result and not _safe_text(result.get("provider")):
        errors.append("provider must be populated")


def _validate_provider_type(result: dict[str, Any], errors: list[str]) -> None:
    """Validate provider_type is ai."""
    if "provider_type" in result and _safe_text(
        result.get("provider_type")
    ) != "ai":
        errors.append('provider_type must be "ai"')


def _validate_asset_type(result: dict[str, Any], errors: list[str]) -> None:
    """Validate asset_type is populated."""
    if "asset_type" in result and not _safe_text(result.get("asset_type")):
        errors.append("asset_type must be populated")


def _validate_download_url(result: dict[str, Any], errors: list[str]) -> None:
    """Validate download_url is populated."""
    if "download_url" in result and not _safe_text(result.get("download_url")):
        errors.append("download_url must be populated")


def _validate_preview_url(result: dict[str, Any], errors: list[str]) -> None:
    """Validate preview_url is populated."""
    if "preview_url" in result and not _safe_text(result.get("preview_url")):
        errors.append("preview_url must be populated")


def _validate_prompt(result: dict[str, Any], errors: list[str]) -> None:
    """Validate prompt is populated."""
    if "prompt" in result and not _safe_text(result.get("prompt")):
        errors.append("prompt must be populated")


def _validate_asset_id(result: dict[str, Any], errors: list[str]) -> None:
    """Validate asset_id is populated."""
    if "asset_id" in result and not _safe_text(result.get("asset_id")):
        errors.append("asset_id must be populated")


def _validate_license(result: dict[str, Any], errors: list[str]) -> None:
    """Validate license is populated."""
    if "license" in result and not _safe_text(result.get("license")):
        errors.append("license must be populated")


def _validate_generation_cost(
    result: dict[str, Any],
    errors: list[str],
) -> None:
    """Validate generation_cost exists."""
    if "generation_cost" in result and result.get("generation_cost") is None:
        errors.append("generation_cost must be populated")


def _validation_result(
    success: bool,
    validated: Any,
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    """Build a structured validation result."""
    return {
        "success": success,
        "validated": validated,
        "errors": list(errors),
        "warnings": list(warnings),
    }


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
