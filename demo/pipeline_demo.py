"""
Purpose:
Demonstrate the current ARKY pipeline using existing production engine outputs.

Input:
interactive topic text

Output:
demo/output/voice_script.json and demo/output/visual_plan.json when possible
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.creator_voice.creator_voice_engine import process_record as process_voice_record
from scripts.visual_planning.visual_planning_engine import process_record as process_visual_record


OUTPUT_DIR = PROJECT_ROOT / "demo" / "output"
SCRIPTS_PATH = PROJECT_ROOT / "outputs" / "scripts.json"
VOICE_OUTPUT_PATH = OUTPUT_DIR / "voice_script.json"
VISUAL_OUTPUT_PATH = OUTPUT_DIR / "visual_plan.json"


def main() -> None:
    """
    Purpose:
    Run the interactive pipeline demonstration.

    Arguments:
    None

    Returns:
    None
    """
    topic = input("Enter Topic: ").strip()

    _print_stage("Trend Intelligence", "using existing generated artifacts")
    _print_stage("Editorial Intelligence", "using existing generated artifacts")
    _print_stage("Script Strategy", "using existing generated artifacts")
    _print_stage("Script Generation", "loading scripts.json")

    script_record = _select_script_record(topic)

    if script_record is None:
        print("Demo stopped: outputs/scripts.json is unavailable or contains no usable records.")
        print("External services or credentials may be required to regenerate upstream outputs.")
        return

    _print_stage("Creator Voice", "processing selected script")
    voice_result = process_voice_record(script_record)

    if voice_result.get("status") != "passed":
        print(f"Demo stopped: Creator Voice failed: {voice_result}")
        return

    _save_json(VOICE_OUTPUT_PATH, voice_result["output"])
    print(f"Saved voice script: {VOICE_OUTPUT_PATH}")

    _print_stage("Visual Planning", "processing Creator Voice output")
    visual_result = process_visual_record(voice_result["output"])

    if not visual_result.get("success"):
        print(f"Demo stopped: Visual Planning failed: {visual_result}")
        return

    _save_json(VISUAL_OUTPUT_PATH, visual_result)
    print(f"Saved visual plan: {VISUAL_OUTPUT_PATH}")
    print("Demo complete.")


def _select_script_record(topic: str) -> dict[str, Any] | None:
    """
    Purpose:
    Select a script record from existing Script Generation output.

    Arguments:
    topic: requested demo topic

    Returns:
    selected script record or None
    """
    records = _load_json_list(SCRIPTS_PATH)

    if not records:
        return None

    if not topic:
        return records[0]

    normalized_topic = topic.lower()

    for record in records:
        haystack = " ".join(
            str(record.get(field, ""))
            for field in ("script_id", "source_topic", "spoken_script")
        ).lower()

        if normalized_topic in haystack:
            return record

    print("Topic not found in existing script output; using the first available script record.")
    return records[0]


def _load_json_list(path: Path) -> list[dict[str, Any]]:
    """
    Purpose:
    Load a JSON list from disk.

    Arguments:
    path: input JSON path

    Returns:
    list of dictionary records
    """
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as input_file:
        data = json.load(input_file)

    if not isinstance(data, list):
        return []

    return [record for record in data if isinstance(record, dict)]


def _save_json(path: Path, data: dict[str, Any]) -> None:
    """
    Purpose:
    Save demo output JSON.

    Arguments:
    path: output path
    data: JSON-serializable dictionary

    Returns:
    None
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as output_file:
        json.dump(data, output_file, indent=4, ensure_ascii=False)


def _print_stage(stage: str, status: str) -> None:
    """
    Purpose:
    Display demo progress.

    Arguments:
    stage: pipeline stage name
    status: stage status text

    Returns:
    None
    """
    print(f"{stage}: {status}")


if __name__ == "__main__":
    main()
