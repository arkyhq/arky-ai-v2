"""
Purpose:
Map editorial and strategy objects into a deterministic script blueprint.

Input:
one editorial dictionary and one strategy dictionary

Output:
one script blueprint dictionary
"""

from __future__ import annotations

import json
import logging
from typing import Any


logger = logging.getLogger(__name__)

LOW_CONFIDENCE_THRESHOLD = 0.5
MEDIUM_CONFIDENCE_THRESHOLD = 0.7

DURATION_BY_PACING = {
    "slow": 42,
    "medium": 45,
    "fast": 38,
}

DURATION_BY_DENSITY = {
    "low": -6,
    "medium": 0,
    "high": 8,
}

LOW_CONFIDENCE_DURATION_CAP = 38
HIGH_RISK_DURATION_CAP = 40
MIN_DURATION_SECONDS = 30
MAX_DURATION_SECONDS = 60

SCRIPT_GOALS = {
    "controversy": "explain the discussion without escalating unverified claims",
    "creator_update": "summarize what changed and why viewers care",
    "tribute": "provide respectful context and emotional meaning",
    "meme": "explain the joke or reaction clearly",
    "wholesome": "highlight the positive moment and why it resonated",
    "viral_clip": "explain what caught attention and the reaction around it",
    "industry_update": "explain the update and its audience impact",
    "community_discussion": "summarize the debate and why the community is engaged",
    "simple_news": "deliver a clear update with context and takeaway",
    "audience_reaction": "explain what people are reacting to and why",
    "nostalgic_moment": "connect the moment to memory and meaning",
    "creator_exposed": "summarize the issue cautiously without asserting unverified claims",
    "gaming_integrity": "explain the integrity concern and audience stakes",
    "unknown": "explain the topic cautiously using only confirmed input details",
}

OPENING_GOALS = {
    "context_first": "start with the basic context",
    "conflict_first": "start with the central tension using cautious wording",
    "entity_first": "start by identifying the main entity",
    "question_first": "start with the question the story answers",
    "reaction_first": "start with the audience reaction",
    "stakes_first": "start with why the update matters",
    "timeline_first": "start with the sequence of events only if provided",
}

ENDING_OBJECTIVES = {
    "clean_resolution": "end with a concise takeaway",
    "open_question": "end by naming the unresolved audience question",
    "what_next": "end with what viewers should watch for next",
    "audience_reflection": "end by reflecting the audience reaction",
    "contextual_takeaway": "end with the broader context",
    "soft_landing": "end gently without adding new claims",
}

REVEAL_TO_SECTION = {
    "context": "context",
    "entity": "entity_setup",
    "key_detail": "key_detail",
    "conflict": "conflict",
    "reaction": "reaction",
    "stakes": "stakes",
    "timeline": "timeline",
    "why_it_matters": "why_it_matters",
    "payoff": "payoff",
    "caution": "caution",
}

REVEAL_TO_TRANSITION = {
    "context": "establish context",
    "entity": "identify main entity",
    "key_detail": "move to key detail",
    "conflict": "introduce tension cautiously",
    "reaction": "move to audience reaction",
    "stakes": "explain stakes",
    "timeline": "sequence known events",
    "why_it_matters": "connect to audience relevance",
    "payoff": "deliver takeaway",
    "caution": "add claim-safety context",
}

FACT_FIELDS_BY_REVEAL = {
    "context": ("story_summary",),
    "entity": ("main_entities",),
    "key_detail": ("story_summary",),
    "conflict": ("primary_conflict",),
    "reaction": ("why_people_care",),
    "stakes": ("why_people_care",),
    "timeline": (),
    "why_it_matters": ("why_people_care",),
    "payoff": ("story_summary", "why_people_care"),
    "caution": ("risk_level", "confidence"),
}

EMPTY_VALUES = {"", "unknown", "none", "unclear", "n/a"}


