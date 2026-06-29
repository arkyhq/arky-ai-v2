# Script Strategy Engine Specification

## Status

This document defines the engineering contract for the Script Strategy Engine.

The Trend Intelligence Engine and Editorial Intelligence Engine are frozen. This engine must consume their outputs without requiring changes to either engine.

## Pipeline Position

```text
Trend Intelligence Engine
-> Editorial Intelligence Engine
-> Script Strategy Engine
-> Script Generation Engine
-> Creator Voice Engine
-> Visual Planning Engine
-> Asset Intelligence Engine
-> Subtitle Engine
-> TTS Engine
-> Video Builder
```

## Core Purpose

The Script Strategy Engine answers one question:

> Given this editorial understanding, what is the most effective storytelling strategy for a 30-60 second short video?

It decides the strategic shape of the story. It does not write the story.

## Non-Responsibilities

The Script Strategy Engine must not:

- Write scripts.
- Generate exact hook text.
- Generate captions.
- Rewrite trend or editorial text.
- Add creator voice.
- Select visuals.
- Choose assets.
- Plan subtitles.
- Generate TTS instructions.
- Perform editorial analysis.
- Invent facts.
- Override the Editorial Intelligence Engine's factual understanding.

## Inputs

The engine consumes rows from `outputs/editorial_trends.json`.

Each input row is a trend dictionary merged with editorial intelligence. The engine should preserve all input fields and append a strategy object or strategy fields, depending on final implementation choice.

### Input Field Contract

| Field | Required | Purpose | Strategy Usage | Low-Confidence Handling |
|---|---:|---|---|---|
| `topic` | Yes | Human-readable trend title. | Use only as a label and lightweight context. | Do not infer missing facts from vague topic text. |
| `source` | Yes | Origin of trend, such as `reddit` or `google_trends`. | May influence pacing confidence, not story facts. | If unknown, use neutral source assumptions. |
| `trend_score` | Optional | Priority score from Trend Engine. | May influence urgency and pacing intensity. | If missing, use medium urgency. |
| `story_type` | Yes | Editorial classification of the story shape. | Primary driver of strategy mapping. | If `unknown`, use `simple_news` fallback strategy. |
| `main_entities` | Yes | Named people, shows, brands, creators, or objects. | Use to determine whether strategy can center entities. | If empty, avoid entity-led strategy. |
| `story_summary` | Yes | Concise editorial understanding. | Main factual context for strategy decisions. | If empty or generic, choose low-risk explanatory strategy. |
| `why_people_care` | Yes | Audience relevance signal. | Drives viewer trigger and emotional emphasis. | If weak, use informational strategy rather than emotional strategy. |
| `primary_conflict` | Yes | Core tension, if known. | Drives reveal order and retention pattern. | If `unknown`, avoid conflict-led strategy. |
| `confidence` | Yes | Editorial confidence from `0.0` to `1.0`. | Controls strategy aggressiveness and information density. | Below `0.5`, use conservative pacing and avoid strong claims. |
| `editorial_tags` | Yes | Short topical labels. | Secondary signal for archetype mapping. | If tags conflict with story type, prefer story type and confidence. |
| `risk_level` | Yes | `low`, `medium`, or `high`. | Controls caution, claim strength, and ending style. | If missing or invalid, treat as `medium`. |
| `evergreen` | Yes | Whether the story remains useful beyond the moment. | Influences urgency and ending style. | If unknown, assume `false`. |

## Output Contract

The Script Strategy Engine produces a deterministic strategy object for each editorial trend.

Recommended output shape:

```json
{
  "strategy": {
    "strategy_version": "1.0",
    "story_archetype": "simple_news",
    "opening_style": "context_first",
    "hook_direction": "why_it_matters",
    "hook_strength": "medium",
    "story_arc": "context_tension_payoff",
    "reveal_order": ["context", "key_detail", "why_it_matters", "payoff"],
    "emotion_curve": ["curiosity", "clarity", "resolution"],
    "viewer_trigger": "curiosity",
    "retention_pattern": "single_open_loop",
    "curiosity_gap": "moderate",
    "ending_style": "clean_resolution",
    "pacing": "medium",
    "information_density": "medium",
    "pause_points": ["after_context", "before_payoff"],
    "claim_safety": "normal",
    "strategy_confidence": 0.82,
    "fallback_used": false
  }
}
```

