"""
Purpose:
Validate and repair one narration output object.

Input:
one narration dictionary

Output:
one validated narration dictionary
"""

from __future__ import annotations

import logging
import re
from copy import deepcopy
from typing import Any


logger = logging.getLogger(__name__)


class NarrationOutputValidationError(ValueError):
    """
    Purpose:
    Report unrecoverable narration output validation failures.

    Input:
    validation failure details

    Output:
    explicit validation exception
    """


REQUIRED_FIELDS = {
    "script_id",
    "spoken_script",
    "estimated_duration_seconds",
    "word_count",
    "claim_safety",
    "generator",
    "fallback_used",
}

MIN_DURATION_SECONDS = 20
MAX_DURATION_SECONDS = 70

CLAIM_SAFETY_VALUES = {"normal", "careful", "very_careful"}
GENERATOR_VALUES = {"groq", "deterministic_fallback"}
SAFE_GENERATOR = "deterministic_fallback"

OPTIONAL_DEFAULTS = {
    "metadata": {},
}

FORBIDDEN_PATTERNS = {
    "markdown heading": re.compile(r"^\s{0,3}#{1,6}\s+", re.MULTILINE),
    "markdown code fence": re.compile(r"```"),
    "html": re.compile(r"<[^>]+>"),
    "ai disclaimer": re.compile(r"\bas an ai\b", re.IGNORECASE),
    "script preface": re.compile(r"\bhere is (your|the) script\b", re.IGNORECASE),
    "prompt leakage": re.compile(
        r"\b(prompt|instructions?|system message|developer message|required_output_schema)\b",
        re.IGNORECASE,
    ),
    "planning language": re.compile(
        r"\b(here is the context|what is clear|the ending should|the context is|central detail|key detail|"
        r"establish(?:es|ing)? context|connect(?:s|ing)? the topic|viewer interest|"
        r"the main thing to know|in conclusion|overall)\b",
        re.IGNORECASE,
    ),
    "factual expansion indicator": re.compile(
        r"\b(this proves|this means|this shows|serves as a reminder|"
        r"no wonder|everyone is talking|always exciting|did not disappoint)\b",
        re.IGNORECASE,
    ),
    "json fragment": re.compile(r'[{]\s*"[^"]+"\s*:'),
    "placeholder text": re.compile(
        r"\b(lorem ipsum|placeholder|insert here|todo|tbd|sample text)\b",
        re.IGNORECASE,
    ),
    "unfinished response": re.compile(r"(\.\.\.|[,;:]\s*)$"),
}


