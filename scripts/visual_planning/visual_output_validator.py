"""
Purpose:
Validate generated Visual Plans before they leave the Visual Planning Engine.

Input:
one Visual Plan result or a sequence of Visual Plan results

Output:
deterministic validation reports for visual plan structure and consistency
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

try:
    from scripts.visual_planning.visual_constitution import (
        get_asset_categories,
        get_camera_movements,
        get_shot_types,
        get_transition_types,
        get_visual_styles,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution support
    from visual_constitution import (
        get_asset_categories,
        get_camera_movements,
        get_shot_types,
        get_transition_types,
        get_visual_styles,
    )


VALIDATED_STAGE = "visual_output_validator"
REQUIRED_TOP_LEVEL_FIELDS = (
    "trend_id",
    "visual_plan",
    "generation_source",
    "fallback_used",
)
REQUIRED_SCENE_FIELDS = (
    "scene_id",
    "start_time",
    "end_time",
    "narration_segment",
    "shot_type",
    "camera_movement",
    "visual_focus",
    "asset_requirement",
    "transition_type",
)
OPTIONAL_ASSET_LIST_FIELDS = ("asset_requirements", "asset_list")
ALLOWED_GENERATION_SOURCES = frozenset({"groq", "fallback"})

ERROR_MESSAGES = {
    "VOUT001": "Missing visual plan.",
    "VOUT002": "Missing scene field.",
    "VOUT003": "Invalid timing.",
    "VOUT004": "Invalid shot type.",
    "VOUT005": "Invalid camera motion.",
    "VOUT006": "Invalid transition.",
    "VOUT007": "Invalid visual style.",
    "VOUT008": "Invalid asset list.",
    "VOUT009": "Invalid narration.",
    "VOUT010": "Invalid scene structure.",
}

__all__ = ("validate_visual_plan", "validate_visual_plans")


def validate_visual_plan(result: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Validate one generated Visual Plan result.

    Arguments:
    result: Visual Planner output dictionary

    Returns:
    deterministic validation report
    """
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    if not isinstance(result, dict):
        _add_issue(errors, "VOUT010", "result")
        return _build_report(errors, warnings)

    _validate_top_level(result, errors)

    visual_plan = result.get("visual_plan")
    if isinstance(visual_plan, list) and visual_plan:
        _validate_scenes(visual_plan, errors)

    return _build_report(errors, warnings)


