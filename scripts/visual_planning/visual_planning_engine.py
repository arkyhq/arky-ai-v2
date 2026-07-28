"""
Purpose:
Orchestrate the Visual Planning Engine pipeline.

Input:
one Creator Voice record or a sequence of records

Output:
structured Visual Planning results and batch summaries
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

try:
    from scripts.visual_planning.visual_mapper import build_visual_blueprint
    from scripts.visual_planning.visual_output_validator import validate_visual_plan
    from scripts.visual_planning.visual_planner import plan_visuals
    from scripts.visual_planning.visual_validator import validate_visual_blueprint
except ModuleNotFoundError:  # pragma: no cover - direct script execution support
    from visual_mapper import build_visual_blueprint
    from visual_output_validator import validate_visual_plan
    from visual_planner import plan_visuals
    from visual_validator import validate_visual_blueprint


SUCCESS_STAGE = "complete"
INPUT_VALIDATION_STAGE = "input_validation"
PLANNING_STAGE = "visual_planner"
OUTPUT_VALIDATION_STAGE = "output_validation"
UNEXPECTED_STAGE = "unexpected_exception"

_build_visual_blueprint: Callable[[dict[str, Any]], dict[str, Any]] = build_visual_blueprint
_validate_visual_blueprint: Callable[[dict[str, Any]], dict[str, Any]] = validate_visual_blueprint
_plan_visuals: Callable[[dict[str, Any]], dict[str, Any]] = plan_visuals
_validate_visual_plan: Callable[[dict[str, Any]], dict[str, Any]] = validate_visual_plan

__all__ = ("process_record", "process_batch")


def process_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Process one record through the Visual Planning Engine modules.

    Arguments:
    record: Creator Voice output record

    Returns:
    successful or failed Visual Planning result
    """
    try:
        visual_blueprint = _build_visual_blueprint(record)
        input_validation = _validate_visual_blueprint(visual_blueprint)

        if not input_validation["valid"]:
            return _failure_result(
                visual_blueprint,
                INPUT_VALIDATION_STAGE,
                input_validation["errors"],
            )

        planned = _plan_visuals(visual_blueprint)

        if not isinstance(planned, dict):
            return _failure_result(
                visual_blueprint,
                PLANNING_STAGE,
                [{"message": "Planner returned invalid result."}],
            )

        output_validation = _validate_visual_plan(planned)

        if not output_validation["valid"]:
            return _failure_result(
                visual_blueprint,
                OUTPUT_VALIDATION_STAGE,
                output_validation["errors"],
            )

        return {
            "trend_id": planned.get("trend_id", visual_blueprint.get("trend_id", "")),
            "success": True,
            "visual_plan": planned.get("visual_plan", []),
            "validation": {
                "input": input_validation,
                "output": output_validation,
            },
            "fallback_used": bool(planned.get("fallback_used")),
            "generation_source": planned.get("generation_source", ""),
        }
    except Exception as exc:
        return _failure_result(
            record,
            UNEXPECTED_STAGE,
            [{"message": str(exc)}],
        )


