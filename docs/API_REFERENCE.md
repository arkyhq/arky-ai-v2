# API Reference

Signatures only. Private helpers are intentionally omitted.

## AI

- `scripts.ai.groq_client.extract_json(response_text: str) -> dict[str, Any]`
- `scripts.ai.groq_client.request_json(prompt: str) -> dict[str, Any]`
- `scripts.ai.prompt_builder.load_prompt(prompt_path: Path = EDITORIAL_ANALYSIS_PROMPT_PATH) -> str`
- `scripts.ai.prompt_builder.build_editorial_prompt(trend: dict[str, Any]) -> str`

## Trend Intelligence

- `scripts.scraper.reddit_scraper.scrape_reddit_posts(subreddits: list[str] | None = None) -> list[dict[str, Any]]`
- `scripts.scraper.google_trends_scraper.collect_trends(regions: list[str] | None = None) -> list[dict[str, Any]]`
- `scripts.scraper.deduplicator.normalize_title(title: str) -> str`
- `scripts.scraper.deduplicator.similarity_score(first_title: str, second_title: str) -> int`
- `scripts.scraper.deduplicator.choose_best(first_trend: dict[str, Any], second_trend: dict[str, Any]) -> dict[str, Any]`
- `scripts.scraper.deduplicator.remove_duplicates(trends: list[dict[str, Any]]) -> list[dict[str, Any]]`
- `scripts.scraper.entertainment_filter.normalize_text(text: str) -> str`
- `scripts.scraper.entertainment_filter.calculate_score(trend: dict[str, Any]) -> int`
- `scripts.scraper.entertainment_filter.is_entertainment(trend: dict[str, Any]) -> bool`
- `scripts.scraper.entertainment_filter.filter_trends(trends: list[dict[str, Any]]) -> list[dict[str, Any]]`
- `scripts.scraper.trend_ranker.calculate_reddit_score(trend: dict[str, Any]) -> float`
- `scripts.scraper.trend_ranker.calculate_google_score(trend: dict[str, Any]) -> float`
- `scripts.scraper.trend_ranker.calculate_freshness(trend: dict[str, Any]) -> float`
- `scripts.scraper.trend_ranker.calculate_source_score(trend: dict[str, Any]) -> float`
- `scripts.scraper.trend_ranker.calculate_metadata_bonus(trend: dict[str, Any]) -> float`
- `scripts.scraper.trend_ranker.calculate_final_score(trend: dict[str, Any]) -> int`
- `scripts.scraper.trend_ranker.rank_trends(trends: list[dict[str, Any]]) -> list[dict[str, Any]]`
- `scripts.pipeline.trend_pipeline.collect_all_trends() -> tuple[list[dict[str, Any]], dict[str, int]]`
- `scripts.pipeline.trend_pipeline.process_trends(trends: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]`
- `scripts.pipeline.trend_pipeline.save_results(trends: list[dict[str, Any]], output_path: Path = OUTPUT_PATH) -> Path`
- `scripts.pipeline.trend_pipeline.run_pipeline() -> tuple[list[dict[str, Any]], dict[str, int | float], Path]`

## Editorial Intelligence

- `scripts.intelligence.editorial_engine.load_trends(input_path: Path = OUTPUT_TRENDS_PATH) -> list[dict[str, Any]]`
- `scripts.intelligence.editorial_engine.fallback_editorial(trend: dict[str, Any]) -> dict[str, Any]`
- `scripts.intelligence.editorial_engine.validate_editorial_response(response: dict[str, Any], trend: dict[str, Any]) -> dict[str, Any]`
- `scripts.intelligence.editorial_engine.analyze_trend(trend: dict[str, Any]) -> dict[str, Any]`
- `scripts.intelligence.editorial_engine.save_editorial_trends(editorial_trends: list[dict[str, Any]], output_path: Path = OUTPUT_EDITORIAL_TRENDS_PATH) -> Path`
- `scripts.intelligence.editorial_engine.run_editorial_engine() -> list[dict[str, Any]]`