def map_script_blueprint(
    editorial: dict[str, Any],
    strategy: dict[str, Any],
) -> dict[str, Any]:
    """
    Purpose:
    Convert editorial and strategy objects into a deterministic script blueprint.

    Arguments:
    editorial: editorial intelligence dictionary
    strategy: script strategy dictionary

    Returns:
    script blueprint dictionary
    """
    editorial_confidence = _get_confidence(editorial)
    strategy_confidence = _get_strategy_confidence(strategy)
    risk_level = _get_risk_level(editorial)
    claim_safety = _choose_claim_safety(strategy, risk_level)
    fallback_used = bool(strategy.get("fallback_used")) or _is_low_confidence(
        editorial_confidence,
        strategy_confidence,
    )

    blueprint = {
        "script_id": _build_script_id(editorial, strategy),
        "source_topic": _get_source_topic(editorial),
        "script_goal": _choose_script_goal(strategy),
        "estimated_duration_seconds": _estimate_duration(
            strategy,
            editorial_confidence,
            strategy_confidence,
            risk_level,
        ),
        "opening_goal": _choose_opening_goal(strategy, fallback_used, risk_level),
        "body_sections": _build_body_sections(editorial, strategy, claim_safety),
        "closing_goal": _choose_closing_goal(strategy, fallback_used),
        "facts_to_include": _collect_facts_to_include(editorial),
        "facts_to_avoid": _collect_facts_to_avoid(editorial, strategy, risk_level),
        "entity_order": _get_entity_order(editorial),
        "transition_plan": _build_transition_plan(strategy),
        "ending_objective": _choose_ending_objective(strategy, fallback_used),
        "claim_safety": claim_safety,
        "script_confidence": _calculate_script_confidence(
            editorial_confidence,
            strategy_confidence,
            fallback_used,
        ),
        "fallback_used": fallback_used,
    }

    logger.info("Mapped script blueprint: %s", blueprint["script_id"])
    return blueprint


def _build_script_id(editorial: dict[str, Any], strategy: dict[str, Any]) -> str:
    """
    Purpose:
    Build a deterministic script blueprint identifier.

    Arguments:
    editorial: editorial intelligence dictionary
    strategy: script strategy dictionary

    Returns:
    script identifier
    """
    topic = _get_source_topic(editorial).lower().strip()
    archetype = str(strategy.get("story_archetype", "unknown") or "unknown").lower()
    normalized_topic = "_".join(topic.split())[:48] or "unknown_topic"
    return f"script_blueprint_{archetype}_{normalized_topic}"


def _get_source_topic(editorial: dict[str, Any]) -> str:
    """
    Purpose:
    Determine source topic from available editorial fields.

    Arguments:
    editorial: editorial intelligence dictionary

    Returns:
    source topic
    """
    for field in ("topic", "source_topic", "story_summary"):
        value = editorial.get(field)

        if _has_text(value):
            return str(value).strip()

    entities = _get_entity_order(editorial)
    return entities[0] if entities else "unknown topic"


def _choose_script_goal(strategy: dict[str, Any]) -> str:
    """
    Purpose:
    Choose the overall script objective from strategy archetype.

    Arguments:
    strategy: script strategy dictionary

    Returns:
    script goal
    """
    archetype = str(strategy.get("story_archetype", "unknown") or "unknown").lower()
    return SCRIPT_GOALS.get(archetype, SCRIPT_GOALS["unknown"])


def _estimate_duration(
    strategy: dict[str, Any],
    editorial_confidence: float,
    strategy_confidence: float,
    risk_level: str,
) -> int:
    """
    Purpose:
    Estimate blueprint target duration using pacing, density, confidence, and risk.

    Arguments:
    strategy: script strategy dictionary
    editorial_confidence: bounded editorial confidence
    strategy_confidence: bounded strategy confidence
    risk_level: normalized risk level

    Returns:
    estimated duration in seconds
    """
    pacing = str(strategy.get("pacing", "medium") or "medium").lower()
    density = str(strategy.get("information_density", "medium") or "medium").lower()
    duration = DURATION_BY_PACING.get(pacing, DURATION_BY_PACING["medium"])
    duration += DURATION_BY_DENSITY.get(density, DURATION_BY_DENSITY["medium"])

    if _is_low_confidence(editorial_confidence, strategy_confidence):
        duration = min(duration, LOW_CONFIDENCE_DURATION_CAP)

    if risk_level == "high":
        duration = min(duration, HIGH_RISK_DURATION_CAP)

    return max(MIN_DURATION_SECONDS, min(MAX_DURATION_SECONDS, duration))


