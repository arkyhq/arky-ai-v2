"""Fallback behavior checks for AI-adjacent production modules."""

from __future__ import annotations

from scripts.creator_voice.voice_transformer import transform_voice
from scripts.visual_planning import visual_planner
from scripts.visual_planning.visual_output_validator import validate_visual_plan


def test_creator_voice_transformer_falls_back_without_narration() -> None:
    """Verify missing narration returns deterministic fallback instead of crashing."""
    result = transform_voice({"trend_id": "trend_qa", "metadata": {}, "voice_blueprint": {}})

    assert result["generation_source"] == "fallback"
    assert result["fallback_used"] is True


def test_visual_planner_empty_ai_response_falls_back(monkeypatch) -> None:
    """Verify empty AI response produces constitution-compliant fallback."""
    monkeypatch.setattr(visual_planner, "_groq_requester", lambda prompt: {})
    record = {
        "trend_id": "trend_qa",
        "voice_script": "The story is gaining attention. Fans are watching closely.",
        "metadata": {"source": "test"},
        "visual_blueprint": {
            "estimated_duration": 6,
            "estimated_scene_count": 3,
        },
    }

    result = visual_planner.plan_visuals(record)
    report = validate_visual_plan(result)

    assert result["fallback_used"] is True
    assert report["valid"] is True
