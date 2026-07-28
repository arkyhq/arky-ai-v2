"""
Purpose:
Validate AI-generated Creator Voice output before engine acceptance.

Input:
one Creator Voice output record or a sequence of output records

Output:
deterministic validation reports for safety, structure, and compliance
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

try:
    from scripts.creator_voice.voice_constitution import get_forbidden_rules
except ModuleNotFoundError:  # pragma: no cover - direct script execution support
    from voice_constitution import get_forbidden_rules


VALIDATED_STAGE = "voice_output_validator"
PASS_SEVERITY = "PASS"
WARNING_SEVERITY = "WARNING"
FAIL_SEVERITY = "FAIL"

REQUIRED_FIELDS = (
    "trend_id",
    "voice_script",
    "metadata",
    "generation_source",
    "fallback_used",
)

FIELD_TYPES = {
    "trend_id": str,
    "voice_script": str,
    "metadata": dict,
    "generation_source": str,
    "fallback_used": bool,
}

ALLOWED_GENERATION_SOURCES = frozenset({"groq", "fallback"})

ERROR_MESSAGES = {
    "VOICE101": "Empty voice script.",
    "VOICE102": "Prompt leakage detected.",
    "VOICE103": "Planning language detected.",
    "VOICE104": "Markdown or HTML detected.",
    "VOICE105": "Sentence fragment detected.",
    "VOICE106": "Repetition detected.",
    "VOICE107": "Constitution violation detected.",
    "VOICE108": "Entity mismatch detected.",
    "VOICE109": "Number or date mismatch detected.",
    "VOICE110": "Invalid output structure.",
}

PROMPT_LEAKAGE_PATTERNS = (
    r"\bhere is (your|the)\b",
    r"\bas requested\b",
    r"\breturn json\b",
    r"\bjson only\b",
    r"\binput payload\b",
    r"\boutput schema\b",
    r"\bthe prompt\b",
    r"\bprompt says\b",
)

PLANNING_LANGUAGE_PATTERNS = (
    r"\bopening goal\b",
    r"\bclosing goal\b",
    r"\bending objective\b",
    r"\btransition plan\b",
    r"\bbody section\b",
    r"\bviewer trigger\b",
    r"\bcuriosity gap\b",
    r"\bthe ending should\b",
    r"\bthe script should\b",
    r"\bthe strategy is\b",
)

MARKDOWN_HTML_PATTERNS = (
    r"```",
    r"^\s{0,3}#{1,6}\s+",
    r"\*\*[^*]+\*\*",
    r"^\s*[-*+]\s+",
    r"<[a-zA-Z][^>]*>",
    r"</[a-zA-Z][^>]*>",
)

AI_SELF_REFERENCE_PATTERNS = (
    r"\bas an ai\b",
    r"\bi am an ai\b",
    r"\bi cannot\b",
    r"\bi don't have access\b",
    r"\bmy training data\b",
)

PLACEHOLDER_PATTERNS = (
    r"\blorem ipsum\b",
    r"\bplaceholder\b",
    r"\btbd\b",
    r"\bto be added\b",
    r"\binsert\b.+\bhere\b",
)

FRAGMENT_STARTERS = frozenset(
    {
        "because",
        "although",
        "while",
        "if",
        "when",
        "since",
        "unless",
    }
)

NUMBER_DATE_PATTERN = re.compile(
    r"\b(?:\d+(?:[.,]\d+)*%?|\d{1,2}/\d{1,2}/\d{2,4}|"
    r"\d{4}|jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|"
    r"may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|"
    r"oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b",
    flags=re.IGNORECASE,
)

__all__ = ("validate_voice_output", "validate_voice_outputs")


def validate_voice_output(record: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Validate one Creator Voice output record.

    Arguments:
    record: Creator Voice output dictionary

    Returns:
    deterministic validation report
    """
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    info: dict[str, Any] = {}

    if not isinstance(record, dict):
        _add_issue(errors, "VOICE110", "record")
        return _build_report(errors, warnings, info)

    _validate_structure(record, errors)

    voice_script = record.get("voice_script")
    metadata = record.get("metadata")

    if isinstance(voice_script, str):
        script = voice_script.strip()
        info["word_count"] = _word_count(script)

        if not script:
            _add_issue(errors, "VOICE101", "voice_script")
        else:
            _validate_script_surface(script, errors)
            _validate_repetition(script, errors)
            _validate_preservation(script, metadata, errors, warnings)

    return _build_report(errors, warnings, info)


