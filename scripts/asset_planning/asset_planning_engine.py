"""
Purpose:
Orchestrate the Asset Planning Engine pipeline.

Input:
one validated Visual Plan result or a sequence of Visual Plan results

Output:
validated Asset Manifest results or deterministic error structures
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

try:
    from scripts.asset_planning.asset_mapper import build_asset_blueprint
    from scripts.asset_planning.asset_output_validator import validate_asset_manifest
    from scripts.asset_planning.asset_planner import plan_assets
    from scripts.asset_planning.asset_validator import validate_asset_blueprint
except ModuleNotFoundError:  # pragma: no cover - direct script execution support
    from asset_mapper import build_asset_blueprint
    from asset_output_validator import validate_asset_manifest
    from asset_planner import plan_assets
    from asset_validator import validate_asset_blueprint


SUCCESS_STAGE = "complete"
BLUEPRINT_VALIDATION_STAGE = "asset_blueprint_validation"
MANIFEST_VALIDATION_STAGE = "asset_manifest_validation"
UNEXPECTED_STAGE = "unexpected_exception"

_build_asset_blueprint: Callable[[dict[str, Any]], dict[str, Any]] = build_asset_blueprint
_validate_asset_blueprint: Callable[[dict[str, Any]], dict[str, Any]] = (
    validate_asset_blueprint
)
_plan_assets: Callable[[dict[str, Any]], dict[str, Any]] = plan_assets
_validate_asset_manifest: Callable[[dict[str, Any]], dict[str, Any]] = (
    validate_asset_manifest
)

__all__ = ("process_record", "process_batch")


def process_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Process one Visual Plan result through the Asset Planning Engine.

    Arguments:
    record: validated Visual Plan result

    Returns:
    successful Asset Manifest result or deterministic error structure
    """
    try:
        asset_blueprint = _build_asset_blueprint(record)
        blueprint_report = _validate_asset_blueprint(asset_blueprint)

        if not blueprint_report["valid"]:
            return _failure_result(
                asset_blueprint,
                BLUEPRINT_VALIDATION_STAGE,
                blueprint_report["errors"],
                _safe_metadata(asset_blueprint),
            )

        asset_manifest = _plan_assets(asset_blueprint)
        manifest_report = _validate_asset_manifest(asset_manifest)

        if not manifest_report["valid"]:
            return _failure_result(
                asset_blueprint,
                MANIFEST_VALIDATION_STAGE,
                manifest_report["errors"],
                _safe_metadata(asset_blueprint),
            )

        return {
            "trend_id": asset_manifest.get(
                "trend_id",
                asset_blueprint.get("trend_id", ""),
            ),
            "success": True,
            "asset_manifest": asset_manifest["asset_manifest"],
            "metadata": _safe_metadata(asset_blueprint),
            "validation": {
                "blueprint": blueprint_report,
                "manifest": manifest_report,
            },
            "fallback_used": bool(asset_manifest.get("fallback_used")),
            "generation_source": asset_manifest.get("generation_source", ""),
        }
    except Exception as exc:
        return _failure_result(
            record,
            UNEXPECTED_STAGE,
            [{"message": str(exc)}],
            _safe_metadata(record),
        )