def validate_visual_plans(
    results: Iterable[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """
    Purpose:
    Validate multiple generated Visual Plan results.

    Arguments:
    results: iterable of Visual Planner output dictionaries

    Returns:
    immutable tuple of validation reports
    """
    if not isinstance(results, Iterable) or isinstance(results, (str, bytes)):
        return (validate_visual_plan(results),)

    return tuple(validate_visual_plan(result) for result in results)


def _validate_top_level(
    result: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate Visual Plan top-level structure.

    Arguments:
    result: Visual Planner output dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in result:
            code = "VOUT001" if field == "visual_plan" else "VOUT010"
            _add_issue(errors, code, field)

    if "visual_plan" in result:
        visual_plan = result["visual_plan"]

        if not isinstance(visual_plan, list) or not visual_plan:
            _add_issue(errors, "VOUT001", "visual_plan")

    trend_id = result.get("trend_id")
    generation_source = result.get("generation_source")
    fallback_used = result.get("fallback_used")

    if not isinstance(trend_id, str) or not trend_id.strip():
        _add_issue(errors, "VOUT010", "trend_id")

    if not isinstance(generation_source, str) or generation_source not in ALLOWED_GENERATION_SOURCES:
        _add_issue(errors, "VOUT010", "generation_source")

    if not isinstance(fallback_used, bool):
        _add_issue(errors, "VOUT010", "fallback_used")


def _validate_scenes(
    visual_plan: list[Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate scene schema, timing, and sequencing.

    Arguments:
    visual_plan: visual scene list
    errors: mutable validation error list

    Returns:
    None
    """
    previous_end_time: float | None = None

    for expected_index, scene in enumerate(visual_plan, start=1):
        if not isinstance(scene, dict):
            _add_issue(errors, "VOUT010", f"scene_{expected_index}")
            continue

        _validate_scene_fields(scene, expected_index, errors)

        if _scene_has_required_fields(scene):
            _validate_scene_values(scene, expected_index, previous_end_time, errors)

            end_time = scene.get("end_time")
            if isinstance(end_time, (int, float)):
                previous_end_time = float(end_time)


def _validate_scene_fields(
    scene: dict[str, Any],
    expected_index: int,
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate required scene fields exist.

    Arguments:
    scene: visual scene dictionary
    expected_index: expected one-based scene index
    errors: mutable validation error list

    Returns:
    None
    """
    for field in REQUIRED_SCENE_FIELDS:
        if field not in scene:
            _add_issue(errors, "VOUT002", f"scene_{expected_index}.{field}")


def _validate_scene_values(
    scene: dict[str, Any],
    expected_index: int,
    previous_end_time: float | None,
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate scene values against schema and constitution vocabularies.

    Arguments:
    scene: visual scene dictionary
    expected_index: expected one-based scene index
    previous_end_time: previous scene end time
    errors: mutable validation error list

    Returns:
    None
    """
    if scene.get("scene_id") != expected_index:
        _add_issue(errors, "VOUT010", f"scene_{expected_index}.scene_id")

    _validate_timing(scene, expected_index, previous_end_time, errors)
    _validate_narration(scene, expected_index, errors)
    _validate_vocabularies(scene, expected_index, errors)
    _validate_asset_lists(scene, expected_index, errors)


def _validate_timing(
    scene: dict[str, Any],
    expected_index: int,
    previous_end_time: float | None,
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate scene timing consistency.

    Arguments:
    scene: visual scene dictionary
    expected_index: expected one-based scene index
    previous_end_time: previous scene end time
    errors: mutable validation error list

    Returns:
    None
    """
    start_time = scene.get("start_time")
    end_time = scene.get("end_time")

    if not isinstance(start_time, (int, float)) or not isinstance(end_time, (int, float)):
        _add_issue(errors, "VOUT003", f"scene_{expected_index}.timing")
        return

    if start_time < 0 or end_time <= start_time:
        _add_issue(errors, "VOUT003", f"scene_{expected_index}.timing")

    if previous_end_time is not None and start_time < previous_end_time:
        _add_issue(errors, "VOUT003", f"scene_{expected_index}.start_time")


def _validate_narration(
    scene: dict[str, Any],
    expected_index: int,
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate scene narration segment integrity.

    Arguments:
    scene: visual scene dictionary
    expected_index: expected one-based scene index
    errors: mutable validation error list

    Returns:
    None
    """
    narration_segment = scene.get("narration_segment")
    visual_focus = scene.get("visual_focus")

    if not isinstance(narration_segment, str) or not narration_segment.strip():
        _add_issue(errors, "VOUT009", f"scene_{expected_index}.narration_segment")

    if not isinstance(visual_focus, str) or not visual_focus.strip():
        _add_issue(errors, "VOUT010", f"scene_{expected_index}.visual_focus")


def _validate_vocabularies(
    scene: dict[str, Any],
    expected_index: int,
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate scene values against Visual Constitution vocabularies.

    Arguments:
    scene: visual scene dictionary
    expected_index: expected one-based scene index
    errors: mutable validation error list

    Returns:
    None
    """
    if scene.get("shot_type") not in get_shot_types():
        _add_issue(errors, "VOUT004", f"scene_{expected_index}.shot_type")

    if scene.get("camera_movement") not in get_camera_movements():
        _add_issue(errors, "VOUT005", f"scene_{expected_index}.camera_movement")

    if scene.get("transition_type") not in get_transition_types():
        _add_issue(errors, "VOUT006", f"scene_{expected_index}.transition_type")

    if "visual_style" in scene and scene.get("visual_style") not in get_visual_styles():
        _add_issue(errors, "VOUT007", f"scene_{expected_index}.visual_style")


def _validate_asset_lists(
    scene: dict[str, Any],
    expected_index: int,
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate asset requirement fields.

    Arguments:
    scene: visual scene dictionary
    expected_index: expected one-based scene index
    errors: mutable validation error list

    Returns:
    None
    """
    asset_requirement = scene.get("asset_requirement")

    if asset_requirement not in get_asset_categories():
        _add_issue(errors, "VOUT008", f"scene_{expected_index}.asset_requirement")

    for field in OPTIONAL_ASSET_LIST_FIELDS:
        if field in scene and not _is_valid_asset_list(scene[field]):
            _add_issue(errors, "VOUT008", f"scene_{expected_index}.{field}")


def _scene_has_required_fields(scene: dict[str, Any]) -> bool:
    """
    Purpose:
    Check whether a scene contains all required fields.

    Arguments:
    scene: visual scene dictionary

    Returns:
    required field presence flag
    """
    return all(field in scene for field in REQUIRED_SCENE_FIELDS)


def _is_valid_asset_list(value: Any) -> bool:
    """
    Purpose:
    Validate optional asset list values.

    Arguments:
    value: optional asset list value

    Returns:
    asset list validity flag
    """
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


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
    Build the stable Visual Output Validator report.

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


def _valid_scene() -> dict[str, Any]:
    """
    Purpose:
    Build valid scene for self-tests.

    Arguments:
    None

    Returns:
    valid scene dictionary
    """
    return {
        "scene_id": 1,
        "start_time": 0.0,
        "end_time": 3.0,
        "narration_segment": "The story is gaining attention.",
        "shot_type": "headline_card",
        "camera_movement": "static",
        "visual_focus": "source_supported_context",
        "asset_requirement": "text_card",
        "transition_type": "none",
        "visual_style": get_visual_styles()[0],
    }


def _valid_result() -> dict[str, Any]:
    """
    Purpose:
    Build valid Visual Plan result for self-tests.

    Arguments:
    None

    Returns:
    valid Visual Plan result
    """
    return {
        "trend_id": "trend_001",
        "visual_plan": [_valid_scene()],
        "generation_source": "groq",
        "fallback_used": False,
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
    Run deterministic Visual Output Validator self-tests.

    Arguments:
    None

    Returns:
    aggregate test result
    """
    missing_plan = _valid_result()
    missing_plan.pop("visual_plan")

    missing_scene_field = _valid_result()
    missing_scene_field["visual_plan"][0].pop("shot_type")

    invalid_timing = _valid_result()
    invalid_timing["visual_plan"][0]["end_time"] = 0.0

    invalid_shot = _valid_result()
    invalid_shot["visual_plan"][0]["shot_type"] = "fake_shot"

    invalid_transition = _valid_result()
    invalid_transition["visual_plan"][0]["transition_type"] = "fake_transition"

    invalid_style = _valid_result()
    invalid_style["visual_plan"][0]["visual_style"] = "fake_style"

    empty_narration = _valid_result()
    empty_narration["visual_plan"][0]["narration_segment"] = ""

    invalid_asset_list = _valid_result()
    invalid_asset_list["visual_plan"][0]["asset_requirements"] = "text_card"

    fallback_output = _valid_result()
    fallback_output["generation_source"] = "fallback"
    fallback_output["fallback_used"] = True

    tests = (
        validate_visual_plan(_valid_result())["valid"],
        _has_error(validate_visual_plan(missing_plan), "VOUT001"),
        _has_error(validate_visual_plan(missing_scene_field), "VOUT002"),
        _has_error(validate_visual_plan(invalid_timing), "VOUT003"),
        _has_error(validate_visual_plan(invalid_shot), "VOUT004"),
        _has_error(validate_visual_plan(invalid_transition), "VOUT006"),
        _has_error(validate_visual_plan(invalid_style), "VOUT007"),
        _has_error(validate_visual_plan(empty_narration), "VOUT009"),
        _has_error(validate_visual_plan(invalid_asset_list), "VOUT008"),
        validate_visual_plan(fallback_output)["valid"],
    )

    return all(tests)


if __name__ == "__main__":
    print("PASS" if _run_self_tests() else "FAIL")
