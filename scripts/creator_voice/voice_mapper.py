"""
Purpose:
Build deterministic Creator Voice blueprints from script generation records.

Input:
one validated Script Generation record or a sequence of records

Output:
voice blueprint dictionaries for downstream Creator Voice transformation
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

try:
    from scripts.creator_voice.voice_constitution import (
        get_voice_metadata,
        get_voice_targets,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution support
    from voice_constitution import get_voice_metadata, get_voice_targets


REQUIRED_FIELDS = ("trend_id", "narration")


def build_voice_blueprint(record: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Build one deterministic voice blueprint from one script generation record.

    Arguments:
    record: validated Script Generation record

    Returns:
    mapped voice blueprint dictionary or deterministic error object
    """
    if not isinstance(record, dict):
        return _error_response("invalid_record", "Record must be a dictionary.")

    missing_fields = _missing_required_fields(record)

    if missing_fields:
        return _error_response(
            "missing_required_fields",
            "Required fields are missing.",
            missing_fields,
            record,
        )

    metadata = record.get("metadata")

    return {
        "trend_id": record["trend_id"],
        "voice_blueprint": _build_blueprint(record),
        "narration": record["narration"],
        "metadata": metadata if isinstance(metadata, dict) else {},
    }


def map_voice_records(records: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    """
    Purpose:
    Build deterministic voice blueprints for multiple records.

    Arguments:
    records: iterable of Script Generation records

    Returns:
    immutable tuple of mapped voice blueprint dictionaries
    """
    if not isinstance(records, Iterable):
        return (_error_response("invalid_records", "Records must be iterable."),)

    return tuple(build_voice_blueprint(record) for record in records)


def _build_blueprint(record: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Build voice blueprint metadata without modifying narration.

    Arguments:
    record: validated Script Generation record

    Returns:
    voice blueprint dictionary
    """
    voice_metadata = get_voice_metadata()
    voice_targets = get_voice_targets()
    strategy = record.get("strategy")

    return {
        "voice_name": voice_metadata["voice_name"],
        "voice_version": voice_metadata["voice_version"],
        "tone": _choose_tone(record),
        "energy": voice_targets["energy_level"],
        "curiosity": voice_targets["curiosity_level"],
        "sentence_style": _sentence_style(voice_targets),
        "transition_style": "smooth_spoken_transitions",
        "hook_priority": _hook_priority(strategy),
        "ending_style": voice_targets["preferred_ending_style"],
        "preserve_entities": True,
        "preserve_numbers": True,
        "preserve_dates": True,
        "preserve_order": True,
    }


def _choose_tone(record: dict[str, Any]) -> str:
    """
    Purpose:
    Select tone from available structured metadata.

    Arguments:
    record: validated Script Generation record

    Returns:
    tone label
    """
    metadata = record.get("metadata")

    if isinstance(metadata, dict) and metadata.get("risk_level") == "high":
        return "careful_confident"

    return "clear_confident"


def _sentence_style(voice_targets: dict[str, Any]) -> str:
    """
    Purpose:
    Build sentence style label from constitution targets.

    Arguments:
    voice_targets: immutable voice target mapping

    Returns:
    sentence style label
    """
    sentence_range = voice_targets["preferred_sentence_range_words"]
    return f"short_spoken_{sentence_range[0]}_to_{sentence_range[1]}_words"


def _hook_priority(strategy: Any) -> bool:
    """
    Purpose:
    Determine whether hook priority is enabled from structured strategy data.

    Arguments:
    strategy: optional strategy dictionary

    Returns:
    hook priority flag
    """
    if not isinstance(strategy, dict):
        return True

    return strategy.get("curiosity_gap") not in {"none", "low"}


def _missing_required_fields(record: dict[str, Any]) -> tuple[str, ...]:
    """
    Purpose:
    Identify missing required input fields.

    Arguments:
    record: input record

    Returns:
    missing field names
    """
    return tuple(field for field in REQUIRED_FIELDS if field not in record)


def _error_response(
    code: str,
    message: str,
    missing_fields: tuple[str, ...] = (),
    record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Purpose:
    Build structured deterministic error object.

    Arguments:
    code: error code
    message: error message
    missing_fields: missing required fields
    record: optional source record

    Returns:
    error dictionary
    """
    return {
        "trend_id": _safe_trend_id(record),
        "error": {
            "code": code,
            "message": message,
            "missing_fields": missing_fields,
        },
        "voice_blueprint": {},
        "narration": _safe_narration(record),
        "metadata": _safe_metadata(record),
    }


def _safe_trend_id(record: dict[str, Any] | None) -> str | None:
    """
    Purpose:
    Preserve trend identifier when safely available.

    Arguments:
    record: optional source record

    Returns:
    trend identifier or None
    """
    if not isinstance(record, dict):
        return None

    trend_id = record.get("trend_id")
    return trend_id if isinstance(trend_id, str) and trend_id else None


def _safe_narration(record: dict[str, Any] | None) -> str | None:
    """
    Purpose:
    Preserve narration when safely available.

    Arguments:
    record: optional source record

    Returns:
    narration or None
    """
    if not isinstance(record, dict):
        return None

    narration = record.get("narration")
    return narration if isinstance(narration, str) else None


def _safe_metadata(record: dict[str, Any] | None) -> dict[str, Any]:
    """
    Purpose:
    Preserve metadata when safely available.

    Arguments:
    record: optional source record

    Returns:
    metadata dictionary
    """
    if not isinstance(record, dict):
        return {}

    metadata = record.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _self_test_valid_record_mapping() -> bool:
    """
    Purpose:
    Verify valid record mapping.

    Arguments:
    None

    Returns:
    test result
    """
    record = _sample_record()
    mapped = build_voice_blueprint(record)
    return mapped["trend_id"] == record["trend_id"] and "error" not in mapped


def _self_test_missing_narration() -> bool:
    """
    Purpose:
    Verify missing narration creates an error object.

    Arguments:
    None

    Returns:
    test result
    """
    record = _sample_record()
    record.pop("narration")
    mapped = build_voice_blueprint(record)
    return mapped.get("error", {}).get("missing_fields") == ("narration",)


def _self_test_missing_trend_id() -> bool:
    """
    Purpose:
    Verify missing trend identifier creates an error object.

    Arguments:
    None

    Returns:
    test result
    """
    record = _sample_record()
    record.pop("trend_id")
    mapped = build_voice_blueprint(record)
    return mapped.get("error", {}).get("missing_fields") == ("trend_id",)


def _self_test_blueprint_fields_exist() -> bool:
    """
    Purpose:
    Verify expected blueprint fields exist.

    Arguments:
    None

    Returns:
    test result
    """
    fields = {
        "voice_name",
        "voice_version",
        "tone",
        "energy",
        "curiosity",
        "sentence_style",
        "transition_style",
        "hook_priority",
        "ending_style",
        "preserve_entities",
        "preserve_numbers",
        "preserve_dates",
        "preserve_order",
    }
    mapped = build_voice_blueprint(_sample_record())
    return fields <= set(mapped["voice_blueprint"])


def _self_test_narration_unchanged() -> bool:
    """
    Purpose:
    Verify narration is preserved exactly.

    Arguments:
    None

    Returns:
    test result
    """
    record = _sample_record()
    mapped = build_voice_blueprint(record)
    return mapped["narration"] == record["narration"]


def _self_test_metadata_preserved() -> bool:
    """
    Purpose:
    Verify metadata is preserved exactly.

    Arguments:
    None

    Returns:
    test result
    """
    record = _sample_record()
    mapped = build_voice_blueprint(record)
    return mapped["metadata"] == record["metadata"]


def _sample_record() -> dict[str, Any]:
    """
    Purpose:
    Build sample Script Generation record for self-tests.

    Arguments:
    None

    Returns:
    sample record
    """
    return {
        "trend_id": "trend_001",
        "strategy": {
            "curiosity_gap": "moderate",
        },
        "narration": "A new entertainment story is getting attention online.",
        "metadata": {
            "risk_level": "low",
            "source": "script_generation",
        },
    }


if __name__ == "__main__":
    tests = (
        _self_test_valid_record_mapping(),
        _self_test_missing_narration(),
        _self_test_missing_trend_id(),
        _self_test_blueprint_fields_exist(),
        _self_test_narration_unchanged(),
        _self_test_metadata_preserved(),
    )
    print("PASS" if all(tests) else "FAIL")
