"""
Purpose:
Validate and repair one deterministic script blueprint.

Input:
one script blueprint dictionary

Output:
one validated script blueprint dictionary
"""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any


logger = logging.getLogger(__name__)


class ScriptBlueprintValidationError(ValueError):
    """
    Purpose:
    Report unrecoverable script blueprint validation failures.

    Input:
    validation failure details

    Output:
    explicit validation exception
    """


MIN_DURATION_SECONDS = 30
MAX_DURATION_SECONDS = 60

REQUIRED_FIELDS = {
    "script_id",
    "source_topic",
    "script_goal",
    "estimated_duration_seconds",
    "opening_goal",
    "body_sections",
    "closing_goal",
    "facts_to_include",
    "facts_to_avoid",
    "entity_order",
    "transition_plan",
    "ending_objective",
    "claim_safety",
    "script_confidence",
    "fallback_used",
}

OPTIONAL_LIST_FIELDS = {
    "facts_to_include",
    "facts_to_avoid",
    "entity_order",
    "transition_plan",
}

SAFE_DEFAULTS = {
    "script_id": "script_blueprint_unknown",
    "source_topic": "unknown topic",
    "script_goal": "explain the topic cautiously using only confirmed input details",
    "estimated_duration_seconds": 38,
    "opening_goal": "start with neutral context and avoid dramatic framing",
    "body_sections": [
        {
            "section_type": "context",
            "source_fields": ["story_summary"],
            "purpose": "establish the basic story context",
            "claim_safety": "careful",
        }
    ],
    "closing_goal": "close with a cautious factual takeaway",
    "facts_to_include": [],
    "facts_to_avoid": [
        "quotes not present in editorial input",
        "statistics not present in editorial input",
        "dates not present in editorial input",
        "timeline details not present in editorial input",
    ],
    "entity_order": [],
    "transition_plan": ["establish context", "move to key detail", "deliver takeaway"],
    "ending_objective": "leave the viewer with a safe factual takeaway",
    "claim_safety": "careful",
    "script_confidence": 0.0,
    "fallback_used": True,
}

CLAIM_SAFETY_VALUES = {"normal", "careful", "very_careful"}

SECTION_TYPES = {
    "context",
    "entity_setup",
    "key_detail",
    "conflict",
    "reaction",
    "stakes",
    "timeline",
    "why_it_matters",
    "payoff",
    "caution",
}

TEXT_FIELDS = {
    "script_id",
    "source_topic",
    "script_goal",
    "opening_goal",
    "closing_goal",
    "ending_objective",
}


