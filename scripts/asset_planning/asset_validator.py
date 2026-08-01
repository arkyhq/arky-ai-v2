"""
Purpose:
Validate deterministic Asset Blueprints before asset planning.

Input:
one Asset Blueprint record or a sequence of Asset Blueprint records

Output:
deterministic validation reports for schema, statistics, categories, and
render constraints
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

try:
    from scripts.asset_planning.asset_constitution import (
        get_asset_categories,
        get_render_constraints,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution support
    from asset_constitution import get_asset_categories, get_render_constraints


VALIDATED_STAGE = "asset_validator"
ALLOWED_COMPLEXITY = frozenset({"low", "medium", "high"})

TOP_LEVEL_REQUIRED_FIELDS = (
    "trend_id",
    "metadata",
    "visual_plan",
    "generation_source",
    "fallback_used",
    "asset_blueprint",
)

BLUEPRINT_REQUIRED_FIELDS = (
    "engine_name",
    "engine_version",
    "asset_counts",
    "planning_statistics",
    "render_complexity",
    "render_constraints",
)

STATISTIC_REQUIRED_FIELDS = (
    "scene_count",
    "total_duration",
    "average_scene_duration",
    "total_estimated_assets",
    "unique_asset_categories",
    "timed_scene_count",
    "fallback_scene_count",
)

SCENE_REQUIRED_FIELDS = (
    "scene_id",
    "start_time",
    "end_time",
    "narration_segment",
    "asset_requirement",
)

ERROR_MESSAGES = {
    "ASSET001": "Missing required field.",
    "ASSET002": "Invalid field type.",
    "ASSET003": "Invalid metadata.",
    "ASSET004": "Invalid scene integrity.",
    "ASSET005": "Invalid planning statistics.",
    "ASSET006": "Invalid render complexity.",
    "ASSET007": "Invalid asset category.",
    "ASSET008": "Invalid render constraints.",
    "ASSET009": "Invalid asset counts.",
    "ASSET010": "Invalid schema.",
}

__all__ = ("validate_asset_blueprint", "validate_asset_blueprints")


def validate_asset_blueprint(record: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Validate one Asset Blueprint record.

    Arguments:
    record: Asset Blueprint dictionary

    Returns:
    deterministic validation report
    """
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    if not isinstance(record, dict):
        _add_issue(errors, "ASSET010", "record")
        return _build_report(errors, warnings)

    _validate_top_level(record, errors)

    asset_blueprint = record.get("asset_blueprint")
    if isinstance(asset_blueprint, dict):
        _validate_asset_blueprint_body(asset_blueprint, errors)
        _validate_consistency(record, asset_blueprint, errors)

    return _build_report(errors, warnings)


