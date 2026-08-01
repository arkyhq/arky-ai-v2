"""
Purpose:
Plan asset manifests from validated Asset Blueprints.

Input:
one validated Asset Blueprint or a sequence of Asset Blueprints

Output:
Asset Manifest dictionaries for downstream asset generation and rendering
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from typing import Any

try:
    from scripts.ai.groq_client import request_json
    from scripts.asset_planning.asset_constitution import (
        get_asset_categories,
        get_background_categories,
        get_broll_categories,
        get_character_categories,
        get_color_palette,
        get_icon_vocabulary,
        get_logo_rules,
        get_music_categories,
        get_overlay_types,
        get_prompt_templates,
        get_render_constraints,
        get_sfx_categories,
        get_typography,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution support
    from asset_constitution import (
        get_asset_categories,
        get_background_categories,
        get_broll_categories,
        get_character_categories,
        get_color_palette,
        get_icon_vocabulary,
        get_logo_rules,
        get_music_categories,
        get_overlay_types,
        get_prompt_templates,
        get_render_constraints,
        get_sfx_categories,
        get_typography,
    )

    request_json = None


MANIFEST_FIELD = "asset_manifest"
GROQ_GENERATION_SOURCE = "groq"
FALLBACK_GENERATION_SOURCE = "fallback"
DEFAULT_ASSET_CONFIDENCE = 0.75

_GroqRequester = Callable[[str], dict[str, Any]]
_groq_requester: _GroqRequester | None = request_json

__all__ = ("plan_assets", "plan_assets_batch")


def plan_assets(asset_blueprint: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Convert one validated Asset Blueprint into an Asset Manifest.

    Arguments:
    asset_blueprint: validated Asset Blueprint dictionary

    Returns:
    Asset Manifest result dictionary
    """
    if not _has_required_input(asset_blueprint):
        return _build_fallback_manifest(asset_blueprint)

    try:
        prompt = _build_prompt(asset_blueprint)
        response = _call_groq(prompt)

        if not _basic_manifest_check(response):
            return _build_fallback_manifest(asset_blueprint)

        return {
            "trend_id": _safe_text(asset_blueprint.get("trend_id")),
            "asset_manifest": response[MANIFEST_FIELD],
            "generation_source": GROQ_GENERATION_SOURCE,
            "fallback_used": False,
        }
    except Exception:
        return _build_fallback_manifest(asset_blueprint)