def validate_script_blueprint(blueprint: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Validate and repair one script blueprint.

    Arguments:
    blueprint: script blueprint dictionary

    Returns:
    validated script blueprint dictionary
    """
    if not isinstance(blueprint, dict):
        raise ScriptBlueprintValidationError("Script blueprint must be a dictionary")

    missing_fields = REQUIRED_FIELDS - set(blueprint)
    unrecoverable_missing = missing_fields - OPTIONAL_LIST_FIELDS

    if unrecoverable_missing:
        missing = ", ".join(sorted(unrecoverable_missing))
        raise ScriptBlueprintValidationError(f"Missing required script blueprint fields: {missing}")

    repaired = deepcopy(blueprint)
    _repair_text_fields(repaired)
    _repair_duration(repaired)
    _repair_claim_safety(repaired)
    _repair_confidence(repaired)
    _repair_fallback_flag(repaired)
    _repair_optional_lists(repaired)
    _repair_body_sections(repaired)
    _repair_fact_lists(repaired)
    _repair_entity_order(repaired)
    _repair_transition_plan(repaired)

    logger.info("Script blueprint validation completed")
    return repaired


def _repair_text_fields(blueprint: dict[str, Any]) -> None:
    """
    Purpose:
    Repair empty string fields where safe defaults exist.

    Arguments:
    blueprint: script blueprint dictionary

    Returns:
    None
    """
    for field in TEXT_FIELDS:
        value = blueprint.get(field)

        if not isinstance(value, str) or not value.strip():
            blueprint[field] = SAFE_DEFAULTS[field]
        else:
            blueprint[field] = value.strip()


def _repair_duration(blueprint: dict[str, Any]) -> None:
    """
    Purpose:
    Clamp estimated duration into allowed short-video limits.

    Arguments:
    blueprint: script blueprint dictionary

    Returns:
    None
    """
    try:
        duration = int(round(float(blueprint.get("estimated_duration_seconds"))))
    except (TypeError, ValueError):
        duration = SAFE_DEFAULTS["estimated_duration_seconds"]

    blueprint["estimated_duration_seconds"] = max(
        MIN_DURATION_SECONDS,
        min(MAX_DURATION_SECONDS, duration),
    )


def _repair_claim_safety(blueprint: dict[str, Any]) -> None:
    """
    Purpose:
    Repair claim safety enum values.

    Arguments:
    blueprint: script blueprint dictionary

    Returns:
    None
    """
    value = blueprint.get("claim_safety")

    if not isinstance(value, str):
        blueprint["claim_safety"] = SAFE_DEFAULTS["claim_safety"]
        return

    normalized = value.strip().lower()
    blueprint["claim_safety"] = (
        normalized if normalized in CLAIM_SAFETY_VALUES else SAFE_DEFAULTS["claim_safety"]
    )


def _repair_confidence(blueprint: dict[str, Any]) -> None:
    """
    Purpose:
    Clamp script confidence into the valid range.

    Arguments:
    blueprint: script blueprint dictionary

    Returns:
    None
    """
    try:
        confidence = float(blueprint.get("script_confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0

    blueprint["script_confidence"] = max(0.0, min(1.0, confidence))


def _repair_fallback_flag(blueprint: dict[str, Any]) -> None:
    """
    Purpose:
    Repair fallback flag into a boolean.

    Arguments:
    blueprint: script blueprint dictionary

    Returns:
    None
    """
    value = blueprint.get("fallback_used")

    if isinstance(value, bool):
        return

    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in {"true", "1", "yes"}:
            blueprint["fallback_used"] = True
            return

        if normalized in {"false", "0", "no"}:
            blueprint["fallback_used"] = False
            return

    blueprint["fallback_used"] = SAFE_DEFAULTS["fallback_used"]


def _repair_optional_lists(blueprint: dict[str, Any]) -> None:
    """
    Purpose:
    Repair missing optional list fields.

    Arguments:
    blueprint: script blueprint dictionary

    Returns:
    None
    """
    for field in OPTIONAL_LIST_FIELDS:
        if field not in blueprint or not isinstance(blueprint[field], list):
            blueprint[field] = deepcopy(SAFE_DEFAULTS[field])


def _repair_body_sections(blueprint: dict[str, Any]) -> None:
    """
    Purpose:
    Repair body section shape without inventing facts.

    Arguments:
    blueprint: script blueprint dictionary

    Returns:
    None
    """
    sections = blueprint.get("body_sections")

    if not isinstance(sections, list):
        blueprint["body_sections"] = deepcopy(SAFE_DEFAULTS["body_sections"])
        return

    repaired_sections = []

    for section in sections:
        if not isinstance(section, dict):
            continue

        section_type = _safe_section_type(section.get("section_type"))
        source_fields = _string_list(section.get("source_fields"))
        purpose = _safe_text(section.get("purpose"), "advance the script plan")
        claim_safety = _safe_claim_safety(section.get("claim_safety"))

        repaired_sections.append(
            {
                "section_type": section_type,
                "source_fields": source_fields,
                "purpose": purpose,
                "claim_safety": claim_safety,
            }
        )

    blueprint["body_sections"] = repaired_sections or deepcopy(SAFE_DEFAULTS["body_sections"])


def _repair_fact_lists(blueprint: dict[str, Any]) -> None:
    """
    Purpose:
    Remove duplicate facts and forbidden fact categories.

    Arguments:
    blueprint: script blueprint dictionary

    Returns:
    None
    """
    blueprint["facts_to_include"] = _dedupe_fact_dicts(blueprint.get("facts_to_include"))
    blueprint["facts_to_avoid"] = _dedupe_strings(blueprint.get("facts_to_avoid"))


def _repair_entity_order(blueprint: dict[str, Any]) -> None:
    """
    Purpose:
    Remove duplicate entities while preserving original order.

    Arguments:
    blueprint: script blueprint dictionary

    Returns:
    None
    """
    blueprint["entity_order"] = _dedupe_strings(blueprint.get("entity_order"))


def _repair_transition_plan(blueprint: dict[str, Any]) -> None:
    """
    Purpose:
    Repair transition sequence into a non-empty ordered string list.

    Arguments:
    blueprint: script blueprint dictionary

    Returns:
    None
    """
    transitions = _dedupe_strings(blueprint.get("transition_plan"))
    blueprint["transition_plan"] = transitions or deepcopy(SAFE_DEFAULTS["transition_plan"])


def _safe_section_type(value: Any) -> str:
    """
    Purpose:
    Repair section type enum values.

    Arguments:
    value: raw section type

    Returns:
    valid section type
    """
    if not isinstance(value, str):
        return "context"

    normalized = value.strip().lower()
    return normalized if normalized in SECTION_TYPES else "context"


def _safe_claim_safety(value: Any) -> str:
    """
    Purpose:
    Repair claim safety values used inside body sections.

    Arguments:
    value: raw claim safety

    Returns:
    valid claim safety
    """
    if not isinstance(value, str):
        return SAFE_DEFAULTS["claim_safety"]

    normalized = value.strip().lower()
    return normalized if normalized in CLAIM_SAFETY_VALUES else SAFE_DEFAULTS["claim_safety"]


def _safe_text(value: Any, default: str) -> str:
    """
    Purpose:
    Repair text values without inventing factual content.

    Arguments:
    value: raw text
    default: safe default text

    Returns:
    repaired text
    """
    if not isinstance(value, str) or not value.strip():
        return default

    return value.strip()


def _string_list(value: Any) -> list[str]:
    """
    Purpose:
    Convert a value into a deduplicated list of strings.

    Arguments:
    value: raw list value

    Returns:
    string list
    """
    if not isinstance(value, list):
        return []

    return _dedupe_strings(value)


def _dedupe_strings(value: Any) -> list[str]:
    """
    Purpose:
    Deduplicate string values while preserving order.

    Arguments:
    value: raw list value

    Returns:
    deduplicated string list
    """
    if not isinstance(value, list):
        return []

    repaired = []
    seen = set()

    for item in value:
        if not isinstance(item, str) or not item.strip():
            continue

        normalized = item.strip()
        key = normalized.lower()

        if key in seen:
            continue

        seen.add(key)
        repaired.append(normalized)

    return repaired


def _dedupe_fact_dicts(value: Any) -> list[dict[str, str]]:
    """
    Purpose:
    Deduplicate explicit fact dictionaries without inventing facts.

    Arguments:
    value: raw fact list

    Returns:
    deduplicated fact dictionaries
    """
    if not isinstance(value, list):
        return []

    repaired = []
    seen = set()

    for fact in value:
        if not isinstance(fact, dict):
            continue

        source_field = fact.get("source_field")
        fact_value = fact.get("value")

        if not isinstance(source_field, str) or not source_field.strip():
            continue

        if not isinstance(fact_value, str) or not fact_value.strip():
            continue

        repaired_fact = {
            "source_field": source_field.strip(),
            "value": fact_value.strip(),
        }
        key = (repaired_fact["source_field"].lower(), repaired_fact["value"].lower())

        if key in seen:
            continue

        seen.add(key)
        repaired.append(repaired_fact)

    return repaired


def _base_valid_blueprint() -> dict[str, Any]:
    """
    Purpose:
    Build a valid script blueprint sample for self-tests.

    Arguments:
    None

    Returns:
    valid script blueprint dictionary
    """
    return {
        "script_id": "script_blueprint_simple_news_streaming_series",
        "source_topic": "Streaming series reaction",
        "script_goal": "deliver a clear update with context and takeaway",
        "estimated_duration_seconds": 45,
        "opening_goal": "start with the basic context",
        "body_sections": [
            {
                "section_type": "context",
                "source_fields": ["story_summary"],
                "purpose": "establish the factual context",
                "claim_safety": "careful",
            }
        ],
        "closing_goal": "end with a concise takeaway",
        "facts_to_include": [
            {
                "source_field": "story_summary",
                "value": "A streaming series is gaining attention online.",
            }
        ],
        "facts_to_avoid": ["quotes not present in editorial input"],
        "entity_order": ["Netflix"],
        "transition_plan": ["establish context", "move to key detail"],
        "ending_objective": "end with a concise takeaway",
        "claim_safety": "careful",
        "script_confidence": 0.82,
        "fallback_used": False,
    }


def _run_test(name: str, blueprint: Any, expect_error: bool = False) -> None:
    """
    Purpose:
    Run one validator self-test and print PASS or FAIL.

    Arguments:
    name: test name
    blueprint: blueprint input
    expect_error: whether validation should fail

    Returns:
    None
    """
    try:
        validate_script_blueprint(blueprint)
        passed = not expect_error
    except ScriptBlueprintValidationError:
        passed = expect_error

    print(f"{name}: {'PASS' if passed else 'FAIL'}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    valid = _base_valid_blueprint()

    missing_optional = _base_valid_blueprint()
    missing_optional.pop("entity_order")

    duplicate_facts = _base_valid_blueprint()
    duplicate_facts["facts_to_include"].append(
        {
            "source_field": "story_summary",
            "value": "A streaming series is gaining attention online.",
        }
    )

    duplicate_entities = _base_valid_blueprint()
    duplicate_entities["entity_order"] = ["Netflix", "netflix", "Actor A"]

    invalid_enum = _base_valid_blueprint()
    invalid_enum["claim_safety"] = "reckless"
    invalid_enum["body_sections"][0]["section_type"] = "not_a_section"

    duration_too_long = _base_valid_blueprint()
    duration_too_long["estimated_duration_seconds"] = 95

    duration_too_short = _base_valid_blueprint()
    duration_too_short["estimated_duration_seconds"] = 10

    confidence_above = _base_valid_blueprint()
    confidence_above["script_confidence"] = 3

    confidence_below = _base_valid_blueprint()
    confidence_below["script_confidence"] = -2

    missing_required = _base_valid_blueprint()
    missing_required.pop("script_goal")

    _run_test("valid blueprint", valid)
    _run_test("missing optional field", missing_optional)
    _run_test("duplicate facts", duplicate_facts)
    _run_test("duplicate entities", duplicate_entities)
    _run_test("invalid enum", invalid_enum)
    _run_test("duration too long", duration_too_long)
    _run_test("duration too short", duration_too_short)
    _run_test("confidence above 1", confidence_above)
    _run_test("confidence below 0", confidence_below)
    _run_test("missing required field", missing_required, expect_error=True)