The output must not contain generated script lines.

## Output Fields

### `strategy_version`

- Purpose: Version the strategy schema for future compatibility.
- Type: string.
- Allowed values: semantic version string, starting with `"1.0"`.
- Validation: required, non-empty.
- Example: `"1.0"`.

### `story_archetype`

- Purpose: Normalized strategy-facing story shape.
- Type: string.
- Allowed values:
  - `controversy`
  - `creator_update`
  - `tribute`
  - `meme`
  - `wholesome`
  - `viral_clip`
  - `industry_update`
  - `community_discussion`
  - `simple_news`
  - `audience_reaction`
  - `nostalgic_moment`
  - `creator_exposed`
  - `gaming_integrity`
  - `unknown`
- Validation: required; fallback to `unknown`.
- Example: `"industry_update"`.

### `opening_style`

- Purpose: Define how the video should begin structurally.
- Type: string.
- Allowed values:
  - `context_first`
  - `conflict_first`
  - `entity_first`
  - `question_first`
  - `reaction_first`
  - `stakes_first`
  - `timeline_first`
- Validation: required.
- Example: `"conflict_first"`.

This is not hook text. It is a structural instruction for the Script Generation Engine.

### `hook_direction`

- Purpose: Define the strategic promise of the opening.
- Type: string.
- Allowed values:
  - `what_happened`
  - `why_it_matters`
  - `what_changed`
  - `who_is_involved`
  - `why_people_are_reacting`
  - `what_people_missed`
  - `what_happens_next`
- Validation: required.
- Example: `"why_people_are_reacting"`.

This field must not contain final hook wording.

### `hook_strength`

- Purpose: Control how aggressive the opening may be.
- Type: string.
- Allowed values: `low`, `medium`, `high`.
- Validation: required.
- Example: `"medium"`.

Rules:

- `high` only when confidence is high and risk is low.
- `low` when risk is high or confidence is below `0.5`.
- Never use high hook strength for vague, high-risk, or low-confidence stories.

### `story_arc`

- Purpose: Define the strategic sequence of the narrative.
- Type: string.
- Allowed values:
  - `context_tension_payoff`
  - `setup_reveal_reaction`
  - `claim_context_implication`
  - `timeline_turn_resolution`
  - `problem_response_outcome`
  - `question_answer_takeaway`
  - `moment_context_meaning`
- Validation: required.
- Example: `"setup_reveal_reaction"`.

### `reveal_order`

- Purpose: Define the order in which information should be revealed.
- Type: array of strings.
- Allowed values per item:
  - `context`
  - `entity`
  - `key_detail`
  - `conflict`
  - `reaction`
  - `stakes`
  - `timeline`
  - `why_it_matters`
  - `payoff`
  - `caution`
- Validation: required, 3-6 items, no duplicates.
- Example: `["entity", "conflict", "reaction", "payoff"]`.

### `emotion_curve`

- Purpose: Define the intended viewer emotional progression.
- Type: array of strings.
- Allowed values:
  - `curiosity`
  - `surprise`
  - `concern`
  - `amusement`
  - `nostalgia`
  - `admiration`
  - `skepticism`
  - `clarity`
  - `relief`
  - `resolution`
- Validation: required, 2-4 items.
- Example: `["curiosity", "surprise", "clarity"]`.

### `viewer_trigger`

- Purpose: Identify the main reason a viewer keeps watching.
- Type: string.
- Allowed values:
  - `curiosity`
  - `identity`
  - `controversy`
  - `emotion`
  - `nostalgia`
  - `social_proof`
  - `utility`
  - `surprise`
- Validation: required.
- Example: `"curiosity"`.

### `retention_pattern`

- Purpose: Define the retention mechanism without writing copy.
- Type: string.
- Allowed values:
  - `linear_explanation`
  - `single_open_loop`
  - `delayed_context`
  - `escalating_reveals`
  - `reaction_build`
  - `timeline_countdown`
  - `contrast_pattern`
- Validation: required.
- Example: `"single_open_loop"`.

### `curiosity_gap`

- Purpose: Control how much information is intentionally delayed.
- Type: string.
- Allowed values: `none`, `light`, `moderate`, `strong`.
- Validation: required.
- Example: `"moderate"`.

