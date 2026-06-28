"""
Purpose:
Produce structured editorial intelligence for ranked trends.

Input:
outputs/trends.json

Output:
outputs/editorial_trends.json
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import OUTPUT_EDITORIAL_TRENDS_PATH, OUTPUT_TRENDS_PATH
from scripts.ai.groq_client import request_json
from scripts.ai.prompt_builder import build_editorial_prompt


logger = logging.getLogger(__name__)

EDITORIAL_SCHEMA_DEFAULTS = {
    "story_type": "unknown",
    "main_entities": [],
    "story_summary": "",
    "why_people_care": "",
    "primary_conflict": "",
    "confidence": 0.0,
    "editorial_tags": [],
    "risk_level": "low",
    "evergreen": False,
}


def load_trends(input_path: Path = OUTPUT_TRENDS_PATH) -> list[dict[str, Any]]:
    """
    Purpose:
    Load ranked trends from disk.

    Arguments:
    input_path: ranked trends JSON path

    Returns:
    ranked trend dictionaries
    """
    if not input_path.exists():
        logger.warning("Trends input file not found: %s", input_path)
        return []

    with input_path.open("r", encoding="utf-8") as input_file:
        trends = json.load(input_file)

    if not isinstance(trends, list):
        logger.warning("Trends input is not a list")
        return []

    logger.info("Loaded trends: %s", len(trends))
    return [trend for trend in trends if isinstance(trend, dict)]


def fallback_editorial(trend: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Build safe editorial defaults for one trend.

    Arguments:
    trend: ranked trend dictionary

    Returns:
    editorial fallback dictionary
    """
    fallback = EDITORIAL_SCHEMA_DEFAULTS.copy()
    fallback["story_summary"] = str(trend.get("topic", "") or "")
    return fallback


def _coerce_string_list(value: Any) -> list[str]:
    """
    Purpose:
    Repair list fields into string lists.

    Arguments:
    value: model-provided list value

    Returns:
    string list
    """
    if not isinstance(value, list):
        return []

    return [str(item) for item in value if item not in ("", None)]


def _coerce_bool(value: Any, default: bool = False) -> bool:
    """
    Purpose:
    Repair boolean fields from common JSON-like values.

    Arguments:
    value: model-provided boolean value
    default: fallback boolean value

    Returns:
    repaired boolean
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in {"true", "yes", "1"}:
            return True

        if normalized in {"false", "no", "0"}:
            return False

    return default


def validate_editorial_response(response: dict[str, Any], trend: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Validate and repair editorial JSON fields.

    Arguments:
    response: parsed Groq response dictionary
    trend: ranked trend dictionary

    Returns:
    validated editorial dictionary
    """
    repaired = fallback_editorial(trend)

    if not isinstance(response, dict):
        return repaired

    repaired["story_type"] = str(response.get("story_type") or repaired["story_type"])
    repaired["story_summary"] = str(response.get("story_summary") or repaired["story_summary"])
    repaired["why_people_care"] = str(response.get("why_people_care") or "")
    repaired["primary_conflict"] = str(response.get("primary_conflict") or "")
    repaired["evergreen"] = _coerce_bool(response.get("evergreen"), repaired["evergreen"])

    risk_level = str(response.get("risk_level") or repaired["risk_level"]).lower()
    repaired["risk_level"] = risk_level if risk_level in {"low", "medium", "high"} else "low"

    repaired["main_entities"] = _coerce_string_list(response.get("main_entities"))
    repaired["editorial_tags"] = _coerce_string_list(response.get("editorial_tags"))

    try:
        confidence = float(response.get("confidence", repaired["confidence"]))
        repaired["confidence"] = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        repaired["confidence"] = 0.0

    return repaired


def analyze_trend(trend: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Generate editorial intelligence for one trend.

    Arguments:
    trend: ranked trend dictionary

    Returns:
    trend dictionary merged with editorial fields
    """
    try:
        prompt = build_editorial_prompt(trend)
        response = request_json(prompt)
        editorial_fields = validate_editorial_response(response, trend)
        logger.info("Editorial success: %s", trend.get("topic", ""))
    except Exception as exc:
        logger.warning("Editorial failure for %s: %s", trend.get("topic", ""), exc)
        editorial_fields = fallback_editorial(trend)

    return trend | editorial_fields


def save_editorial_trends(
    editorial_trends: list[dict[str, Any]],
    output_path: Path = OUTPUT_EDITORIAL_TRENDS_PATH,
) -> Path:
    """
    Purpose:
    Save editorial trends to disk.

    Arguments:
    editorial_trends: trends merged with editorial intelligence
    output_path: output JSON path

    Returns:
    saved output path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(editorial_trends, output_file, indent=4, ensure_ascii=False)

    logger.info("Saved output: %s", output_path)
    return output_path


def run_editorial_engine() -> list[dict[str, Any]]:
    """
    Purpose:
    Run editorial analysis for all ranked trends.

    Arguments:
    None

    Returns:
    trends merged with editorial intelligence
    """
    trends = load_trends()
    editorial_trends = [analyze_trend(trend) for trend in trends]
    save_editorial_trends(editorial_trends)
    return editorial_trends


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    results = run_editorial_engine()
    print(f"Editorial trends: {len(results)}")
