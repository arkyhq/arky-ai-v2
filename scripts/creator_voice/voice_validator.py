"""
Purpose:
Validate deterministic Creator Voice blueprints before transformation.

Input:
one mapped Creator Voice record or a sequence of mapped records

Output:
deterministic validation reports for structure and constitution compliance
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

try:
    from scripts.creator_voice.voice_constitution import (
        get_voice_metadata,
        get_voice_targets,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution support
    from voice_constitution import get_voice_metadata, get_voice_targets


VALIDATED_STAGE = "voice_validator"

TOP_LEVEL_REQUIRED_FIELDS = (
    "trend_id",
    "narration",
    "metadata",
    "voice_blueprint",
)

BLUEPRINT_REQUIRED_FIELDS = (
    "voice_name",
    "voice_version",
    "tone",
    "energy",
    "curiosity",
    "sentence_style",
    "transition_style",
    "hook_priority",
    "ending_style",
    "preserve_entities",
    "preserve_numbers",
    "preserve_dates",
    "preserve_order",
)

TOP_LEVEL_TYPES = {
    "trend_id": str,
    "narration": str,
    "metadata": dict,
    "voice_blueprint": dict,
}

BLUEPRINT_TYPES = {
    "voice_name": str,
    "voice_version": str,
    "tone": str,
    "energy": str,
    "curiosity": str,
    "sentence_style": str,
    "transition_style": str,
    "hook_priority": bool,
    "ending_style": str,
    "preserve_entities": bool,
    "preserve_numbers": bool,
    "preserve_dates": bool,
    "preserve_order": bool,
}

ALLOWED_TONES = frozenset({"clear_confident", "careful_confident"})
ALLOWED_TRANSITION_STYLES = frozenset({"smooth_spoken_transitions"})
REQUIRED_BOOLEAN_VALUES = {
    "preserve_entities": True,
    "preserve_numbers": True,
    "preserve_dates": True,
    "preserve_order": True,
}

ERROR_MESSAGES = {
    "VOICE001": "Missing trend_id.",
    "VOICE002": "Missing narration.",
    "VOICE003": "Missing voice_blueprint.",
    "VOICE004": "Invalid field type.",
    "VOICE005": "Missing metadata.",
    "VOICE006": "Missing constitution field.",
    "VOICE007": "Empty required field.",
    "VOICE008": "Invalid blueprint value.",
}

__all__ = ("validate_voice_blueprint", "validate_voice_records")


def validate_voice_blueprint(record: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Validate one mapped Creator Voice record.

    Arguments:
    record: mapped Creator Voice record

    Returns:
    deterministic validation report
    """
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    if not isinstance(record, dict):
        _add_issue(errors, "VOICE004", "record")
        return _build_report(errors, warnings)

    _validate_top_level(record, errors)

    blueprint = record.get("voice_blueprint")
    if isinstance(blueprint, dict):
        _validate_blueprint(blueprint, errors)

    return _build_report(errors, warnings)


