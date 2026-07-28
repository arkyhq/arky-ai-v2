"""Deterministic integration checks for current production pipeline layers."""

from __future__ import annotations

from scripts.creator_voice.creator_voice_engine import process_record as process_voice
from scripts.visual_planning.visual_planning_engine import process_record as process_visual


def _script_record() -> dict[str, object]:
    script = "Zendaya discussed 2 new movie updates in June. Fans are watching closely."
    return {
        "script_id": "script_qa",
        "spoken_script": script,
        "metadata": {
            "entities": ["Zendaya"],
            "source_narration": script,
        },
    }


def test_creator_voice_to_visual_planning_pipeline() -> None:
    """Verify Creator Voice output can flow into Visual Planning."""
    voice_result = process_voice(_script_record())

    assert voice_result["status"] == "passed"

    visual_result = process_visual(voice_result["output"])

    assert visual_result["success"] is True
    assert visual_result["trend_id"] == "script_qa"
    assert visual_result["visual_plan"]
