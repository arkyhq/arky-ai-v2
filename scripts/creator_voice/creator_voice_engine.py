"""
Purpose:
Orchestrate the complete Creator Voice pipeline.

Input:
outputs/scripts.json

Output:
outputs/voice_scripts.json and execution summary
"""

from __future__ import annotations

import json
import logging
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.creator_voice.voice_mapper import build_voice_blueprint
from scripts.creator_voice.voice_output_validator import validate_voice_output
from scripts.creator_voice.voice_transformer import transform_voice
from scripts.creator_voice.voice_validator import validate_voice_blueprint


INPUT_SCRIPTS_PATH = PROJECT_ROOT / "outputs" / "scripts.json"
OUTPUT_VOICE_SCRIPTS_PATH = PROJECT_ROOT / "outputs" / "voice_scripts.json"
SUCCESS_STATUS = "passed"
FAILED_STATUS = "failed"

logger = logging.getLogger(__name__)

_build_voice_blueprint: Callable[[dict[str, Any]], dict[str, Any]] = build_voice_blueprint
_validate_voice_blueprint: Callable[[dict[str, Any]], dict[str, Any]] = validate_voice_blueprint
_transform_voice: Callable[[dict[str, Any]], dict[str, Any]] = transform_voice
_validate_voice_output: Callable[[dict[str, Any]], dict[str, Any]] = validate_voice_output

__all__ = ("run_creator_voice_engine", "process_record")


def run_creator_voice_engine() -> tuple[list[dict[str, Any]], dict[str, Any], Path]:
    """
    Purpose:
    Run the Creator Voice Engine orchestration.

    Arguments:
    None

    Returns:
    accepted voice scripts, execution summary, output path
    """
    started_at = time.perf_counter()
    input_records = _load_records(INPUT_SCRIPTS_PATH)
    output_records: list[dict[str, Any]] = []
    failed = 0
    warnings = 0
    fallback_used = 0

    for record in input_records:
        processed = process_record(record)

        if processed["status"] != SUCCESS_STATUS:
            failed += 1
            warnings += processed["warning_count"]
            continue

        output_records.append(processed["output"])
        warnings += processed["warning_count"]
        fallback_used += int(processed["output"]["fallback_used"])

    output_path = _save_records(output_records, OUTPUT_VOICE_SCRIPTS_PATH)
    summary = {
        "loaded": len(input_records),
        "processed": len(input_records),
        "passed": len(output_records),
        "failed": failed,
        "warnings": warnings,
        "fallback_used": fallback_used,
        "execution_time": round(time.perf_counter() - started_at, 3),
        "output_path": str(output_path),
    }

    logger.info("Creator Voice summary: %s", summary)
    return output_records, summary, output_path


def process_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Process one script record through the Creator Voice modules.

    Arguments:
    record: Script Generation output record

    Returns:
    per-record orchestration result
    """
    try:
        voice_input = _normalize_input_record(record)
        mapped = _build_voice_blueprint(voice_input)
        blueprint_report = _validate_voice_blueprint(mapped)

        if not blueprint_report["valid"]:
            return _failed_result("blueprint_validation_failed", blueprint_report)

        transformed = _transform_voice(mapped)
        output_record = _build_output_record(mapped, transformed)
        output_report = _validate_voice_output(output_record)

        if not output_report["valid"]:
            return _failed_result("output_validation_failed", output_report)

        return {
            "status": SUCCESS_STATUS,
            "output": output_record,
            "warning_count": blueprint_report["warning_count"]
            + output_report["warning_count"],
            "validation": {
                "blueprint": blueprint_report,
                "output": output_report,
            },
        }
    except Exception as exc:
        return {
            "status": FAILED_STATUS,
            "reason": "unexpected_error",
            "error": str(exc),
            "warning_count": 0,
            "validation": {},
        }


def _normalize_input_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Adapt script output fields to the public voice mapper contract.

    Arguments:
    record: Script Generation output record

    Returns:
    Creator Voice mapper input record
    """
    if not isinstance(record, dict):
        return {}

    trend_id = record.get("trend_id") or record.get("script_id")
    narration = record.get("narration") or record.get("spoken_script")
    metadata = record.get("metadata")

    return {
        "trend_id": trend_id,
        "narration": narration,
        "metadata": metadata if isinstance(metadata, dict) else {},
        "strategy": record.get("strategy", {}),
    }


