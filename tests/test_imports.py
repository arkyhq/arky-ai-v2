"""Import checks for production infrastructure and frozen engines."""

from __future__ import annotations

import importlib


MODULES = (
    "config.settings",
    "scripts.ai.groq_client",
    "scripts.pipeline.trend_pipeline",
    "scripts.intelligence.editorial_engine",
    "scripts.strategy.script_strategy_engine",
    "scripts.script_generation.script_engine",
    "scripts.creator_voice.creator_voice_engine",
    "scripts.visual_planning.visual_planning_engine",
    "utils.logger",
)


def test_core_modules_import() -> None:
    """Verify core release modules import without circular dependency errors."""
    for module_name in MODULES:
        importlib.import_module(module_name)