Rules:

- `strong` requires high confidence, low risk, and clear payoff.
- `none` is preferred for tributes, high-risk topics, and low-confidence stories.

### `ending_style`

- Purpose: Define the ending strategy.
- Type: string.
- Allowed values:
  - `clean_resolution`
  - `open_question`
  - `what_next`
  - `audience_reflection`
  - `contextual_takeaway`
  - `soft_landing`
- Validation: required.
- Example: `"what_next"`.

This is not a call-to-action or caption.

### `pacing`

- Purpose: Define overall speed of information delivery.
- Type: string.
- Allowed values: `slow`, `medium`, `fast`.
- Validation: required.
- Example: `"fast"`.

Rules:

- Low confidence reduces pacing by one level.
- High risk cannot use `fast` pacing unless the story is purely factual and simple.

### `information_density`

- Purpose: Define how much information should be packed into the script.
- Type: string.
- Allowed values: `low`, `medium`, `high`.
- Validation: required.
- Example: `"medium"`.

Rules:

- High density is appropriate for industry updates and simple news.
- Low density is appropriate for emotional, vague, or high-risk stories.

### `pause_points`

- Purpose: Suggest structural pause locations for script rhythm.
- Type: array of strings.
- Allowed values:
  - `after_opening`
  - `after_context`
  - `before_reveal`
  - `after_reveal`
  - `before_payoff`
  - `before_ending`
- Validation: optional, max 3 items.
- Example: `["after_context", "before_payoff"]`.

Pause points are strategic rhythm markers, not subtitle timing.

### `claim_safety`

- Purpose: Tell later engines how cautious wording should be.
- Type: string.
- Allowed values: `normal`, `careful`, `very_careful`.
- Validation: required.
- Example: `"careful"`.

Rules:

- `risk_level = high` -> `very_careful`.
- `confidence < 0.5` -> at least `careful`.
- Unknown conflict -> at least `careful`.

### `strategy_confidence`

- Purpose: Confidence in the strategy selection, not the factual story.
- Type: number.
- Allowed range: `0.0` to `1.0`.
- Validation: required, clamp to range.
- Example: `0.82`.

### `fallback_used`

- Purpose: Indicate whether safe default strategy was used.
- Type: boolean.
- Allowed values: `true`, `false`.
- Validation: required.
- Example: `false`.

## Fields That Do Not Belong In Strategy

The following should be owned by later engines:

| Field | Owner | Reason |
|---|---|---|
| Exact hook text | Script Generation Engine | Strategy defines direction, not wording. |
| Full script | Script Generation Engine | Strategy does not write. |
| Creator phrasing | Creator Voice Engine | Voice adaptation happens later. |
| Scene descriptions | Visual Planning Engine | Strategy may define priority, not visuals. |
| Asset choices | Asset Intelligence Engine | Requires media inventory and search. |
| Subtitle chunks | Subtitle Engine | Timing comes after script/audio. |
| TTS voice or speed | TTS Engine | Audio delivery is downstream. |
| Thumbnail/caption | Later packaging layer | Not part of story strategy. |

## Responsibilities

### Script Strategy Engine Owns

- Mapping editorial understanding to storytelling strategy.
- Selecting story archetype.
- Choosing reveal order.
- Choosing retention pattern.
- Choosing pacing and density.
- Choosing safe claim posture.
- Producing a validated strategy schema.
- Falling back safely when editorial input is weak.

### Editorial Intelligence Engine Owns

- Understanding what the trend is.
- Identifying story type.
- Identifying entities.
- Summarizing why people care.
- Estimating confidence and risk.

### Script Generation Engine Owns

- Writing actual spoken script.
- Writing hook text.
- Writing transitions.
- Choosing phrasing.
- Producing the 30-60 second script.

### Creator Voice Engine Owns

- Adapting script tone.
- Matching creator style.
- Changing sentence rhythm.
- Adding channel-specific language.

### Visual Planning Engine Owns

- Translating script beats into visual beats.
- Planning visual sequence.
- Suggesting shot or scene types.

## Story Archetype Mapping

### `controversy`