def _build_output_record(
    mapped: dict[str, Any],
    transformed: dict[str, Any],
) -> dict[str, Any]:
    """
    Purpose:
    Combine transformed voice script with preserved metadata.

    Arguments:
    mapped: mapped Creator Voice record
    transformed: transformed Creator Voice output

    Returns:
    Creator Voice output record
    """
    metadata = dict(mapped.get("metadata", {}))
    metadata.setdefault("source_narration", mapped.get("narration", ""))

    return {
        "trend_id": transformed.get("trend_id") or mapped.get("trend_id"),
        "voice_script": transformed.get("voice_script", ""),
        "metadata": metadata,
        "generation_source": transformed.get("generation_source", "fallback"),
        "fallback_used": bool(transformed.get("fallback_used")),
    }


def _failed_result(reason: str, report: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Build a deterministic failed per-record result.

    Arguments:
    reason: failure reason
    report: validation report

    Returns:
    failed orchestration result
    """
    return {
        "status": FAILED_STATUS,
        "reason": reason,
        "warning_count": report.get("warning_count", 0),
        "validation": report,
    }


def _load_records(input_path: Path) -> list[dict[str, Any]]:
    """
    Purpose:
    Load input records from JSON.

    Arguments:
    input_path: input JSON path

    Returns:
    dictionary records
    """
    if not input_path.exists():
        logger.warning("Input file not found: %s", input_path)
        return []

    with input_path.open("r", encoding="utf-8") as input_file:
        data = json.load(input_file)

    if not isinstance(data, list):
        logger.warning("Input file is not a list: %s", input_path)
        return []

    return [row for row in data if isinstance(row, dict)]


def _save_records(records: list[dict[str, Any]], output_path: Path) -> Path:
    """
    Purpose:
    Save accepted voice scripts to JSON.

    Arguments:
    records: accepted Creator Voice output records
    output_path: output JSON path

    Returns:
    saved output path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(records, output_file, indent=4, ensure_ascii=False)

    return output_path


def _sample_record() -> dict[str, Any]:
    """
    Purpose:
    Build one script output record for self-tests.

    Arguments:
    None

    Returns:
    sample script output record
    """
    script = "Zendaya discussed 2 new movie updates in June. Fans are watching closely."

    return {
        "script_id": "script_001",
        "spoken_script": script,
        "metadata": {
            "entities": ["Zendaya"],
            "source_narration": script,
        },
    }


def _with_mocked_modules(
    mapper: Callable[[dict[str, Any]], dict[str, Any]],
    blueprint_validator: Callable[[dict[str, Any]], dict[str, Any]],
    transformer: Callable[[dict[str, Any]], dict[str, Any]],
    output_validator: Callable[[dict[str, Any]], dict[str, Any]],
    test: Callable[[], bool],
) -> bool:
    """
    Purpose:
    Run a self-test with temporary public API mocks.

    Arguments:
    mapper: mocked voice mapper
    blueprint_validator: mocked blueprint validator
    transformer: mocked transformer
    output_validator: mocked output validator
    test: test callable

    Returns:
    test result
    """
    global _build_voice_blueprint
    global _validate_voice_blueprint
    global _transform_voice
    global _validate_voice_output

    original_mapper = _build_voice_blueprint
    original_blueprint_validator = _validate_voice_blueprint
    original_transformer = _transform_voice
    original_output_validator = _validate_voice_output

    _build_voice_blueprint = mapper
    _validate_voice_blueprint = blueprint_validator
    _transform_voice = transformer
    _validate_voice_output = output_validator

    try:
        return test()
    finally:
        _build_voice_blueprint = original_mapper
        _validate_voice_blueprint = original_blueprint_validator
        _transform_voice = original_transformer
        _validate_voice_output = original_output_validator


def _valid_report(warnings: int = 0) -> dict[str, Any]:
    """
    Purpose:
    Build valid mocked validation report.

    Arguments:
    warnings: warning count

    Returns:
    validation report
    """
    return {
        "valid": True,
        "error_count": 0,
        "warning_count": warnings,
        "errors": [],
        "warnings": [],
        "validated_at_stage": "mock",
    }


def _invalid_report() -> dict[str, Any]:
    """
    Purpose:
    Build invalid mocked validation report.

    Arguments:
    None

    Returns:
    validation report
    """
    return {
        "valid": False,
        "error_count": 1,
        "warning_count": 0,
        "errors": [{"code": "MOCK", "field": "mock", "message": "mock"}],
        "warnings": [],
        "validated_at_stage": "mock",
    }


def _mock_mapper(record: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Build minimal mapped record for self-tests.

    Arguments:
    record: normalized record

    Returns:
    mapped Creator Voice record
    """
    return {
        "trend_id": record.get("trend_id"),
        "narration": record.get("narration"),
        "metadata": record.get("metadata", {}),
        "voice_blueprint": {"mock": True},
    }


def _mock_transformer(record: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Build mocked transformed voice output.

    Arguments:
    record: mapped Creator Voice record

    Returns:
    transformed voice output
    """
    return {
        "trend_id": record.get("trend_id"),
        "voice_script": record.get("narration", ""),
        "generation_source": "groq",
        "fallback_used": False,
    }


def _mock_fallback_transformer(record: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Build mocked fallback voice output.

    Arguments:
    record: mapped Creator Voice record

    Returns:
    transformed fallback output
    """
    result = _mock_transformer(record)
    result["generation_source"] = "fallback"
    result["fallback_used"] = True
    return result


def _test_success_path() -> bool:
    """
    Purpose:
    Verify successful record processing.

    Arguments:
    None

    Returns:
    test result
    """
    return _with_mocked_modules(
        _mock_mapper,
        lambda mapped: _valid_report(),
        _mock_transformer,
        lambda output: _valid_report(),
        lambda: process_record(_sample_record())["status"] == SUCCESS_STATUS,
    )


def _test_validation_failure() -> bool:
    """
    Purpose:
    Verify blueprint validation failure is isolated.

    Arguments:
    None

    Returns:
    test result
    """
    return _with_mocked_modules(
        _mock_mapper,
        lambda mapped: _invalid_report(),
        _mock_transformer,
        lambda output: _valid_report(),
        lambda: process_record(_sample_record())["reason"]
        == "blueprint_validation_failed",
    )


def _test_transformer_fallback() -> bool:
    """
    Purpose:
    Verify transformer fallback is counted as accepted when output validates.

    Arguments:
    None

    Returns:
    test result
    """
    return _with_mocked_modules(
        _mock_mapper,
        lambda mapped: _valid_report(),
        _mock_fallback_transformer,
        lambda output: _valid_report(),
        lambda: process_record(_sample_record())["output"]["fallback_used"] is True,
    )


def _test_output_validation_failure() -> bool:
    """
    Purpose:
    Verify invalid transformed output is discarded.

    Arguments:
    None

    Returns:
    test result
    """
    return _with_mocked_modules(
        _mock_mapper,
        lambda mapped: _valid_report(),
        _mock_transformer,
        lambda output: _invalid_report(),
        lambda: process_record(_sample_record())["reason"]
        == "output_validation_failed",
    )


def _test_empty_input() -> bool:
    """
    Purpose:
    Verify empty input engine run completes.

    Arguments:
    None

    Returns:
    test result
    """
    started_at = time.perf_counter()
    summary = {
        "loaded": 0,
        "processed": 0,
        "passed": 0,
        "failed": 0,
        "warnings": 0,
        "fallback_used": 0,
        "execution_time": round(time.perf_counter() - started_at, 3),
        "output_path": str(OUTPUT_VOICE_SCRIPTS_PATH),
    }
    return summary["loaded"] == 0 and summary["passed"] == 0


def _run_self_tests() -> bool:
    """
    Purpose:
    Run deterministic Creator Voice orchestrator self-tests.

    Arguments:
    None

    Returns:
    aggregate test result
    """
    tests = (
        _test_success_path(),
        _test_validation_failure(),
        _test_transformer_fallback(),
        _test_output_validation_failure(),
        _test_empty_input(),
    )
    return all(tests)


if __name__ == "__main__":
    print("PASS" if _run_self_tests() else "FAIL")