## Script Strategy

- `scripts.strategy.strategy_mapper.map_strategy(editorial: dict[str, Any]) -> dict[str, Any]`
- `scripts.strategy.strategy_validator.validate_strategy(strategy: dict[str, Any]) -> dict[str, Any]`
- `scripts.strategy.strategy_refiner.build_refinement_prompt(editorial: dict[str, Any], strategy: dict[str, Any]) -> str`
- `scripts.strategy.strategy_refiner.refine_strategy(editorial: dict[str, Any], deterministic_strategy: dict[str, Any]) -> dict[str, Any]`
- `scripts.strategy.strategy_refiner.merge_refinement(deterministic_strategy: dict[str, Any], refinement: dict[str, Any]) -> dict[str, Any]`
- `scripts.strategy.script_strategy_engine.load_editorial_trends(input_path: Path = OUTPUT_EDITORIAL_TRENDS_PATH) -> list[dict[str, Any]]`
- `scripts.strategy.script_strategy_engine.should_refine() -> bool`
- `scripts.strategy.script_strategy_engine.process_editorial_row(editorial: dict[str, Any]) -> tuple[dict[str, Any] | None, bool]`
- `scripts.strategy.script_strategy_engine.save_strategies(strategies: list[dict[str, Any]], output_path: Path = OUTPUT_SCRIPT_STRATEGIES_PATH) -> Path`
- `scripts.strategy.script_strategy_engine.run_strategy_engine() -> tuple[list[dict[str, Any]], dict[str, Any], Path]`

## Script Generation

- `scripts.script_generation.script_mapper.map_script_blueprint(editorial: dict[str, Any], strategy: dict[str, Any]) -> dict[str, Any]`
- `scripts.script_generation.script_validator.validate_script_blueprint(blueprint: dict[str, Any]) -> dict[str, Any]`
- `scripts.script_generation.script_narrator.narrate_script(editorial: dict[str, Any], strategy: dict[str, Any], blueprint: dict[str, Any]) -> dict[str, Any]`
- `scripts.script_generation.script_narrator.build_narration_prompt(editorial: dict[str, Any], strategy: dict[str, Any], blueprint: dict[str, Any]) -> str`
- `scripts.script_generation.script_narrator.build_fallback_narration(editorial: dict[str, Any], strategy: dict[str, Any], blueprint: dict[str, Any]) -> dict[str, Any]`
- `scripts.script_generation.script_output_validator.validate_narration_output(narration: dict[str, Any]) -> dict[str, Any]`
- `scripts.script_generation.script_engine.load_json_list(input_path: Path) -> list[dict[str, Any]]`
- `scripts.script_generation.script_engine.process_script_row(editorial: dict[str, Any], strategy: dict[str, Any]) -> tuple[dict[str, Any] | None, bool]`
- `scripts.script_generation.script_engine.build_output_script(narration: dict[str, Any], blueprint: dict[str, Any], strategy: dict[str, Any]) -> dict[str, Any]`
- `scripts.script_generation.script_engine.save_scripts(scripts: list[dict[str, Any]], output_path: Path = OUTPUT_SCRIPTS_PATH) -> Path`
- `scripts.script_generation.script_engine.run_script_engine() -> tuple[list[dict[str, Any]], dict[str, Any], Path]`

## Creator Voice