def process_batch(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """
    Purpose:
    Process multiple records through the Visual Planning Engine.

    Arguments:
    records: iterable of Creator Voice output records

    Returns:
    batch summary with per-record results
    """
    if not isinstance(records, Iterable) or isinstance(records, (str, bytes)):
        results = [process_record(records)]
    else:
        results = [process_record(record) for record in records]

    successful = sum(1 for result in results if result.get("success") is True)
    failed = len(results) - successful

    return {
        "processed": len(results),
        "successful": successful,
        "failed": failed,
        "results": results,
    }


def _failure_result(
    record: dict[str, Any] | None,
    error_stage: str,
    errors: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Purpose:
    Build a deterministic failed orchestration result.

    Arguments:
    record: source or intermediate record
    error_stage: failed pipeline stage
    errors: structured errors

    Returns:
    failed Visual Planning result
    """
    return {
        "trend_id": _safe_trend_id(record),
        "success": False,
        "error_stage": error_stage,
        "errors": errors,
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


def _sample_record() -> dict[str, Any]:
    """
    Purpose:
    Build sample Creator Voice record for self-tests.

    Arguments:
    None

    Returns:
    sample Creator Voice record
    """
    return {
        "trend_id": "trend_001",
        "voice_script": "The story is gaining attention. Fans are watching closely.",
        "generation_source": "groq",
        "fallback_used": False,
        "metadata": {"source": "creator_voice"},
    }


def _sample_blueprint() -> dict[str, Any]:
    """
    Purpose:
    Build sample Visual Blueprint for self-tests.

    Arguments:
    None

    Returns:
    sample Visual Blueprint
    """
    return {
        "trend_id": "trend_001",
        "voice_script": "The story is gaining attention.",
        "metadata": {"source": "creator_voice"},
        "visual_blueprint": {"estimated_scene_count": 1},
    }


def _sample_plan(fallback_used: bool = False) -> dict[str, Any]:
    """
    Purpose:
    Build sample Visual Plan for self-tests.

    Arguments:
    fallback_used: fallback flag

    Returns:
    sample Visual Plan result
    """
    return {
        "trend_id": "trend_001",
        "visual_plan": [{"scene_id": 1}],
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
    validation report
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
    validation report
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
    input_validator: Callable[[dict[str, Any]], dict[str, Any]],
    planner: Callable[[dict[str, Any]], dict[str, Any]],
    output_validator: Callable[[dict[str, Any]], dict[str, Any]],
    test: Callable[[], bool],
) -> bool:
    """
    Purpose:
    Run a self-test with temporary public API mocks.

    Arguments:
    mapper: mocked mapper
    input_validator: mocked input validator
    planner: mocked planner
    output_validator: mocked output validator
    test: self-test callable

    Returns:
    self-test result
    """
    global _build_visual_blueprint
    global _validate_visual_blueprint
    global _plan_visuals
    global _validate_visual_plan

    original_mapper = _build_visual_blueprint
    original_input_validator = _validate_visual_blueprint
    original_planner = _plan_visuals
    original_output_validator = _validate_visual_plan

    _build_visual_blueprint = mapper
    _validate_visual_blueprint = input_validator
    _plan_visuals = planner
    _validate_visual_plan = output_validator

    try:
        return test()
    finally:
        _build_visual_blueprint = original_mapper
        _validate_visual_blueprint = original_input_validator
        _plan_visuals = original_planner
        _validate_visual_plan = original_output_validator


def _test_valid_record() -> bool:
    """
    Purpose:
    Verify successful orchestration path.

    Arguments:
    None

    Returns:
    test result
    """
    return _with_mocked_modules(
        lambda record: _sample_blueprint(),
        lambda blueprint: _valid_report(),
        lambda blueprint: _sample_plan(),
        lambda plan: _valid_report(),
        lambda: process_record(_sample_record())["success"] is True,
    )


def _test_invalid_blueprint() -> bool:
    """
    Purpose:
    Verify invalid blueprint fails at input validation.

    Arguments:
    None

    Returns:
    test result
    """
    return _with_mocked_modules(
        lambda record: _sample_blueprint(),
        lambda blueprint: _invalid_report(),
        lambda blueprint: _sample_plan(),
        lambda plan: _valid_report(),
        lambda: process_record(_sample_record())["error_stage"]
        == INPUT_VALIDATION_STAGE,
    )


def _test_planner_fallback() -> bool:
    """
    Purpose:
    Verify planner fallback remains successful when output validates.

    Arguments:
    None

    Returns:
    test result
    """
    return _with_mocked_modules(
        lambda record: _sample_blueprint(),
        lambda blueprint: _valid_report(),
        lambda blueprint: _sample_plan(fallback_used=True),
        lambda plan: _valid_report(),
        lambda: process_record(_sample_record())["fallback_used"] is True,
    )


def _test_invalid_planner_output() -> bool:
    """
    Purpose:
    Verify invalid planner output fails at output validation.

    Arguments:
    None

    Returns:
    test result
    """
    return _with_mocked_modules(
        lambda record: _sample_blueprint(),
        lambda blueprint: _valid_report(),
        lambda blueprint: _sample_plan(),
        lambda plan: _invalid_report(),
        lambda: process_record(_sample_record())["error_stage"]
        == OUTPUT_VALIDATION_STAGE,
    )


def _test_partial_batch_failure() -> bool:
    """
    Purpose:
    Verify mixed batch continues processing after failure.

    Arguments:
    None

    Returns:
    test result
    """
    def input_validator(blueprint: dict[str, Any]) -> dict[str, Any]:
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
        input_validator,
        lambda blueprint: _sample_plan(),
        lambda plan: _valid_report(),
        lambda: process_batch(records)["successful"] == 2
        and process_batch(records)["failed"] == 1,
    )


def _test_multiple_records() -> bool:
    """
    Purpose:
    Verify multiple valid records process successfully.

    Arguments:
    None

    Returns:
    test result
    """
    return _with_mocked_modules(
        lambda record: _sample_blueprint(),
        lambda blueprint: _valid_report(),
        lambda blueprint: _sample_plan(),
        lambda plan: _valid_report(),
        lambda: process_batch((_sample_record(), _sample_record()))["successful"] == 2,
    )


def _test_empty_batch() -> bool:
    """
    Purpose:
    Verify empty batch summary.

    Arguments:
    None

    Returns:
    test result
    """
    summary = process_batch(())
    return summary["processed"] == 0 and summary["results"] == []


def _test_unexpected_exception() -> bool:
    """
    Purpose:
    Verify unexpected module exception is captured.

    Arguments:
    None

    Returns:
    test result
    """
    def raise_error(record: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("mock failure")

    return _with_mocked_modules(
        raise_error,
        lambda blueprint: _valid_report(),
        lambda blueprint: _sample_plan(),
        lambda plan: _valid_report(),
        lambda: process_record(_sample_record())["error_stage"] == UNEXPECTED_STAGE,
    )


def _run_self_tests() -> bool:
    """
    Purpose:
    Run deterministic Visual Planning Engine self-tests.

    Arguments:
    None

    Returns:
    aggregate test result
    """
    tests = (
        _test_valid_record(),
        _test_invalid_blueprint(),
        _test_planner_fallback(),
        _test_invalid_planner_output(),
        _test_partial_batch_failure(),
        _test_multiple_records(),
        _test_empty_batch(),
        _test_unexpected_exception(),
    )
    return all(tests)


if __name__ == "__main__":
    print("PASS" if _run_self_tests() else "FAIL")
