"""
Purpose:
Transform validated neutral narration into the canonical ARKY Creator Voice.

Input:
one validated Creator Voice record or a sequence of validated records

Output:
voice transformation dictionaries for downstream Creator Voice validation
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from typing import Any

try:
    from scripts.ai.groq_client import request_json
    from scripts.creator_voice.voice_constitution import (
        build_voice_guidelines,
        get_voice_metadata,
        get_voice_targets,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution support
    from voice_constitution import (
        build_voice_guidelines,
        get_voice_metadata,
        get_voice_targets,
    )

    request_json = None


GROQ_GENERATION_SOURCE = "groq"
FALLBACK_GENERATION_SOURCE = "fallback"
VOICE_SCRIPT_FIELD = "voice_script"

_GroqRequester = Callable[[str], dict[str, Any]]
_groq_requester: _GroqRequester | None = request_json

__all__ = ("transform_voice", "transform_voice_records")


def transform_voice(record: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Transform one validated narration into ARKY Creator Voice.

    Arguments:
    record: validated Creator Voice record

    Returns:
    voice transformation dictionary
    """
    narration = _extract_narration(record)

    if not narration:
        return _build_fallback(record)

    try:
        prompt = _build_prompt(record)
        response = _call_groq(prompt)

        if not _basic_response_check(response):
            return _build_fallback(record)

        return {
            "trend_id": _extract_trend_id(record),
            "voice_script": response[VOICE_SCRIPT_FIELD].strip(),
            "generation_source": GROQ_GENERATION_SOURCE,
            "fallback_used": False,
        }
    except Exception:
        return _build_fallback(record)