- `scripts.creator_voice.voice_constitution.get_voice_metadata() -> MappingProxyType[str, str]`
- `scripts.creator_voice.voice_constitution.get_core_principles() -> tuple[str, ...]`
- `scripts.creator_voice.voice_constitution.get_style_rules() -> tuple[str, ...]`
- `scripts.creator_voice.voice_constitution.get_forbidden_rules() -> tuple[str, ...]`
- `scripts.creator_voice.voice_constitution.get_voice_targets() -> MappingProxyType[str, Any]`
- `scripts.creator_voice.voice_constitution.build_voice_guidelines() -> tuple[str, ...]`
- `scripts.creator_voice.voice_mapper.build_voice_blueprint(record: dict[str, Any]) -> dict[str, Any]`
- `scripts.creator_voice.voice_mapper.map_voice_records(records: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]`
- `scripts.creator_voice.voice_validator.validate_voice_blueprint(record: dict[str, Any]) -> dict[str, Any]`
- `scripts.creator_voice.voice_validator.validate_voice_records(records: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]`
- `scripts.creator_voice.voice_transformer.transform_voice(record: dict[str, Any]) -> dict[str, Any]`
- `scripts.creator_voice.voice_transformer.transform_voice_records(records: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]`
- `scripts.creator_voice.voice_output_validator.validate_voice_output(record: dict[str, Any]) -> dict[str, Any]`
- `scripts.creator_voice.voice_output_validator.validate_voice_outputs(records: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]`
- `scripts.creator_voice.creator_voice_engine.run_creator_voice_engine() -> tuple[list[dict[str, Any]], dict[str, Any], Path]`
- `scripts.creator_voice.creator_voice_engine.process_record(record: dict[str, Any]) -> dict[str, Any]`

## Visual Planning

- `scripts.visual_planning.visual_constitution.get_visual_metadata() -> MappingProxyType[str, str]`
- `scripts.visual_planning.visual_constitution.get_shot_types() -> tuple[str, ...]`
- `scripts.visual_planning.visual_constitution.get_camera_movements() -> tuple[str, ...]`
- `scripts.visual_planning.visual_constitution.get_visual_styles() -> tuple[str, ...]`
- `scripts.visual_planning.visual_constitution.get_scene_rules() -> tuple[str, ...]`
- `scripts.visual_planning.visual_constitution.get_asset_categories() -> tuple[str, ...]`
- `scripts.visual_planning.visual_constitution.get_transition_types() -> tuple[str, ...]`
- `scripts.visual_planning.visual_constitution.get_forbidden_rules() -> tuple[str, ...]`
- `scripts.visual_planning.visual_constitution.get_quality_targets() -> MappingProxyType[str, Any]`
- `scripts.visual_planning.visual_constitution.get_output_schema() -> MappingProxyType[str, type]`
- `scripts.visual_planning.visual_mapper.build_visual_blueprint(record: dict[str, Any]) -> dict[str, Any]`
- `scripts.visual_planning.visual_mapper.build_visual_blueprints(records: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]`
- `scripts.visual_planning.visual_validator.validate_visual_blueprint(record: dict[str, Any]) -> dict[str, Any]`
- `scripts.visual_planning.visual_validator.validate_visual_blueprints(records: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]`
- `scripts.visual_planning.visual_planner.plan_visuals(record: dict[str, Any]) -> dict[str, Any]`
- `scripts.visual_planning.visual_planner.plan_visuals_batch(records: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]`
- `scripts.visual_planning.visual_output_validator.validate_visual_plan(result: dict[str, Any]) -> dict[str, Any]`
- `scripts.visual_planning.visual_output_validator.validate_visual_plans(results: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]`
- `scripts.visual_planning.visual_planning_engine.process_record(record: dict[str, Any]) -> dict[str, Any]`
- `scripts.visual_planning.visual_planning_engine.process_batch(records: Iterable[dict[str, Any]]) -> dict[str, Any]`

## Utilities

- `scripts.utils.cache_manager.save_cache(cache_path: Path, data: Any) -> bool`
- `scripts.utils.cache_manager.load_cache(cache_path: Path, default: Any = None) -> dict[str, Any] | Any`
- `scripts.utils.cache_manager.is_cache_valid(cache_path: Path, expiration_seconds: int) -> bool`
- `scripts.utils.cache_manager.get_cached_data(cache_path: Path, expiration_seconds: int, default: Any = None) -> Any`
- `scripts.utils.cache_manager.get_stale_cached_data(cache_path: Path, default: Any = None) -> Any`
