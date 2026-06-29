"""
Purpose:
Optionally refine deterministic script strategy with Groq.

Input:
one editorial dictionary and one deterministic strategy dictionary

Output:
one refined strategy dictionary
"""

from __future__ import annotations

import json
import logging
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import GROQ_API_KEY
from scripts.ai.groq_client import request_json


logger = logging.getLogger(__name__)

PROTECTED_FIELDS = {
    "story_archetype",
    "story_arc",
    "opening_style",
    "opening_intensity",
    "claim_safety",
    "fallback_used",
}

REFINABLE_FIELDS = {
    "reveal_order",
    "emotion_curve",
    "viewer_trigger",
    "retention_pattern",
    "curiosity_gap",
    "ending_style",
    "pacing",
    "information_density",
}


def build_refinement_prompt(
    editorial: dict[str, Any],
    strategy: dict[str, Any],
) -> str:
    """
    Purpose:
    Build the Groq prompt for optional strategy refinement.

    Arguments:
    editorial: editorial trend dictionary
    strategy: deterministic strategy dictionary

    Returns:
    prompt text
    """
    payload = {
        "editorial": {
            "story_type": editorial.get("story_type"),
            "main_entities": editorial.get("main_entities"),
            "story_summary": editorial.get("story_summary"),
            "why_people_care": editorial.get("why_people_care"),
            "primary_conflict": editorial.get("primary_conflict"),
            "confidence": editorial.get("confidence"),
            "editorial_tags": editorial.get("editorial_tags"),
            "risk_level": editorial.get("risk_level"),
            "evergreen": editorial.get("evergreen"),
        },
        "deterministic_strategy": strategy,
        "protected_fields": sorted(PROTECTED_FIELDS),
        "refinable_fields": sorted(REFINABLE_FIELDS),
    }

    return (
        "You are ARKY's optional Strategy Refiner.\n"
        "Return JSON only. Do not use markdown, code fences, or explanations.\n"
        "Never invent facts.\n"
        "Never contradict the editorial object.\n"
        "Never override deterministic decisions.\n"
        "You may refine only the fields listed in refinable_fields.\n"
        "Never remove fields, rename fields, or introduce new field names.\n"
        "Protected fields must remain exactly unchanged if included.\n"
        "Non-refinable fields must remain exactly unchanged if included.\n"
        "Schema-compatible response formats are:\n"
        "1. A complete strategy object with every deterministic_strategy field preserved.\n"
        "2. A partial object containing only refinable_fields that should change.\n"
        "If no safe refinement is useful, return the deterministic_strategy unchanged.\n\n"
        f"Payload:\n{json.dumps(payload, ensure_ascii=False)}"
    )


def refine_strategy(
    editorial: dict[str, Any],
    deterministic_strategy: dict[str, Any],
) -> dict[str, Any]:
    """
    Purpose:
    Refine allowed strategy fields while preserving deterministic fields.

    Arguments:
    editorial: editorial trend dictionary
    deterministic_strategy: deterministic strategy dictionary

    Returns:
    refined strategy dictionary or original deterministic strategy
    """
    original_strategy = deepcopy(deterministic_strategy)

    try:
        logger.info("AI refinement started")
        prompt = build_refinement_prompt(editorial, original_strategy)
        response = request_json(prompt)
        refined_strategy = merge_refinement(original_strategy, response)
        logger.info("AI refinement succeeded")
        return refined_strategy
    except Exception as exc:
        logger.warning("Fallback to deterministic strategy: %s", exc)
        return original_strategy


def merge_refinement(
    deterministic_strategy: dict[str, Any],
    ai_response: dict[str, Any],
) -> dict[str, Any]:
    """
    Purpose:
    Merge only allowed AI-refined fields into deterministic strategy.

    Arguments:
    deterministic_strategy: original deterministic strategy dictionary
    ai_response: Groq JSON response dictionary

    Returns:
    merged strategy dictionary
    """
    if not isinstance(ai_response, dict):
        raise ValueError("AI refinement response must be a dictionary")

    _ensure_schema_compatible(deterministic_strategy, ai_response)
    _ensure_frozen_fields_unchanged(deterministic_strategy, ai_response)

    merged_strategy = deepcopy(deterministic_strategy)

    for field in REFINABLE_FIELDS:
        if field in ai_response:
            merged_strategy[field] = ai_response[field]

    return merged_strategy


def _ensure_schema_compatible(
    deterministic_strategy: dict[str, Any],
    ai_response: dict[str, Any],
) -> None:
    """
    Purpose:
    Ensure AI response uses only known strategy fields.

    Arguments:
    deterministic_strategy: original deterministic strategy dictionary
    ai_response: Groq JSON response dictionary

    Returns:
    None
    """
    unknown_fields = set(ai_response) - set(deterministic_strategy)

    if unknown_fields:
        unknown = ", ".join(sorted(unknown_fields))
        raise ValueError(f"AI refinement returned unknown fields: {unknown}")


def _ensure_frozen_fields_unchanged(
    deterministic_strategy: dict[str, Any],
    ai_response: dict[str, Any],
) -> None:
    """
    Purpose:
    Ensure AI response does not alter non-refinable deterministic fields.

    Arguments:
    deterministic_strategy: original deterministic strategy dictionary
    ai_response: Groq JSON response dictionary

    Returns:
    None
    """
    frozen_fields = set(deterministic_strategy) - REFINABLE_FIELDS

    for field in frozen_fields:
        if field in ai_response and ai_response[field] != deterministic_strategy.get(field):
            raise ValueError(f"AI refinement changed frozen field: {field}")


def _sample_editorial() -> dict[str, Any]:
    """
    Purpose:
    Provide a sample editorial object for demonstration.

    Arguments:
    None

    Returns:
    sample editorial dictionary
    """
    return {
        "story_type": "simple_news",
        "main_entities": ["Netflix"],
        "story_summary": "Netflix series is trending.",
        "why_people_care": "Viewers are looking for streaming recommendations.",
        "primary_conflict": "unknown",
        "confidence": 0.72,
        "editorial_tags": ["streaming", "series"],
        "risk_level": "low",
        "evergreen": False,
    }


def _sample_strategy() -> dict[str, Any]:
    """
    Purpose:
    Provide a sample deterministic strategy for demonstration.

    Arguments:
    None

    Returns:
    sample strategy dictionary
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
        "strategy_confidence": 0.82,
        "fallback_used": False,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    editorial_sample = _sample_editorial()
    strategy_sample = _sample_strategy()

    if GROQ_API_KEY:
        result = refine_strategy(editorial_sample, strategy_sample)
        print(json.dumps(result, indent=4))
    else:
        print(json.dumps(refine_strategy(editorial_sample, strategy_sample), indent=4))