def _choose_opening_goal(
    strategy: dict[str, Any],
    fallback_used: bool,
    risk_level: str,
) -> str:
    """
    Purpose:
    Choose opening planning goal without writing an opening sentence.

    Arguments:
    strategy: script strategy dictionary
    fallback_used: whether conservative fallback is active
    risk_level: normalized risk level

    Returns:
    opening goal
    """
    if fallback_used or risk_level == "high":
        return "start with neutral context and avoid dramatic framing"

    opening_style = str(strategy.get("opening_style", "context_first") or "context_first").lower()
    return OPENING_GOALS.get(opening_style, OPENING_GOALS["context_first"])


def _build_body_sections(
    editorial: dict[str, Any],
    strategy: dict[str, Any],
    claim_safety: str,
) -> list[dict[str, Any]]:
    """
    Purpose:
    Build ordered body planning sections from reveal order.

    Arguments:
    editorial: editorial intelligence dictionary
    strategy: script strategy dictionary
    claim_safety: selected claim safety

    Returns:
    body section dictionaries
    """
    sections = []
    reveal_order = strategy.get("reveal_order")

    if not isinstance(reveal_order, list) or not reveal_order:
        reveal_order = ["context", "key_detail", "why_it_matters", "payoff"]

    for reveal in reveal_order:
        reveal_name = str(reveal or "").strip().lower()
        section_type = REVEAL_TO_SECTION.get(reveal_name)

        if not section_type:
            continue

        sections.append(
            {
                "section_type": section_type,
                "source_fields": list(FACT_FIELDS_BY_REVEAL.get(reveal_name, ())),
                "purpose": _section_purpose(reveal_name, claim_safety),
                "claim_safety": claim_safety,
            }
        )

    return sections or [
        {
            "section_type": "context",
            "source_fields": ["story_summary"],
            "purpose": "establish the basic story context",
            "claim_safety": claim_safety,
        }
    ]


def _section_purpose(reveal: str, claim_safety: str) -> str:
    """
    Purpose:
    Describe section intent without generating narration.

    Arguments:
    reveal: reveal order item
    claim_safety: selected claim safety

    Returns:
    section purpose
    """
    caution = " with cautious wording" if claim_safety == "very_careful" else ""
    purposes = {
        "context": "establish the factual context",
        "entity": "identify the main entity",
        "key_detail": "cover the central detail",
        "conflict": "explain the stated tension",
        "reaction": "summarize audience reaction",
        "stakes": "explain why it matters",
        "timeline": "include only provided sequence details",
        "why_it_matters": "connect the topic to viewer interest",
        "payoff": "prepare the final takeaway",
        "caution": "add uncertainty or safety context",
    }
    return f"{purposes.get(reveal, 'advance the story flow')}{caution}"


def _choose_closing_goal(strategy: dict[str, Any], fallback_used: bool) -> str:
    """
    Purpose:
    Choose closing planning goal without writing a closing sentence.

    Arguments:
    strategy: script strategy dictionary
    fallback_used: whether conservative fallback is active

    Returns:
    closing goal
    """
    if fallback_used:
        return "close with a cautious factual takeaway"

    ending_style = str(strategy.get("ending_style", "clean_resolution") or "clean_resolution").lower()
    return ENDING_OBJECTIVES.get(ending_style, ENDING_OBJECTIVES["clean_resolution"])


def _collect_facts_to_include(editorial: dict[str, Any]) -> list[dict[str, str]]:
    """
    Purpose:
    Collect only explicit facts from editorial input.

    Arguments:
    editorial: editorial intelligence dictionary

    Returns:
    fact source dictionaries
    """
    facts = []

    for field in ("story_summary", "why_people_care", "primary_conflict"):
        value = editorial.get(field)

        if _has_text(value):
            facts.append({"source_field": field, "value": str(value).strip()})

    entities = _get_entity_order(editorial)

    if entities:
        facts.append({"source_field": "main_entities", "value": ", ".join(entities)})

    return facts


