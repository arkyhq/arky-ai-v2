"""
Purpose:
Validate and repair one deterministic script strategy object.

Input:
one strategy dictionary

Output:
one validated strategy dictionary
"""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any


logger = logging.getLogger(__name__)


class StrategyValidationError(ValueError):
    """
    Purpose:
    Report unrecoverable strategy validation failures.

    Input:
    validation failure details

    Output:
    explicit validation exception
    """


SAFE_DEFAULTS = {
    "story_archetype": "unknown",
    "opening_style": "context_first",
    "hook_direction": "what_happened",
    "opening_intensity": "low",
    "story_arc": "question_answer_takeaway",
    "reveal_order": ["context", "key_detail", "why_it_matters"],
    "emotion_curve": ["curiosity", "clarity"],
    "viewer_trigger": "curiosity",
    "retention_pattern": "linear_explanation",
    "curiosity_gap": "none",
    "ending_style": "clean_resolution",
    "pacing": "medium",
    "information_density": "low",
    "claim_safety": "careful",
    "strategy_confidence": 0.0,
    "fallback_used": True,
}

REQUIRED_FIELDS = set(SAFE_DEFAULTS)
OPTIONAL_REPAIR_FIELDS = {
    "reveal_order",
    "emotion_curve",
}

ENUMS = {
    "story_archetype": {
        "controversy",
        "creator_update",
        "tribute",
        "meme",
        "wholesome",
        "viral_clip",
        "industry_update",
        "community_discussion",
        "simple_news",
        "audience_reaction",
        "nostalgic_moment",
        "creator_exposed",
        "gaming_integrity",
        "unknown",
    },
    "opening_style": {
        "context_first",
        "conflict_first",
        "entity_first",
        "question_first",
        "reaction_first",
        "stakes_first",
        "timeline_first",
    },
    "hook_direction": {
        "what_happened",
        "why_it_matters",
        "what_changed",
        "who_is_involved",
        "why_people_are_reacting",
        "what_people_missed",
        "what_happens_next",
    },
    "opening_intensity": {"low", "medium", "high"},
    "story_arc": {
        "context_tension_payoff",
        "setup_reveal_reaction",
        "claim_context_implication",
        "timeline_turn_resolution",
        "problem_response_outcome",
        "question_answer_takeaway",
        "moment_context_meaning",
    },
    "viewer_trigger": {
        "curiosity",
        "identity",
        "controversy",
        "emotion",
        "nostalgia",
        "social_proof",
        "utility",
        "surprise",
    },
    "retention_pattern": {
        "linear_explanation",
        "single_open_loop",
        "delayed_context",
        "escalating_reveals",
        "reaction_build",
        "timeline_countdown",
        "contrast_pattern",
    },
    "curiosity_gap": {"none", "light", "moderate", "strong"},
    "ending_style": {
        "clean_resolution",
        "open_question",
        "what_next",
        "audience_reflection",
        "contextual_takeaway",
        "soft_landing",
    },
    "pacing": {"slow", "medium", "fast"},
    "information_density": {"low", "medium", "high"},
    "claim_safety": {"normal", "careful", "very_careful"},
}

LIST_ENUMS = {
    "reveal_order": {
        "context",
        "entity",
        "key_detail",
        "conflict",
        "reaction",
        "stakes",
        "timeline",
        "why_it_matters",
        "payoff",
        "caution",
    },
    "emotion_curve": {
        "curiosity",
        "surprise",
        "concern",
        "amusement",
        "nostalgia",
        "admiration",
        "skepticism",
        "clarity",
        "relief",
        "resolution",
    },
}

LIST_LIMITS = {
    "reveal_order": (3, 6),
    "emotion_curve": (2, 4),
}