def validate_voice_outputs(
    records: Iterable[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """
    Purpose:
    Validate multiple Creator Voice output records.

    Arguments:
    records: iterable of Creator Voice output dictionaries

    Returns:
    immutable tuple of validation reports
    """
    if not isinstance(records, Iterable) or isinstance(records, (str, bytes)):
        return (validate_voice_output(records),)

    return tuple(validate_voice_output(record) for record in records)


def _validate_structure(
    record: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate required output fields and field types.

    Arguments:
    record: Creator Voice output dictionary
    errors: mutable validation error list

    Returns:
    None
    """
    for field in REQUIRED_FIELDS:
        if field not in record:
            _add_issue(errors, "VOICE110", field)
            continue

        value = record[field]

        if not isinstance(value, FIELD_TYPES[field]):
            _add_issue(errors, "VOICE110", field)
            continue

        if isinstance(value, str) and not value.strip():
            code = "VOICE101" if field == "voice_script" else "VOICE110"
            _add_issue(errors, code, field)

        if field == "metadata" and not value:
            _add_issue(errors, "VOICE110", field)

    generation_source = record.get("generation_source")
    if (
        isinstance(generation_source, str)
        and generation_source not in ALLOWED_GENERATION_SOURCES
    ):
        _add_issue(errors, "VOICE110", "generation_source")


def _validate_script_surface(
    script: str,
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate surface safety without rewriting narration.

    Arguments:
    script: Creator Voice script
    errors: mutable validation error list

    Returns:
    None
    """
    checks = (
        ("VOICE102", PROMPT_LEAKAGE_PATTERNS),
        ("VOICE103", PLANNING_LANGUAGE_PATTERNS),
        ("VOICE104", MARKDOWN_HTML_PATTERNS),
        ("VOICE107", AI_SELF_REFERENCE_PATTERNS),
        ("VOICE107", PLACEHOLDER_PATTERNS),
    )

    for code, patterns in checks:
        if _matches_any(script, patterns):
            _add_issue(errors, code, "voice_script")

    if _has_sentence_fragment(script):
        _add_issue(errors, "VOICE105", "voice_script")

    if _violates_forbidden_rules(script):
        _add_issue(errors, "VOICE107", "voice_script")


def _validate_repetition(
    script: str,
    errors: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Detect repeated sentences or paragraphs.

    Arguments:
    script: Creator Voice script
    errors: mutable validation error list

    Returns:
    None
    """
    sentences = _normalized_sentences(script)
    paragraphs = _normalized_paragraphs(script)

    if _has_duplicate_item(sentences) or _has_duplicate_item(paragraphs):
        _add_issue(errors, "VOICE106", "voice_script")


def _validate_preservation(
    script: str,
    metadata: Any,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    """
    Purpose:
    Validate metadata-based preservation hints when available.

    Arguments:
    script: Creator Voice script
    metadata: output metadata
    errors: mutable validation error list
    warnings: mutable validation warning list

    Returns:
    None
    """
    if not isinstance(metadata, dict) or not metadata:
        _add_issue(errors, "VOICE110", "metadata")
        return

    required_entities = _string_sequence(metadata.get("entities"))
    required_entities += _string_sequence(metadata.get("main_entities"))

    missing_entities = tuple(
        entity for entity in dict.fromkeys(required_entities)
        if entity and entity.lower() not in script.lower()
    )

    if missing_entities:
        _add_issue(errors, "VOICE108", "metadata.entities")

    source_text = _source_text(metadata)
    if source_text:
        source_values = set(_extract_number_date_values(source_text))
        output_values = set(_extract_number_date_values(script))

        if not source_values <= output_values:
            _add_issue(errors, "VOICE109", "voice_script")

    if not source_text and not required_entities:
        _add_issue(warnings, "VOICE107", "metadata")


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    """
    Purpose:
    Check text against deterministic regex patterns.

    Arguments:
    text: text to inspect
    patterns: regex patterns

    Returns:
    match flag
    """
    return any(re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE) for pattern in patterns)


def _has_sentence_fragment(script: str) -> bool:
    """
    Purpose:
    Detect obvious sentence fragments.

    Arguments:
    script: Creator Voice script

    Returns:
    sentence fragment flag
    """
    sentences = _sentence_candidates(script)

    for sentence in sentences:
        words = re.findall(r"[A-Za-z0-9']+", sentence)

        if not words:
            continue

        first_word = words[0].lower()
        has_terminal_punctuation = sentence.rstrip().endswith((".", "!", "?"))

        if first_word in FRAGMENT_STARTERS and len(words) < 5:
            return True

        if len(words) >= 4 and not has_terminal_punctuation:
            return True

    return False


def _violates_forbidden_rules(script: str) -> bool:
    """
    Purpose:
    Detect explicit forbidden constitution terms.

    Arguments:
    script: Creator Voice script

    Returns:
    constitution violation flag
    """
    lowered_script = script.lower()
    forbidden_terms = (
        "bullet list",
        "visual direction",
        "subtitle direction",
        "voice synthesis",
        "clickbait",
        "fabricated",
        "unsupported assumption",
    )
    constitution_terms = tuple(rule.rstrip(".").lower() for rule in get_forbidden_rules())

    return any(term in lowered_script for term in forbidden_terms + constitution_terms)


def _normalized_sentences(script: str) -> tuple[str, ...]:
    """
    Purpose:
    Normalize sentences for repetition checks.

    Arguments:
    script: Creator Voice script

    Returns:
    normalized sentence strings
    """
    return tuple(
        _normalize_text(sentence)
        for sentence in _sentence_candidates(script)
        if _normalize_text(sentence)
    )


def _normalized_paragraphs(script: str) -> tuple[str, ...]:
    """
    Purpose:
    Normalize paragraphs for repetition checks.

    Arguments:
    script: Creator Voice script

    Returns:
    normalized paragraph strings
    """
    return tuple(
        _normalize_text(paragraph)
        for paragraph in re.split(r"\n\s*\n", script)
        if _normalize_text(paragraph)
    )


def _sentence_candidates(script: str) -> tuple[str, ...]:
    """
    Purpose:
    Split script into sentence-like candidates.

    Arguments:
    script: Creator Voice script

    Returns:
    sentence candidate strings
    """
    return tuple(
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", script.strip())
        if sentence.strip()
    )


def _has_duplicate_item(items: tuple[str, ...]) -> bool:
    """
    Purpose:
    Detect duplicated normalized items.

    Arguments:
    items: normalized text items

    Returns:
    duplicate flag
    """
    return len(items) != len(set(items))


def _normalize_text(text: str) -> str:
    """
    Purpose:
    Normalize text for deterministic comparison.

    Arguments:
    text: source text

    Returns:
    normalized text
    """
    return re.sub(r"\s+", " ", text.strip().lower())


def _string_sequence(value: Any) -> tuple[str, ...]:
    """
    Purpose:
    Safely normalize metadata string sequences.

    Arguments:
    value: metadata value

    Returns:
    string tuple
    """
    if not isinstance(value, (list, tuple)):
        return ()

    return tuple(item.strip() for item in value if isinstance(item, str) and item.strip())


def _source_text(metadata: dict[str, Any]) -> str:
    """
    Purpose:
    Safely locate source text for preservation checks.

    Arguments:
    metadata: output metadata

    Returns:
    source text or empty string
    """
    for field in ("source_narration", "original_narration", "narration"):
        value = metadata.get(field)

        if isinstance(value, str) and value.strip():
            return value

    return ""


def _extract_number_date_values(text: str) -> tuple[str, ...]:
    """
    Purpose:
    Extract number and date-like values for preservation checks.

    Arguments:
    text: source text

    Returns:
    normalized number/date values
    """
    return tuple(match.group(0).lower() for match in NUMBER_DATE_PATTERN.finditer(text))


def _word_count(text: str) -> int:
    """
    Purpose:
    Count words in voice script.

    Arguments:
    text: Creator Voice script

    Returns:
    word count
    """
    return len(re.findall(r"\b\w+\b", text))


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
    code: stable issue code
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
    info: dict[str, Any],
) -> dict[str, Any]:
    """
    Purpose:
    Build stable Creator Voice output validation report.

    Arguments:
    errors: validation errors
    warnings: validation warnings
    info: validation metadata

    Returns:
    validation report dictionary
    """
    severity = FAIL_SEVERITY if errors else WARNING_SEVERITY if warnings else PASS_SEVERITY

    return {
        "valid": not errors,
        "severity": severity,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "info": info,
        "errors": errors,
        "warnings": warnings,
        "validated_at_stage": VALIDATED_STAGE,
    }


def _valid_record() -> dict[str, Any]:
    """
    Purpose:
    Build valid Creator Voice output record for self-tests.

    Arguments:
    None

    Returns:
    valid output record
    """
    script = "Taylor Swift announced 3 new shows in June. Fans are watching closely."

    return {
        "trend_id": "trend_001",
        "voice_script": script,
        "metadata": {
            "entities": ["Taylor Swift"],
            "source_narration": script,
        },
        "generation_source": "groq",
        "fallback_used": False,
    }


def _has_error(report: dict[str, Any], code: str) -> bool:
    """
    Purpose:
    Check whether a validation report contains an error code.

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
    Run deterministic self-tests.

    Arguments:
    None

    Returns:
    aggregate test result
    """
    empty_output = _valid_record()
    empty_output["voice_script"] = " "

    prompt_leakage = _valid_record()
    prompt_leakage["voice_script"] = "Here is your script. Taylor Swift announced 3 new shows in June."

    markdown = _valid_record()
    markdown["voice_script"] = "# Taylor Swift announced 3 new shows in June."

    html = _valid_record()
    html["voice_script"] = "<p>Taylor Swift announced 3 new shows in June.</p>"

    sentence_fragment = _valid_record()
    sentence_fragment["voice_script"] = "Because of."

    repeated_sentence = _valid_record()
    repeated_sentence["voice_script"] = (
        "Taylor Swift announced 3 new shows in June. "
        "Taylor Swift announced 3 new shows in June."
    )

    missing_metadata = _valid_record()
    missing_metadata.pop("metadata")

    missing_trend_id = _valid_record()
    missing_trend_id.pop("trend_id")

    tests = (
        validate_voice_output(_valid_record())["valid"],
        _has_error(validate_voice_output(empty_output), "VOICE101"),
        _has_error(validate_voice_output(prompt_leakage), "VOICE102"),
        _has_error(validate_voice_output(markdown), "VOICE104"),
        _has_error(validate_voice_output(html), "VOICE104"),
        _has_error(validate_voice_output(sentence_fragment), "VOICE105"),
        _has_error(validate_voice_output(repeated_sentence), "VOICE106"),
        _has_error(validate_voice_output(missing_metadata), "VOICE110"),
        _has_error(validate_voice_output(missing_trend_id), "VOICE110"),
        _has_error(validate_voice_output("invalid"), "VOICE110"),
    )

    return all(tests)


if __name__ == "__main__":
    print("PASS" if _run_self_tests() else "FAIL")