def process_batch(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """
    Purpose:
    Process multiple Visual Plan results through Asset Planning.

    Arguments:
    records: iterable of validated Visual Plan results

    Returns:
    deterministic batch summary
    """
    if not isinstance(records, Iterable) or isinstance(records, (str, bytes)):
        results = [process_record(records)]
    else:
        results = [process_record(record) for record in records]

    successful = sum(1 for result in results if result.get("success") is True)

    return {
        "processed": len(results),
        "successful": successful,
        "failed": len(results) - successful,
        "results": results,
    }


def _failure_result(
    record: dict[str, Any] | None,
    error_stage: str,
    errors: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """
    Purpose:
    Build deterministic failed orchestration result.

    Arguments:
    record: source or intermediate record
    error_stage: failed pipeline stage
    errors: structured validation or runtime errors
    metadata: preserved metadata

    Returns:
    failed result dictionary
    """
    return {
        "trend_id": _safe_trend_id(record),
        "success": False,
        "error_stage": error_stage,
        "errors": errors,
        "metadata": metadata,
    }


def _safe_trend_id(record: dict[str, Any] | None) -> str:
    """
    Purpose:
    Preserve trend identifier when available.

    Arguments:
    record: source or intermediate record

    Returns:
    trend identifier or empty string
    """
    if not isinstance(record, dict):
        return ""

    trend_id = record.get("trend_id")
    return trend_id if isinstance(trend_id, str) else ""


def _safe_metadata(record: dict[str, Any] | None) -> dict[str, Any]:
    """
    Purpose:
    Preserve metadata when available.

    Arguments:
    record: source or intermediate record

    Returns:
    metadata dictionary
    """
    if not isinstance(record, dict):
        return {}

    metadata = record.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _sample_record() -> dict[str, Any]:
    """
    Purpose:
    Build sample Visual Plan result for self-tests.

    Arguments:
    None

    Returns:
    sample Visual Plan result
    """
    return {
        "trend_id": "trend_001",
        "metadata": {"source": "visual_planning"},
        "generation_source": "fallback",
        "fallback_used": True,
        "visual_plan": [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 3.0,
                "narration_segment": "The story is gaining attention.",
                "asset_requirement": "text_card",
            }
        ],
    }


def _sample_blueprint() -> dict[str, Any]:
    """
    Purpose:
    Build sample Asset Blueprint for self-tests.

    Arguments:
    None

    Returns:
    sample Asset Blueprint
    """
    return {
        "trend_id": "trend_001",
        "metadata": {"source": "visual_planning"},
        "visual_plan": (),
        "generation_source": "fallback",
        "fallback_used": True,
        "asset_blueprint": {"mock": True},
    }


def _sample_manifest(fallback_used: bool = False) -> dict[str, Any]:
    """
    Purpose:
    Build sample Asset Manifest result for self-tests.

    Arguments:
    fallback_used: fallback flag

    Returns:
    sample Asset Manifest result
    """
    return {
        "trend_id": "trend_001",
        "asset_manifest": {"asset_manifest_id": "asset_manifest_trend_001"},
        "generation_source": "fallback" if fallback_used else "groq",
        "fallback_used": fallback_used,
    }


def _valid_report() -> dict[str, Any]:
    """
    Purpose:
    Build valid mocked validation report.

    Arguments:
    None

    Returns:
    validation report dictionary
    """
    return {
        "valid": True,
        "error_count": 0,
        "warning_count": 0,
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
    validation report dictionary
    """
    return {
        "valid": False,
        "error_count": 1,
        "warning_count": 0,
        "errors": [{"code": "MOCK", "message": "mock failure"}],
        "warnings": [],
        "validated_at_stage": "mock",
    }


def _with_mocked_modules(
    mapper: Callable[[dict[str, Any]], dict[str, Any]],
    blueprint_validator: Callable[[dict[str, Any]], dict[str, Any]],
    planner: Callable[[dict[str, Any]], dict[str, Any]],
    output_validator: Callable[[dict[str, Any]], dict[str, Any]],
    test: Callable[[], bool],
) -> bool:
    """
    Purpose:
    Run a self-test with temporary public API mocks.

    Arguments:
    mapper: mocked mapper
    blueprint_validator: mocked blueprint validator
    planner: mocked planner
    output_validator: mocked output validator
    test: self-test callable

    Returns:
    self-test result
    """
    global _build_asset_blueprint
    global _validate_asset_blueprint
    global _plan_assets
    global _validate_asset_manifest

    original_mapper = _build_asset_blueprint
    original_blueprint_validator = _validate_asset_blueprint
    original_planner = _plan_assets
    original_output_validator = _validate_asset_manifest

    _build_asset_blueprint = mapper
    _validate_asset_blueprint = blueprint_validator
    _plan_assets = planner
    _validate_asset_manifest = output_validator

    try:
        return test()
    finally:
        _build_asset_blueprint = original_mapper
        _validate_asset_blueprint = original_blueprint_validator
        _plan_assets = original_planner
        _validate_asset_manifest = original_output_validator


def _test_success_path() -> bool:
    """
    Purpose:
    Verify successful orchestration path.

    Arguments:
    None

    Returns:
    self-test result
    """
    return _with_mocked_modules(
        lambda record: _sample_blueprint(),
        lambda blueprint: _valid_report(),
        lambda blueprint: _sample_manifest(),
        lambda manifest: _valid_report(),
        lambda: process_record(_sample_record())["success"] is True,
    )


def _test_blueprint_validation_failure() -> bool:
    """
    Purpose:
    Verify blueprint validation failure stops the record.

    Arguments:
    None

    Returns:
    self-test result
    """
    return _with_mocked_modules(
        lambda record: _sample_blueprint(),
        lambda blueprint: _invalid_report(),
        lambda blueprint: _sample_manifest(),
        lambda manifest: _valid_report(),
        lambda: process_record(_sample_record())["error_stage"]
        == BLUEPRINT_VALIDATION_STAGE,
    )


def _test_manifest_validation_failure() -> bool:
    """
    Purpose:
    Verify manifest validation failure stops the record.

    Arguments:
    None

    Returns:
    self-test result
    """
    return _with_mocked_modules(
        lambda record: _sample_blueprint(),
        lambda blueprint: _valid_report(),
        lambda blueprint: _sample_manifest(),
        lambda manifest: _invalid_report(),
        lambda: process_record(_sample_record())["error_stage"]
        == MANIFEST_VALIDATION_STAGE,
    )


def _test_batch_processing() -> bool:
    """
    Purpose:
    Verify batch processing counts successes and failures.

    Arguments:
    None

    Returns:
    self-test result
    """
    def blueprint_validator(blueprint: dict[str, Any]) -> dict[str, Any]:
        if blueprint.get("trend_id") == "bad":
            return _invalid_report()
        return _valid_report()

    def mapper(record: dict[str, Any]) -> dict[str, Any]:
        blueprint = _sample_blueprint()
        blueprint["trend_id"] = record.get("trend_id", "")
        return blueprint

    records = (_sample_record(), {"trend_id": "bad"}, _sample_record())

    return _with_mocked_modules(
        mapper,
        blueprint_validator,
        lambda blueprint: _sample_manifest(),
        lambda manifest: _valid_report(),
        lambda: process_batch(records)["successful"] == 2
        and process_batch(records)["failed"] == 1,
    )


def _test_unexpected_exception() -> bool:
    """
    Purpose:
    Verify unexpected exceptions become deterministic errors.

    Arguments:
    None

    Returns:
    self-test result
    """
    def raise_error(record: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("mock failure")

    return _with_mocked_modules(
        raise_error,
        lambda blueprint: _valid_report(),
        lambda blueprint: _sample_manifest(),
        lambda manifest: _valid_report(),
        lambda: process_record(_sample_record())["error_stage"] == UNEXPECTED_STAGE,
    )


def _run_self_tests() -> bool:
    """
    Purpose:
    Run deterministic Asset Planning Engine self-tests.

    Arguments:
    None

    Returns:
    aggregate self-test result
    """
    tests = (
        _test_success_path(),
        _test_blueprint_validation_failure(),
        _test_manifest_validation_failure(),
        _test_batch_processing(),
        _test_unexpected_exception(),
    )
    return all(tests)


if __name__ == "__main__":
    print("PASS" if _run_self_tests() else "FAIL")