def transform_voice_records(
    records: Iterable[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """
    Purpose:
    Transform multiple validated narrations into ARKY Creator Voice.

    Arguments:
    records: iterable of validated Creator Voice records

    Returns:
    immutable tuple of transformation dictionaries
    """
    if not isinstance(records, Iterable) or isinstance(records, (str, bytes)):
        return (transform_voice(records),)

    return tuple(transform_voice(record) for record in records)


def _build_prompt(record: dict[str, Any]) -> str:
    """
    Purpose:
    Build the Creator Voice transformation prompt from constitution rules.

    Arguments:
    record: validated Creator Voice record

    Returns:
    prompt string
    """
    guidelines = "\n\n".join(build_voice_guidelines())
    voice_metadata = get_voice_metadata()
    voice_targets = get_voice_targets()
    payload = {
        "trend_id": _extract_trend_id(record),
        "narration": _extract_narration(record),
        "metadata": _safe_mapping(record, "metadata"),
        "voice_blueprint": _safe_mapping(record, "voice_blueprint"),
        "voice_targets": dict(voice_targets),
    }

    return (
        f"{voice_metadata['voice_name']} v{voice_metadata['voice_version']}\n\n"
        f"{guidelines}\n\n"
        "Task:\n"
        "Rewrite presentation only into the canonical ARKY Creator Voice.\n"
        "Preserve the exact meaning, facts, names, dates, numbers, chronology, "
        "editorial intent, strategy intent, and ambiguity.\n"
        "Do not add context, interpretation, speculation, or explanation.\n"
        "Do not remove facts from the source narration.\n"
        "Do not include markdown, HTML, code blocks, prompt leakage, planning "
        "language, or AI self-reference.\n\n"
        "Return JSON only with exactly this schema:\n"
        '{"voice_script": "final rewritten spoken narration"}\n\n'
        "Input:\n"
        f"{json.dumps(payload, ensure_ascii=True, sort_keys=True)}"
    )


def _call_groq(prompt: str) -> dict[str, Any]:
    """
    Purpose:
    Call the shared Groq JSON client.

    Arguments:
    prompt: Creator Voice transformation prompt

    Returns:
    parsed JSON response
    """
    if _groq_requester is None:
        raise RuntimeError("Groq requester is unavailable.")

    return _groq_requester(prompt)


def _basic_response_check(response: dict[str, Any]) -> bool:
    """
    Purpose:
    Check only basic response structure before downstream validation.

    Arguments:
    response: parsed Groq response

    Returns:
    response usability flag
    """
    if not isinstance(response, dict):
        return False

    voice_script = response.get(VOICE_SCRIPT_FIELD)

    return isinstance(voice_script, str) and bool(voice_script.strip())


def _build_fallback(record: dict[str, Any] | None) -> dict[str, Any]:
    """
    Purpose:
    Build deterministic fallback output without rewriting narration.

    Arguments:
    record: optional validated Creator Voice record

    Returns:
    fallback transformation dictionary
    """
    return {
        "trend_id": _extract_trend_id(record),
        "voice_script": _extract_narration(record),
        "generation_source": FALLBACK_GENERATION_SOURCE,
        "fallback_used": True,
    }


def _extract_trend_id(record: dict[str, Any] | None) -> str | None:
    """
    Purpose:
    Safely preserve trend identifier.

    Arguments:
    record: optional validated Creator Voice record

    Returns:
    trend identifier or None
    """
    if not isinstance(record, dict):
        return None

    trend_id = record.get("trend_id")
    return trend_id if isinstance(trend_id, str) and trend_id.strip() else None


def _extract_narration(record: dict[str, Any] | None) -> str:
    """
    Purpose:
    Safely preserve narration text.

    Arguments:
    record: optional validated Creator Voice record

    Returns:
    narration text or empty string
    """
    if not isinstance(record, dict):
        return ""

    narration = record.get("narration")

    if not isinstance(narration, str):
        return ""

    return narration.strip()


def _safe_mapping(record: dict[str, Any], field: str) -> dict[str, Any]:
    """
    Purpose:
    Safely preserve mapping fields for prompt context.

    Arguments:
    record: validated Creator Voice record
    field: mapping field name

    Returns:
    mapping value or empty dictionary
    """
    value = record.get(field)
    return value if isinstance(value, dict) else {}


def _sample_record() -> dict[str, Any]:
    """
    Purpose:
    Build a valid sample Creator Voice record for self-tests.

    Arguments:
    None

    Returns:
    sample record
    """
    voice_metadata = get_voice_metadata()
    voice_targets = get_voice_targets()

    return {
        "trend_id": "trend_001",
        "narration": "A new entertainment story is getting attention online.",
        "metadata": {"source": "script_generation"},
        "voice_blueprint": {
            "voice_name": voice_metadata["voice_name"],
            "voice_version": voice_metadata["voice_version"],
            "tone": "clear_confident",
            "energy": voice_targets["energy_level"],
            "curiosity": voice_targets["curiosity_level"],
            "sentence_style": "short_spoken_6_to_14_words",
            "transition_style": "smooth_spoken_transitions",
            "hook_priority": True,
            "ending_style": voice_targets["preferred_ending_style"],
            "preserve_entities": True,
            "preserve_numbers": True,
            "preserve_dates": True,
            "preserve_order": True,
        },
    }


def _with_stubbed_groq(
    stub: _GroqRequester | None,
    test: Callable[[], bool],
) -> bool:
    """
    Purpose:
    Run a self-test with a temporary Groq requester stub.

    Arguments:
    stub: temporary requester function
    test: self-test callable

    Returns:
    self-test result
    """
    global _groq_requester

    original_requester = _groq_requester
    _groq_requester = stub

    try:
        return test()
    finally:
        _groq_requester = original_requester


def _test_successful_transformation() -> bool:
    """
    Purpose:
    Verify successful mocked AI transformation.

    Arguments:
    None

    Returns:
    test result
    """
    return _with_stubbed_groq(
        lambda prompt: {"voice_script": "This story is getting attention now."},
        lambda: transform_voice(_sample_record()) == {
            "trend_id": "trend_001",
            "voice_script": "This story is getting attention now.",
            "generation_source": GROQ_GENERATION_SOURCE,
            "fallback_used": False,
        },
    )


def _test_empty_ai_response() -> bool:
    """
    Purpose:
    Verify empty AI response falls back.

    Arguments:
    None

    Returns:
    test result
    """
    return _with_stubbed_groq(
        lambda prompt: {"voice_script": " "},
        lambda: transform_voice(_sample_record())["fallback_used"] is True,
    )


def _test_exception_fallback() -> bool:
    """
    Purpose:
    Verify AI exceptions fall back.

    Arguments:
    None

    Returns:
    test result
    """
    def raise_error(prompt: str) -> dict[str, Any]:
        raise RuntimeError("stub failure")

    return _with_stubbed_groq(
        raise_error,
        lambda: transform_voice(_sample_record())["generation_source"]
        == FALLBACK_GENERATION_SOURCE,
    )


def _test_missing_narration() -> bool:
    """
    Purpose:
    Verify missing narration returns fallback.

    Arguments:
    None

    Returns:
    test result
    """
    record = _sample_record()
    record.pop("narration")
    result = transform_voice(record)
    return result["fallback_used"] is True and result["voice_script"] == ""


def _test_prompt_assembly() -> bool:
    """
    Purpose:
    Verify prompt contains constitution and input payload.

    Arguments:
    None

    Returns:
    test result
    """
    prompt = _build_prompt(_sample_record())
    required_text = (
        "Return JSON only",
        "Preserve every fact exactly.",
        "voice_blueprint",
        "trend_001",
    )
    return all(text in prompt for text in required_text)


def _run_self_tests() -> bool:
    """
    Purpose:
    Run deterministic transformer self-tests.

    Arguments:
    None

    Returns:
    aggregate test result
    """
    tests = (
        _test_successful_transformation(),
        _test_empty_ai_response(),
        _test_exception_fallback(),
        _test_missing_narration(),
        _test_prompt_assembly(),
    )
    return all(tests)


if __name__ == "__main__":
    print("PASS" if _run_self_tests() else "FAIL")
