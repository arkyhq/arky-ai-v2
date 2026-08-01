"""
Purpose:
Validate Asset Manifests produced by the Asset Planner.

Input:
one Asset Manifest result or a sequence of Asset Manifest results

Output:
deterministic validation reports for schema, vocabularies, prompts,
continuity, render metadata, typography, and color palette
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

try:
    from scripts.asset_planning.asset_constitution import (
        get_asset_categories,
        get_color_palette,
        get_icon_vocabulary,
        get_music_categories,
        get_prompt_templates,
        get_render_constraints,
        get_sfx_categories,
        get_typography,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution support
    from asset_constitution import (
        get_asset_categories,
        get_color_palette,
        get_icon_vocabulary,
        get_music_categories,
        get_prompt_templates,
        get_render_constraints,
        get_sfx_categories,
        get_typography,
    )


VALIDATED_STAGE = "asset_output_validator"
ALLOWED_GENERATION_SOURCES = frozenset({"groq", "fallback"})

TOP_LEVEL_REQUIRED_FIELDS = (
    "trend_id",
    "asset_manifest",
    "generation_source",
    "fallback_used",
)

MANIFEST_REQUIRED_FIELDS = (
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
)

ASSET_REQUIRED_FIELDS = (
    "asset_id",
    "category",
    "quantity",
)

ERROR_MESSAGES = {
    "AOUT001": "Missing manifest.",
    "AOUT002": "Missing required field.",
    "AOUT003": "Invalid field type.",
    "AOUT004": "Invalid asset category.",
    "AOUT005": "Invalid prompt.",
    "AOUT006": "Invalid vocabulary value.",
    "AOUT007": "Invalid continuity metadata.",
    "AOUT008": "Invalid render metadata.",
    "AOUT009": "Invalid typography.",
    "AOUT010": "Invalid color palette.",
}

__all__ = ("validate_asset_manifest", "validate_asset_manifests")


def validate_asset_manifest(result: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Validate one Asset Manifest result.

    Arguments:
    result: Asset Planner output dictionary

    Returns:
    deterministic validation report
    """
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    if not isinstance(result, dict):
        _add_issue(errors, "AOUT001", "result")
        return _build_report(errors, warnings)

    _validate_top_level(result, errors)

    manifest = result.get("asset_manifest")
    if isinstance(manifest, dict):
        _validate_manifest(manifest, errors)

    return _build_report(errors, warnings)