def _collect_facts_to_avoid(
    editorial: dict[str, Any],
    strategy: dict[str, Any],
    risk_level: str,
) -> list[str]:
    """
    Purpose:
    List fact categories the script generator must not invent.

    Arguments:
    editorial: editorial intelligence dictionary
    strategy: script strategy dictionary
    risk_level: normalized risk level

    Returns:
    forbidden fact categories
    """
    avoided = [
        "quotes not present in editorial input",
        "statistics not present in editorial input",
        "dates not present in editorial input",
        "timeline details not present in editorial input",
        "entities not present in main_entities",
        "opinions not present in editorial input",
    ]

    if risk_level == "high" or strategy.get("claim_safety") == "very_careful":
        avoided.extend(
            [
                "definitive blame",
                "unverified allegations",
                "dramatic escalation",
            ]
        )

    if not _has_text(editorial.get("primary_conflict")):
        avoided.append("invented conflict")

    return avoided


def _get_entity_order(editorial: dict[str, Any]) -> list[str]:
    """
    Purpose:
    Preserve explicit entity order from editorial input.

    Arguments:
    editorial: editorial intelligence dictionary

    Returns:
    ordered entity names
    """
    entities = editorial.get("main_entities")

    if not isinstance(entities, list):
        return []

    ordered_entities = []
    seen_entities = set()

    for entity in entities:
        if not _has_text(entity):
            continue

        normalized = str(entity).strip()
        key = normalized.lower()

        if key in seen_entities:
            continue

        seen_entities.add(key)
        ordered_entities.append(normalized)

    return ordered_entities


def _build_transition_plan(strategy: dict[str, Any]) -> list[str]:
    """
    Purpose:
    Build transition sequence from reveal order.

    Arguments:
    strategy: script strategy dictionary

    Returns:
    transition plan
    """
    reveal_order = strategy.get("reveal_order")

    if not isinstance(reveal_order, list):
        return ["establish context", "move to key detail", "deliver takeaway"]

    transitions = []

    for reveal in reveal_order:
        reveal_name = str(reveal or "").strip().lower()
        transition = REVEAL_TO_TRANSITION.get(reveal_name)

        if transition:
            transitions.append(transition)

    return transitions or ["establish context", "move to key detail", "deliver takeaway"]


def _choose_ending_objective(strategy: dict[str, Any], fallback_used: bool) -> str:
    """
    Purpose:
    Choose final objective for script ending.

    Arguments:
    strategy: script strategy dictionary
    fallback_used: whether conservative fallback is active

    Returns:
    ending objective
    """
    if fallback_used:
        return "leave the viewer with a safe factual takeaway"

    ending_style = str(strategy.get("ending_style", "clean_resolution") or "clean_resolution").lower()
    return ENDING_OBJECTIVES.get(ending_style, ENDING_OBJECTIVES["clean_resolution"])


def _choose_claim_safety(strategy: dict[str, Any], risk_level: str) -> str:
    """
    Purpose:
    Select claim safety from strategy and editorial risk.

    Arguments:
    strategy: script strategy dictionary
    risk_level: normalized risk level

    Returns:
    claim safety level
    """
    strategy_safety = str(strategy.get("claim_safety", "careful") or "careful").lower()
    order = {"normal": 0, "careful": 1, "very_careful": 2}
    reverse_order = {value: key for key, value in order.items()}
    required = "very_careful" if risk_level == "high" else "careful"
    return reverse_order[max(order.get(strategy_safety, 1), order[required])]


def _calculate_script_confidence(
    editorial_confidence: float,
    strategy_confidence: float,
    fallback_used: bool,
) -> float:
    """
    Purpose:
    Calculate confidence in the deterministic blueprint.

    Arguments:
    editorial_confidence: bounded editorial confidence
    strategy_confidence: bounded strategy confidence
    fallback_used: whether conservative fallback is active

    Returns:
    blueprint confidence
    """
    if fallback_used:
        return round(min(editorial_confidence, strategy_confidence, 0.45), 2)

    confidence = (editorial_confidence + strategy_confidence) / 2
    return round(max(0.0, min(1.0, confidence)), 2)