def plan_assets_batch(
    asset_blueprints: Iterable[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """
    Purpose:
    Convert multiple Asset Blueprints into Asset Manifest results.

    Arguments:
    asset_blueprints: iterable of validated Asset Blueprint dictionaries

    Returns:
    immutable tuple of Asset Manifest result dictionaries
    """
    if not isinstance(asset_blueprints, Iterable) or isinstance(asset_blueprints, (str, bytes)):
        return (plan_assets(asset_blueprints),)

    return tuple(plan_assets(asset_blueprint) for asset_blueprint in asset_blueprints)


def _build_prompt(asset_blueprint: dict[str, Any]) -> str:
    """
    Purpose:
    Build the Asset Planner prompt from approved constitution values.

    Arguments:
    asset_blueprint: validated Asset Blueprint dictionary

    Returns:
    prompt string
    """
    constitution = {
        "asset_categories": get_asset_categories(),
        "character_categories": get_character_categories(),
        "background_categories": get_background_categories(),
        "broll_categories": get_broll_categories(),
        "overlay_types": get_overlay_types(),
        "icon_vocabulary": get_icon_vocabulary(),
        "logo_rules": get_logo_rules(),
        "music_categories": get_music_categories(),
        "sfx_categories": get_sfx_categories(),
        "color_palette": dict(get_color_palette()),
        "typography": dict(get_typography()),
        "prompt_templates": dict(get_prompt_templates()),
        "render_constraints": dict(get_render_constraints()),
    }

    return (
        "You are the ARKY Asset Planning Engine.\n"
        "Plan asset requirements only. Do not generate images, video, audio, "
        "or rendered output.\n"
        "Use only the approved constitution vocabularies.\n"
        "Never invent unsupported categories, facts, entities, locations, "
        "logos, or evidence.\n"
        "Return JSON only with exactly this top-level schema:\n"
        '{"asset_manifest": {"asset_manifest_id": "string", '
        '"source_visual_plan_id": "string", "trend_id": "string", '
        '"assets": [], "required_assets": [], "optional_assets": [], '
        '"music_requirements": [], "sfx_requirements": [], '
        '"render_constraints": {}, "rights_notes": [], '
        '"continuity_notes": [], "render_hints": [], '
        '"fallback_used": false, "asset_confidence": 0.0}}\n\n'
        "Constitution:\n"
        f"{json.dumps(constitution, ensure_ascii=True, sort_keys=True)}\n\n"
        "Validated Asset Blueprint:\n"
        f"{json.dumps(asset_blueprint, ensure_ascii=True, sort_keys=True)}"
    )


def _call_groq(prompt: str) -> dict[str, Any]:
    """
    Purpose:
    Call the shared Groq JSON client.

    Arguments:
    prompt: Asset Planner prompt

    Returns:
    parsed JSON response dictionary
    """
    if _groq_requester is None:
        raise RuntimeError("Groq requester is unavailable.")

    return _groq_requester(prompt)


def _basic_manifest_check(response: dict[str, Any]) -> bool:
    """
    Purpose:
    Check only basic Asset Manifest structure before downstream validation.

    Arguments:
    response: parsed AI response dictionary

    Returns:
    manifest usability flag
    """
    if not isinstance(response, dict):
        return False

    manifest = response.get(MANIFEST_FIELD)

    if not isinstance(manifest, dict):
        return False

    required_fields = {
        "asset_manifest_id",
        "source_visual_plan_id",
        "trend_id",
        "assets",
        "required_assets",
        "optional_assets",
        "music_requirements",
        "sfx_requirements",
        "render_constraints",
        "rights_notes",
        "fallback_used",
        "asset_confidence",
    }

    return required_fields <= set(manifest)


def _build_fallback_manifest(asset_blueprint: dict[str, Any] | None) -> dict[str, Any]:
    """
    Purpose:
    Build a deterministic constitution-compliant Asset Manifest.

    Arguments:
    asset_blueprint: optional validated Asset Blueprint dictionary

    Returns:
    fallback Asset Manifest result dictionary
    """
    trend_id = _safe_text(asset_blueprint.get("trend_id")) if isinstance(asset_blueprint, dict) else ""
    blueprint_body = _safe_mapping(asset_blueprint.get("asset_blueprint")) if isinstance(
        asset_blueprint,
        dict,
    ) else {}
    asset_counts = _safe_mapping(blueprint_body.get("asset_counts"))
    visual_plan = _safe_scenes(asset_blueprint)
    required_assets = _build_required_assets(asset_counts, visual_plan)
    manifest = {
        "asset_manifest_id": _manifest_id(trend_id),
        "source_visual_plan_id": trend_id,
        "trend_id": trend_id,
        "assets": required_assets,
        "required_assets": required_assets,
        "optional_assets": _build_optional_assets(visual_plan),
        "music_requirements": [_music_requirement()],
        "sfx_requirements": _build_sfx_requirements(visual_plan),
        "render_constraints": dict(get_render_constraints()),
        "rights_notes": tuple(get_logo_rules()),
        "continuity_notes": _build_continuity_notes(visual_plan),
        "render_hints": _build_render_hints(blueprint_body),
        "fallback_used": True,
        "asset_confidence": DEFAULT_ASSET_CONFIDENCE,
    }

    return {
        "trend_id": trend_id,
        "asset_manifest": manifest,
        "generation_source": FALLBACK_GENERATION_SOURCE,
        "fallback_used": True,
    }


def _build_required_assets(
    asset_counts: dict[str, Any],
    visual_plan: tuple[dict[str, Any], ...],
) -> list[dict[str, Any]]:
    """
    Purpose:
    Build deterministic required asset entries from asset counts and scenes.

    Arguments:
    asset_counts: estimated asset counts from Asset Blueprint
    visual_plan: preserved visual scenes

    Returns:
    required asset dictionaries
    """
    required_assets: list[dict[str, Any]] = []
    approved_categories = set(get_asset_categories())

    for category, count in asset_counts.items():
        if category in approved_categories and isinstance(count, int) and count > 0:
            required_assets.append(
                {
                    "asset_id": f"{category}_{len(required_assets) + 1}",
                    "category": category,
                    "quantity": count,
                    "prompt_template": _prompt_template_for_category(category),
                }
            )

    if not required_assets and visual_plan:
        required_assets.append(
            {
                "asset_id": "text_card_1",
                "category": "text_card",
                "quantity": len(visual_plan),
                "prompt_template": get_prompt_templates()["overlay_asset"],
            }
        )

    return required_assets


def _build_optional_assets(visual_plan: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    """
    Purpose:
    Build deterministic optional asset requirements.

    Arguments:
    visual_plan: preserved visual scenes

    Returns:
    optional asset dictionaries
    """
    if not visual_plan:
        return []

    return [
        {
            "asset_id": "icon_support_1",
            "category": "icon",
            "quantity": min(len(visual_plan), 3),
            "approved_icons": get_icon_vocabulary()[:3],
        }
    ]


def _music_requirement() -> dict[str, str]:
    """
    Purpose:
    Build deterministic music requirement.

    Arguments:
    None

    Returns:
    music requirement dictionary
    """
    return {
        "category": "subtle_news_bed",
        "usage": "background_music",
    }


def _build_sfx_requirements(visual_plan: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    """
    Purpose:
    Build deterministic sound effect requirements.

    Arguments:
    visual_plan: preserved visual scenes

    Returns:
    sound effect requirement dictionaries
    """
    if len(visual_plan) <= 1:
        return [{"category": "none", "usage": "no_scene_transition_sfx"}]

    return [
        {
            "category": "soft_whoosh",
            "usage": "scene_transition",
        }
    ]


def _build_continuity_notes(visual_plan: tuple[dict[str, Any], ...]) -> list[str]:
    """
    Purpose:
    Build deterministic continuity notes.

    Arguments:
    visual_plan: preserved visual scenes

    Returns:
    continuity note strings
    """
    if not visual_plan:
        return ["No visual scenes were provided."]

    return [
        "Preserve narration order across all asset requirements.",
        "Keep visual tone consistent across scenes.",
        "Do not add entities, locations, or claims beyond the visual plan.",
    ]


def _build_render_hints(blueprint_body: dict[str, Any]) -> list[str]:
    """
    Purpose:
    Build deterministic render hints from blueprint complexity.

    Arguments:
    blueprint_body: nested asset_blueprint dictionary

    Returns:
    render hint strings
    """
    complexity = _safe_text(blueprint_body.get("render_complexity")) or "low"
    palette = get_color_palette()
    typography = get_typography()

    return [
        f"Render complexity: {complexity}.",
        f"Use {palette['background']} as the default background-safe color.",
        f"Use {typography['primary_font']} for primary text assets.",
    ]


def _prompt_template_for_category(category: str) -> str:
    """
    Purpose:
    Select a deterministic prompt template for an approved asset category.

    Arguments:
    category: approved asset category

    Returns:
    prompt template fragment
    """
    templates = get_prompt_templates()

    if category in {"music_bed", "sound_effect"}:
        return templates["audio_asset"]

    if category in {"overlay_graphic", "text_card", "icon", "logo"}:
        return templates["overlay_asset"]

    return templates["image_asset"]


def _has_required_input(value: Any) -> bool:
    """
    Purpose:
    Check minimum input required for asset planning.

    Arguments:
    value: candidate Asset Blueprint

    Returns:
    required input flag
    """
    return (
        isinstance(value, dict)
        and isinstance(value.get("asset_blueprint"), dict)
        and isinstance(value.get("visual_plan"), tuple)
        and bool(_safe_text(value.get("trend_id")))
    )


def _safe_mapping(value: Any) -> dict[str, Any]:
    """
    Purpose:
    Safely preserve dictionary values.

    Arguments:
    value: candidate mapping

    Returns:
    mapping value or empty dictionary
    """
    return value if isinstance(value, dict) else {}


def _safe_scenes(asset_blueprint: dict[str, Any] | None) -> tuple[dict[str, Any], ...]:
    """
    Purpose:
    Safely preserve visual plan scene dictionaries.

    Arguments:
    asset_blueprint: candidate Asset Blueprint

    Returns:
    immutable tuple of visual scene dictionaries
    """
    if not isinstance(asset_blueprint, dict):
        return ()

    visual_plan = asset_blueprint.get("visual_plan")

    if not isinstance(visual_plan, tuple):
        return ()

    return tuple(scene for scene in visual_plan if isinstance(scene, dict))


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


def _manifest_id(trend_id: str) -> str:
    """
    Purpose:
    Build deterministic Asset Manifest identifier.

    Arguments:
    trend_id: trend identifier

    Returns:
    asset manifest identifier
    """
    return f"asset_manifest_{trend_id or 'unknown'}"


def _sample_blueprint() -> dict[str, Any]:
    """
    Purpose:
    Build a sample validated Asset Blueprint for self-tests.

    Arguments:
    None

    Returns:
    sample Asset Blueprint dictionary
    """
    return {
        "trend_id": "trend_001",
        "metadata": {"source": "asset_mapper"},
        "generation_source": "fallback",
        "fallback_used": True,
        "visual_plan": (
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 3.0,
                "narration_segment": "The story is gaining attention.",
                "asset_requirement": "text_card",
            },
        ),
        "asset_blueprint": {
            "asset_counts": {
                "text_card": 1,
                "overlay_graphic": 1,
            },
            "render_complexity": "low",
        },
    }


def _with_stubbed_groq(
    stub: _GroqRequester | None,
    test: Callable[[], bool],
) -> bool:
    """
    Purpose:
    Run a self-test with a temporary Groq requester stub.

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
    Build a valid mocked AI Asset Manifest response.

    Arguments:
    None

    Returns:
    mocked AI response dictionary
    """
    fallback_manifest = _build_fallback_manifest(_sample_blueprint())["asset_manifest"]
    fallback_manifest["fallback_used"] = False
    return {"asset_manifest": fallback_manifest}


def _self_test_ai_success() -> bool:
    """
    Purpose:
    Verify mocked AI planning path returns Groq source.

    Arguments:
    None

    Returns:
    self-test result
    """
    return _with_stubbed_groq(
        lambda prompt: _valid_ai_response(),
        lambda: plan_assets(_sample_blueprint())["generation_source"] == GROQ_GENERATION_SOURCE,
    )


def _self_test_empty_response_fallback() -> bool:
    """
    Purpose:
    Verify empty AI response uses deterministic fallback.

    Arguments:
    None

    Returns:
    self-test result
    """
    return _with_stubbed_groq(
        lambda prompt: {},
        lambda: plan_assets(_sample_blueprint())["fallback_used"] is True,
    )


def _self_test_exception_fallback() -> bool:
    """
    Purpose:
    Verify AI exceptions use deterministic fallback.

    Arguments:
    None

    Returns:
    self-test result
    """
    def raise_error(prompt: str) -> dict[str, Any]:
        raise RuntimeError("mock failure")

    return _with_stubbed_groq(
        raise_error,
        lambda: plan_assets(_sample_blueprint())["generation_source"]
        == FALLBACK_GENERATION_SOURCE,
    )


def _self_test_batch() -> bool:
    """
    Purpose:
    Verify batch planning returns immutable results.

    Arguments:
    None

    Returns:
    self-test result
    """
    results = plan_assets_batch((_sample_blueprint(), _sample_blueprint()))
    return isinstance(results, tuple) and len(results) == 2


def _run_self_tests() -> bool:
    """
    Purpose:
    Run deterministic Asset Planner self-tests.

    Arguments:
    None

    Returns:
    aggregate self-test result
    """
    tests = (
        _self_test_ai_success(),
        _self_test_empty_response_fallback(),
        _self_test_exception_fallback(),
        _self_test_batch(),
    )
    return all(tests)


if __name__ == "__main__":
    print("PASS" if _run_self_tests() else "FAIL")
