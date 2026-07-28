"""
Purpose:
Plan shot-by-shot visuals from validated Visual Blueprints.

Input:
one validated Visual Blueprint record or a sequence of records

Output:
structured Visual Plan dictionaries for downstream validation
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from typing import Any

try:
    from scripts.ai.groq_client import request_json
    from scripts.visual_planning.visual_constitution import (
        get_asset_categories,
        get_camera_movements,
        get_quality_targets,
        get_scene_rules,
        get_shot_types,
        get_transition_types,
        get_visual_styles,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution support
    from visual_constitution import (
        get_asset_categories,
        get_camera_movements,
        get_quality_targets,
        get_scene_rules,
        get_shot_types,
        get_transition_types,
        get_visual_styles,
    )

    request_json = None


GROQ_GENERATION_SOURCE = "groq"
FALLBACK_GENERATION_SOURCE = "fallback"
VISUAL_PLAN_FIELD = "visual_plan"
DEFAULT_SCENE_COUNT = 3

_GroqRequester = Callable[[str], dict[str, Any]]
_groq_requester: _GroqRequester | None = request_json

__all__ = ("plan_visuals", "plan_visuals_batch")


def plan_visuals(record: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Plan visuals for one validated Visual Blueprint record.

    Arguments:
    record: validated Visual Blueprint record

    Returns:
    visual planning dictionary
    """
    if not _has_required_input(record):
        return _build_fallback_plan(record)

    try:
        prompt = _build_prompt(record)
        response = _call_groq(prompt)

        if not _validate_basic_response(response):
            return _build_fallback_plan(record)

        return {
            "trend_id": _safe_text(record.get("trend_id")),
            "visual_plan": response[VISUAL_PLAN_FIELD],
            "generation_source": GROQ_GENERATION_SOURCE,
            "fallback_used": False,
        }
    except Exception:
        return _build_fallback_plan(record)


