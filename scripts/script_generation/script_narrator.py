"""
Purpose:
Convert a validated script blueprint into natural spoken narration.

Input:
one editorial dictionary, one strategy dictionary, and one validated script blueprint

Output:
one narration dictionary
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import GROQ_API_KEY
from scripts.ai.groq_client import request_json
from scripts.script_generation.script_output_validator import validate_narration_output


logger = logging.getLogger(__name__)

REQUIRED_NARRATION_FIELDS = {
    "script_id",
    "spoken_script",
    "estimated_duration_seconds",
    "word_count",
    "claim_safety",
    "generator",
    "fallback_used",
}

MAX_DURATION_DRIFT_SECONDS = 8
WORDS_PER_SECOND = {
    "slow": 2.0,
    "medium": 2.4,
    "fast": 2.8,
}

FORBIDDEN_PATTERNS = (
    r"```",
    r"\bcut to\b",
    r"\bshow\b",
    r"\bvoiceover\b",
    r"\bsubtitle\b",
    r"\bcaption\b",
    r"\bthumbnail\b",
)


def narrate_script(
    editorial: dict[str, Any],
    strategy: dict[str, Any],
    blueprint: dict[str, Any],
) -> dict[str, Any]:
    """
    Purpose:
    Produce one spoken narration from a validated script blueprint.

    Arguments:
    editorial: editorial intelligence dictionary
    strategy: strategy dictionary
    blueprint: validated script blueprint dictionary

    Returns:
    narration dictionary
    """
    try:
        logger.info("Script narration started")
        prompt = build_narration_prompt(editorial, strategy, blueprint)
        response = request_json(prompt)
        narration = _validate_narration_response(response, blueprint)
        logger.info("Script narration succeeded")
        return narration
    except Exception as exc:
        logger.warning("Fallback to deterministic narration: %s", exc)
        return build_fallback_narration(editorial, strategy, blueprint)


def build_narration_prompt(
    editorial: dict[str, Any],
    strategy: dict[str, Any],
    blueprint: dict[str, Any],
) -> str:
    """
    Purpose:
    Build Groq prompt for narration generation.

    Arguments:
    editorial: editorial intelligence dictionary
    strategy: strategy dictionary
    blueprint: validated script blueprint dictionary

    Returns:
    prompt text
    """
    payload = {
        "editorial_context": {
            "story_type": editorial.get("story_type"),
            "story_summary": editorial.get("story_summary"),
            "why_people_care": editorial.get("why_people_care"),
            "primary_conflict": editorial.get("primary_conflict"),
            "main_entities": editorial.get("main_entities"),
            "confidence": editorial.get("confidence"),
            "risk_level": editorial.get("risk_level"),
            "evergreen": editorial.get("evergreen"),
        },
        "strategy_constraints": {
            "story_archetype": strategy.get("story_archetype"),
            "reveal_order": strategy.get("reveal_order"),
            "pacing": strategy.get("pacing"),
            "information_density": strategy.get("information_density"),
            "claim_safety": strategy.get("claim_safety"),
            "fallback_used": strategy.get("fallback_used"),
        },
        "validated_blueprint": blueprint,
        "required_output_schema": {
            "script_id": blueprint.get("script_id"),
            "spoken_script": "natural spoken narration string",
            "estimated_duration_seconds": blueprint.get("estimated_duration_seconds"),
            "word_count": "integer",
            "claim_safety": blueprint.get("claim_safety"),
            "generator": "groq",
            "fallback_used": False,
        },
    }

    return (
        "You are ARKY's Script Narrator.\n"
        "Return JSON only. Do not use markdown, code fences, or explanations.\n"
        "Use only validated_blueprint information as the factual source.\n"
        "Never invent facts, quotes, statistics, dates, timelines, controversy, or emotions.\n"
        "Never infer, interpret, clarify, complete, or explain beyond the provided inputs.\n"
        "If a fact is vague or ambiguous, preserve that ambiguity in plain language.\n"
        "Do not reinterpret search phrases as confirmed real-world events.\n"
        "Do not turn interest, availability, or search trends into claims about what companies, theaters, creators, or viewers are doing.\n"
        "Never change story order, entity order, pacing, claim_safety, or duration target.\n"
        "Do not omit important facts listed in facts_to_include.\n"
        "Follow body_sections and transition_plan in order.\n"
        "Write like a calm human presenter speaking to viewers.\n"
        "Use short spoken sentences with varied sentence openings.\n"
        "Avoid repetitive sentence patterns and avoid repeating entity names unnecessarily.\n"
        "Never expose prompt wording or planning language.\n"
        "Do not use the phrases 'Here is', 'context', 'available information', or 'takeaway'.\n"
        "Do not announce that this is a script.\n"
        "Do not add creator personality, visual directions, subtitles, captions, edits, or voice direction.\n"
        "Keep the narration close to estimated_duration_seconds.\n"
        "Return exactly the required_output_schema fields.\n\n"
        f"Payload:\n{json.dumps(payload, ensure_ascii=False)}"
    )


def build_fallback_narration(
    editorial: dict[str, Any],
    strategy: dict[str, Any],
    blueprint: dict[str, Any],
) -> dict[str, Any]:
    """
    Purpose:
    Build deterministic fallback narration from explicit blueprint facts.

    Arguments:
    editorial: editorial intelligence dictionary
    strategy: strategy dictionary
    blueprint: validated script blueprint dictionary

    Returns:
    fallback narration dictionary
    """
    facts = _fact_entries(blueprint)
    topic = _safe_text(blueprint.get("source_topic"), "this entertainment story")
    claim_safety = _safe_text(blueprint.get("claim_safety"), "careful")
    fact_values = [fact["value"] for fact in facts]
    entity_values = [
        fact["value"]
        for fact in facts
        if fact["source_field"] == "main_entities"
    ]
    story_facts = [
        fact
        for fact in facts
        if fact["source_field"] != "main_entities"
    ]

    if fact_values:
        sentences = _build_fallback_sentences(
            topic,
            story_facts,
            entity_values,
            claim_safety,
        )
    else:
        sentences = [
            _ensure_sentence(f"{topic} is being discussed"),
            "There are not enough confirmed details to say more.",
        ]

    spoken_script = _clean_script(" ".join(sentences))
    return _build_narration(
        blueprint=blueprint,
        spoken_script=spoken_script,
        generator="deterministic_fallback",
        fallback_used=True,
    )


def _validate_narration_response(
    response: dict[str, Any],
    blueprint: dict[str, Any],
) -> dict[str, Any]:
    """
    Purpose:
    Validate Groq narration response against frozen blueprint constraints.

    Arguments:
    response: Groq JSON response dictionary
    blueprint: validated script blueprint dictionary

    Returns:
    validated narration dictionary
    """
    if not isinstance(response, dict):
        raise ValueError("Narration response must be a dictionary")

    missing_fields = REQUIRED_NARRATION_FIELDS - set(response)

    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"Narration response missing fields: {missing}")

    if response.get("script_id") != blueprint.get("script_id"):
        raise ValueError("Narration response changed script_id")

    if response.get("claim_safety") != blueprint.get("claim_safety"):
        raise ValueError("Narration response changed claim_safety")

    spoken_script = response.get("spoken_script")

    if not isinstance(spoken_script, str) or not spoken_script.strip():
        raise ValueError("Narration response has empty spoken_script")

    cleaned_script = _clean_script(spoken_script)
    _ensure_no_forbidden_output(cleaned_script)
    _ensure_entities_preserved(cleaned_script, blueprint)
    _ensure_duration_close(response, blueprint)

    narration = _build_narration(
        blueprint=blueprint,
        spoken_script=cleaned_script,
        generator="groq",
        fallback_used=False,
    )
    validate_narration_output(narration)
    return narration


def _build_narration(
    blueprint: dict[str, Any],
    spoken_script: str,
    generator: str,
    fallback_used: bool,
) -> dict[str, Any]:
    """
    Purpose:
    Build normalized narration output.

    Arguments:
    blueprint: validated script blueprint dictionary
    spoken_script: spoken narration text
    generator: generator identifier
    fallback_used: whether deterministic fallback was used

    Returns:
    narration dictionary
    """
    word_count = _word_count(spoken_script)
    return {
        "script_id": blueprint.get("script_id", "script_blueprint_unknown"),
        "spoken_script": spoken_script,
        "estimated_duration_seconds": _estimate_duration(
            word_count,
            blueprint.get("estimated_duration_seconds", 38),
        ),
        "word_count": word_count,
        "claim_safety": blueprint.get("claim_safety", "careful"),
        "generator": generator,
        "fallback_used": fallback_used,
    }


def _ensure_no_forbidden_output(spoken_script: str) -> None:
    """
    Purpose:
    Reject narration that contains non-narration production language.

    Arguments:
    spoken_script: spoken narration text

    Returns:
    None
    """
    lowered = spoken_script.lower()

    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, lowered):
            raise ValueError("Narration response contains forbidden production language")


def _ensure_entities_preserved(spoken_script: str, blueprint: dict[str, Any]) -> None:
    """
    Purpose:
    Ensure explicit blueprint entities are not omitted.

    Arguments:
    spoken_script: spoken narration text
    blueprint: validated script blueprint dictionary

    Returns:
    None
    """
    entity_order = blueprint.get("entity_order")

    if not isinstance(entity_order, list):
        return

    lowered_script = spoken_script.lower()

    for entity in entity_order:
        if isinstance(entity, str) and entity.strip() and entity.lower() not in lowered_script:
            raise ValueError(f"Narration response omitted entity: {entity}")


def _ensure_duration_close(response: dict[str, Any], blueprint: dict[str, Any]) -> None:
    """
    Purpose:
    Ensure model duration estimate stays close to blueprint target.

    Arguments:
    response: Groq JSON response dictionary
    blueprint: validated script blueprint dictionary

    Returns:
    None
    """
    try:
        response_duration = float(response.get("estimated_duration_seconds"))
        target_duration = float(blueprint.get("estimated_duration_seconds", 38))
    except (TypeError, ValueError):
        raise ValueError("Narration response duration is invalid")

    if abs(response_duration - target_duration) > MAX_DURATION_DRIFT_SECONDS:
        raise ValueError("Narration response changed duration significantly")


def _estimate_duration(word_count: int, fallback_duration: Any) -> int:
    """
    Purpose:
    Estimate spoken duration from word count and blueprint fallback.

    Arguments:
    word_count: narration word count
    fallback_duration: blueprint duration value

    Returns:
    estimated duration in seconds
    """
    try:
        target = int(round(float(fallback_duration)))
    except (TypeError, ValueError):
        target = 38

    if word_count <= 0:
        return target

    estimated = int(round(word_count / WORDS_PER_SECOND["medium"]))

    if abs(estimated - target) > MAX_DURATION_DRIFT_SECONDS:
        return target

    return max(20, min(70, estimated or target))


def _fact_entries(blueprint: dict[str, Any]) -> list[dict[str, str]]:
    """
    Purpose:
    Extract explicit fact entries from blueprint.

    Arguments:
    blueprint: validated script blueprint dictionary

    Returns:
    fact dictionaries
    """
    facts = blueprint.get("facts_to_include")

    if not isinstance(facts, list):
        return []

    entries = []
    seen = set()

    for fact in facts:
        if not isinstance(fact, dict):
            continue

        source_field = fact.get("source_field")
        value = fact.get("value")

        if not isinstance(source_field, str) or not source_field.strip():
            continue

        if not isinstance(value, str) or not value.strip():
            continue

        entry = {
            "source_field": source_field.strip(),
            "value": value.strip(),
        }
        key = (entry["source_field"].lower(), entry["value"].lower())

        if key in seen:
            continue

        seen.add(key)
        entries.append(entry)

    return entries


def _build_fallback_sentences(
    topic: str,
    story_facts: list[dict[str, str]],
    entity_values: list[str],
    claim_safety: str,
) -> list[str]:
    """
    Purpose:
    Build clean deterministic fallback narration sentences.

    Arguments:
    topic: source topic
    story_facts: explicit non-entity facts
    entity_values: explicit entity facts
    claim_safety: blueprint claim safety

    Returns:
    spoken fallback sentences
    """
    sentences = []

    if story_facts:
        sentences.extend(_fact_to_sentence(fact, claim_safety) for fact in story_facts)
    else:
        sentences.append(_ensure_sentence(f"{topic} is being discussed"))

    entity_sentence = _entity_sentence(entity_values)

    if entity_sentence:
        sentences.append(entity_sentence)

    closing = _closing_sentence(claim_safety)

    if closing:
        sentences.append(closing)

    return sentences


def _fact_to_sentence(fact: dict[str, str], claim_safety: str) -> str:
    """
    Purpose:
    Convert one explicit fact into cautious fallback narration.

    Arguments:
    fact: explicit fact dictionary
    claim_safety: blueprint claim safety

    Returns:
    fallback sentence
    """
    source_field = fact["source_field"]
    value = fact["value"]

    if source_field == "why_people_care":
        sentence = _reason_to_sentence(value)
    else:
        sentence = _statement_to_sentence(value)

    if claim_safety == "very_careful":
        return _ensure_sentence(_soften_claim(sentence))

    return _ensure_sentence(sentence)


def _statement_to_sentence(value: str) -> str:
    """
    Purpose:
    Convert an explicit statement into a complete fallback sentence.

    Arguments:
    value: explicit fact value

    Returns:
    complete sentence
    """
    cleaned = value.strip()

    if not cleaned:
        return "The topic is being discussed."

    if not _looks_like_sentence(cleaned):
        return f"The topic is {cleaned}"

    return _capitalize_first(cleaned)


def _reason_to_sentence(value: str) -> str:
    """
    Purpose:
    Convert explicit audience-interest text into a complete sentence.

    Arguments:
    value: explicit audience-interest value

    Returns:
    complete sentence
    """
    cleaned = value.strip()
    lowered = cleaned.lower()

    if not cleaned:
        return "People are interested in the topic."

    if lowered.startswith(("people ", "viewers ", "fans ", "audiences ", "users ")):
        return _capitalize_first(cleaned)

    if lowered.startswith("interest in "):
        return f"People are interested in {cleaned[12:].strip()}."

    if lowered.startswith("public interest in "):
        return f"People are interested in {cleaned[19:].strip()}."

    if lowered.startswith("to "):
        return f"People are looking {cleaned}."

    return f"People are interested in {cleaned}."


def _soften_claim(fact: str) -> str:
    """
    Purpose:
    Soften a high-risk fact without changing its meaning.

    Arguments:
    fact: explicit fact text

    Returns:
    cautious fact text
    """
    lowered = fact.strip().lower()

    if lowered.startswith(("claims", "a claim", "an allegation", "allegations")):
        return fact

    return f"People are discussing that {fact}"


def _entity_sentence(entity_values: list[str]) -> str:
    """
    Purpose:
    Build one natural entity sentence without repeating names excessively.

    Arguments:
    entity_values: explicit entity facts

    Returns:
    entity sentence or empty string
    """
    if not entity_values:
        return ""

    normalized_entities = _normalize_entities(entity_values)
    entities = _join_entities(normalized_entities[:2])
    return _ensure_sentence(f"The named topic includes {entities}")


def _normalize_entities(entity_values: list[str]) -> list[str]:
    """
    Purpose:
    Normalize explicit entity values into individual names.

    Arguments:
    entity_values: raw entity values

    Returns:
    normalized entity list
    """
    entities = []
    seen = set()

    for value in entity_values:
        for entity in value.split(","):
            normalized = entity.strip()

            if not normalized:
                continue

            key = normalized.lower()

            if key in seen:
                continue

            seen.add(key)
            entities.append(normalized)

    return entities


def _join_entities(entities: list[str]) -> str:
    """
    Purpose:
    Join explicit entities into natural spoken text.

    Arguments:
    entities: entity names

    Returns:
    joined entity text
    """
    if not entities:
        return ""

    if len(entities) == 1:
        return entities[0]

    return f"{entities[0]} and {entities[1]}"


def _capitalize_first(text: str) -> str:
    """
    Purpose:
    Capitalize the first character without changing the rest of the fact.

    Arguments:
    text: explicit fact text

    Returns:
    capitalized text
    """
    stripped = text.strip()

    if not stripped:
        return stripped

    return f"{stripped[0].upper()}{stripped[1:]}"


def _looks_like_sentence(text: str) -> bool:
    """
    Purpose:
    Detect whether a fact already reads like a complete sentence.

    Arguments:
    text: explicit fact text

    Returns:
    True when the text has a simple verb signal
    """
    lowered = text.lower()
    verb_patterns = (
        r"\b(is|are|was|were|be|being|been)\b",
        r"\b(has|have|had)\b",
        r"\b(do|does|did)\b",
        r"\b(can|could|will|would|should|may|might|must)\b",
        r"\b(want|wants|wanted)\b",
        r"\b(include|includes|included)\b",
        r"\b(trending|released|available|searching|discussing|gaining|facing|circulated)\b",
    )
    return any(re.search(pattern, lowered) for pattern in verb_patterns)


def _ensure_sentence(text: str) -> str:
    """
    Purpose:
    Ensure fallback narration fragments end as spoken sentences.

    Arguments:
    text: raw sentence text

    Returns:
    sentence text
    """
    cleaned = text.strip()

    if cleaned.endswith((".", "?", "!")):
        return cleaned

    return f"{cleaned}."


def _closing_sentence(claim_safety: str) -> str:
    """
    Purpose:
    Build a safe deterministic closing sentence.

    Arguments:
    claim_safety: blueprint claim safety

    Returns:
    closing sentence
    """
    if claim_safety == "very_careful":
        return "It is worth separating what is confirmed from what is still being debated."

    return ""


def _clean_script(spoken_script: str) -> str:
    """
    Purpose:
    Normalize narration text without changing facts.

    Arguments:
    spoken_script: raw narration text

    Returns:
    cleaned narration text
    """
    cleaned = re.sub(r"```(?:json)?", "", spoken_script, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _word_count(spoken_script: str) -> int:
    """
    Purpose:
    Count spoken narration words.

    Arguments:
    spoken_script: spoken narration text

    Returns:
    word count
    """
    return len(re.findall(r"\b[\w'-]+\b", spoken_script))


def _safe_text(value: Any, default: str) -> str:
    """
    Purpose:
    Read safe text with fallback.

    Arguments:
    value: raw text value
    default: fallback text

    Returns:
    text value
    """
    if not isinstance(value, str) or not value.strip():
        return default

    return value.strip()


def _sample_editorial() -> dict[str, Any]:
    """
    Purpose:
    Provide sample editorial object for demonstration.

    Arguments:
    None

    Returns:
    sample editorial dictionary
    """
    return {
        "topic": "Streaming series reaction",
        "story_type": "simple_news",
        "main_entities": ["Netflix"],
        "story_summary": "A streaming series is gaining attention online.",
        "why_people_care": "Viewers are discussing whether the series is worth watching.",
        "primary_conflict": "unknown",
        "confidence": 0.78,
        "risk_level": "low",
        "evergreen": False,
    }


def _sample_strategy() -> dict[str, Any]:
    """
    Purpose:
    Provide sample strategy object for demonstration.

    Arguments:
    None

    Returns:
    sample strategy dictionary
    """
    return {
        "story_archetype": "simple_news",
        "reveal_order": ["context", "key_detail", "why_it_matters", "payoff"],
        "pacing": "medium",
        "information_density": "medium",
        "claim_safety": "normal",
        "fallback_used": False,
    }


def _sample_blueprint() -> dict[str, Any]:
    """
    Purpose:
    Provide sample validated blueprint for demonstration.

    Arguments:
    None

    Returns:
    sample blueprint dictionary
    """
    return {
        "script_id": "script_blueprint_simple_news_streaming_series_reaction",
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
            },
            {
                "section_type": "why_it_matters",
                "source_fields": ["why_people_care"],
                "purpose": "connect the topic to viewer interest",
                "claim_safety": "careful",
            },
        ],
        "closing_goal": "end with a concise takeaway",
        "facts_to_include": [
            {
                "source_field": "story_summary",
                "value": "A streaming series is gaining attention online.",
            },
            {
                "source_field": "why_people_care",
                "value": "Viewers are discussing whether the series is worth watching.",
            },
            {
                "source_field": "main_entities",
                "value": "Netflix",
            },
        ],
        "facts_to_avoid": [
            "quotes not present in editorial input",
            "statistics not present in editorial input",
            "dates not present in editorial input",
        ],
        "entity_order": ["Netflix"],
        "transition_plan": ["establish context", "connect to audience relevance", "deliver takeaway"],
        "ending_objective": "end with a concise takeaway",
        "claim_safety": "careful",
        "script_confidence": 0.81,
        "fallback_used": False,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    editorial_sample = _sample_editorial()
    strategy_sample = _sample_strategy()
    blueprint_sample = _sample_blueprint()

    if GROQ_API_KEY:
        result = narrate_script(editorial_sample, strategy_sample, blueprint_sample)
    else:
        result = build_fallback_narration(editorial_sample, strategy_sample, blueprint_sample)

    print(json.dumps(result, indent=4))