def validate_voice_records(
    records: Iterable[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """
    Purpose:
    Validate multiple mapped Creator Voice records.

    Arguments:
    records: iterable of mapped Creator Voice records

    Returns:
    immutable tuple of validation reports
    """
    if not isinstance(records, Iterable) or isinstance(records, (str, bytes)):
        return (validate_voice_blueprint(records),)

    return tuple(validate_voice_blueprint(record) for record in records)


def _validate_top_level(
    record: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate required top-level fields.

    Arguments:
    record: mapped Creator Voice record
    errors: mutable validation error list

    Returns:
    None
    """
    for field in TOP_LEVEL_REQUIRED_FIELDS:
        if field not in record:
            _add_issue(errors, _missing_top_level_code(field), field)
            continue

        value = record[field]
        if not isinstance(value, TOP_LEVEL_TYPES[field]):
            _add_issue(errors, "VOICE004", field)
            continue

        if _is_empty_required_value(value):
            _add_issue(errors, _empty_top_level_code(field), field)


def _validate_blueprint(
    blueprint: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate required voice blueprint fields and values.

    Arguments:
    blueprint: voice blueprint dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    for field in BLUEPRINT_REQUIRED_FIELDS:
        if field not in blueprint:
            _add_issue(errors, "VOICE006", field)
            continue

        value = blueprint[field]
        if not isinstance(value, BLUEPRINT_TYPES[field]):
            _add_issue(errors, "VOICE004", field)
            continue

        if _is_empty_required_value(value):
            _add_issue(errors, "VOICE007", field)

    _validate_constitution_values(blueprint, errors)


def _validate_constitution_values(
    blueprint: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate blueprint values against the Voice Constitution.

    Arguments:
    blueprint: voice blueprint dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    voice_metadata = get_voice_metadata()
    voice_targets = get_voice_targets()
    constitution_values = {
        "voice_name": voice_metadata["voice_name"],
        "voice_version": voice_metadata["voice_version"],
        "energy": voice_targets["energy_level"],
        "curiosity": voice_targets["curiosity_level"],
        "ending_style": voice_targets["preferred_ending_style"],
    }

    for field, expected_value in constitution_values.items():
        if field in blueprint and blueprint[field] != expected_value:
            _add_issue(errors, "VOICE008", field)

    if blueprint.get("tone") not in ALLOWED_TONES:
        _add_issue(errors, "VOICE008", "tone")

    if blueprint.get("transition_style") not in ALLOWED_TRANSITION_STYLES:
        _add_issue(errors, "VOICE008", "transition_style")

    for field, expected_value in REQUIRED_BOOLEAN_VALUES.items():
        if field in blueprint and blueprint[field] is not expected_value:
            _add_issue(errors, "VOICE008", field)


def _missing_top_level_code(field: str) -> str:
    """
    Purpose:
    Select stable error code for missing top-level fields.

    Arguments:
    field: top-level field name

    Returns:
    stable validation error code
    """
    codes = {
        "trend_id": "VOICE001",
        "narration": "VOICE002",
        "metadata": "VOICE005",
        "voice_blueprint": "VOICE003",
    }
    return codes[field]


def _empty_top_level_code(field: str) -> str:
    """
    Purpose:
    Select stable error code for empty top-level fields.

    Arguments:
    field: top-level field name

    Returns:
    stable validation error code
    """
    if field == "metadata":
        return "VOICE005"

    return "VOICE007"


def _is_empty_required_value(value: Any) -> bool:
    """
    Purpose:
    Detect empty required values without inspecting narration quality.

    Arguments:
    value: field value

    Returns:
    empty value flag
    """
    if isinstance(value, str):
        return not value.strip()

    if isinstance(value, dict):
        return not value

    return False


def _add_issue(
    issues: list[dict[str, str]],
    code: str,
    field: str,
) -> None:
    """
    Purpose:
    Add one structured validation issue.

    Arguments:
    issues: mutable issue list
    code: stable issue code
    field: affected field name

    Returns:
    None
    """
    issues.append(
        {
            "code": code,
            "field": field,
            "message": ERROR_MESSAGES[code],
        }
    )


def _build_report(
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> dict[str, Any]:
    """
    Purpose:
    Build the stable validation report.

    Arguments:
    errors: validation errors
    warnings: validation warnings

    Returns:
    validation report dictionary
    """
    return {
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "validated_at_stage": VALIDATED_STAGE,
    }


def _valid_record() -> dict[str, Any]:
    """
    Purpose:
    Build one valid mapped Creator Voice record for self-tests.

    Arguments:
    None

    Returns:
    valid mapped Creator Voice record
    """
    voice_metadata = get_voice_metadata()
    voice_targets = get_voice_targets()

    return {
        "trend_id": "trend_001",
        "narration": "A new entertainment story is getting attention online.",
        "metadata": {"source": "script_generation"},
        "voice_blueprint": {
            "voice_name": voice_metadata["voice_name"],
            "voice_version": voice_metadata["voice_version"],
            "tone": "clear_confident",
            "energy": voice_targets["energy_level"],
            "curiosity": voice_targets["curiosity_level"],
            "sentence_style": "short_spoken_6_to_14_words",
            "transition_style": "smooth_spoken_transitions",
            "hook_priority": True,
            "ending_style": voice_targets["preferred_ending_style"],
            "preserve_entities": True,
            "preserve_numbers": True,
            "preserve_dates": True,
            "preserve_order": True,
        },
    }


def _has_error(report: dict[str, Any], code: str) -> bool:
    """
    Purpose:
    Check whether a validation report contains an error code.

    Arguments:
    report: validation report
    code: expected stable error code

    Returns:
    matching error flag
    """
    return any(error["code"] == code for error in report["errors"])


def _run_self_tests() -> bool:
    """
    Purpose:
    Run lightweight deterministic self-tests.

    Arguments:
    None

    Returns:
    aggregate test result
    """
    valid_record = _valid_record()

    missing_trend_id = _valid_record()
    missing_trend_id.pop("trend_id")

    missing_narration = _valid_record()
    missing_narration.pop("narration")

    missing_blueprint = _valid_record()
    missing_blueprint.pop("voice_blueprint")

    invalid_type = _valid_record()
    invalid_type["trend_id"] = 123

    empty_metadata = _valid_record()
    empty_metadata["metadata"] = {}

    invalid_boolean = _valid_record()
    invalid_boolean["voice_blueprint"]["preserve_order"] = "yes"

    invalid_constitution_value = _valid_record()
    invalid_constitution_value["voice_blueprint"]["voice_name"] = "Other Voice"

    tests = (
        validate_voice_blueprint(valid_record)["valid"],
        _has_error(validate_voice_blueprint(missing_trend_id), "VOICE001"),
        _has_error(validate_voice_blueprint(missing_narration), "VOICE002"),
        _has_error(validate_voice_blueprint(missing_blueprint), "VOICE003"),
        _has_error(validate_voice_blueprint(invalid_type), "VOICE004"),
        _has_error(validate_voice_blueprint(empty_metadata), "VOICE005"),
        _has_error(validate_voice_blueprint(invalid_boolean), "VOICE004"),
        _has_error(
            validate_voice_blueprint(invalid_constitution_value),
            "VOICE008",
        ),
    )

    return all(tests)


if __name__ == "__main__":
    print("PASS" if _run_self_tests() else "FAIL")