def validate_strategy(strategy: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Validate and repair one strategy object.

    Arguments:
    strategy: strategy dictionary

    Returns:
    validated strategy dictionary
    """
    if not isinstance(strategy, dict):
        raise StrategyValidationError("Strategy object must be a dictionary")

    missing_required = REQUIRED_FIELDS - set(strategy)
    unrecoverable_missing = missing_required - OPTIONAL_REPAIR_FIELDS

    if unrecoverable_missing:
        missing = ", ".join(sorted(unrecoverable_missing))
        raise StrategyValidationError(f"Missing required strategy fields: {missing}")

    repaired = deepcopy(strategy)
    _repair_optional_fields(repaired)
    _repair_enum_fields(repaired)
    _repair_list_fields(repaired)
    _repair_confidence(repaired)
    _repair_boolean(repaired)
    _repair_logical_consistency(repaired)

    logger.info("Strategy validation completed")
    return repaired


def _repair_optional_fields(strategy: dict[str, Any]) -> None:
    """
    Purpose:
    Repair missing fields that have safe default values.

    Arguments:
    strategy: strategy dictionary

    Returns:
    None
    """
    for field in OPTIONAL_REPAIR_FIELDS:
        if field not in strategy:
            strategy[field] = deepcopy(SAFE_DEFAULTS[field])


def _repair_enum_fields(strategy: dict[str, Any]) -> None:
    """
    Purpose:
    Repair invalid enum and empty string fields.

    Arguments:
    strategy: strategy dictionary

    Returns:
    None
    """
    for field, allowed_values in ENUMS.items():
        value = strategy.get(field)

        if not isinstance(value, str) or not value.strip():
            strategy[field] = SAFE_DEFAULTS[field]
            continue

        normalized = value.strip().lower()
        strategy[field] = normalized if normalized in allowed_values else SAFE_DEFAULTS[field]


def _repair_list_fields(strategy: dict[str, Any]) -> None:
    """
    Purpose:
    Repair list fields by filtering invalid values and duplicates.

    Arguments:
    strategy: strategy dictionary

    Returns:
    None
    """
    for field, allowed_values in LIST_ENUMS.items():
        value = strategy.get(field)

        if not isinstance(value, list):
            strategy[field] = deepcopy(SAFE_DEFAULTS[field])
            continue

        repaired_values = []
        seen_values = set()

        for item in value:
            if not isinstance(item, str):
                continue

            normalized = item.strip().lower()

            if normalized not in allowed_values or normalized in seen_values:
                continue

            seen_values.add(normalized)
            repaired_values.append(normalized)

        min_length, max_length = LIST_LIMITS[field]

        if len(repaired_values) < min_length:
            repaired_values = deepcopy(SAFE_DEFAULTS[field])

        strategy[field] = repaired_values[:max_length]


def _repair_confidence(strategy: dict[str, Any]) -> None:
    """
    Purpose:
    Repair strategy confidence into the valid range.

    Arguments:
    strategy: strategy dictionary

    Returns:
    None
    """
    try:
        confidence = float(strategy.get("strategy_confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0

    strategy["strategy_confidence"] = max(0.0, min(1.0, confidence))


def _repair_boolean(strategy: dict[str, Any]) -> None:
    """
    Purpose:
    Repair fallback_used into a boolean.

    Arguments:
    strategy: strategy dictionary

    Returns:
    None
    """
    value = strategy.get("fallback_used")

    if isinstance(value, bool):
        return

    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in {"true", "1", "yes"}:
            strategy["fallback_used"] = True
            return

        if normalized in {"false", "0", "no"}:
            strategy["fallback_used"] = False
            return

    strategy["fallback_used"] = SAFE_DEFAULTS["fallback_used"]


def _repair_logical_consistency(strategy: dict[str, Any]) -> None:
    """
    Purpose:
    Repair logically unsafe strategy combinations.

    Arguments:
    strategy: strategy dictionary

    Returns:
    None
    """
    if strategy["claim_safety"] == "very_careful":
        if strategy["curiosity_gap"] == "strong":
            strategy["curiosity_gap"] = "moderate"

        if strategy["opening_intensity"] == "high":
            strategy["opening_intensity"] = "medium"

        if strategy["pacing"] == "fast":
            strategy["pacing"] = "medium"

    if strategy["fallback_used"]:
        strategy["strategy_confidence"] = min(strategy["strategy_confidence"], 0.0)


def _base_valid_strategy() -> dict[str, Any]:
    """
    Purpose:
    Build a valid strategy sample for self-tests.

    Arguments:
    None

    Returns:
    valid strategy dictionary
    """
    return {
        "story_archetype": "simple_news",
        "opening_style": "context_first",
        "hook_direction": "what_happened",
        "opening_intensity": "medium",
        "story_arc": "context_tension_payoff",
        "reveal_order": ["context", "key_detail", "why_it_matters", "payoff"],
        "emotion_curve": ["curiosity", "clarity", "resolution"],
        "viewer_trigger": "curiosity",
        "retention_pattern": "single_open_loop",
        "curiosity_gap": "light",
        "ending_style": "clean_resolution",
        "pacing": "medium",
        "information_density": "medium",
        "claim_safety": "normal",
        "strategy_confidence": 0.8,
        "fallback_used": False,
    }


def _run_test(name: str, strategy: Any, expect_error: bool = False) -> None:
    """
    Purpose:
    Run one validator self-test and print PASS or FAIL.

    Arguments:
    name: test name
    strategy: strategy input
    expect_error: whether validation should fail

    Returns:
    None
    """
    try:
        validate_strategy(strategy)
        passed = not expect_error
    except StrategyValidationError:
        passed = expect_error

    print(f"{name}: {'PASS' if passed else 'FAIL'}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    valid = _base_valid_strategy()

    missing_optional = _base_valid_strategy()
    missing_optional.pop("reveal_order")

    invalid_enum = _base_valid_strategy()
    invalid_enum["opening_style"] = "too_much"

    confidence_above = _base_valid_strategy()
    confidence_above["strategy_confidence"] = 3

    confidence_below = _base_valid_strategy()
    confidence_below["strategy_confidence"] = -2

    duplicate_reveal = _base_valid_strategy()
    duplicate_reveal["reveal_order"] = ["context", "context", "key_detail", "payoff"]

    duplicate_emotion = _base_valid_strategy()
    duplicate_emotion["emotion_curve"] = ["curiosity", "curiosity", "clarity"]

    missing_required = _base_valid_strategy()
    missing_required.pop("story_archetype")

    _run_test("valid strategy object", valid)
    _run_test("missing optional field", missing_optional)
    _run_test("invalid enum value", invalid_enum)
    _run_test("confidence above 1", confidence_above)
    _run_test("confidence below 0", confidence_below)
    _run_test("duplicate reveal_order", duplicate_reveal)
    _run_test("duplicate emotion_curve", duplicate_emotion)
    _run_test("missing required field", missing_required, expect_error=True)