- Opening approach: conflict first.
- Reveal order: entity -> conflict -> reaction -> stakes -> caution.
- Viewer emotion: curiosity -> concern -> clarity.
- Retention style: escalating reveals.
- Ending style: contextual takeaway.
- Pacing: medium.
- Notes: Use careful claim safety. Avoid strong curiosity gaps if facts are uncertain.

### `creator_update`

- Opening approach: entity first.
- Reveal order: entity -> what_changed -> why_it_matters -> what_next.
- Viewer emotion: curiosity -> clarity -> anticipation.
- Retention style: single open loop.
- Ending style: what next.
- Pacing: medium to fast.
- Notes: Works best when main entity is explicit.

### `tribute`

- Opening approach: context first or entity first.
- Reveal order: entity -> moment -> meaning -> audience reflection.
- Viewer emotion: admiration -> nostalgia -> reflection.
- Retention style: linear explanation.
- Ending style: soft landing.
- Pacing: slow.
- Notes: Avoid curiosity bait. Avoid strong open loops.

### `meme`

- Opening approach: reaction first.
- Reveal order: moment -> reaction -> context -> payoff.
- Viewer emotion: amusement -> surprise -> clarity.
- Retention style: reaction build.
- Ending style: clean resolution.
- Pacing: fast.
- Notes: High density is usually harmful.

### `wholesome`

- Opening approach: moment first.
- Reveal order: moment -> context -> why_people_care -> soft payoff.
- Viewer emotion: warmth -> admiration -> relief.
- Retention style: linear explanation.
- Ending style: soft landing.
- Pacing: slow to medium.
- Notes: Avoid conflict-led framing.

### `viral_clip`

- Opening approach: stakes first or reaction first.
- Reveal order: moment -> context -> reaction -> payoff.
- Viewer emotion: curiosity -> surprise -> clarity.
- Retention style: delayed context.
- Ending style: clean resolution.
- Pacing: fast.
- Notes: The Script Generation Engine may later describe the clip, but Strategy must not invent visuals.

### `industry_update`

- Opening approach: what changed first.
- Reveal order: key_detail -> context -> implication -> what_next.
- Viewer emotion: curiosity -> clarity -> anticipation.
- Retention style: contrast pattern.
- Ending style: what next.
- Pacing: medium.
- Notes: Higher information density is acceptable.

### `community_discussion`

- Opening approach: why people are reacting.
- Reveal order: topic -> reaction -> competing views -> takeaway.
- Viewer emotion: curiosity -> skepticism -> clarity.
- Retention style: reaction build.
- Ending style: open question.
- Pacing: medium.
- Notes: Avoid choosing sides unless editorial data explicitly supports it.

### `simple_news`

- Opening approach: context first or what happened first.
- Reveal order: context -> key_detail -> why_it_matters -> payoff.
- Viewer emotion: curiosity -> clarity -> resolution.
- Retention style: linear explanation or single open loop.
- Ending style: clean resolution.
- Pacing: medium.
- Notes: Default fallback archetype for unknown but usable stories.

### `audience_reaction`

- Opening approach: reaction first.
- Reveal order: reaction -> cause -> context -> takeaway.
- Viewer emotion: curiosity -> surprise -> clarity.
- Retention style: reaction build.
- Ending style: audience reflection.
- Pacing: medium to fast.
- Notes: Use only if audience reaction is present in editorial fields.

### `nostalgic_moment`

- Opening approach: entity or moment first.
- Reveal order: entity -> memory cue -> why_it_resonates -> reflection.
- Viewer emotion: nostalgia -> warmth -> reflection.
- Retention style: linear explanation.
- Ending style: audience reflection.
- Pacing: slow to medium.
- Notes: Avoid controversy framing.

### `creator_exposed`

- Opening approach: conflict first.
- Reveal order: entity -> allegation_or_issue -> reaction -> caution -> what_next.
- Viewer emotion: curiosity -> concern -> skepticism.
- Retention style: escalating reveals.
- Ending style: contextual takeaway.
- Pacing: medium.
- Notes: Requires high claim safety. If confidence is low, downgrade to `community_discussion` or `simple_news`.

### `gaming_integrity`

- Opening approach: stakes first.
- Reveal order: game_or_creator -> integrity_issue -> community_reaction -> implication.
- Viewer emotion: curiosity -> concern -> clarity.
- Retention style: escalating reveals.
- Ending style: what next.
- Pacing: medium to fast.
- Notes: Use careful claim safety unless facts are explicit.

