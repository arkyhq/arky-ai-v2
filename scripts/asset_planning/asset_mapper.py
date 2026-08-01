"""
Purpose:
Build deterministic Asset Blueprints from validated Visual Plans.

Input:
one validated Visual Plan result or a sequence of Visual Plan results

Output:
Asset Blueprint dictionaries containing asset planning metadata only
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

try:
    from scripts.asset_planning.asset_constitution import (
        get_asset_categories,
        get_asset_metadata,
        get_render_constraints,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution support
    from asset_constitution import (
        get_asset_categories,
        get_asset_metadata,
        get_render_constraints,
    )


LOW_COMPLEXITY_SCENE_LIMIT = 3
MEDIUM_COMPLEXITY_SCENE_LIMIT = 6
LOW_COMPLEXITY_ASSET_LIMIT = 5
MEDIUM_COMPLEXITY_ASSET_LIMIT = 10

__all__ = ("build_asset_blueprint", "build_asset_blueprints")


def build_asset_blueprint(record: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Convert one validated Visual Plan into a deterministic Asset Blueprint.

    Arguments:
    record: validated Visual Plan result

    Returns:
    Asset Blueprint dictionary
    """
    visual_plan = _safe_scenes(record)
    asset_counts = _estimate_asset_counts(visual_plan)
    planning_statistics = _build_planning_statistics(visual_plan, asset_counts)

    return {
        "trend_id": _safe_text(record.get("trend_id")) if isinstance(record, dict) else "",
        "metadata": _safe_mapping(record.get("metadata")) if isinstance(record, dict) else {},
        "visual_plan": visual_plan,
        "generation_source": _safe_text(record.get("generation_source"))
        if isinstance(record, dict)
        else "",
        "fallback_used": bool(record.get("fallback_used")) if isinstance(record, dict) else True,
        "asset_blueprint": {
            "engine_name": get_asset_metadata()["engine_name"],
            "engine_version": get_asset_metadata()["engine_version"],
            "asset_counts": asset_counts,
            "planning_statistics": planning_statistics,
            "render_complexity": _estimate_render_complexity(planning_statistics),
            "render_constraints": dict(get_render_constraints()),
        },
    }