def validate_narration_output(narration: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Validate and repair one narration output object.

    Arguments:
    narration: narration dictionary

    Returns:
    validated narration dictionary
    """
    if not isinstance(narration, dict):
        raise NarrationOutputValidationError("Narration output must be a dictionary")

    missing_fields = REQUIRED_FIELDS - set(narration)

    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise NarrationOutputValidationError(f"Missing required narration fields: {missing}")

    repaired = deepcopy(narration)
    _repair_optional_metadata(repaired)
    _repair_text_fields(repaired)
    _repair_spoken_script(repaired)
    _validate_spoken_script_content(repaired["spoken_script"])
    _repair_duration(repaired)
    _repair_word_count(repaired)
    _repair_claim_safety(repaired)
    _repair_generator(repaired)
    _repair_fallback_flag(repaired)

    logger.info("Narration output validation completed")
    return repaired


def _repair_optional_metadata(narration: dict[str, Any]) -> None:
    """
    Purpose:
    Repair optional metadata field.

    Arguments:
    narration: narration dictionary

    Returns:
    None
    """
    if "metadata" not in narration or not isinstance(narration.get("metadata"), dict):
        narration["metadata"] = deepcopy(OPTIONAL_DEFAULTS["metadata"])


def _repair_text_fields(narration: dict[str, Any]) -> None:
    """
    Purpose:
    Repair non-script text fields without changing narration meaning.

    Arguments:
    narration: narration dictionary

    Returns:
    None
    """
    script_id = narration.get("script_id")

    if not isinstance(script_id, str) or not script_id.strip():
        raise NarrationOutputValidationError("script_id must be a non-empty string")

    narration["script_id"] = script_id.strip()


def _repair_spoken_script(narration: dict[str, Any]) -> None:
    """
    Purpose:
    Normalize whitespace in spoken narration.

    Arguments:
    narration: narration dictionary

    Returns:
    None
    """
    spoken_script = narration.get("spoken_script")

    if not isinstance(spoken_script, str):
        raise NarrationOutputValidationError("spoken_script must be a string")

    repaired = spoken_script.strip()
    repaired = re.sub(r"[ \t]+", " ", repaired)
    repaired = re.sub(r"\n\s*\n+", "\n\n", repaired)

    if not repaired:
        raise NarrationOutputValidationError("spoken_script is empty after repair")

    narration["spoken_script"] = repaired


def _validate_spoken_script_content(spoken_script: str) -> None:
    """
    Purpose:
    Reject narration content that is not clean spoken narration.

    Arguments:
    spoken_script: repaired narration text

    Returns:
    None
    """
    for label, pattern in FORBIDDEN_PATTERNS.items():
        if pattern.search(spoken_script):
            raise NarrationOutputValidationError(f"spoken_script contains {label}")

    if _has_duplicate_paragraph(spoken_script):
        raise NarrationOutputValidationError("spoken_script contains duplicate paragraph")

    if _has_duplicate_consecutive_sentence(spoken_script):
        raise NarrationOutputValidationError("spoken_script contains duplicate consecutive sentence")

    if _has_sentence_fragment(spoken_script):
        raise NarrationOutputValidationError("spoken_script contains sentence fragment")


def _repair_duration(narration: dict[str, Any]) -> None:
    """
    Purpose:
    Repair estimated duration into configured limits.

    Arguments:
    narration: narration dictionary

    Returns:
    None
    """
    try:
        duration = int(round(float(narration.get("estimated_duration_seconds"))))
    except (TypeError, ValueError):
        duration = MIN_DURATION_SECONDS

    if duration < 0:
        duration = abs(duration)

    narration["estimated_duration_seconds"] = max(
        MIN_DURATION_SECONDS,
        min(MAX_DURATION_SECONDS, duration),
    )


def _repair_word_count(narration: dict[str, Any]) -> None:
    """
    Purpose:
    Repair word count to match spoken narration.

    Arguments:
    narration: narration dictionary

    Returns:
    None
    """
    narration["word_count"] = _word_count(narration["spoken_script"])


def _repair_claim_safety(narration: dict[str, Any]) -> None:
    """
    Purpose:
    Validate claim safety without changing valid safety intent.

    Arguments:
    narration: narration dictionary

    Returns:
    None
    """
    value = narration.get("claim_safety")

    if not isinstance(value, str):
        raise NarrationOutputValidationError("claim_safety must be a string")

    normalized = value.strip().lower()

    if normalized not in CLAIM_SAFETY_VALUES:
        raise NarrationOutputValidationError("claim_safety has invalid value")

    narration["claim_safety"] = normalized


def _repair_generator(narration: dict[str, Any]) -> None:
    """
    Purpose:
    Repair invalid generator values using safe fallback.

    Arguments:
    narration: narration dictionary

    Returns:
    None
    """
    value = narration.get("generator")

    if not isinstance(value, str):
        narration["generator"] = SAFE_GENERATOR
        return

    normalized = value.strip().lower()
    narration["generator"] = normalized if normalized in GENERATOR_VALUES else SAFE_GENERATOR


def _repair_fallback_flag(narration: dict[str, Any]) -> None:
    """
    Purpose:
    Repair fallback flag into a boolean.

    Arguments:
    narration: narration dictionary

    Returns:
    None
    """
    value = narration.get("fallback_used")

    if isinstance(value, bool):
        return

    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in {"true", "1", "yes"}:
            narration["fallback_used"] = True
            return

        if normalized in {"false", "0", "no"}:
            narration["fallback_used"] = False
            return

    narration["fallback_used"] = narration.get("generator") == SAFE_GENERATOR


def _word_count(spoken_script: str) -> int:
    """
    Purpose:
    Count words in spoken narration.

    Arguments:
    spoken_script: spoken narration text

    Returns:
    word count
    """
    return len(re.findall(r"\b[\w'-]+\b", spoken_script))


def _has_duplicate_paragraph(spoken_script: str) -> bool:
    """
    Purpose:
    Detect repeated paragraphs.

    Arguments:
    spoken_script: spoken narration text

    Returns:
    True when duplicate paragraphs exist
    """
    paragraphs = [
        re.sub(r"\s+", " ", paragraph.strip()).lower()
        for paragraph in spoken_script.split("\n\n")
        if paragraph.strip()
    ]
    return len(paragraphs) != len(set(paragraphs))


def _has_duplicate_consecutive_sentence(spoken_script: str) -> bool:
    """
    Purpose:
    Detect repeated adjacent sentences.

    Arguments:
    spoken_script: spoken narration text

    Returns:
    True when adjacent duplicate sentences exist
    """
    sentences = [
        sentence.strip().lower()
        for sentence in re.split(r"(?<=[.!?])\s+", spoken_script)
        if sentence.strip()
    ]

    return any(current == previous for previous, current in zip(sentences, sentences[1:]))


def _has_sentence_fragment(spoken_script: str) -> bool:
    """
    Purpose:
    Detect obvious sentence fragments in narration.

    Arguments:
    spoken_script: spoken narration text

    Returns:
    True when obvious fragments exist
    """
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", spoken_script)
        if sentence.strip()
    ]

    for sentence in sentences:
        words = re.findall(r"\b[\w'-]+\b", sentence)

        if len(words) < 3:
            return True

        first_character = sentence.lstrip()[0]

        if not (first_character.isupper() or first_character.isdigit() or first_character in {"'", "\""}):
            return True

        if not _has_verb_signal(sentence):
            return True

    return False


def _has_verb_signal(sentence: str) -> bool:
    """
    Purpose:
    Detect whether a sentence has a basic verb signal.

    Arguments:
    sentence: narration sentence

    Returns:
    True when sentence appears complete
    """
    lowered = sentence.lower()
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


def _base_valid_narration() -> dict[str, Any]:
    """
    Purpose:
    Build a valid narration sample for self-tests.

    Arguments:
    None

    Returns:
    valid narration dictionary
    """
    script = (
        "A streaming series is gaining attention online. "
        "Viewers are discussing whether the series is worth watching. "
        "Netflix is at the center of this conversation."
    )
    return {
        "script_id": "script_blueprint_simple_news_streaming_series_reaction",
        "spoken_script": script,
        "estimated_duration_seconds": 45,
        "word_count": 999,
        "claim_safety": "careful",
        "generator": "groq",
        "fallback_used": False,
    }


def _run_test(name: str, narration: Any, expect_error: bool = False) -> None:
    """
    Purpose:
    Run one validator self-test and print PASS or FAIL.

    Arguments:
    name: test name
    narration: narration input
    expect_error: whether validation should fail

    Returns:
    None
    """
    try:
        validate_narration_output(narration)
        passed = not expect_error
    except NarrationOutputValidationError:
        passed = expect_error

    print(f"{name}: {'PASS' if passed else 'FAIL'}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    valid = _base_valid_narration()

    empty_narration = _base_valid_narration()
    empty_narration["spoken_script"] = "   "

    markdown_heading = _base_valid_narration()
    markdown_heading["spoken_script"] = "# Script\nA streaming series is gaining attention online."

    markdown_code_fence = _base_valid_narration()
    markdown_code_fence["spoken_script"] = "```json\nA streaming series is gaining attention online.\n```"

    html = _base_valid_narration()
    html["spoken_script"] = "<p>A streaming series is gaining attention online.</p>"

    ai_disclaimer = _base_valid_narration()
    ai_disclaimer["spoken_script"] = "As an AI, I can say a streaming series is gaining attention."

    duplicate_paragraph = _base_valid_narration()
    duplicate_paragraph["spoken_script"] = (
        "A streaming series is gaining attention online.\n\n"
        "A streaming series is gaining attention online."
    )

    incorrect_word_count = _base_valid_narration()
    incorrect_word_count["word_count"] = -10

    invalid_generator = _base_valid_narration()
    invalid_generator["generator"] = "unknown_provider"

    missing_required = _base_valid_narration()
    missing_required.pop("spoken_script")

    _run_test("valid narration", valid)
    _run_test("empty narration", empty_narration, expect_error=True)
    _run_test("markdown heading", markdown_heading, expect_error=True)
    _run_test("markdown code fence", markdown_code_fence, expect_error=True)
    _run_test("HTML", html, expect_error=True)
    _run_test("As an AI", ai_disclaimer, expect_error=True)
    _run_test("duplicate paragraph", duplicate_paragraph, expect_error=True)
    _run_test("incorrect word count", incorrect_word_count)
    _run_test("invalid generator", invalid_generator)
    _run_test("missing required field", missing_required, expect_error=True)