def validate_asset_blueprints(
    records: Iterable[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """
    Purpose:
    Validate multiple Asset Blueprint records.

    Arguments:
    records: iterable of Asset Blueprint dictionaries

    Returns:
    immutable tuple of validation reports
    """
    if not isinstance(records, Iterable) or isinstance(records, (str, bytes)):
        return (validate_asset_blueprint(records),)

    return tuple(validate_asset_blueprint(record) for record in records)


def _validate_top_level(
    record: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate top-level Asset Blueprint fields.

    Arguments:
    record: Asset Blueprint dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    for field in TOP_LEVEL_REQUIRED_FIELDS:
        if field not in record:
            _add_issue(errors, "ASSET001", field)

    type_rules = {
        "trend_id": str,
        "metadata": dict,
        "visual_plan": tuple,
        "generation_source": str,
        "fallback_used": bool,
        "asset_blueprint": dict,
    }

    for field, expected_type in type_rules.items():
        if field in record and not isinstance(record[field], expected_type):
            _add_issue(errors, "ASSET002", field)

    if isinstance(record.get("trend_id"), str) and not record["trend_id"].strip():
        _add_issue(errors, "ASSET001", "trend_id")

    if isinstance(record.get("metadata"), dict) and not record["metadata"]:
        _add_issue(errors, "ASSET003", "metadata")

    visual_plan = record.get("visual_plan")
    if isinstance(visual_plan, tuple):
        _validate_scenes(visual_plan, errors)


def _validate_asset_blueprint_body(
    asset_blueprint: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate Asset Blueprint body fields.

    Arguments:
    asset_blueprint: nested asset_blueprint dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    for field in BLUEPRINT_REQUIRED_FIELDS:
        if field not in asset_blueprint:
            _add_issue(errors, "ASSET001", f"asset_blueprint.{field}")

    if isinstance(asset_blueprint.get("asset_counts"), dict):
        _validate_asset_counts(asset_blueprint["asset_counts"], errors)

    if isinstance(asset_blueprint.get("planning_statistics"), dict):
        _validate_statistics(asset_blueprint["planning_statistics"], errors)

    complexity = asset_blueprint.get("render_complexity")
    if not isinstance(complexity, str) or complexity not in ALLOWED_COMPLEXITY:
        _add_issue(errors, "ASSET006", "asset_blueprint.render_complexity")

    if isinstance(asset_blueprint.get("render_constraints"), dict):
        _validate_render_constraints(asset_blueprint["render_constraints"], errors)


def _validate_scenes(
    scenes: tuple[Any, ...],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate preserved scene integrity.

    Arguments:
    scenes: preserved visual plan scenes
    errors: mutable validation error list

    Returns:
    None
    """
    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            _add_issue(errors, "ASSET004", f"visual_plan.{index}")
            continue

        for field in SCENE_REQUIRED_FIELDS:
            if field not in scene:
                _add_issue(errors, "ASSET004", f"visual_plan.{index}.{field}")

        asset_requirement = scene.get("asset_requirement")
        if isinstance(asset_requirement, str) and asset_requirement not in get_asset_categories():
            _add_issue(errors, "ASSET007", f"visual_plan.{index}.asset_requirement")


def _validate_asset_counts(
    asset_counts: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate asset count categories and values.

    Arguments:
    asset_counts: asset count mapping
    errors: mutable validation error list

    Returns:
    None
    """
    approved_categories = set(get_asset_categories())

    for category, count in asset_counts.items():
        if category not in approved_categories:
            _add_issue(errors, "ASSET007", f"asset_counts.{category}")

        if not isinstance(count, int) or count < 0:
            _add_issue(errors, "ASSET009", f"asset_counts.{category}")

    missing_categories = approved_categories - set(asset_counts)
    for category in missing_categories:
        _add_issue(errors, "ASSET009", f"asset_counts.{category}")


def _validate_statistics(
    statistics: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate planning statistics structure and numeric values.

    Arguments:
    statistics: planning statistics dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    for field in STATISTIC_REQUIRED_FIELDS:
        if field not in statistics:
            _add_issue(errors, "ASSET005", f"planning_statistics.{field}")

    integer_fields = (
        "scene_count",
        "total_estimated_assets",
        "unique_asset_categories",
        "timed_scene_count",
        "fallback_scene_count",
    )

    for field in integer_fields:
        value = statistics.get(field)
        if not isinstance(value, int) or value < 0:
            _add_issue(errors, "ASSET005", f"planning_statistics.{field}")

    for field in ("total_duration", "average_scene_duration"):
        value = statistics.get(field)
        if not isinstance(value, (int, float)) or value < 0:
            _add_issue(errors, "ASSET005", f"planning_statistics.{field}")


def _validate_render_constraints(
    constraints: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate render constraints against constitution keys.

    Arguments:
    constraints: render constraints dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    expected_constraints = dict(get_render_constraints())

    for key, expected_value in expected_constraints.items():
        if key not in constraints:
            _add_issue(errors, "ASSET008", f"render_constraints.{key}")
            continue

        if type(constraints[key]) is not type(expected_value):
            _add_issue(errors, "ASSET008", f"render_constraints.{key}")


def _validate_consistency(
    record: dict[str, Any],
    asset_blueprint: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate consistency between scenes, counts, and statistics.

    Arguments:
    record: Asset Blueprint dictionary
    asset_blueprint: nested asset_blueprint dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    scenes = record.get("visual_plan")
    statistics = asset_blueprint.get("planning_statistics")
    asset_counts = asset_blueprint.get("asset_counts")

    if not isinstance(scenes, tuple) or not isinstance(statistics, dict):
        return

    if statistics.get("scene_count") != len(scenes):
        _add_issue(errors, "ASSET005", "planning_statistics.scene_count")

    if isinstance(asset_counts, dict):
        total_assets = sum(count for count in asset_counts.values() if isinstance(count, int))
        if statistics.get("total_estimated_assets") != total_assets:
            _add_issue(errors, "ASSET005", "planning_statistics.total_estimated_assets")


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
    code: deterministic error code
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
    Build a deterministic validation report.

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


def _valid_blueprint() -> dict[str, Any]:
    """
    Purpose:
    Build a valid Asset Blueprint for self-tests.

    Arguments:
    None

    Returns:
    valid Asset Blueprint dictionary
    """
    asset_counts = {category: 0 for category in get_asset_categories()}
    asset_counts["text_card"] = 1
    scene = {
        "scene_id": 1,
        "start_time": 0.0,
        "end_time": 3.0,
        "narration_segment": "The story is gaining attention.",
        "asset_requirement": "text_card",
    }
    return {
        "trend_id": "trend_001",
        "metadata": {"source": "visual_planning"},
        "visual_plan": (scene,),
        "generation_source": "fallback",
        "fallback_used": True,
        "asset_blueprint": {
            "engine_name": "ARKY Asset Planning Engine",
            "engine_version": "0.8",
            "asset_counts": asset_counts,
            "planning_statistics": {
                "scene_count": 1,
                "total_duration": 3.0,
                "average_scene_duration": 3.0,
                "total_estimated_assets": 1,
                "unique_asset_categories": 1,
                "timed_scene_count": 1,
                "fallback_scene_count": 0,
            },
            "render_complexity": "low",
            "render_constraints": dict(get_render_constraints()),
        },
    }


def _has_error(report: dict[str, Any], code: str) -> bool:
    """
    Purpose:
    Determine whether a report contains an error code.

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
    Run deterministic Asset Validator self-tests.

    Arguments:
    None

    Returns:
    aggregate self-test result
    """
    missing_field = _valid_blueprint()
    missing_field.pop("trend_id")

    invalid_category = _valid_blueprint()
    invalid_category["asset_blueprint"]["asset_counts"]["fake_asset"] = 1

    invalid_complexity = _valid_blueprint()
    invalid_complexity["asset_blueprint"]["render_complexity"] = "extreme"

    invalid_constraints = _valid_blueprint()
    invalid_constraints["asset_blueprint"]["render_constraints"]["width"] = "1080"

    tests = (
        validate_asset_blueprint(_valid_blueprint())["valid"],
        _has_error(validate_asset_blueprint(missing_field), "ASSET001"),
        _has_error(validate_asset_blueprint(invalid_category), "ASSET007"),
        _has_error(validate_asset_blueprint(invalid_complexity), "ASSET006"),
        _has_error(validate_asset_blueprint(invalid_constraints), "ASSET008"),
        len(validate_asset_blueprints((_valid_blueprint(), _valid_blueprint()))) == 2,
    )
    return all(tests)


if __name__ == "__main__":
    print("PASS" if _run_self_tests() else "FAIL")
