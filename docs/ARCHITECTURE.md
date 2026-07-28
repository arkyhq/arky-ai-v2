# ARKY-AI-SYSTEM Architecture

## Overview

ARKY-AI-SYSTEM is a staged short-form entertainment video pipeline. Each engine owns one narrow responsibility and passes structured JSON-like Python dictionaries to the next stage.

Current frozen release: `v0.7`.

## Pipeline

Trend Intelligence -> Editorial Intelligence -> Script Strategy -> Script Generation -> Creator Voice -> Visual Planning -> Asset Planning -> Asset Generation -> Rendering -> Publishing -> Analytics

## Engines

### Trend Intelligence

Collects Reddit and Google Trends candidates, removes duplicates, filters entertainment topics, and assigns deterministic priority scores.

Public entry points include trend collectors, filtering helpers, ranking helpers, and `scripts.pipeline.trend_pipeline.run_pipeline()`.

### Editorial Intelligence

Converts ranked trends into editorial understanding. It validates Groq output and uses deterministic fallback behavior when needed.

Public entry point: `scripts.intelligence.editorial_engine.run_editorial_engine()`.

### Script Strategy

Maps editorial objects into storytelling strategy objects. Deterministic mapping and validation are primary; Groq refinement is optional and protected.

Public entry point: `scripts.strategy.script_strategy_engine.run_strategy_engine()`.

### Script Generation

Builds a script blueprint, validates it, generates spoken narration, validates narration output, and writes script records.

Public entry point: `scripts.script_generation.script_engine.run_script_engine()`.

### Creator Voice

Maps generated scripts to the canonical ARKY voice contract, validates voice blueprints, optionally transforms narration with Groq, validates the final voice output, and orchestrates accepted voice scripts.

Public entry points: `run_creator_voice_engine()` and `process_record()`.

### Visual Planning

Maps Creator Voice records into visual blueprints, validates them, plans shot-by-shot visuals, validates visual output, and returns final plans.

Public entry points: `process_record()` and `process_batch()`.

## Design Philosophy

- One responsibility per module.
- Deterministic stages before AI refinement.
- AI modules may improve expression or planning detail but must not override protected facts, structure, or safety.
- Validators are deterministic gates.
- Engines continue processing remaining rows when one row fails.
- External dependency failure must degrade gracefully.

## AI Boundaries

Only explicitly named AI modules may call Groq:

- `scripts.ai.groq_client`
- `scripts.strategy.strategy_refiner`
- `scripts.script_generation.script_narrator`
- `scripts.creator_voice.voice_transformer`
- `scripts.visual_planning.visual_planner`

All mappers, validators, constitutions, and orchestrators remain deterministic.

## Deterministic Modules

Constitution modules define immutable rules and vocabularies. Mapper modules convert structured records into blueprints. Validator modules check schema and safety. Orchestrators coordinate public APIs without duplicating business logic.

## Configuration

Runtime configuration is centralized in `config/settings.py`. Modules should import settings instead of reading environment variables directly.

## Release Strategy

Each engine is frozen only after compilation, imports, public API checks, deterministic self-tests, integration tests, fallback tests, and QA review pass.