### `unknown`

- Opening approach: context first.
- Reveal order: context -> key_detail -> why_it_matters.
- Viewer emotion: curiosity -> clarity.
- Retention style: linear explanation.
- Ending style: clean resolution.
- Pacing: medium or slow.
- Notes: Use low hook strength, low curiosity gap, and careful claim safety.

## Retention Design

### When Curiosity Loops Should Be Used

Use curiosity loops when:

- Editorial confidence is at least `0.65`.
- The story has a clear payoff.
- Risk level is `low` or `medium`.
- The topic has an explicit conflict, reaction, reveal, or change.

### When Curiosity Loops Should Not Be Used

Avoid curiosity loops when:

- The story is a tribute or wholesome moment.
- The topic is high risk.
- Editorial confidence is below `0.5`.
- The payoff is unclear.
- The input is too generic.

### When Open Loops Are Harmful

Open loops are harmful when they imply facts the system does not know. They are also harmful when they delay essential context in sensitive stories.

High-risk topics should prefer clarity before curiosity.

### Payoff Timing

For 30-60 second videos:

- Low-risk viral stories: payoff between 60-75 percent of runtime.
- Simple news: payoff between 50-65 percent.
- High-risk or low-confidence stories: payoff early, between 35-50 percent.
- Tribute or wholesome stories: no hard delayed payoff required.

### Information Density By Story Type

| Story Type | Density |
|---|---|
| `industry_update` | high |
| `simple_news` | medium |
| `controversy` | medium |
| `creator_update` | medium |
| `viral_clip` | low to medium |
| `meme` | low |
| `tribute` | low |
| `wholesome` | low |
| `unknown` | low |

### Pacing By Confidence

| Editorial Confidence | Pacing Rule |
|---:|---|
| `0.80-1.00` | May use archetype default. |
| `0.60-0.79` | Use medium pacing unless archetype demands slow. |
| `0.40-0.59` | Use slow or medium; reduce hook strength. |
| `< 0.40` | Use slow, low-density, linear explanation. |

## Deterministic vs LLM Responsibilities

The Script Strategy Engine should be hybrid.

### Deterministic Decisions

These must remain deterministic:

- Required output schema.
- Field validation.
- Fallback behavior.
- Confidence thresholds.
- Risk-based claim safety.
- Allowed values.
- Story type to archetype fallback.
- Low-confidence downgrades.
- Whether LLM output is accepted or repaired.

### LLM-Refinable Decisions

Groq may refine:

- More nuanced `viewer_trigger`.
- Better `emotion_curve` within allowed values.
- Cleaner `reveal_order` within allowed values.
- `ending_style` when multiple safe options exist.
- `strategy_confidence` estimate, if validated.

### LLM Must Never Override

Groq must never override:

- Editorial facts.
- Risk level.
- Confidence thresholds.
- Required schema.
- Allowed enum values.
- Safe fallback requirements.
- Factual uncertainty.

If LLM output conflicts with deterministic safety rules, deterministic rules win.

## Validation Requirements

### Required Fields

Every strategy object must include:

- `strategy_version`
- `story_archetype`
- `opening_style`
- `hook_direction`
- `hook_strength`
- `story_arc`
- `reveal_order`
- `emotion_curve`
- `viewer_trigger`
- `retention_pattern`
- `curiosity_gap`
- `ending_style`
- `pacing`
- `information_density`
- `pause_points`
- `claim_safety`
- `strategy_confidence`
- `fallback_used`

### Validation Rules

- Unknown enum values must be replaced with safe defaults.
- Missing arrays must become empty arrays or default arrays.
- Arrays must be deduplicated.
- Arrays must contain only allowed strings.
- Numeric confidence must be clamped to `0.0-1.0`.
- `fallback_used` must be boolean.
- No generated script text is allowed.

### Safe Defaults