def _get_confidence(editorial: dict[str, Any]) -> float:
    """
    Purpose:
    Read editorial confidence as a bounded number.

    Arguments:
    editorial: editorial intelligence dictionary

    Returns:
    confidence between 0.0 and 1.0
    """
    return _bounded_float(editorial.get("confidence", 0.0))


def _get_strategy_confidence(strategy: dict[str, Any]) -> float:
    """
    Purpose:
    Read strategy confidence as a bounded number.

    Arguments:
    strategy: script strategy dictionary

    Returns:
    confidence between 0.0 and 1.0
    """
    return _bounded_float(strategy.get("strategy_confidence", 0.0))


def _get_risk_level(editorial: dict[str, Any]) -> str:
    """
    Purpose:
    Read normalized editorial risk level.

    Arguments:
    editorial: editorial intelligence dictionary

    Returns:
    normalized risk level
    """
    risk_level = str(editorial.get("risk_level", "medium") or "medium").lower()
    return risk_level if risk_level in {"low", "medium", "high"} else "medium"


def _is_low_confidence(editorial_confidence: float, strategy_confidence: float) -> bool:
    """
    Purpose:
    Determine whether conservative blueprint behavior is needed.

    Arguments:
    editorial_confidence: bounded editorial confidence
    strategy_confidence: bounded strategy confidence

    Returns:
    True when either confidence signal is low
    """
    return (
        editorial_confidence < LOW_CONFIDENCE_THRESHOLD
        or strategy_confidence < LOW_CONFIDENCE_THRESHOLD
    )


def _bounded_float(value: Any) -> float:
    """
    Purpose:
    Convert a value into a bounded confidence number.

    Arguments:
    value: raw confidence value

    Returns:
    bounded float
    """
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0

    return max(0.0, min(1.0, number))


def _has_text(value: Any) -> bool:
    """
    Purpose:
    Determine whether a value contains usable explicit text.

    Arguments:
    value: input value

    Returns:
    True when text is usable
    """
    if not isinstance(value, str):
        return False

    normalized = value.strip().lower()
    return normalized not in EMPTY_VALUES


def _sample_pairs() -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """
    Purpose:
    Provide sample editorial and strategy pairs for demonstration.

    Arguments:
    None

    Returns:
    sample editorial and strategy pairs
    """
    return [
        (
            {
                "topic": "Streaming series reaction",
                "story_type": "simple_news",
                "main_entities": ["Netflix"],
                "story_summary": "A streaming series is gaining attention online.",
                "why_people_care": "Viewers are discussing whether the series is worth watching.",
                "primary_conflict": "unknown",
                "confidence": 0.78,
                "editorial_tags": ["streaming", "series"],
                "risk_level": "low",
                "evergreen": False,
            },
            {
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
                "strategy_confidence": 0.84,
                "fallback_used": False,
            },
        ),
        (
            {
                "topic": "Creator allegation discussion",
                "story_type": "creator_exposed",
                "main_entities": ["Creator A"],
                "story_summary": "A creator is facing renewed discussion after claims circulated online.",
                "why_people_care": "Fans are debating the situation and waiting for verified updates.",
                "primary_conflict": "claims circulated online",
                "confidence": 0.46,
                "editorial_tags": ["creator", "discussion"],
                "risk_level": "high",
                "evergreen": False,
            },
            {
                "story_archetype": "creator_exposed",
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
                "strategy_confidence": 0.42,
                "fallback_used": False,
            },
        ),
        (
            {
                "topic": "Nostalgic actor moment",
                "story_type": "nostalgic_moment",
                "main_entities": ["Actor B"],
                "story_summary": "An old interview clip from an actor is being shared again.",
                "why_people_care": "Fans are revisiting a familiar moment from earlier entertainment culture.",
                "primary_conflict": "unknown",
                "confidence": 0.71,
                "editorial_tags": ["nostalgia", "actor"],
                "risk_level": "low",
                "evergreen": True,
            },
            {
                "story_archetype": "nostalgic_moment",
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
                "strategy_confidence": 0.76,
                "fallback_used": False,
            },
        ),
    ]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    for editorial_sample, strategy_sample in _sample_pairs():
        print(json.dumps(map_script_blueprint(editorial_sample, strategy_sample), indent=4))
