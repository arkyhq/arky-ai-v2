"""
Purpose:
Orchestrate deterministic script strategy generation.

Input:
outputs/editorial_trends.json

Output:
outputs/script_strategies.json
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import GROQ_API_KEY, OUTPUT_EDITORIAL_TRENDS_PATH, SCRIPT_PROVIDER
from scripts.strategy.strategy_mapper import map_strategy
from scripts.strategy.strategy_refiner import refine_strategy
from scripts.strategy.strategy_validator import StrategyValidationError, validate_strategy


OUTPUT_SCRIPT_STRATEGIES_PATH = PROJECT_ROOT / "outputs" / "script_strategies.json"

logger = logging.getLogger(__name__)


def load_editorial_trends(input_path: Path = OUTPUT_EDITORIAL_TRENDS_PATH) -> list[dict[str, Any]]:
    """
    Purpose:
    Load editorial trend objects from disk.

    Arguments:
    input_path: editorial trends JSON path

    Returns:
    editorial trend dictionaries
    """
    if not input_path.exists():
        logger.warning("Editorial input file not found: %s", input_path)
        return []

    with input_path.open("r", encoding="utf-8") as input_file:
        editorial_trends = json.load(input_file)

    if not isinstance(editorial_trends, list):
        logger.warning("Editorial input is not a list")
        return []

    return [trend for trend in editorial_trends if isinstance(trend, dict)]


def should_refine() -> bool:
    """
    Purpose:
    Decide whether optional Groq strategy refinement is enabled.

    Arguments:
    None

    Returns:
    True when refinement can run, otherwise False
    """
    return SCRIPT_PROVIDER.lower() == "groq" and bool(GROQ_API_KEY)


def process_editorial_row(
    editorial: dict[str, Any],
    refinement_enabled: bool,
) -> tuple[dict[str, Any] | None, bool, bool]:
    """
    Purpose:
    Process one editorial row through mapper, validator, optional refiner, and validator.

    Arguments:
    editorial: editorial trend dictionary
    refinement_enabled: whether optional refinement should run

    Returns:
    strategy, refined flag, fallback flag
    """
    deterministic_strategy = validate_strategy(map_strategy(editorial))

    if not refinement_enabled:
        return deterministic_strategy, False, False

    try:
        refined_strategy = refine_strategy(editorial, deterministic_strategy)
        validated_refined_strategy = validate_strategy(refined_strategy)
        refined = validated_refined_strategy != deterministic_strategy
        return validated_refined_strategy, refined, not refined
    except Exception as exc:
        logger.warning("Refinement discarded; using deterministic strategy: %s", exc)
        return deterministic_strategy, False, True


def save_strategies(
    strategies: list[dict[str, Any]],
    output_path: Path = OUTPUT_SCRIPT_STRATEGIES_PATH,
) -> Path:
    """
    Purpose:
    Save strategy objects to disk.

    Arguments:
    strategies: validated strategy dictionaries
    output_path: output JSON path

    Returns:
    saved output path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(strategies, output_file, indent=4, ensure_ascii=False)

    return output_path


def run_strategy_engine() -> tuple[list[dict[str, Any]], dict[str, Any], Path]:
    """
    Purpose:
    Run the Script Strategy Engine orchestration.

    Arguments:
    None

    Returns:
    strategies, execution summary, output path
    """
    started_at = time.perf_counter()
    editorial_trends = load_editorial_trends()
    refinement_enabled = should_refine()
    strategies: list[dict[str, Any]] = []
    rows_refined = 0
    rows_fallback = 0
    rows_failed = 0

    logger.info("Rows loaded: %s", len(editorial_trends))

    for editorial in editorial_trends:
        try:
            strategy, refined, fallback = process_editorial_row(editorial, refinement_enabled)

            if strategy is None:
                rows_failed += 1
                continue

            strategies.append(strategy)
            rows_refined += int(refined)
            rows_fallback += int(fallback)
        except StrategyValidationError as exc:
            rows_failed += 1
            logger.warning("Strategy row failed validation: %s", exc)
        except Exception as exc:
            rows_failed += 1
            logger.warning("Strategy row failed: %s", exc)

    output_path = save_strategies(strategies)
    summary = {
        "rows_loaded": len(editorial_trends),
        "rows_processed": len(strategies),
        "rows_refined": rows_refined,
        "rows_fallback": rows_fallback,
        "rows_failed": rows_failed,
        "execution_time": round(time.perf_counter() - started_at, 3),
        "output_path": str(output_path),
    }

    logger.info("Rows processed: %s", summary["rows_processed"])
    logger.info("Rows refined: %s", rows_refined)
    logger.info("Rows fallback: %s", rows_fallback)
    logger.info("Rows failed: %s", rows_failed)
    logger.info("Execution time: %ss", summary["execution_time"])
    logger.info("Output path: %s", output_path)

    return strategies, summary, output_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    _, run_summary, _ = run_strategy_engine()
    print(json.dumps(run_summary, indent=4))