def validate_asset_manifests(
    results: Iterable[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """
    Purpose:
    Validate multiple Asset Manifest results.

    Arguments:
    results: iterable of Asset Planner output dictionaries

    Returns:
    immutable tuple of validation reports
    """
    if not isinstance(results, Iterable) or isinstance(results, (str, bytes)):
        return (validate_asset_manifest(results),)

    return tuple(validate_asset_manifest(result) for result in results)


def _validate_top_level(
    result: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate top-level Asset Manifest result fields.

    Arguments:
    result: Asset Planner output dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    for field in TOP_LEVEL_REQUIRED_FIELDS:
        if field not in result:
            code = "AOUT001" if field == "asset_manifest" else "AOUT002"
            _add_issue(errors, code, field)

    type_rules = {
        "trend_id": str,
        "asset_manifest": dict,
        "generation_source": str,
        "fallback_used": bool,
    }

    for field, expected_type in type_rules.items():
        if field in result and not isinstance(result[field], expected_type):
            _add_issue(errors, "AOUT003", field)

    generation_source = result.get("generation_source")
    if isinstance(generation_source, str) and generation_source not in ALLOWED_GENERATION_SOURCES:
        _add_issue(errors, "AOUT006", "generation_source")


def _validate_manifest(
    manifest: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate Asset Manifest schema and constitution compliance.

    Arguments:
    manifest: nested Asset Manifest dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    for field in MANIFEST_REQUIRED_FIELDS:
        if field not in manifest:
            _add_issue(errors, "AOUT002", f"asset_manifest.{field}")

    _validate_manifest_types(manifest, errors)
    _validate_asset_lists(manifest, errors)
    _validate_audio_requirements(manifest, errors)
    _validate_render_metadata(manifest, errors)
    _validate_continuity(manifest, errors)
    _validate_optional_design_metadata(manifest, errors)


def _validate_manifest_types(
    manifest: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate required Asset Manifest field types.

    Arguments:
    manifest: nested Asset Manifest dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    type_rules = {
        "asset_manifest_id": str,
        "source_visual_plan_id": str,
        "trend_id": str,
        "assets": list,
        "required_assets": list,
        "optional_assets": list,
        "music_requirements": list,
        "sfx_requirements": list,
        "render_constraints": dict,
        "rights_notes": (list, tuple),
        "fallback_used": bool,
        "asset_confidence": (int, float),
    }

    for field, expected_type in type_rules.items():
        if field in manifest and not isinstance(manifest[field], expected_type):
            _add_issue(errors, "AOUT003", f"asset_manifest.{field}")

    confidence = manifest.get("asset_confidence")
    if isinstance(confidence, (int, float)) and not 0 <= confidence <= 1:
        _add_issue(errors, "AOUT003", "asset_manifest.asset_confidence")


def _validate_asset_lists(
    manifest: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate required and optional asset entries.

    Arguments:
    manifest: nested Asset Manifest dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    for list_name in ("assets", "required_assets", "optional_assets"):
        asset_list = manifest.get(list_name)

        if not isinstance(asset_list, list):
            continue

        for index, asset in enumerate(asset_list, start=1):
            _validate_asset_entry(asset, f"{list_name}.{index}", errors)


def _validate_asset_entry(
    asset: Any,
    field_prefix: str,
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate one asset manifest entry.

    Arguments:
    asset: candidate asset dictionary
    field_prefix: field path prefix
    errors: mutable validation error list

    Returns:
    None
    """
    if not isinstance(asset, dict):
        _add_issue(errors, "AOUT003", field_prefix)
        return

    for field in ASSET_REQUIRED_FIELDS:
        if field not in asset:
            _add_issue(errors, "AOUT002", f"{field_prefix}.{field}")

    category = asset.get("category")
    if isinstance(category, str) and category not in get_asset_categories():
        _add_issue(errors, "AOUT004", f"{field_prefix}.category")

    quantity = asset.get("quantity")
    if isinstance(quantity, int):
        if quantity < 0:
            _add_issue(errors, "AOUT003", f"{field_prefix}.quantity")
    elif "quantity" in asset:
        _add_issue(errors, "AOUT003", f"{field_prefix}.quantity")

    prompt_template = asset.get("prompt_template")
    if "prompt_template" in asset and not _is_approved_prompt(prompt_template):
        _add_issue(errors, "AOUT005", f"{field_prefix}.prompt_template")

    approved_icons = asset.get("approved_icons")
    if "approved_icons" in asset and not _is_approved_icon_list(approved_icons):
        _add_issue(errors, "AOUT006", f"{field_prefix}.approved_icons")


def _validate_audio_requirements(
    manifest: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate music and sound effect requirements.

    Arguments:
    manifest: nested Asset Manifest dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    _validate_category_entries(
        manifest.get("music_requirements"),
        get_music_categories(),
        "music_requirements",
        errors,
    )
    _validate_category_entries(
        manifest.get("sfx_requirements"),
        get_sfx_categories(),
        "sfx_requirements",
        errors,
    )


def _validate_category_entries(
    entries: Any,
    approved_values: tuple[str, ...],
    field_name: str,
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate list entries containing category fields.

    Arguments:
    entries: candidate list of category dictionaries
    approved_values: approved vocabulary values
    field_name: manifest field name
    errors: mutable validation error list

    Returns:
    None
    """
    if not isinstance(entries, list):
        return

    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            _add_issue(errors, "AOUT003", f"{field_name}.{index}")
            continue

        category = entry.get("category")
        if not isinstance(category, str) or category not in approved_values:
            _add_issue(errors, "AOUT006", f"{field_name}.{index}.category")


def _validate_render_metadata(
    manifest: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate render constraints metadata.

    Arguments:
    manifest: nested Asset Manifest dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    constraints = manifest.get("render_constraints")
    if not isinstance(constraints, dict):
        return

    approved_constraints = dict(get_render_constraints())
    for key, approved_value in approved_constraints.items():
        if key not in constraints:
            _add_issue(errors, "AOUT008", f"render_constraints.{key}")
            continue

        if type(constraints[key]) is not type(approved_value):
            _add_issue(errors, "AOUT008", f"render_constraints.{key}")


def _validate_continuity(
    manifest: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate continuity notes and rights notes.

    Arguments:
    manifest: nested Asset Manifest dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    for field in ("continuity_notes", "rights_notes", "render_hints"):
        if field in manifest and not _is_string_sequence(manifest[field]):
            _add_issue(errors, "AOUT007", f"asset_manifest.{field}")


def _validate_optional_design_metadata(
    manifest: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate optional typography and color palette metadata when present.

    Arguments:
    manifest: nested Asset Manifest dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    if "typography" in manifest and manifest["typography"] != dict(get_typography()):
        _add_issue(errors, "AOUT009", "asset_manifest.typography")

    if "color_palette" in manifest and manifest["color_palette"] != dict(get_color_palette()):
        _add_issue(errors, "AOUT010", "asset_manifest.color_palette")


def _is_approved_prompt(value: Any) -> bool:
    """
    Purpose:
    Check whether a prompt template matches approved prompt fragments.

    Arguments:
    value: candidate prompt template

    Returns:
    approved prompt flag
    """
    return isinstance(value, str) and value in set(get_prompt_templates().values())


def _is_approved_icon_list(value: Any) -> bool:
    """
    Purpose:
    Check whether an icon list uses only approved icon vocabulary.

    Arguments:
    value: candidate icon list

    Returns:
    approved icon list flag
    """
    if not isinstance(value, (list, tuple)):
        return False

    approved_icons = set(get_icon_vocabulary())
    return all(isinstance(item, str) and item in approved_icons for item in value)


def _is_string_sequence(value: Any) -> bool:
    """
    Purpose:
    Check whether a value is a sequence of strings.

    Arguments:
    value: candidate sequence

    Returns:
    string sequence flag
    """
    return isinstance(value, (list, tuple)) and all(isinstance(item, str) for item in value)


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
    Build deterministic Asset Manifest validation report.

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


def _valid_manifest_result() -> dict[str, Any]:
    """
    Purpose:
    Build a valid Asset Manifest result for self-tests.

    Arguments:
    None

    Returns:
    valid Asset Manifest result dictionary
    """
    manifest = {
        "asset_manifest_id": "asset_manifest_trend_001",
        "source_visual_plan_id": "trend_001",
        "trend_id": "trend_001",
        "assets": [
            {
                "asset_id": "text_card_1",
                "category": "text_card",
                "quantity": 1,
                "prompt_template": get_prompt_templates()["overlay_asset"],
            }
        ],
        "required_assets": [
            {
                "asset_id": "text_card_1",
                "category": "text_card",
                "quantity": 1,
                "prompt_template": get_prompt_templates()["overlay_asset"],
            }
        ],
        "optional_assets": [
            {
                "asset_id": "icon_support_1",
                "category": "icon",
                "quantity": 1,
                "approved_icons": get_icon_vocabulary()[:2],
            }
        ],
        "music_requirements": [{"category": "subtle_news_bed", "usage": "background_music"}],
        "sfx_requirements": [{"category": "soft_whoosh", "usage": "scene_transition"}],
        "render_constraints": dict(get_render_constraints()),
        "rights_notes": ("Use approved rights only.",),
        "continuity_notes": ("Preserve narration order.",),
        "render_hints": ("Use approved palette.",),
        "fallback_used": True,
        "asset_confidence": 0.75,
    }
    return {
        "trend_id": "trend_001",
        "asset_manifest": manifest,
        "generation_source": "fallback",
        "fallback_used": True,
    }


def _has_error(report: dict[str, Any], code: str) -> bool:
    """
    Purpose:
    Determine whether a validation report contains a code.

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
    Run deterministic Asset Output Validator self-tests.

    Arguments:
    None

    Returns:
    aggregate self-test result
    """
    missing_manifest = _valid_manifest_result()
    missing_manifest.pop("asset_manifest")

    invalid_category = _valid_manifest_result()
    invalid_category["asset_manifest"]["assets"][0]["category"] = "fake_asset"

    invalid_prompt = _valid_manifest_result()
    invalid_prompt["asset_manifest"]["assets"][0]["prompt_template"] = "fake prompt"

    invalid_music = _valid_manifest_result()
    invalid_music["asset_manifest"]["music_requirements"][0]["category"] = "fake_music"

    invalid_render = _valid_manifest_result()
    invalid_render["asset_manifest"]["render_constraints"]["width"] = "1080"

    invalid_typography = _valid_manifest_result()
    invalid_typography["asset_manifest"]["typography"] = {"primary_font": "Wrong"}

    invalid_palette = _valid_manifest_result()
    invalid_palette["asset_manifest"]["color_palette"] = {"primary": "#000000"}

    tests = (
        validate_asset_manifest(_valid_manifest_result())["valid"],
        _has_error(validate_asset_manifest(missing_manifest), "AOUT001"),
        _has_error(validate_asset_manifest(invalid_category), "AOUT004"),
        _has_error(validate_asset_manifest(invalid_prompt), "AOUT005"),
        _has_error(validate_asset_manifest(invalid_music), "AOUT006"),
        _has_error(validate_asset_manifest(invalid_render), "AOUT008"),
        _has_error(validate_asset_manifest(invalid_typography), "AOUT009"),
        _has_error(validate_asset_manifest(invalid_palette), "AOUT010"),
        len(validate_asset_manifests((_valid_manifest_result(), _valid_manifest_result()))) == 2,
    )
    return all(tests)


if __name__ == "__main__":
    print("PASS" if _run_self_tests() else "FAIL")
