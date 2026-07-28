"""
Purpose:
Build deterministic Visual Blueprints from Creator Voice records.

Input:
one validated Creator Voice record or a sequence of records

Output:
visual blueprint dictionaries containing planning metadata only
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

try:
    from scripts.visual_planning.visual_constitution import (
        get_quality_targets,
        get_visual_styles,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution support
    from visual_constitution import get_quality_targets, get_visual_styles


WORDS_PER_SECOND = 2.6
MIN_DURATION_SECONDS = 5
MIN_SCENE_COUNT = 1
LOW_PACING_WORD_LIMIT = 35
MODERATE_PACING_WORD_LIMIT = 80

__all__ = ("build_visual_blueprint", "build_visual_blueprints")


def build_visual_blueprint(record: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Build one deterministic Visual Blueprint from one Creator Voice record.

    Arguments:
    record: validated Creator Voice record

    Returns:
    Visual Blueprint dictionary
    """
    if not isinstance(record, dict):
        return _error_blueprint(None, "", {}, None)

    voice_script = _safe_text(record.get("voice_script"))
    metadata = record.get("metadata")
    word_count = _count_words(voice_script)
    sentence_count = _count_sentences(voice_script)
    estimated_duration = _estimate_duration(word_count)

    return {
        "trend_id": _safe_text(record.get("trend_id")),
        "voice_script": voice_script,
        "generation_source": _safe_text(record.get("generation_source")),
        "metadata": metadata if isinstance(metadata, dict) else {},
        "visual_blueprint": {
            "estimated_duration": estimated_duration,
            "estimated_scene_count": _estimate_scene_count(
                estimated_duration,
                sentence_count,
            ),
            "word_count": word_count,
            "sentence_count": sentence_count,
            "pacing": _determine_pacing(word_count),
            "scene_strategy": _determine_scene_strategy(sentence_count),
            "default_visual_style": _default_visual_style(),
        },
    }