def plan_visuals_batch(
    records: Iterable[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """
    Purpose:
    Plan visuals for multiple validated Visual Blueprint records.

    Arguments:
    records: iterable of validated Visual Blueprint records

    Returns:
    immutable tuple of visual planning dictionaries
    """
    if not isinstance(records, Iterable) or isinstance(records, (str, bytes)):
        return (plan_visuals(records),)

    return tuple(plan_visuals(record) for record in records)


def _build_prompt(record: dict[str, Any]) -> str:
    """
    Purpose:
    Build the Visual Planner prompt from constitution vocabularies.

    Arguments:
    record: validated Visual Blueprint record

    Returns:
    prompt string
    """
    payload = {
        "trend_id": _safe_text(record.get("trend_id")),
        "voice_script": _safe_text(record.get("voice_script")),
        "visual_blueprint": _safe_mapping(record.get("visual_blueprint")),
        "metadata": _safe_mapping(record.get("metadata")),
    }
    constitution = {
        "shot_types": get_shot_types(),
        "camera_movements": get_camera_movements(),
        "visual_styles": get_visual_styles(),
        "scene_rules": get_scene_rules(),
        "asset_categories": get_asset_categories(),
        "transition_types": get_transition_types(),
        "quality_targets": dict(get_quality_targets()),
    }

    return (
        "You are the ARKY Visual Planning Engine.\n"
        "Plan visuals only. Never rewrite narration.\n"
        "Use only the provided input and constitution vocabularies.\n"
        "Never invent facts, characters, locations, evidence, quotes, or events.\n"
        "Every scene must support the narration without adding meaning.\n"
        "Return JSON only. Do not include markdown or explanations.\n\n"
        "Return exactly this schema:\n"
        '{"visual_plan": [{"scene_id": 1, "start_time": 0.0, '
        '"end_time": 3.0, "narration_segment": "text", '
        '"shot_type": "constitution value", '
        '"camera_movement": "constitution value", '
        '"visual_focus": "source-supported focus", '
        '"asset_requirement": "constitution value", '
        '"transition_type": "constitution value"}]}\n\n'
        "Constitution:\n"
        f"{json.dumps(constitution, ensure_ascii=True, sort_keys=True)}\n\n"
        "Input:\n"
        f"{json.dumps(payload, ensure_ascii=True, sort_keys=True)}"
    )


def _call_groq(prompt: str) -> dict[str, Any]:
    """
    Purpose:
    Call the shared Groq JSON client.

    Arguments:
    prompt: visual planning prompt

    Returns:
    parsed JSON response
    """
    if _groq_requester is None:
        raise RuntimeError("Groq requester is unavailable.")

    return _groq_requester(prompt)


def _validate_basic_response(response: dict[str, Any]) -> bool:
    """
    Purpose:
    Check basic AI response shape before downstream validation.

    Arguments:
    response: parsed AI response

    Returns:
    response usability flag
    """
    if not isinstance(response, dict):
        return False

    visual_plan = response.get(VISUAL_PLAN_FIELD)

    if not isinstance(visual_plan, list) or not visual_plan:
        return False

    return all(_is_basic_scene(scene) for scene in visual_plan)


def _build_fallback_plan(record: dict[str, Any] | None) -> dict[str, Any]:
    """
    Purpose:
    Build deterministic visual fallback plan.

    Arguments:
    record: optional validated Visual Blueprint record

    Returns:
    fallback visual planning dictionary
    """
    voice_script = _safe_text(record.get("voice_script")) if isinstance(record, dict) else ""
    blueprint = _safe_mapping(record.get("visual_blueprint")) if isinstance(record, dict) else {}
    scene_count = _fallback_scene_count(blueprint, voice_script)
    segments = _split_narration(voice_script, scene_count)
    duration = _fallback_duration(blueprint, scene_count)
    scene_duration = duration / scene_count if scene_count else 0
    visual_plan = []

    for index, segment in enumerate(segments, start=1):
        start_time = round((index - 1) * scene_duration, 2)
        end_time = round(index * scene_duration, 2)
        visual_plan.append(
            {
                "scene_id": index,
                "start_time": start_time,
                "end_time": end_time,
                "narration_segment": segment,
                "shot_type": _fallback_shot_type(index),
                "camera_movement": "static",
                "visual_focus": "source_supported_context",
                "asset_requirement": "text_card",
                "transition_type": _fallback_transition(index),
            }
        )

    return {
        "trend_id": _safe_text(record.get("trend_id")) if isinstance(record, dict) else "",
        "visual_plan": visual_plan,
        "generation_source": FALLBACK_GENERATION_SOURCE,
        "fallback_used": True,
    }


def _has_required_input(record: Any) -> bool:
    """
    Purpose:
    Check minimum input needed for visual planning.

    Arguments:
    record: candidate Visual Blueprint record

    Returns:
    required input flag
    """
    if not isinstance(record, dict):
        return False

    return bool(
        _safe_text(record.get("trend_id"))
        and _safe_text(record.get("voice_script"))
        and isinstance(record.get("visual_blueprint"), dict)
        and isinstance(record.get("metadata"), dict)
    )


def _is_basic_scene(scene: Any) -> bool:
    """
    Purpose:
    Check basic scene object shape.

    Arguments:
    scene: candidate scene object

    Returns:
    basic scene validity flag
    """
    required_fields = {
        "scene_id",
        "start_time",
        "end_time",
        "narration_segment",
        "shot_type",
        "camera_movement",
        "visual_focus",
        "asset_requirement",
        "transition_type",
    }

    if not isinstance(scene, dict) or not required_fields <= set(scene):
        return False

    return (
        isinstance(scene["scene_id"], int)
        and isinstance(scene["narration_segment"], str)
        and isinstance(scene["visual_focus"], str)
        and scene["shot_type"] in get_shot_types()
        and scene["camera_movement"] in get_camera_movements()
        and scene["asset_requirement"] in get_asset_categories()
        and scene["transition_type"] in get_transition_types()
    )


def _safe_text(value: Any) -> str:
    """
    Purpose:
    Safely normalize text fields.

    Arguments:
    value: source value

    Returns:
    stripped text or empty string
    """
    return value.strip() if isinstance(value, str) else ""


def _safe_mapping(value: Any) -> dict[str, Any]:
    """
    Purpose:
    Safely normalize mapping values.

    Arguments:
    value: source value

    Returns:
    mapping or empty dictionary
    """
    return value if isinstance(value, dict) else {}


def _fallback_scene_count(blueprint: dict[str, Any], voice_script: str) -> int:
    """
    Purpose:
    Determine deterministic fallback scene count.

    Arguments:
    blueprint: visual blueprint metadata
    voice_script: narration text

    Returns:
    fallback scene count
    """
    if not voice_script:
        return 0

    scene_count = blueprint.get("estimated_scene_count")

    if isinstance(scene_count, int) and scene_count > 0:
        return scene_count

    return DEFAULT_SCENE_COUNT


def _fallback_duration(blueprint: dict[str, Any], scene_count: int) -> float:
    """
    Purpose:
    Determine deterministic fallback duration.

    Arguments:
    blueprint: visual blueprint metadata
    scene_count: fallback scene count

    Returns:
    fallback duration in seconds
    """
    duration = blueprint.get("estimated_duration")

    if isinstance(duration, (int, float)) and duration > 0:
        return float(duration)

    return float(scene_count * get_quality_targets()["preferred_scene_duration_seconds"][0])


def _split_narration(voice_script: str, scene_count: int) -> tuple[str, ...]:
    """
    Purpose:
    Split narration into deterministic fallback scene segments.

    Arguments:
    voice_script: narration text
    scene_count: target scene count

    Returns:
    narration segments
    """
    if scene_count <= 0:
        return ()

    sentences = [
        sentence.strip()
        for sentence in voice_script.replace("?", ".").replace("!", ".").split(".")
        if sentence.strip()
    ]

    if not sentences:
        return tuple("" for _ in range(scene_count))

    if len(sentences) >= scene_count:
        leading = sentences[: scene_count - 1]
        trailing = " ".join(sentences[scene_count - 1 :])
        return tuple(leading + [trailing])

    return tuple(sentences + [sentences[-1]] * (scene_count - len(sentences)))


def _fallback_shot_type(scene_index: int) -> str:
    """
    Purpose:
    Select deterministic fallback shot type.

    Arguments:
    scene_index: one-based scene index

    Returns:
    shot type from constitution
    """
    shot_types = get_shot_types()
    return shot_types[(scene_index - 1) % len(shot_types)]


def _fallback_transition(scene_index: int) -> str:
    """
    Purpose:
    Select deterministic fallback transition.

    Arguments:
    scene_index: one-based scene index

    Returns:
    transition type from constitution
    """
    return "none" if scene_index == 1 else "cut"


def _sample_record() -> dict[str, Any]:
    """
    Purpose:
    Build sample Visual Blueprint record for self-tests.

    Arguments:
    None

    Returns:
    sample record
    """
    return {
        "trend_id": "trend_001",
        "voice_script": "The story is gaining attention. Fans are watching closely.",
        "generation_source": "groq",
        "metadata": {"source": "creator_voice"},
        "visual_blueprint": {
            "estimated_duration": 6,
            "estimated_scene_count": 3,
            "word_count": 9,
            "sentence_count": 2,
            "pacing": "light",
            "scene_strategy": "sentence_aligned_visual_beats",
            "default_visual_style": get_visual_styles()[0],
        },
    }


def _with_stubbed_groq(
    stub: _GroqRequester | None,
    test: Callable[[], bool],
) -> bool:
    """
    Purpose:
    Run a self-test with a temporary Groq requester.

    Arguments:
    stub: temporary requester function
    test: self-test callable

    Returns:
    self-test result
    """
    global _groq_requester

    original_requester = _groq_requester
    _groq_requester = stub

    try:
        return test()
    finally:
        _groq_requester = original_requester


def _valid_ai_response() -> dict[str, Any]:
    """
    Purpose:
    Build valid mocked AI visual plan response.

    Arguments:
    None

    Returns:
    mocked AI response
    """
    return {
        "visual_plan": [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 3.0,
                "narration_segment": "The story is gaining attention.",
                "shot_type": "headline_card",
                "camera_movement": "static",
                "visual_focus": "source_supported_context",
                "asset_requirement": "text_card",
                "transition_type": "none",
            }
        ]
    }


def _test_valid_planning() -> bool:
    """
    Purpose:
    Verify valid mocked AI planning.

    Arguments:
    None

    Returns:
    test result
    """
    return _with_stubbed_groq(
        lambda prompt: _valid_ai_response(),
        lambda: plan_visuals(_sample_record())["generation_source"] == GROQ_GENERATION_SOURCE,
    )


def _test_timeout() -> bool:
    """
    Purpose:
    Verify timeout-like exception falls back.

    Arguments:
    None

    Returns:
    test result
    """
    def raise_timeout(prompt: str) -> dict[str, Any]:
        raise TimeoutError("timeout")

    return _with_stubbed_groq(
        raise_timeout,
        lambda: plan_visuals(_sample_record())["fallback_used"] is True,
    )


def _test_empty_response() -> bool:
    """
    Purpose:
    Verify empty AI response falls back.

    Arguments:
    None

    Returns:
    test result
    """
    return _with_stubbed_groq(
        lambda prompt: {},
        lambda: plan_visuals(_sample_record())["generation_source"]
        == FALLBACK_GENERATION_SOURCE,
    )


def _test_invalid_schema() -> bool:
    """
    Purpose:
    Verify invalid AI schema falls back.

    Arguments:
    None

    Returns:
    test result
    """
    return _with_stubbed_groq(
        lambda prompt: {"visual_plan": [{"shot_type": "bad"}]},
        lambda: plan_visuals(_sample_record())["fallback_used"] is True,
    )


def _test_missing_narration() -> bool:
    """
    Purpose:
    Verify missing narration falls back.

    Arguments:
    None

    Returns:
    test result
    """
    record = _sample_record()
    record.pop("voice_script")
    result = plan_visuals(record)
    return result["fallback_used"] is True and result["visual_plan"] == []


def _test_fallback() -> bool:
    """
    Purpose:
    Verify deterministic fallback contains scenes.

    Arguments:
    None

    Returns:
    test result
    """
    return _with_stubbed_groq(
        None,
        lambda: len(plan_visuals(_sample_record())["visual_plan"]) == 3,
    )


def _run_self_tests() -> bool:
    """
    Purpose:
    Run deterministic Visual Planner self-tests.

    Arguments:
    None

    Returns:
    aggregate test result
    """
    tests = (
        _test_valid_planning(),
        _test_timeout(),
        _test_empty_response(),
        _test_invalid_schema(),
        _test_missing_narration(),
        _test_fallback(),
    )
    return all(tests)


if __name__ == "__main__":
    print("PASS" if _run_self_tests() else "FAIL")