```json
{
  "strategy_version": "1.0",
  "story_archetype": "unknown",
  "opening_style": "context_first",
  "hook_direction": "what_happened",
  "hook_strength": "low",
  "story_arc": "question_answer_takeaway",
  "reveal_order": ["context", "key_detail", "why_it_matters"],
  "emotion_curve": ["curiosity", "clarity"],
  "viewer_trigger": "curiosity",
  "retention_pattern": "linear_explanation",
  "curiosity_gap": "none",
  "ending_style": "clean_resolution",
  "pacing": "medium",
  "information_density": "low",
  "pause_points": [],
  "claim_safety": "careful",
  "strategy_confidence": 0.0,
  "fallback_used": true
}
```

## Failure Handling

### Low-Confidence Stories

- Use `hook_strength = low`.
- Use `curiosity_gap = none` or `light`.
- Use `claim_safety = careful`.
- Prefer `linear_explanation`.
- Set `strategy_confidence` no higher than editorial confidence.

### Missing Editorial Fields

- Missing `story_type`: use `unknown`.
- Missing `story_summary`: use topic only as label.
- Missing entities: avoid entity-led opening.
- Missing conflict: avoid conflict-led opening.

### Conflicting Metadata

If `story_type`, `tags`, and `summary` disagree:

1. Prefer `risk_level` for safety decisions.
2. Prefer `confidence` for aggressiveness decisions.
3. Prefer `story_type` for archetype decisions.
4. Use tags only as secondary hints.

### Generic Trends

For trends like `"netflix movies"`:

- Use `simple_news` or `unknown`.
- Use low curiosity gap.
- Avoid implying a specific controversy or release.
- Keep strategy broad and low-risk.

### Unknown Story Types

Map to `unknown`, then apply safe defaults.

### LLM Failure

If Groq fails:

- Use deterministic safe default strategy.
- Set `fallback_used = true`.
- Continue processing remaining rows.

### Invalid JSON

If JSON can be repaired:

- Repair fields into schema.
- Validate enums.
- Apply safety overrides.

If JSON cannot be repaired:

- Use safe defaults.
- Continue processing.

## Integration Contract

### Input From Editorial Intelligence Engine

Input file:

```text
outputs/editorial_trends.json
```

Expected row shape:

```json
{
  "topic": "string",
  "source": "google_trends",
  "trend_score": 63,
  "story_type": "simple_news",
  "main_entities": [],
  "story_summary": "string",
  "why_people_care": "string",
  "primary_conflict": "unknown",
  "confidence": 0.6,
  "editorial_tags": [],
  "risk_level": "low",
  "evergreen": false
}
```

### Output To Script Generation Engine

Recommended output file:

```text
outputs/strategy_trends.json
```

Each row should preserve the editorial row and append `strategy`.

The Script Generation Engine must treat strategy fields as structural guidance, not final wording.

## Freeze Criteria

The Script Strategy Engine can be frozen only when all criteria pass.

### Unit Testing

- Story type mapping tests.
- Low-confidence fallback tests.
- High-risk safety tests.
- Unknown story type tests.
- Enum validation tests.
- Invalid JSON repair tests.
- Missing field tests.

### Integration Testing

- Reads valid `outputs/editorial_trends.json`.
- Writes valid strategy output.
- Preserves input trend/editorial fields.
- Processes empty input safely.
- Continues after per-row failure.

### Schema Validation

- Every output row includes all required strategy fields.
- All enum values are allowed.
- Arrays contain only allowed values.
- `strategy_confidence` is clamped.
- No script text appears in strategy fields.

### Content-Quality Review

Review a representative sample of:

- Generic trend.
- Low-confidence trend.
- High-risk trend.
- Controversy.
- Wholesome story.
- Industry update.
- Creator update.
- Meme or viral clip.

### Deterministic Consistency

The same input must produce the same deterministic baseline strategy every run.

If Groq refinement is enabled, final output must still pass deterministic validation and safety overrides.

### LLM Fallback Testing

Validate behavior when:

- Groq key is missing.
- Groq times out.
- Groq returns invalid JSON.
- Groq returns disallowed enum values.
- Groq returns script text.
- Groq contradicts risk or confidence constraints.

## Implementation Boundaries

The implementation should be small and modular, but this document does not prescribe Python code.

Recommended conceptual modules:

- Strategy mapper.
- Optional LLM refiner.
- Schema validator.
- Fallback builder.
- Engine runner.

No module should write scripts, hooks, captions, creator voice, visual plans, or media instructions.