def build_asset_blueprints(
    records: Iterable[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """
    Purpose:
    Convert multiple Visual Plan results into deterministic Asset Blueprints.

    Arguments:
    records: iterable of validated Visual Plan results

    Returns:
    immutable tuple of Asset Blueprint dictionaries
    """
    if not isinstance(records, Iterable) or isinstance(records, (str, bytes)):
        return (build_asset_blueprint(records),)

    return tuple(build_asset_blueprint(record) for record in records)


def _safe_scenes(record: Any) -> tuple[dict[str, Any], ...]:
    """
    Purpose:
    Safely preserve visual plan scene dictionaries.

    Arguments:
    record: candidate Visual Plan result

    Returns:
    immutable tuple of scene dictionaries
    """
    if not isinstance(record, dict):
        return ()

    visual_plan = record.get("visual_plan")

    if not isinstance(visual_plan, list):
        return ()

    return tuple(scene for scene in visual_plan if isinstance(scene, dict))


def _estimate_asset_counts(scenes: tuple[dict[str, Any], ...]) -> dict[str, int]:
    """
    Purpose:
    Estimate required asset counts from existing scene asset requirements.

    Arguments:
    scenes: visual plan scenes

    Returns:
    mapping of approved asset categories to deterministic counts
    """
    counts = {category: 0 for category in get_asset_categories()}

    for scene in scenes:
        asset_requirement = scene.get("asset_requirement")

        if isinstance(asset_requirement, str) and asset_requirement in counts:
            counts[asset_requirement] += 1

        for asset in _safe_asset_list(scene.get("asset_requirements")):
            if asset in counts:
                counts[asset] += 1

        for asset in _safe_asset_list(scene.get("asset_list")):
            if asset in counts:
                counts[asset] += 1

    return counts


def _build_planning_statistics(
    scenes: tuple[dict[str, Any], ...],
    asset_counts: dict[str, int],
) -> dict[str, Any]:
    """
    Purpose:
    Compute deterministic planning statistics from scenes and asset counts.

    Arguments:
    scenes: visual plan scenes
    asset_counts: estimated asset category counts

    Returns:
    planning statistics dictionary
    """
    durations = [_scene_duration(scene) for scene in scenes]
    total_duration = round(sum(durations), 2)
    total_assets = sum(asset_counts.values())

    return {
        "scene_count": len(scenes),
        "total_duration": total_duration,
        "average_scene_duration": _average(durations),
        "total_estimated_assets": total_assets,
        "unique_asset_categories": sum(1 for count in asset_counts.values() if count > 0),
        "timed_scene_count": sum(1 for duration in durations if duration > 0),
        "fallback_scene_count": sum(
            1
            for scene in scenes
            if _safe_text(scene.get("visual_focus")) == "source_supported_context"
        ),
    }


def _estimate_render_complexity(planning_statistics: dict[str, Any]) -> str:
    """
    Purpose:
    Estimate deterministic render complexity from planning statistics.

    Arguments:
    planning_statistics: computed planning statistics

    Returns:
    render complexity label
    """
    scene_count = planning_statistics.get("scene_count", 0)
    asset_count = planning_statistics.get("total_estimated_assets", 0)

    if scene_count <= LOW_COMPLEXITY_SCENE_LIMIT and asset_count <= LOW_COMPLEXITY_ASSET_LIMIT:
        return "low"

    if (
        scene_count <= MEDIUM_COMPLEXITY_SCENE_LIMIT
        and asset_count <= MEDIUM_COMPLEXITY_ASSET_LIMIT
    ):
        return "medium"

    return "high"


def _scene_duration(scene: dict[str, Any]) -> float:
    """
    Purpose:
    Compute deterministic scene duration when timing exists.

    Arguments:
    scene: visual plan scene

    Returns:
    non-negative scene duration
    """
    start_time = scene.get("start_time")
    end_time = scene.get("end_time")

    if not isinstance(start_time, (int, float)) or not isinstance(end_time, (int, float)):
        return 0.0

    return round(max(0.0, float(end_time) - float(start_time)), 2)


def _average(values: list[float]) -> float:
    """
    Purpose:
    Compute deterministic average for numeric values.

    Arguments:
    values: numeric values

    Returns:
    rounded average or zero
    """
    if not values:
        return 0.0

    return round(sum(values) / len(values), 2)


def _safe_asset_list(value: Any) -> tuple[str, ...]:
    """
    Purpose:
    Safely preserve asset category lists from scene data.

    Arguments:
    value: candidate asset list

    Returns:
    immutable tuple of asset category strings
    """
    if not isinstance(value, list):
        return ()

    return tuple(item for item in value if isinstance(item, str))


def _safe_mapping(value: Any) -> dict[str, Any]:
    """
    Purpose:
    Safely preserve dictionary metadata.

    Arguments:
    value: candidate mapping

    Returns:
    mapping value or empty dictionary
    """
    return value if isinstance(value, dict) else {}


def _safe_text(value: Any) -> str:
    """
    Purpose:
    Safely preserve text values.

    Arguments:
    value: candidate text

    Returns:
    stripped text or empty string
    """
    return value.strip() if isinstance(value, str) else ""


def _sample_record() -> dict[str, Any]:
    """
    Purpose:
    Build a sample Visual Plan result for deterministic self-tests.

    Arguments:
    None

    Returns:
    sample Visual Plan result
    """
    return {
        "trend_id": "trend_001",
        "metadata": {"source": "visual_planning"},
        "generation_source": "fallback",
        "fallback_used": True,
        "visual_plan": [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 3.0,
                "narration_segment": "The story is gaining attention.",
                "shot_type": "establishing_shot",
                "camera_movement": "static",
                "visual_focus": "source_supported_context",
                "asset_requirement": "text_card",
                "transition_type": "none",
            },
            {
                "scene_id": 2,
                "start_time": 3.0,
                "end_time": 6.0,
                "narration_segment": "Fans are watching closely.",
                "shot_type": "close_up",
                "camera_movement": "static",
                "visual_focus": "source_supported_context",
                "asset_requirement": "overlay_graphic",
                "transition_type": "cut",
            },
        ],
    }


def _self_test_single_blueprint() -> bool:
    """
    Purpose:
    Verify one Asset Blueprint is built deterministically.

    Arguments:
    None

    Returns:
    self-test result
    """
    blueprint = build_asset_blueprint(_sample_record())
    asset_blueprint = blueprint["asset_blueprint"]
    return (
        blueprint["trend_id"] == "trend_001"
        and asset_blueprint["asset_counts"]["text_card"] == 1
        and asset_blueprint["asset_counts"]["overlay_graphic"] == 1
        and asset_blueprint["planning_statistics"]["scene_count"] == 2
    )


def _self_test_batch_processing() -> bool:
    """
    Purpose:
    Verify batch processing returns immutable blueprint results.

    Arguments:
    None

    Returns:
    self-test result
    """
    blueprints = build_asset_blueprints((_sample_record(), _sample_record()))
    return isinstance(blueprints, tuple) and len(blueprints) == 2


def _self_test_empty_plan() -> bool:
    """
    Purpose:
    Verify empty visual plans produce zeroed statistics.

    Arguments:
    None

    Returns:
    self-test result
    """
    blueprint = build_asset_blueprint(
        {
            "trend_id": "empty",
            "metadata": {},
            "generation_source": "fallback",
            "fallback_used": True,
            "visual_plan": [],
        }
    )
    statistics = blueprint["asset_blueprint"]["planning_statistics"]
    return statistics["scene_count"] == 0 and statistics["total_estimated_assets"] == 0


def _run_self_tests() -> bool:
    """
    Purpose:
    Run deterministic Asset Mapper self-tests.

    Arguments:
    None

    Returns:
    aggregate self-test result
    """
    tests = (
        _self_test_single_blueprint(),
        _self_test_batch_processing(),
        _self_test_empty_plan(),
    )
    return all(tests)


if __name__ == "__main__":
    print("PASS" if _run_self_tests() else "FAIL")
