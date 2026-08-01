"""
Purpose:
Define the immutable Asset Planning Engine constitution.

Input:
module imports from Asset Planning components

Output:
asset planning metadata, vocabularies, prompt templates, constraints, schemas,
and accessor functions
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any


ENGINE_NAME = "ARKY Asset Planning Engine"
ENGINE_VERSION = "0.8"
ENGINE_DESCRIPTION = (
    "A deterministic asset constitution for selecting approved asset categories, "
    "visual vocabularies, render constraints, and manifest schema contracts before "
    "asset generation or retrieval begins."
)

ASSET_CATEGORIES = (
    "character_reference",
    "background_plate",
    "b_roll_clip",
    "overlay_graphic",
    "icon",
    "logo",
    "music_bed",
    "sound_effect",
    "texture",
    "text_card",
    "licensed_media",
    "generated_still",
)

CHARACTER_CATEGORIES = (
    "public_figure_reference",
    "creator_reference",
    "generic_presenter",
    "silhouette",
    "anonymous_crowd",
    "no_character",
)

BACKGROUND_CATEGORIES = (
    "studio_gradient",
    "newsroom_style",
    "social_media_interface",
    "streaming_platform_context",
    "cinema_context",
    "concert_context",
    "gaming_context",
    "abstract_texture",
    "neutral_context",
)

BROLL_CATEGORIES = (
    "platform_scroll",
    "headline_scan",
    "audience_reaction",
    "streaming_browse",
    "cinema_exterior",
    "concert_lights",
    "gaming_screen",
    "creator_workspace",
    "phone_interaction",
    "neutral_motion_texture",
)

OVERLAY_TYPES = (
    "lower_third",
    "headline_overlay",
    "context_label",
    "timeline_marker",
    "source_badge",
    "safe_claim_note",
    "entity_tag",
    "countdown_marker",
    "transition_label",
)

ICON_VOCABULARY = (
    "play",
    "pause",
    "trending",
    "comment",
    "search",
    "music",
    "film",
    "tv",
    "gamepad",
    "spark",
    "warning",
    "check",
    "clock",
    "source",
)

LOGO_RULES = (
    "Use official logos only when rights and brand usage are approved.",
    "Never recreate protected logos inaccurately.",
    "Never imply sponsorship or endorsement.",
    "Prefer text labels when logo rights are unclear.",
    "Do not distort, recolor, or crop protected marks.",
)

MUSIC_CATEGORIES = (
    "none",
    "light_pulse",
    "subtle_news_bed",
    "pop_culture_energy",
    "soft_tension",
    "warm_resolution",
    "neutral_ambient",
)

SFX_CATEGORIES = (
    "none",
    "soft_whoosh",
    "tap",
    "pop",
    "subtle_riser",
    "transition_hit",
    "notification_blip",
    "soft_chime",
)

COLOR_PALETTE = MappingProxyType(
    {
        "primary": "#F8FAFC",
        "secondary": "#111827",
        "accent": "#38BDF8",
        "warning": "#F59E0B",
        "safe": "#22C55E",
        "danger": "#EF4444",
        "muted": "#64748B",
        "background": "#0F172A",
    }
)

TYPOGRAPHY = MappingProxyType(
    {
        "primary_font": "Inter",
        "fallback_font": "Arial",
        "headline_weight": "700",
        "body_weight": "500",
        "caption_weight": "600",
        "maximum_words_per_text_asset": 12,
        "case_style": "sentence_case",
    }
)

PROMPT_TEMPLATES = MappingProxyType(
    {
        "asset_brief": (
            "Create an asset brief for the approved visual plan. Use only the "
            "provided narration, visual plan, and asset constitution."
        ),
        "image_asset": (
            "Describe a single safe visual asset. Preserve entities and factual "
            "ambiguity. Do not invent evidence, locations, or events."
        ),
        "overlay_asset": (
            "Describe a concise overlay asset using approved typography, palette, "
            "and overlay vocabulary."
        ),
        "audio_asset": (
            "Describe a music or sound effect requirement using approved music and "
            "SFX categories only."
        ),
    }
)

FORBIDDEN_RULES = (
    "Never invent evidence.",
    "Never fabricate screenshots.",
    "Never create fake quotes.",
    "Never imply endorsement without source support.",
    "Never use unlicensed logos or protected marks.",
    "Never add defamatory visual implications.",
    "Never change names, dates, numbers, or chronology.",
    "Never create graphic shock imagery.",
    "Never create hateful, harassing, or sexualized assets.",
    "Never create assets that contradict narration or visual planning.",
    "Never include prompt leakage or production instructions in final assets.",
)

RENDER_CONSTRAINTS = MappingProxyType(
    {
        "aspect_ratio": "9:16",
        "width": 1080,
        "height": 1920,
        "frame_rate": 30,
        "safe_margin_percent": 8,
        "minimum_asset_resolution": (1080, 1080),
        "maximum_text_asset_words": 12,
        "maximum_overlay_lines": 2,
        "preferred_image_format": "png",
        "preferred_video_format": "mp4",
        "preferred_audio_format": "wav",
    }
)

OUTPUT_SCHEMA = MappingProxyType(
    {
        "asset_manifest_id": str,
        "source_visual_plan_id": str,
        "trend_id": str,
        "assets": tuple,
        "required_assets": tuple,
        "optional_assets": tuple,
        "music_requirements": tuple,
        "sfx_requirements": tuple,
        "render_constraints": dict,
        "rights_notes": tuple,
        "fallback_used": bool,
        "asset_confidence": float,
    }
)

__all__ = (
    "get_asset_metadata",
    "get_asset_categories",
    "get_character_categories",
    "get_background_categories",
    "get_broll_categories",
    "get_overlay_types",
    "get_icon_vocabulary",
    "get_logo_rules",
    "get_music_categories",
    "get_sfx_categories",
    "get_color_palette",
    "get_typography",
    "get_prompt_templates",
    "get_forbidden_rules",
    "get_render_constraints",
    "get_output_schema",
)


def get_asset_metadata() -> MappingProxyType[str, str]:
    """
    Purpose:
    Return immutable Asset Planning Engine metadata.

    Arguments:
    None

    Returns:
    immutable mapping containing engine name, version, and description
    """
    return MappingProxyType(
        {
            "engine_name": ENGINE_NAME,
            "engine_version": ENGINE_VERSION,
            "engine_description": ENGINE_DESCRIPTION,
        }
    )


def get_asset_categories() -> tuple[str, ...]:
    """
    Purpose:
    Return approved top-level asset categories.

    Arguments:
    None

    Returns:
    immutable tuple of asset category labels
    """
    return ASSET_CATEGORIES


def get_character_categories() -> tuple[str, ...]:
    """
    Purpose:
    Return approved character asset categories.

    Arguments:
    None

    Returns:
    immutable tuple of character category labels
    """
    return CHARACTER_CATEGORIES


def get_background_categories() -> tuple[str, ...]:
    """
    Purpose:
    Return approved background asset categories.

    Arguments:
    None

    Returns:
    immutable tuple of background category labels
    """
    return BACKGROUND_CATEGORIES


def get_broll_categories() -> tuple[str, ...]:
    """
    Purpose:
    Return approved b-roll asset categories.

    Arguments:
    None

    Returns:
    immutable tuple of b-roll category labels
    """
    return BROLL_CATEGORIES


def get_overlay_types() -> tuple[str, ...]:
    """
    Purpose:
    Return approved overlay asset types.

    Arguments:
    None

    Returns:
    immutable tuple of overlay type labels
    """
    return OVERLAY_TYPES


def get_icon_vocabulary() -> tuple[str, ...]:
    """
    Purpose:
    Return approved icon vocabulary.

    Arguments:
    None

    Returns:
    immutable tuple of icon labels
    """
    return ICON_VOCABULARY


def get_logo_rules() -> tuple[str, ...]:
    """
    Purpose:
    Return immutable logo usage rules.

    Arguments:
    None

    Returns:
    immutable tuple of logo rule strings
    """
    return LOGO_RULES


def get_music_categories() -> tuple[str, ...]:
    """
    Purpose:
    Return approved music categories.

    Arguments:
    None

    Returns:
    immutable tuple of music category labels
    """
    return MUSIC_CATEGORIES


def get_sfx_categories() -> tuple[str, ...]:
    """
    Purpose:
    Return approved sound effect categories.

    Arguments:
    None

    Returns:
    immutable tuple of sound effect category labels
    """
    return SFX_CATEGORIES


def get_color_palette() -> MappingProxyType[str, str]:
    """
    Purpose:
    Return immutable approved color palette.

    Arguments:
    None

    Returns:
    immutable mapping of palette names to hex values
    """
    return COLOR_PALETTE


def get_typography() -> MappingProxyType[str, Any]:
    """
    Purpose:
    Return immutable typography configuration.

    Arguments:
    None

    Returns:
    immutable mapping of typography settings
    """
    return TYPOGRAPHY


def get_prompt_templates() -> MappingProxyType[str, str]:
    """
    Purpose:
    Return reusable prompt template fragments for future asset modules.

    Arguments:
    None

    Returns:
    immutable mapping of template names to template fragments
    """
    return PROMPT_TEMPLATES


def get_forbidden_rules() -> tuple[str, ...]:
    """
    Purpose:
    Return immutable forbidden asset behavior rules.

    Arguments:
    None

    Returns:
    immutable tuple of forbidden rule strings
    """
    return FORBIDDEN_RULES


def get_render_constraints() -> MappingProxyType[str, Any]:
    """
    Purpose:
    Return immutable render constraints for future asset outputs.

    Arguments:
    None

    Returns:
    immutable mapping of render constraint settings
    """
    return RENDER_CONSTRAINTS


def get_output_schema() -> MappingProxyType[str, type]:
    """
    Purpose:
    Return immutable Asset Manifest schema constants.

    Arguments:
    None

    Returns:
    immutable mapping of asset manifest field names to expected Python types
    """
    return OUTPUT_SCHEMA


def _self_test_metadata() -> bool:
    """
    Purpose:
    Verify metadata accessor returns required values.

    Arguments:
    None

    Returns:
    metadata self-test result
    """
    metadata = get_asset_metadata()
    return bool(metadata["engine_name"] and metadata["engine_version"])


def _self_test_vocabularies() -> bool:
    """
    Purpose:
    Verify all vocabulary accessors return populated immutable tuples.

    Arguments:
    None

    Returns:
    vocabulary self-test result
    """
    vocabularies = (
        get_asset_categories(),
        get_character_categories(),
        get_background_categories(),
        get_broll_categories(),
        get_overlay_types(),
        get_icon_vocabulary(),
        get_logo_rules(),
        get_music_categories(),
        get_sfx_categories(),
        get_forbidden_rules(),
    )
    return all(isinstance(vocabulary, tuple) and vocabulary for vocabulary in vocabularies)


def _self_test_mappings() -> bool:
    """
    Purpose:
    Verify mapping accessors return immutable mapping proxy objects.

    Arguments:
    None

    Returns:
    mapping self-test result
    """
    mappings = (
        get_color_palette(),
        get_typography(),
        get_prompt_templates(),
        get_render_constraints(),
        get_output_schema(),
    )
    return all(isinstance(mapping, MappingProxyType) and mapping for mapping in mappings)


def _self_test_schema() -> bool:
    """
    Purpose:
    Verify Asset Manifest schema exposes required fields.

    Arguments:
    None

    Returns:
    schema self-test result
    """
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
    return required_fields <= set(get_output_schema())


def _run_self_tests() -> bool:
    """
    Purpose:
    Run deterministic constitution self-tests.

    Arguments:
    None

    Returns:
    aggregate self-test result
    """
    tests = (
        _self_test_metadata(),
        _self_test_vocabularies(),
        _self_test_mappings(),
        _self_test_schema(),
    )
    return all(tests)


if __name__ == "__main__":
    print("PASS" if _run_self_tests() else "FAIL")
