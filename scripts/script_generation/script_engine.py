"""
Purpose:
Orchestrate script generation from editorial and strategy outputs.

Input:
outputs/editorial_trends.json and outputs/script_strategies.json

Output:
outputs/scripts.json
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

from config.settings import OUTPUT_EDITORIAL_TRENDS_PATH
from scripts.script_generation.script_mapper import map_script_blueprint
from scripts.script_generation.script_narrator import build_fallback_narration, narrate_script
from scripts.script_generation.script_output_validator import (
    NarrationOutputValidationError,
    validate_narration_output,
)
from scripts.script_generation.script_validator import (
    ScriptBlueprintValidationError,
    validate_script_blueprint,
)


OUTPUT_SCRIPT_STRATEGIES_PATH = PROJECT_ROOT / "outputs" / "script_strategies.json"
OUTPUT_SCRIPTS_PATH = PROJECT_ROOT / "outputs" / "scripts.json"

logger = logging.getLogger(__name__)


def load_json_list(input_path: Path) -> list[dict[str, Any]]:
    """
    Purpose:
    Load a JSON list of dictionaries from disk.

    Arguments:
    input_path: JSON file path

    Returns:
    dictionary rows
    """
    if not input_path.exists():
        logger.warning("Input file not found: %s", input_path)
        return []

    with input_path.open("r", encoding="utf-8") as input_file:
        rows = json.load(input_file)

    if not isinstance(rows, list):
        logger.warning("Input file is not a list: %s", input_path)
        return []

    return [row for row in rows if isinstance(row, dict)]


def process_script_row(
    editorial: dict[str, Any],
    strategy: dict[str, Any],
) -> tuple[dict[str, Any] | None, bool]:
    """
    Purpose:
    Process one editorial and strategy pair through the script generation modules.

    Arguments:
    editorial: editorial object
    strategy: strategy object

    Returns:
    output script object and fallback flag
    """
    blueprint = validate_script_blueprint(map_script_blueprint(editorial, strategy))

    try:
        narration = narrate_script(editorial, strategy, blueprint)
    except Exception as exc:
        logger.warning("Narration failed; using fallback narration: %s", exc)
        narration = build_fallback_narration(editorial, strategy, blueprint)

    validated_narration = validate_narration_output(narration)
    output_script = build_output_script(validated_narration, blueprint, strategy)
    return output_script, output_script["fallback_used"]


def build_output_script(
    narration: dict[str, Any],
    blueprint: dict[str, Any],
    strategy: dict[str, Any],
) -> dict[str, Any]:
    """
    Purpose:
    Normalize validated narration into the public scripts output object.

    Arguments:
    narration: validated narration dictionary
    blueprint: validated script blueprint dictionary
    strategy: strategy dictionary

    Returns:
    output script dictionary
    """
    generator = narration.get("generator")
    generation_source = "groq" if generator == "groq" else "fallback"

    return {
        "script_id": narration["script_id"],
        "source_topic": blueprint.get("source_topic", "unknown topic"),
        "spoken_script": narration["spoken_script"],
        "estimated_duration_seconds": narration["estimated_duration_seconds"],
        "word_count": narration["word_count"],
        "claim_safety": narration["claim_safety"],
        "generation_source": generation_source,
        "fallback_used": bool(narration["fallback_used"]),
        "metadata": {
            "blueprint_confidence": blueprint.get("script_confidence"),
            "strategy_archetype": strategy.get("story_archetype"),
            "blueprint_fallback_used": blueprint.get("fallback_used"),
        },
    }


def save_scripts(
    scripts: list[dict[str, Any]],
    output_path: Path = OUTPUT_SCRIPTS_PATH,
) -> Path:
    """
    Purpose:
    Save generated scripts to disk.

    Arguments:
    scripts: output script dictionaries
    output_path: output JSON path

    Returns:
    saved output path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(scripts, output_file, indent=4, ensure_ascii=False)

    return output_path


def run_script_engine() -> tuple[list[dict[str, Any]], dict[str, Any], Path]:
    """
    Purpose:
    Run the Script Generation Engine orchestration.

    Arguments:
    None

    Returns:
    scripts, execution summary, output path
    """
    started_at = time.perf_counter()
    editorial_rows = load_json_list(OUTPUT_EDITORIAL_TRENDS_PATH)
    strategy_rows = load_json_list(OUTPUT_SCRIPT_STRATEGIES_PATH)
    pair_count = min(len(editorial_rows), len(strategy_rows))
    scripts: list[dict[str, Any]] = []
    rows_failed = 0
    rows_fallback = 0

    logger.info("rows_loaded: %s", pair_count)

    for index in range(pair_count):
        try:
            script, fallback_used = process_script_row(
                editorial_rows[index],
                strategy_rows[index],
            )

            if script is None:
                rows_failed += 1
                continue

            scripts.append(script)
            rows_fallback += int(fallback_used)
        except (ScriptBlueprintValidationError, NarrationOutputValidationError) as exc:
            rows_failed += 1
            logger.warning("Script row failed validation: %s", exc)
        except Exception as exc:
            rows_failed += 1
            logger.warning("Script row failed: %s", exc)

    output_path = save_scripts(scripts)
    summary = {
        "rows_loaded": pair_count,
        "rows_generated": len(scripts),
        "rows_validated": len(scripts),
        "rows_failed": rows_failed,
        "rows_fallback": rows_fallback,
        "execution_time": round(time.perf_counter() - started_at, 3),
        "output_path": str(output_path),
    }

    logger.info("rows_generated: %s", summary["rows_generated"])
    logger.info("rows_validated: %s", summary["rows_validated"])
    logger.info("rows_failed: %s", rows_failed)
    logger.info("rows_fallback: %s", rows_fallback)
    logger.info("execution_time: %ss", summary["execution_time"])
    logger.info("output_path: %s", output_path)

    return scripts, summary, output_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    _, run_summary, _ = run_script_engine()
    print(json.dumps(run_summary, indent=4))