def build_visual_blueprints(
    records: Iterable[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """
    Purpose:
    Build Visual Blueprints for multiple Creator Voice records.

    Arguments:
    records: iterable of validated Creator Voice records

    Returns:
    immutable tuple of Visual Blueprint dictionaries
    """
    if not isinstance(records, Iterable) or isinstance(records, (str, bytes)):
        return (build_visual_blueprint(records),)

    return tuple(build_visual_blueprint(record) for record in records)


def _safe_text(value: Any) -> str:
    """
    Purpose:
    Safely normalize optional text fields.

    Arguments:
    value: source value

    Returns:
    stripped text or empty string
    """
    return value.strip() if isinstance(value, str) else ""


def _count_words(text: str) -> int:
    """
    Purpose:
    Count spoken words in narration.

    Arguments:
    text: voice script

    Returns:
    word count
    """
    return len(re.findall(r"\b[\w']+\b", text))


def _count_sentences(text: str) -> int:
    """
    Purpose:
    Count sentence-like units in narration.

    Arguments:
    text: voice script

    Returns:
    sentence count
    """
    if not text.strip():
        return 0

    sentences = re.findall(r"[^.!?]+[.!?]", text)

    if sentences:
        return len(sentences)

    return 1


def _estimate_duration(word_count: int) -> int:
    """
    Purpose:
    Estimate spoken duration from word count.

    Arguments:
    word_count: number of spoken words

    Returns:
    estimated duration in seconds
    """
    if word_count <= 0:
        return 0

    return max(MIN_DURATION_SECONDS, round(word_count / WORDS_PER_SECOND))


def _estimate_scene_count(
    estimated_duration: int,
    sentence_count: int,
) -> int:
    """
    Purpose:
    Estimate scene count from duration and sentence count.

    Arguments:
    estimated_duration: estimated duration in seconds
    sentence_count: sentence count

    Returns:
    estimated scene count
    """
    if estimated_duration <= 0 or sentence_count <= 0:
        return 0

    quality_targets = get_quality_targets()
    min_scenes = max(MIN_SCENE_COUNT, quality_targets["minimum_scene_count"])
    max_scenes = quality_targets["maximum_scene_count"]
    scene_duration = quality_targets["preferred_scene_duration_seconds"][1]
    duration_based_count = round(estimated_duration / scene_duration)
    estimated_count = max(sentence_count, duration_based_count, min_scenes)

    return min(estimated_count, max_scenes)


def _determine_pacing(word_count: int) -> str:
    """
    Purpose:
    Determine deterministic pacing label from narration length.

    Arguments:
    word_count: number of spoken words

    Returns:
    pacing label
    """
    if word_count <= 0:
        return "none"

    if word_count <= LOW_PACING_WORD_LIMIT:
        return "light"

    if word_count <= MODERATE_PACING_WORD_LIMIT:
        return "moderate"

    return "dense"


def _determine_scene_strategy(sentence_count: int) -> str:
    """
    Purpose:
    Determine deterministic scene strategy label.

    Arguments:
    sentence_count: sentence count

    Returns:
    scene strategy label
    """
    if sentence_count <= 0:
        return "no_scene_strategy"

    if sentence_count == 1:
        return "single_visual_beat"

    return "sentence_aligned_visual_beats"


def _default_visual_style() -> str:
    """
    Purpose:
    Return the default visual style from the constitution.

    Arguments:
    None

    Returns:
    visual style label
    """
    return get_visual_styles()[0]


def _error_blueprint(
    trend_id: str | None,
    voice_script: str,
    metadata: dict[str, Any],
    generation_source: str | None,
) -> dict[str, Any]:
    """
    Purpose:
    Build deterministic error-safe Visual Blueprint.

    Arguments:
    trend_id: optional trend identifier
    voice_script: preserved voice script
    metadata: preserved metadata
    generation_source: optional generation source

    Returns:
    error-safe Visual Blueprint dictionary
    """
    return {
        "trend_id": trend_id or "",
        "voice_script": voice_script,
        "generation_source": generation_source or "",
        "metadata": metadata,
        "visual_blueprint": {
            "estimated_duration": 0,
            "estimated_scene_count": 0,
            "word_count": 0,
            "sentence_count": 0,
            "pacing": "none",
            "scene_strategy": "no_scene_strategy",
            "default_visual_style": _default_visual_style(),
        },
    }


def _sample_record(voice_script: str) -> dict[str, Any]:
    """
    Purpose:
    Build sample Creator Voice record for self-tests.

    Arguments:
    voice_script: sample voice script

    Returns:
    sample record
    """
    return {
        "trend_id": "trend_001",
        "voice_script": voice_script,
        "generation_source": "groq",
        "metadata": {"source": "creator_voice"},
    }


def _test_valid_record() -> bool:
    """
    Purpose:
    Verify valid record mapping.

    Arguments:
    None

    Returns:
    test result
    """
    mapped = build_visual_blueprint(
        _sample_record("A new entertainment story is getting attention online.")
    )
    return mapped["trend_id"] == "trend_001" and mapped["visual_blueprint"]["word_count"] > 0


def _test_empty_narration() -> bool:
    """
    Purpose:
    Verify empty narration mapping.

    Arguments:
    None

    Returns:
    test result
    """
    mapped = build_visual_blueprint(_sample_record(""))
    blueprint = mapped["visual_blueprint"]
    return blueprint["word_count"] == 0 and blueprint["estimated_scene_count"] == 0


def _test_one_sentence() -> bool:
    """
    Purpose:
    Verify one-sentence mapping.

    Arguments:
    None

    Returns:
    test result
    """
    mapped = build_visual_blueprint(_sample_record("This story is moving fast."))
    blueprint = mapped["visual_blueprint"]
    return blueprint["sentence_count"] == 1 and blueprint["scene_strategy"] == "single_visual_beat"


def _test_multiple_sentences() -> bool:
    """
    Purpose:
    Verify multi-sentence mapping.

    Arguments:
    None

    Returns:
    test result
    """
    mapped = build_visual_blueprint(
        _sample_record("The story is trending. Fans are reacting. Updates may follow.")
    )
    blueprint = mapped["visual_blueprint"]
    return (
        blueprint["sentence_count"] == 3
        and blueprint["scene_strategy"] == "sentence_aligned_visual_beats"
    )


def _test_long_narration() -> bool:
    """
    Purpose:
    Verify long narration pacing.

    Arguments:
    None

    Returns:
    test result
    """
    script = " ".join(["Entertainment"] * 90) + "."
    mapped = build_visual_blueprint(_sample_record(script))
    return mapped["visual_blueprint"]["pacing"] == "dense"


def _test_missing_metadata() -> bool:
    """
    Purpose:
    Verify missing metadata becomes an empty dictionary.

    Arguments:
    None

    Returns:
    test result
    """
    record = _sample_record("A short script.")
    record.pop("metadata")
    mapped = build_visual_blueprint(record)
    return mapped["metadata"] == {}


def _run_self_tests() -> bool:
    """
    Purpose:
    Run lightweight Visual Mapper self-tests.

    Arguments:
    None

    Returns:
    aggregate test result
    """
    tests = (
        _test_valid_record(),
        _test_empty_narration(),
        _test_one_sentence(),
        _test_multiple_sentences(),
        _test_long_narration(),
        _test_missing_metadata(),
    )
    return all(tests)


if __name__ == "__main__":
    print("PASS" if _run_self_tests() else "FAIL")
