"""
Purpose:
Validate deterministic Visual Blueprints before AI planning.

Input:
one Visual Blueprint record or a sequence of records

Output:
deterministic validation reports for structure and constitution compliance
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

try:
    from scripts.visual_planning.visual_constitution import (
        get_quality_targets,
        get_visual_styles,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution support
    from visual_constitution import get_quality_targets, get_visual_styles


VALIDATED_STAGE = "visual_validator"

TOP_LEVEL_REQUIRED_FIELDS = (
    "trend_id",
    "voice_script",
    "metadata",
    "visual_blueprint",
)

BLUEPRINT_REQUIRED_FIELDS = (
    "estimated_duration",
    "estimated_scene_count",
    "word_count",
    "sentence_count",
    "pacing",
    "scene_strategy",
    "default_visual_style",
)

TOP_LEVEL_TYPES = {
    "trend_id": str,
    "voice_script": str,
    "metadata": dict,
    "visual_blueprint": dict,
}

BLUEPRINT_TYPES = {
    "estimated_duration": int,
    "estimated_scene_count": int,
    "word_count": int,
    "sentence_count": int,
    "pacing": str,
    "scene_strategy": str,
    "default_visual_style": str,
}

ALLOWED_PACING = frozenset({"none", "light", "moderate", "dense"})
ALLOWED_SCENE_STRATEGIES = frozenset(
    {
        "no_scene_strategy",
        "single_visual_beat",
        "sentence_aligned_visual_beats",
    }
)

ERROR_MESSAGES = {
    "VISUAL001": "Missing trend_id.",
    "VISUAL002": "Missing voice_script.",
    "VISUAL003": "Missing visual_blueprint.",
    "VISUAL004": "Missing metadata.",
    "VISUAL005": "Invalid field type.",
    "VISUAL006": "Invalid duration.",
    "VISUAL007": "Invalid scene count.",
    "VISUAL008": "Invalid pacing.",
    "VISUAL009": "Invalid visual style.",
    "VISUAL010": "Invalid blueprint structure.",
}

__all__ = ("validate_visual_blueprint", "validate_visual_blueprints")


def validate_visual_blueprint(record: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Validate one Visual Blueprint record.

    Arguments:
    record: Visual Blueprint record

    Returns:
    deterministic validation report
    """
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    if not isinstance(record, dict):
        _add_issue(errors, "VISUAL010", "record")
        return _build_report(errors, warnings)

    _validate_top_level(record, errors)

    blueprint = record.get("visual_blueprint")
    if isinstance(blueprint, dict):
        _validate_blueprint(blueprint, errors)

    return _build_report(errors, warnings)


