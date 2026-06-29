"""
Purpose:
Map editorial intelligence into deterministic script strategy.

Input:
one editorial trend dictionary

Output:
one strategy dictionary
"""

from __future__ import annotations

import json
import logging
from copy import deepcopy
from typing import Any


logger = logging.getLogger(__name__)

LOW_CONFIDENCE_THRESHOLD = 0.5
HIGH_CONFIDENCE_THRESHOLD = 0.75
MEDIUM_CONFIDENCE_THRESHOLD = 0.6

SAFE_DEFAULT_STRATEGY = {
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

STORY_TYPE_ALIASES = {
    "controversy": "controversy",
    "creator_update": "creator_update",
    "tribute": "tribute",
    "meme": "meme",
    "wholesome": "wholesome",
    "viral_clip": "viral_clip",
    "industry_update": "industry_update",
    "community_discussion": "community_discussion",
    "simple_news": "simple_news",
    "audience_reaction": "audience_reaction",
    "nostalgic_moment": "nostalgic_moment",
    "creator_exposed": "creator_exposed",
    "gaming_integrity": "gaming_integrity",
    "entertainment": "simple_news",
    "historical event": "simple_news",
    "unknown": "unknown",
}

ARCHETYPE_RULES = {
    "controversy": {
        "opening_style": "conflict_first",
        "hook_direction": "why_people_are_reacting",
        "opening_intensity": "medium",
        "story_arc": "context_tension_payoff",
        "reveal_order": ["entity", "conflict", "reaction", "stakes", "caution"],
        "emotion_curve": ["curiosity", "concern", "clarity"],
        "viewer_trigger": "controversy",
        "retention_pattern": "escalating_reveals",
        "curiosity_gap": "moderate",
        "ending_style": "contextual_takeaway",
        "pacing": "medium",
        "information_density": "medium",
        "claim_safety": "careful",
    },
    "creator_update": {
        "opening_style": "entity_first",
        "hook_direction": "what_changed",
        "opening_intensity": "medium",
        "story_arc": "claim_context_implication",
        "reveal_order": ["entity", "key_detail", "why_it_matters", "payoff"],
        "emotion_curve": ["curiosity", "clarity", "resolution"],
        "viewer_trigger": "curiosity",
        "retention_pattern": "single_open_loop",
        "curiosity_gap": "moderate",
        "ending_style": "what_next",
        "pacing": "medium",
        "information_density": "medium",
        "claim_safety": "normal",
    },
    "tribute": {
        "opening_style": "entity_first",
        "hook_direction": "who_is_involved",
        "opening_intensity": "low",
        "story_arc": "moment_context_meaning",
        "reveal_order": ["entity", "context", "why_it_matters", "payoff"],
        "emotion_curve": ["admiration", "nostalgia", "resolution"],
        "viewer_trigger": "emotion",
        "retention_pattern": "linear_explanation",
        "curiosity_gap": "none",
        "ending_style": "soft_landing",
        "pacing": "slow",
        "information_density": "low",
        "claim_safety": "careful",
    },
    "meme": {
        "opening_style": "reaction_first",
        "hook_direction": "why_people_are_reacting",
        "opening_intensity": "high",
        "story_arc": "setup_reveal_reaction",
        "reveal_order": ["key_detail", "reaction", "context", "payoff"],
        "emotion_curve": ["amusement", "surprise", "clarity"],
        "viewer_trigger": "surprise",
        "retention_pattern": "reaction_build",
        "curiosity_gap": "light",
        "ending_style": "clean_resolution",
        "pacing": "fast",
        "information_density": "low",
        "claim_safety": "normal",
    },
    "wholesome": {
        "opening_style": "context_first",
        "hook_direction": "why_it_matters",
        "opening_intensity": "low",
        "story_arc": "moment_context_meaning",
        "reveal_order": ["context", "key_detail", "why_it_matters", "payoff"],
        "emotion_curve": ["admiration", "relief", "resolution"],
        "viewer_trigger": "emotion",
        "retention_pattern": "linear_explanation",
        "curiosity_gap": "none",
        "ending_style": "soft_landing",
        "pacing": "slow",
        "information_density": "low",
        "claim_safety": "normal",
    },
    "viral_clip": {
        "opening_style": "reaction_first",
        "hook_direction": "what_people_missed",
        "opening_intensity": "high",
        "story_arc": "setup_reveal_reaction",
        "reveal_order": ["key_detail", "context", "reaction", "payoff"],
        "emotion_curve": ["curiosity", "surprise", "clarity"],
        "viewer_trigger": "surprise",
        "retention_pattern": "delayed_context",
        "curiosity_gap": "moderate",
        "ending_style": "clean_resolution",
        "pacing": "fast",
        "information_density": "medium",
        "claim_safety": "normal",
    },
    "industry_update": {
        "opening_style": "stakes_first",
        "hook_direction": "what_changed",
        "opening_intensity": "medium",
        "story_arc": "claim_context_implication",
        "reveal_order": ["key_detail", "context", "stakes", "why_it_matters", "payoff"],
        "emotion_curve": ["curiosity", "clarity", "resolution"],
        "viewer_trigger": "utility",
        "retention_pattern": "contrast_pattern",
        "curiosity_gap": "light",
        "ending_style": "what_next",
        "pacing": "medium",
        "information_density": "high",
        "claim_safety": "normal",
    },
    "community_discussion": {
        "opening_style": "reaction_first",
        "hook_direction": "why_people_are_reacting",
        "opening_intensity": "medium",
        "story_arc": "question_answer_takeaway",
        "reveal_order": ["context", "reaction", "key_detail", "why_it_matters"],
        "emotion_curve": ["curiosity", "skepticism", "clarity"],
        "viewer_trigger": "social_proof",
        "retention_pattern": "reaction_build",
        "curiosity_gap": "light",
        "ending_style": "open_question",
        "pacing": "medium",
        "information_density": "medium",
        "claim_safety": "careful",
    },
    "simple_news": {
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
    },
    "audience_reaction": {
        "opening_style": "reaction_first",
        "hook_direction": "why_people_are_reacting",
        "opening_intensity": "medium",
        "story_arc": "setup_reveal_reaction",
        "reveal_order": ["reaction", "key_detail", "context", "payoff"],
        "emotion_curve": ["curiosity", "surprise", "clarity"],
        "viewer_trigger": "social_proof",
        "retention_pattern": "reaction_build",
        "curiosity_gap": "light",
        "ending_style": "audience_reflection",
        "pacing": "medium",
        "information_density": "medium",
        "claim_safety": "normal",
    },
    "nostalgic_moment": {
        "opening_style": "entity_first",
        "hook_direction": "why_it_matters",
        "opening_intensity": "low",
        "story_arc": "moment_context_meaning",
        "reveal_order": ["entity", "context", "why_it_matters", "payoff"],
        "emotion_curve": ["nostalgia", "admiration", "resolution"],
        "viewer_trigger": "nostalgia",
        "retention_pattern": "linear_explanation",
        "curiosity_gap": "none",
        "ending_style": "audience_reflection",
        "pacing": "slow",
        "information_density": "low",
        "claim_safety": "normal",
    },
    "creator_exposed": {
        "opening_style": "conflict_first",
        "hook_direction": "what_happened",
        "opening_intensity": "medium",
        "story_arc": "problem_response_outcome",
        "reveal_order": ["entity", "conflict", "reaction", "caution", "payoff"],
        "emotion_curve": ["curiosity", "concern", "skepticism"],
        "viewer_trigger": "controversy",
        "retention_pattern": "escalating_reveals",
        "curiosity_gap": "moderate",
        "ending_style": "contextual_takeaway",
        "pacing": "medium",
        "information_density": "medium",
        "claim_safety": "very_careful",
    },
    "gaming_integrity": {
        "opening_style": "stakes_first",
        "hook_direction": "why_it_matters",
        "opening_intensity": "medium",
        "story_arc": "problem_response_outcome",
        "reveal_order": ["entity", "conflict", "reaction", "stakes", "payoff"],
        "emotion_curve": ["curiosity", "concern", "clarity"],
        "viewer_trigger": "controversy",
        "retention_pattern": "escalating_reveals",
        "curiosity_gap": "moderate",
        "ending_style": "what_next",
        "pacing": "medium",
        "information_density": "medium",
        "claim_safety": "careful",
    },
}

CONFLICT_HINTS = ("unknown", "none", "unclear", "")
REACTION_HINTS = ("react", "reaction", "debate", "discussion", "viral", "people care")
IDENTITY_HINTS = ("fan", "community", "culture", "audience")


def normalize_story_type(story_type: Any) -> str:
    """
    Purpose:
    Normalize editorial story type into a strategy archetype.

    Arguments:
    story_type: editorial story type value

    Returns:
    strategy archetype
    """
    normalized = str(story_type or "unknown").strip().lower()
    return STORY_TYPE_ALIASES.get(normalized, "unknown")


def has_clear_conflict(editorial: dict[str, Any]) -> bool:
    """
    Purpose:
    Determine whether editorial input contains explicit conflict.

    Arguments:
    editorial: editorial trend dictionary

    Returns:
    True when conflict is explicit, otherwise False
    """
    conflict = str(editorial.get("primary_conflict", "") or "").strip().lower()
    return conflict not in CONFLICT_HINTS


def has_entities(editorial: dict[str, Any]) -> bool:
    """
    Purpose:
    Determine whether editorial input contains main entities.

    Arguments:
    editorial: editorial trend dictionary

    Returns:
    True when entities are present, otherwise False
    """
    entities = editorial.get("main_entities")
    return isinstance(entities, list) and bool(entities)


def get_confidence(editorial: dict[str, Any]) -> float:
    """
    Purpose:
    Read editorial confidence as a bounded number.

    Arguments:
    editorial: editorial trend dictionary

    Returns:
    confidence between 0.0 and 1.0
    """
    try:
        confidence = float(editorial.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0

    return max(0.0, min(1.0, confidence))


def get_risk_level(editorial: dict[str, Any]) -> str:
    """
    Purpose:
    Read editorial risk level.

    Arguments:
    editorial: editorial trend dictionary

    Returns:
    normalized risk level
    """
    risk_level = str(editorial.get("risk_level", "medium") or "medium").lower()
    return risk_level if risk_level in {"low", "medium", "high"} else "medium"


def choose_viewer_trigger(editorial: dict[str, Any], default_trigger: str) -> str:
    """
    Purpose:
    Choose viewer trigger from editorial relevance signals.

    Arguments:
    editorial: editorial trend dictionary
    default_trigger: archetype default trigger

    Returns:
    viewer trigger
    """
    why_people_care = str(editorial.get("why_people_care", "") or "").lower()
    tags = " ".join(str(tag).lower() for tag in editorial.get("editorial_tags", []) if tag)
    combined = f"{why_people_care} {tags}"

    if any(hint in combined for hint in REACTION_HINTS):
        return "social_proof"

    if any(hint in combined for hint in IDENTITY_HINTS):
        return "identity"

    return default_trigger


def apply_entity_rules(strategy: dict[str, Any], editorial: dict[str, Any]) -> None:
    """
    Purpose:
    Downgrade entity-led strategy when entities are absent.

    Arguments:
    strategy: strategy dictionary
    editorial: editorial trend dictionary

    Returns:
    None
    """
    if has_entities(editorial):
        return

    if strategy["opening_style"] == "entity_first":
        strategy["opening_style"] = "context_first"

    strategy["reveal_order"] = [
        item for item in strategy["reveal_order"] if item != "entity"
    ] or SAFE_DEFAULT_STRATEGY["reveal_order"]


def apply_conflict_rules(strategy: dict[str, Any], editorial: dict[str, Any]) -> None:
    """
    Purpose:
    Downgrade conflict-led strategy when conflict is absent.

    Arguments:
    strategy: strategy dictionary
    editorial: editorial trend dictionary

    Returns:
    None
    """
    if has_clear_conflict(editorial):
        return

    if strategy["opening_style"] == "conflict_first":
        strategy["opening_style"] = "context_first"

    if strategy["retention_pattern"] == "escalating_reveals":
        strategy["retention_pattern"] = "linear_explanation"

    strategy["curiosity_gap"] = downgrade_level(strategy["curiosity_gap"], "light")
    strategy["claim_safety"] = max_safety(strategy["claim_safety"], "careful")


def apply_low_confidence_rules(strategy: dict[str, Any], confidence: float) -> None:
    """
    Purpose:
    Apply conservative defaults for low-confidence stories.

    Arguments:
    strategy: strategy dictionary
    confidence: editorial confidence

    Returns:
    None
    """
    if confidence >= LOW_CONFIDENCE_THRESHOLD:
        return

    strategy["opening_intensity"] = "low"
    strategy["curiosity_gap"] = "none"
    strategy["claim_safety"] = max_safety(strategy["claim_safety"], "careful")
    strategy["pacing"] = downgrade_level(strategy["pacing"], "medium")
    strategy["information_density"] = downgrade_level(strategy["information_density"], "low")
    strategy["retention_pattern"] = "linear_explanation"


def apply_high_risk_rules(strategy: dict[str, Any], risk_level: str) -> None:
    """
    Purpose:
    Apply safety limits for high-risk stories.

    Arguments:
    strategy: strategy dictionary
    risk_level: editorial risk level

    Returns:
    None
    """
    if risk_level != "high":
        return

    strategy["opening_intensity"] = downgrade_level(strategy["opening_intensity"], "medium")
    strategy["curiosity_gap"] = downgrade_level(strategy["curiosity_gap"], "moderate")
    strategy["pacing"] = downgrade_level(strategy["pacing"], "medium")
    strategy["claim_safety"] = "very_careful"


def apply_evergreen_rules(strategy: dict[str, Any], editorial: dict[str, Any]) -> None:
    """
    Purpose:
    Soften urgency for evergreen stories.

    Arguments:
    strategy: strategy dictionary
    editorial: editorial trend dictionary

    Returns:
    None
    """
    if not bool(editorial.get("evergreen", False)):
        return

    if strategy["ending_style"] == "what_next":
        strategy["ending_style"] = "contextual_takeaway"

    strategy["pacing"] = downgrade_level(strategy["pacing"], "medium")


def downgrade_level(current: str, maximum: str) -> str:
    """
    Purpose:
    Cap intensity-like levels at a maximum.

    Arguments:
    current: current level
    maximum: maximum allowed level

    Returns:
    capped level
    """
    order = {"none": 0, "low": 0, "light": 1, "medium": 1, "moderate": 2, "fast": 2, "high": 2, "strong": 3}

    if order.get(current, 0) <= order.get(maximum, 0):
        return current

    return maximum


def max_safety(current: str, minimum: str) -> str:
    """
    Purpose:
    Raise claim safety to at least a minimum level.

    Arguments:
    current: current safety level
    minimum: minimum required safety level

    Returns:
    safety level
    """
    order = {"normal": 0, "careful": 1, "very_careful": 2}
    reverse_order = {value: key for key, value in order.items()}
    return reverse_order[max(order.get(current, 0), order.get(minimum, 0))]


def calculate_strategy_confidence(
    editorial: dict[str, Any],
    story_archetype: str,
    fallback_used: bool,
) -> float:
    """
    Purpose:
    Calculate confidence in deterministic strategy selection.

    Arguments:
    editorial: editorial trend dictionary
    story_archetype: selected story archetype
    fallback_used: whether fallback strategy was used

    Returns:
    strategy confidence
    """
    if fallback_used:
        return 0.0

    confidence = get_confidence(editorial)
    bonus = 0.1 if story_archetype != "unknown" else 0.0
    bonus += 0.05 if has_entities(editorial) else 0.0
    bonus += 0.05 if has_clear_conflict(editorial) else 0.0

    return round(max(0.0, min(1.0, confidence + bonus)), 2)


def map_strategy(editorial: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Convert one editorial object into one deterministic strategy object.

    Arguments:
    editorial: editorial trend dictionary

    Returns:
    strategy dictionary
    """
    story_archetype = normalize_story_type(editorial.get("story_type"))
    fallback_used = story_archetype == "unknown"

    if fallback_used:
        strategy = deepcopy(SAFE_DEFAULT_STRATEGY)
        logger.info("Using fallback strategy for unknown story type")
        return strategy

    strategy = deepcopy(ARCHETYPE_RULES[story_archetype])
    strategy["story_archetype"] = story_archetype
    strategy["fallback_used"] = False

    confidence = get_confidence(editorial)
    risk_level = get_risk_level(editorial)

    strategy["viewer_trigger"] = choose_viewer_trigger(editorial, strategy["viewer_trigger"])
    apply_entity_rules(strategy, editorial)
    apply_conflict_rules(strategy, editorial)
    apply_low_confidence_rules(strategy, confidence)
    apply_high_risk_rules(strategy, risk_level)
    apply_evergreen_rules(strategy, editorial)
    strategy["strategy_confidence"] = calculate_strategy_confidence(
        editorial,
        story_archetype,
        strategy["fallback_used"],
    )

    logger.info("Mapped strategy archetype: %s", story_archetype)
    return strategy


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    samples = [
        {
            "story_type": "controversy",
            "confidence": 0.82,
            "risk_level": "medium",
            "primary_conflict": "creator backlash",
            "why_people_care": "fans are debating the creator response",
            "evergreen": False,
            "editorial_tags": ["creator", "reaction"],
            "main_entities": ["Creator A"],
        },
        {
            "story_type": "tribute",
            "confidence": 0.72,
            "risk_level": "low",
            "primary_conflict": "unknown",
            "why_people_care": "audiences remember a beloved artist",
            "evergreen": True,
            "editorial_tags": ["nostalgia"],
            "main_entities": ["Artist B"],
        },
        {
            "story_type": "unknown",
            "confidence": 0.31,
            "risk_level": "high",
            "primary_conflict": "unknown",
            "why_people_care": "",
            "evergreen": False,
            "editorial_tags": [],
            "main_entities": [],
        },
    ]

    for sample in samples:
        print(json.dumps(map_strategy(sample), indent=4))
