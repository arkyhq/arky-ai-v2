"""
Purpose:
Define the immutable Visual Planning Engine constitution.

Input:
module imports from Visual Planning components

Output:
visual planning constants, vocabularies, schema definitions, and accessors
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any


ENGINE_NAME = "ARKY Visual Planning Engine"
ENGINE_VERSION = "0.7"
ENGINE_DESCRIPTION = (
    "A deterministic visual planning layer that converts approved narration "
    "and strategy data into structured scene planning guidance without "
    "selecting assets or generating media."
)

SHOT_TYPES = (
    "establishing_shot",
    "close_up",
    "medium_shot",
    "wide_shot",
    "reaction_shot",
    "detail_shot",
    "screen_capture",
    "headline_card",
    "context_card",
    "timeline_card",
    "comparison_card",
    "proof_card",
    "texture_b_roll",
)

CAMERA_MOVEMENTS = (
    "static",
    "slow_push_in",
    "slow_pull_out",
    "pan_left",
    "pan_right",
    "tilt_up",
    "tilt_down",
    "subtle_zoom",
    "handheld_light",
    "parallax",
)

VISUAL_STYLES = (
    "clear_entertainment_news",
    "clean_pop_culture_context",
    "mobile_first_vertical",
    "high_contrast_readability",
    "fast_but_readable",
    "evidence_forward",
    "emotionally_restrained",
    "platform_native",
)

SCENE_RULES = (
    "Preserve narration meaning exactly.",
    "Support the script without adding facts.",
    "Use visuals to clarify, not reinterpret.",
    "Keep chronology aligned with narration order.",
    "Avoid implying unsupported conflict.",
    "Avoid visual exaggeration for high-risk stories.",
    "Prefer readable visual beats for short-form pacing.",
    "Use neutral context visuals when evidence is limited.",
    "Never create visual claims not present in source material.",
)

ASSET_CATEGORIES = (
    "licensed_image",
    "licensed_video",
    "public_domain_media",
    "creator_provided_media",
    "platform_screenshot",
    "headline_graphic",
    "text_card",
    "abstract_background",
    "brand_safe_b_roll",
    "generated_graphic",
)

TRANSITION_TYPES = (
    "cut",
    "soft_cut",
    "match_cut",
    "push",
    "swipe",
    "fade",
    "quick_flash",
    "text_reveal",
    "timeline_step",
    "none",
)

FORBIDDEN_VISUAL_BEHAVIORS = (
    "Invented evidence.",
    "Fabricated screenshots.",
    "Fake quotes.",
    "Fake documents.",
    "Misleading thumbnails.",
    "Unverified allegations shown as fact.",
    "Graphic shock imagery.",
    "Harassment framing.",
    "Defamatory visual implication.",
    "Unsafe medical, legal, or financial claims.",
    "Visuals that contradict narration.",
    "Visuals that change chronology.",
    "Watermarked stolen media.",
    "Low-resolution unreadable text.",
)

QUALITY_TARGETS = MappingProxyType(
    {
        "aspect_ratio": "9:16",
        "minimum_scene_count": 3,
        "maximum_scene_count": 12,
        "preferred_scene_duration_seconds": (2.0, 5.0),
        "maximum_text_card_words": 12,
        "readability_priority": "high",
        "brand_safety_priority": "high",
        "visual_accuracy_priority": "highest",
        "motion_intensity": "moderate",
        "evidence_threshold": "source_supported",
    }
)

OUTPUT_SCHEMA = MappingProxyType(
    {
        "plan_id": str,
        "source_script_id": str,
        "visual_style": str,
        "scene_count": int,
        "scenes": tuple,
        "asset_requirements": tuple,
        "transition_plan": tuple,
        "safety_notes": tuple,
        "fallback_used": bool,
        "planning_confidence": float,
    }
)


def get_visual_metadata() -> MappingProxyType[str, str]:
    """
    Purpose:
    Return immutable Visual Planning Engine metadata.

    Arguments:
    None

    Returns:
    immutable metadata mapping
    """
    return MappingProxyType(
        {
            "engine_name": ENGINE_NAME,
            "engine_version": ENGINE_VERSION,
            "engine_description": ENGINE_DESCRIPTION,
        }
    )


def get_shot_types() -> tuple[str, ...]:
    """
    Purpose:
    Return supported shot type vocabulary.

    Arguments:
    None

    Returns:
    shot type strings
    """
    return SHOT_TYPES


def get_camera_movements() -> tuple[str, ...]:
    """
    Purpose:
    Return supported camera movement vocabulary.

    Arguments:
    None

    Returns:
    camera movement strings
    """
    return CAMERA_MOVEMENTS


def get_visual_styles() -> tuple[str, ...]:
    """
    Purpose:
    Return supported visual style principles.

    Arguments:
    None

    Returns:
    visual style strings
    """
    return VISUAL_STYLES


def get_scene_rules() -> tuple[str, ...]:
    """
    Purpose:
    Return immutable scene planning rules.

    Arguments:
    None

    Returns:
    scene planning rule strings
    """
    return SCENE_RULES


def get_asset_categories() -> tuple[str, ...]:
    """
    Purpose:
    Return supported asset category vocabulary.

    Arguments:
    None

    Returns:
    asset category strings
    """
    return ASSET_CATEGORIES


def get_transition_types() -> tuple[str, ...]:
    """
    Purpose:
    Return supported transition vocabulary.

    Arguments:
    None

    Returns:
    transition type strings
    """
    return TRANSITION_TYPES


def get_forbidden_rules() -> tuple[str, ...]:
    """
    Purpose:
    Return immutable forbidden visual behavior rules.

    Arguments:
    None

    Returns:
    forbidden visual behavior strings
    """
    return FORBIDDEN_VISUAL_BEHAVIORS


def get_quality_targets() -> MappingProxyType[str, Any]:
    """
    Purpose:
    Return immutable visual quality targets.

    Arguments:
    None

    Returns:
    immutable quality target mapping
    """
    return QUALITY_TARGETS


def get_output_schema() -> MappingProxyType[str, type]:
    """
    Purpose:
    Return immutable Visual Planning output schema constants.

    Arguments:
    None

    Returns:
    immutable output schema mapping
    """
    return OUTPUT_SCHEMA


def _self_test_metadata_exists() -> bool:
    """
    Purpose:
    Verify metadata accessor returns required metadata.

    Arguments:
    None

    Returns:
    test result
    """
    metadata = get_visual_metadata()
    return bool(metadata["engine_name"] and metadata["engine_version"])


def _self_test_vocabularies_populated() -> bool:
    """
    Purpose:
    Verify vocabulary accessors return populated tuples.

    Arguments:
    None

    Returns:
    test result
    """
    vocabularies = (
        get_shot_types(),
        get_camera_movements(),
        get_visual_styles(),
        get_scene_rules(),
        get_asset_categories(),
        get_transition_types(),
        get_forbidden_rules(),
    )
    return all(isinstance(vocabulary, tuple) and vocabulary for vocabulary in vocabularies)


def _self_test_schema_fields_exist() -> bool:
    """
    Purpose:
    Verify output schema contains required fields.

    Arguments:
    None

    Returns:
    test result
    """
    required_fields = {
        "plan_id",
        "source_script_id",
        "visual_style",
        "scene_count",
        "scenes",
        "asset_requirements",
        "transition_plan",
        "safety_notes",
        "fallback_used",
        "planning_confidence",
    }
    return required_fields <= set(get_output_schema())


def _self_test_accessor_types() -> bool:
    """
    Purpose:
    Verify accessors return expected immutable container types.

    Arguments:
    None

    Returns:
    test result
    """
    return (
        isinstance(get_visual_metadata(), MappingProxyType)
        and isinstance(get_quality_targets(), MappingProxyType)
        and isinstance(get_output_schema(), MappingProxyType)
        and isinstance(get_shot_types(), tuple)
    )


def _run_self_tests() -> bool:
    """
    Purpose:
    Run lightweight constitution self-tests.

    Arguments:
    None

    Returns:
    aggregate test result
    """
    tests = (
        _self_test_metadata_exists(),
        _self_test_vocabularies_populated(),
        _self_test_schema_fields_exist(),
        _self_test_accessor_types(),
    )
    return all(tests)


if __name__ == "__main__":
    print("PASS" if _run_self_tests() else "FAIL")