def validate_visual_blueprints(
    records: Iterable[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """
    Purpose:
    Validate multiple Visual Blueprint records.

    Arguments:
    records: iterable of Visual Blueprint records

    Returns:
    immutable tuple of validation reports
    """
    if not isinstance(records, Iterable) or isinstance(records, (str, bytes)):
        return (validate_visual_blueprint(records),)

    return tuple(validate_visual_blueprint(record) for record in records)


def _validate_top_level(
    record: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate top-level Visual Blueprint record fields.

    Arguments:
    record: Visual Blueprint record
    errors: mutable validation error list

    Returns:
    None
    """
    for field in TOP_LEVEL_REQUIRED_FIELDS:
        if field not in record:
            _add_issue(errors, _missing_field_code(field), field)
            continue

        value = record[field]

        if not isinstance(value, TOP_LEVEL_TYPES[field]):
            _add_issue(errors, "VISUAL005", field)
            continue

        if _is_empty_required_value(value):
            _add_issue(errors, _empty_field_code(field), field)


def _validate_blueprint(
    blueprint: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate Visual Blueprint structure and constitution compliance.

    Arguments:
    blueprint: visual_blueprint dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    for field in BLUEPRINT_REQUIRED_FIELDS:
        if field not in blueprint:
            _add_issue(errors, "VISUAL010", field)
            continue

        value = blueprint[field]

        if not isinstance(value, BLUEPRINT_TYPES[field]):
            _add_issue(errors, "VISUAL005", field)

    _validate_numeric_values(blueprint, errors)
    _validate_constitution_values(blueprint, errors)


def _validate_numeric_values(
    blueprint: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate duration, scene count, and count fields.

    Arguments:
    blueprint: visual_blueprint dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    duration = blueprint.get("estimated_duration")
    scene_count = blueprint.get("estimated_scene_count")
    word_count = blueprint.get("word_count")
    sentence_count = blueprint.get("sentence_count")

    if isinstance(duration, int) and duration < 0:
        _add_issue(errors, "VISUAL006", "estimated_duration")

    if isinstance(scene_count, int):
        quality_targets = get_quality_targets()
        max_scenes = quality_targets["maximum_scene_count"]

        if scene_count < 0 or scene_count > max_scenes:
            _add_issue(errors, "VISUAL007", "estimated_scene_count")

    if isinstance(word_count, int) and word_count < 0:
        _add_issue(errors, "VISUAL010", "word_count")

    if isinstance(sentence_count, int) and sentence_count < 0:
        _add_issue(errors, "VISUAL010", "sentence_count")


def _validate_constitution_values(
    blueprint: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate blueprint enum values against constitution vocabularies.

    Arguments:
    blueprint: visual_blueprint dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    pacing = blueprint.get("pacing")
    scene_strategy = blueprint.get("scene_strategy")
    visual_style = blueprint.get("default_visual_style")

    if isinstance(pacing, str) and pacing not in ALLOWED_PACING:
        _add_issue(errors, "VISUAL008", "pacing")

    if isinstance(scene_strategy, str) and scene_strategy not in ALLOWED_SCENE_STRATEGIES:
        _add_issue(errors, "VISUAL010", "scene_strategy")

    if isinstance(visual_style, str) and visual_style not in get_visual_styles():
        _add_issue(errors, "VISUAL009", "default_visual_style")


def _missing_field_code(field: str) -> str:
    """
    Purpose:
    Return stable missing-field error code.

    Arguments:
    field: top-level field name

    Returns:
    error code
    """
    codes = {
        "trend_id": "VISUAL001",
        "voice_script": "VISUAL002",
        "metadata": "VISUAL004",
        "visual_blueprint": "VISUAL003",
    }
    return codes[field]


def _empty_field_code(field: str) -> str:
    """
    Purpose:
    Return stable empty-field error code.

    Arguments:
    field: top-level field name

    Returns:
    error code
    """
    if field == "metadata":
        return "VISUAL004"

    return _missing_field_code(field)


def _is_empty_required_value(value: Any) -> bool:
    """
    Purpose:
    Detect empty required structural values.

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
    code: stable error code
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
    Build the stable Visual Validator report.

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
    Build valid Visual Blueprint record for self-tests.

    Arguments:
    None

    Returns:
    valid Visual Blueprint record
    """
    return {
        "trend_id": "trend_001",
        "voice_script": "A short entertainment story is moving quickly.",
        "metadata": {"source": "creator_voice"},
        "visual_blueprint": {
            "estimated_duration": 5,
            "estimated_scene_count": 3,
            "word_count": 7,
            "sentence_count": 1,
            "pacing": "light",
            "scene_strategy": "single_visual_beat",
            "default_visual_style": get_visual_styles()[0],
        },
    }


def _has_error(report: dict[str, Any], code: str) -> bool:
    """
    Purpose:
    Check whether a validation report contains an error code.

    Arguments:
    report: validation report
    code: expected error code

    Returns:
    matching error flag
    """
    return any(error["code"] == code for error in report["errors"])


def _run_self_tests() -> bool:
    """
    Purpose:
    Run deterministic Visual Validator self-tests.

    Arguments:
    None

    Returns:
    aggregate test result
    """
    missing_trend_id = _valid_record()
    missing_trend_id.pop("trend_id")

    missing_voice_script = _valid_record()
    missing_voice_script.pop("voice_script")

    missing_metadata = _valid_record()
    missing_metadata.pop("metadata")

    missing_blueprint = _valid_record()
    missing_blueprint.pop("visual_blueprint")

    invalid_duration = _valid_record()
    invalid_duration["visual_blueprint"]["estimated_duration"] = -1

    invalid_scene_count = _valid_record()
    invalid_scene_count["visual_blueprint"]["estimated_scene_count"] = 99

    invalid_pacing = _valid_record()
    invalid_pacing["visual_blueprint"]["pacing"] = "extreme"

    invalid_visual_style = _valid_record()
    invalid_visual_style["visual_blueprint"]["default_visual_style"] = "cinematic_fake"

    invalid_field_type = _valid_record()
    invalid_field_type["visual_blueprint"]["word_count"] = "seven"

    tests = (
        validate_visual_blueprint(_valid_record())["valid"],
        _has_error(validate_visual_blueprint(missing_trend_id), "VISUAL001"),
        _has_error(validate_visual_blueprint(missing_voice_script), "VISUAL002"),
        _has_error(validate_visual_blueprint(missing_metadata), "VISUAL004"),
        _has_error(validate_visual_blueprint(missing_blueprint), "VISUAL003"),
        _has_error(validate_visual_blueprint(invalid_duration), "VISUAL006"),
        _has_error(validate_visual_blueprint(invalid_scene_count), "VISUAL007"),
        _has_error(validate_visual_blueprint(invalid_pacing), "VISUAL008"),
        _has_error(validate_visual_blueprint(invalid_visual_style), "VISUAL009"),
        _has_error(validate_visual_blueprint(invalid_field_type), "VISUAL005"),
    )

    return all(tests)


if __name__ == "__main__":
    print("PASS" if _run_self_tests() else "FAIL")
