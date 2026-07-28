"""Public API contract checks."""

from __future__ import annotations

import inspect

import scripts.creator_voice.creator_voice_engine as creator_engine
import scripts.creator_voice.voice_mapper as voice_mapper
import scripts.creator_voice.voice_output_validator as voice_output_validator
import scripts.creator_voice.voice_transformer as voice_transformer
import scripts.creator_voice.voice_validator as voice_validator
import scripts.visual_planning.visual_mapper as visual_mapper
import scripts.visual_planning.visual_output_validator as visual_output_validator
import scripts.visual_planning.visual_planner as visual_planner
import scripts.visual_planning.visual_planning_engine as visual_engine
import scripts.visual_planning.visual_validator as visual_validator


EXPECTED_PUBLIC_APIS = {
    voice_mapper: {"build_voice_blueprint", "map_voice_records"},
    voice_validator: {"validate_voice_blueprint", "validate_voice_records"},
    voice_transformer: {"transform_voice", "transform_voice_records"},
    voice_output_validator: {"validate_voice_output", "validate_voice_outputs"},
    creator_engine: {"run_creator_voice_engine", "process_record"},
    visual_mapper: {"build_visual_blueprint", "build_visual_blueprints"},
    visual_validator: {"validate_visual_blueprint", "validate_visual_blueprints"},
    visual_planner: {"plan_visuals", "plan_visuals_batch"},
    visual_output_validator: {"validate_visual_plan", "validate_visual_plans"},
    visual_engine: {"process_record", "process_batch"},
}


def test_public_api_contracts() -> None:
    """Verify approved public API exports remain stable."""
    for module, expected_names in EXPECTED_PUBLIC_APIS.items():
        public_names = _public_api_names(module)
        if hasattr(module, "__all__"):
            assert public_names == expected_names
        else:
            assert expected_names <= public_names
        for name in expected_names:
            assert callable(getattr(module, name))


def _public_api_names(module: object) -> set[str]:
    """Return public API names from __all__ or public callables."""
    if hasattr(module, "__all__"):
        return set(module.__all__)

    return {
        name
        for name, value in vars(module).items()
        if not name.startswith("_") and inspect.isfunction(value)
    }
