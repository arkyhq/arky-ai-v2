# Script Generation Engine Specification

## Purpose

The Script Generation Engine converts one Editorial Object and one Strategy Object into one clean spoken narration script for a 30-60 second short video.

Its job is to answer:

> "What should the narrator say?"

The engine must produce spoken narration only. It must not add creator personality, visual direction, subtitle timing, voice synthesis, editing instructions, thumbnails, captions, or media plans.

## Pipeline Position

Current frozen pipeline:

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

The Script Generation Engine consumes frozen editorial and strategy outputs. It produces the base narration that later engines may adapt, style, voice, subtitle, and assemble.

## Inputs

The engine receives two objects for the same trend.

### Editorial Object

Produced by the Editorial Intelligence Engine.

| Field | Required | Purpose | Usage |
|---|---:|---|---|
| `story_type` | Yes | Editorial category of the trend | Guides factual framing and script angle |
| `main_entities` | Yes | People, brands, shows, creators, or groups involved | Used only when present and reliable |
| `story_summary` | Yes | Concise factual summary | Primary factual source for the script |
| `why_people_care` | Yes | Audience relevance | Used to explain stakes or emotional relevance |
| `primary_conflict` | Yes | Central tension, debate, or uncertainty | Used only if not empty or unknown |
| `confidence` | Yes | Editorial confidence from 0.0 to 1.0 | Controls caution, specificity, and claim strength |
| `editorial_tags` | Optional | Topic hints | Used for vocabulary and contextual framing only |
| `risk_level` | Yes | Safety and claim risk | Controls cautious language and avoids overstatement |
| `evergreen` | Yes | Whether story is time-sensitive or durable | Influences ending and timestamp language |

Low-confidence editorial fields must be treated cautiously. If `confidence < 0.5`, the script must avoid specific claims beyond the provided summary and should use neutral phrasing such as "appears to", "is being discussed", or "viewers are reacting to".

### Strategy Object

Produced by the Script Strategy Engine.

| Field | Required | Purpose | Usage |
|---|---:|---|---|
| `story_archetype` | Yes | Strategy-level story category | Selects script shape and tone of structure |
| `opening_style` | Yes | How the first sentence should open | Determines the first sentence pattern |
| `hook_direction` | Yes | What the opening should point toward | Guides, but does not write, the opening idea |
| `opening_intensity` | Yes | Strength of the opening | Controls urgency and wording intensity |
| `story_arc` | Yes | Overall script structure | Determines beginning, middle, and ending progression |
| `reveal_order` | Yes | Ordered information beats | Determines beat sequence |
| `emotion_curve` | Yes | Intended viewer emotional movement | Guides wording energy and transitions |
| `viewer_trigger` | Yes | Primary retention driver | Guides emphasis, not factual content |
| `retention_pattern` | Yes | How attention should be held | Controls reveal timing and sentence progression |
| `curiosity_gap` | Yes | Strength of unanswered question | Controls whether delayed payoff is allowed |
| `ending_style` | Yes | Closing structure | Determines final sentence type |
| `pacing` | Yes | Slow, medium, or fast | Controls sentence length and beat density |
| `information_density` | Yes | Low, medium, or high | Controls amount of detail |
| `claim_safety` | Yes | Claim caution level | Controls factual certainty and wording |
| `strategy_confidence` | Yes | Strategy confidence from 0.0 to 1.0 | Controls fallback and strictness |
| `fallback_used` | Yes | Whether safe default strategy was used | Forces conservative script behavior when true |

The Strategy Object controls structure, pacing, and rhetorical flow. It does not supply facts.

## Output

The engine outputs one Script Object.

The script must be a complete spoken narration draft, ready for the Creator Voice Engine.

## JSON Schema

```json
{
  "script_id": "string",
  "source_topic": "string",
  "spoken_script": "string",
  "script_beats": [
    {
      "beat_type": "string",
      "text": "string",
      "estimated_seconds": 0.0
    }
  ],
  "estimated_duration_seconds": 0.0,
  "word_count": 0,
  "reading_level": "string",
  "tone_safety": "string",
  "factual_safety": "string",
  "generation_confidence": 0.0,
  "fallback_used": false,
  "metadata": {}
}
```

### Field Definitions

| Field | Type | Required | Allowed Values / Rules | Purpose | Example |
|---|---|---:|---|---|---|
| `script_id` | string | Yes | Stable unique identifier or deterministic row id | Tracks script object | `"script_0001"` |
| `source_topic` | string | Yes | Non-empty | Links script to trend topic | `"Netflix series reaction"` |
| `spoken_script` | string | Yes | 75-150 words, no markdown | Final narration text | `"A new Netflix series is getting attention..."` |
| `script_beats` | list<object> | Yes | 3-7 beats | Breaks narration into logical spoken units | See schema |
| `beat_type` | string | Yes | `opening`, `context`, `conflict`, `reaction`, `why_it_matters`, `payoff`, `ending`, `caution` | Beat role | `"opening"` |
| `text` | string | Yes | Non-empty spoken sentence or sentence group | Beat narration | `"Here is why people are talking about it."` |
| `estimated_seconds` | number | Yes | `> 0`, total should match duration estimate | Approximate spoken duration | `5.2` |
| `estimated_duration_seconds` | number | Yes | Target 30-60 | Estimated narration runtime | `43.5` |
| `word_count` | integer | Yes | Target 75-150 | Length validation | `112` |
| `reading_level` | string | Yes | `simple`, `standard`, `dense` | Spoken complexity | `"standard"` |
| `tone_safety` | string | Yes | `neutral`, `careful`, `sensitive` | Tone risk level | `"careful"` |
| `factual_safety` | string | Yes | `normal`, `cautious`, `very_cautious` | Claim certainty level | `"cautious"` |
| `generation_confidence` | number | Yes | 0.0-1.0 | Confidence in script usability | `0.82` |
| `fallback_used` | boolean | Yes | true or false | Whether safe fallback script shape was used | `false` |
| `metadata` | object | Yes | Plain JSON only | Diagnostics, not script content | `{"source_strategy": "simple_news"}` |

## Responsibilities

The Script Generation Engine owns:

- Turning editorial facts into spoken narration.
- Following the Strategy Object's story structure.
- Producing a complete 30-60 second base script.
- Maintaining factual caution based on confidence and risk.
- Avoiding unsupported claims.
- Keeping language clear, speakable, and direct.
- Returning a validated Script Object.

## Non-Responsibilities

The engine must not:

- Add creator personality or catchphrases.
- Add visual instructions.
- Add subtitle timing or subtitle chunks.
- Generate TTS audio.
- Choose music, images, clips, or edits.
- Generate thumbnails.
- Generate captions or hashtags.
- Perform new editorial analysis.
- Rank, filter, or deduplicate trends.
- Invent facts, quotes, dates, names, allegations, or outcomes.
- Override deterministic strategy decisions.

## Story Flow

The script must follow the Strategy Object's `reveal_order` and `story_arc`.

Recommended beat structure:

1. Opening: introduce the point of attention.
2. Context: explain what the viewer needs to know.
3. Conflict or key detail: present the central issue, reaction, or shift.
4. Why it matters: connect to audience interest.
5. Payoff or ending: close with the takeaway, open question, or next step.

The script may omit a conflict beat when `primary_conflict` is missing, unknown, or low confidence.

## Sentence Structure

Scripts must sound natural when spoken aloud.

Rules:

- Prefer short sentences.
- Use one idea per sentence.
- Avoid dense clauses.
- Avoid written-report phrasing.
- Avoid markdown, bullet points, scene labels, timestamps, or speaker names.
- Avoid rhetorical overuse.
- Do not include visual directions such as "show a clip" or "cut to".
- Do not include creator voice traits such as slang, catchphrases, or signature tone.

### Pacing-Based Sentence Rules

| Pacing | Sentence Style | Target |
|---|---|---|
| `slow` | Short, clear, explanatory | Sensitive, high-risk, or low-confidence stories |
| `medium` | Balanced sentence length | Default short-form narration |
| `fast` | Shorter beats, quicker reveals | Low-risk viral or meme stories |

High-risk stories must not use aggressive phrasing even if `pacing` is fast.

## Length Rules

Target spoken script length:

- Minimum: 75 words
- Ideal: 90-130 words
- Maximum: 150 words

Duration estimate:

- 30 seconds: approximately 75-90 words
- 45 seconds: approximately 100-125 words
- 60 seconds: approximately 130-150 words

If strategy confidence is low, prefer shorter scripts with fewer claims.

## Timing Rules

The engine must estimate duration using word count and pacing.

Suggested estimate:

- Slow: 2.0 words per second
- Medium: 2.4 words per second
- Fast: 2.8 words per second

The output must include `estimated_duration_seconds`.

If the script exceeds 60 seconds, it must be shortened before output.

## Factual Accuracy Rules

The script may only use facts present in the Editorial Object.

Allowed:

- Rephrasing the provided summary.
- Explaining why the audience cares using provided `why_people_care`.
- Naming entities listed in `main_entities`.
- Referring to conflict only from `primary_conflict`.
- Using cautious uncertainty when confidence is low.

Not allowed:

- Adding new allegations.
- Adding dates not supplied.
- Adding quotes not supplied.
- Naming people not supplied.
- Claiming causation from correlation.
- Presenting rumors as confirmed facts.
- Expanding vague summaries into specific claims.
- Creating timelines not provided by editorial input.

## Hallucination Prevention

The engine must apply strict claim boundaries.

If a field is missing, vague, or low confidence:

- Use generic framing.
- Do not fill the gap.
- Avoid specific claims.
- Prefer "people are discussing" over "this proves".
- Prefer "the conversation centers on" over unsupported certainty.

If `risk_level == "high"` or `claim_safety == "very_careful"`:

- Avoid accusation language.
- Avoid definitive blame.
- Avoid naming alleged wrongdoing unless explicitly present.
- Use neutral phrases such as "discussion", "reaction", "claim", or "reported".

## Deterministic vs LLM Responsibilities

The engine should be hybrid.

### Deterministic Responsibilities

These must be handled by deterministic code:

- Input presence checks.
- Schema validation.
- Word count validation.
- Duration estimation.
- Required output fields.
- Fallback script creation.
- Risk-level safety enforcement.
- Claim-safety enforcement.
- Removing markdown or forbidden formatting.
- Ensuring no visual or creator-voice fields are emitted.

### LLM Responsibilities

An LLM may be used to draft the spoken narration.

The LLM may:

- Convert approved facts into natural spoken prose.
- Follow the strategy's reveal order.
- Adjust sentence flow for pacing.
- Improve clarity and coherence.

The LLM must not:

- Override the Strategy Object.
- Add new facts.
- Add personality or creator style.
- Add visuals or production instructions.
- Change output schema.
- Ignore risk and claim safety.

Deterministic validation must run after any LLM generation.

## Validation

Validation must check:

- Output is a dictionary.
- All required fields exist.
- `spoken_script` is a non-empty string.
- `spoken_script` contains no markdown or code fences.
- `spoken_script` contains no visual planning language.
- `script_beats` is a non-empty list.
- Beat text appears in or aligns with `spoken_script`.
- Word count is within allowed range or repaired.
- Estimated duration is within 30-60 seconds or flagged.
- Enum values are valid.
- Confidence is clamped to 0.0-1.0.
- High-risk stories use cautious factual language.
- Low-confidence stories avoid strong claims.
- No protected strategy decisions are contradicted.

## Failure Handling

### Missing Editorial Fields

Use safe fallback narration only if minimum required fields are present. If `story_summary` is missing, generation should fail for that row with a clear error.

### Missing Strategy Fields

Reject the row unless a validated Strategy Object can be provided by the previous engine.

### Low Confidence

Use a conservative script:

- Shorter length.
- Neutral language.
- No strong curiosity gap.
- No speculative claims.

### High Risk

Use very cautious script language:

- Avoid blame.
- Avoid escalation.
- Use context-first structure.
- Prefer clear summary over dramatic opening.

### LLM Failure

If the LLM fails, times out, returns invalid JSON, or produces unsafe content:

1. Discard the LLM output.
2. Generate deterministic fallback narration if possible.
3. Mark `fallback_used` as `true`.
4. Lower `generation_confidence`.
5. Continue processing other rows.

### Invalid Output

Invalid outputs must not be saved as successful scripts. They must be repaired only when safe. If repair would require inventing facts, the row must fail or use deterministic fallback.

## Integration With Script Strategy Engine

Input contract:

- The Strategy Object must already be validated.
- The engine must not call the Strategy Mapper, Validator, or Refiner directly unless used by a future orchestrator.
- The engine must treat strategy fields as structural constraints.

Expected input pairing:

```json
{
  "editorial": {},
  "strategy": {}
}
```

The implementation may pair rows by index or stable identifiers, but must not infer missing relationships.

## Integration With Creator Voice Engine

The Script Generation Engine outputs a neutral base narration.

The Creator Voice Engine may later:

- Adjust tone.
- Add creator-specific phrasing.
- Improve rhythm.
- Add personality.
- Adapt phrasing for a specific channel.

The Creator Voice Engine must not need to reconstruct facts or strategy. It should receive:

- `spoken_script`
- `script_beats`
- factual safety metadata
- editorial and strategy references if needed

The base script must therefore be clean, neutral, and structurally complete.

## Safe Defaults

When uncertain, use:

```json
{
  "reading_level": "simple",
  "tone_safety": "careful",
  "factual_safety": "cautious",
  "generation_confidence": 0.5,
  "fallback_used": true
}
```

Fallback narration should use:

- context-first opening
- neutral explanation
- no accusation language
- clean resolution ending
- 75-100 words

## Freeze Criteria

The Script Generation Engine may be frozen only when all conditions pass:

### Unit Testing

- Valid editorial and strategy input generates valid script output.
- Missing required editorial fields fail clearly.
- Missing strategy fields fail clearly.
- Low-confidence inputs produce cautious language.
- High-risk inputs produce cautious language.
- LLM failure produces deterministic fallback.
- Invalid LLM JSON is discarded.
- Word count and duration checks pass.

### Integration Testing

- Runs successfully after the frozen Script Strategy Engine.
- Processes a realistic batch of editorial and strategy rows.
- Continues when individual rows fail.
- Produces valid output JSON.
- Does not modify previous engine outputs.

### Schema Validation

- Every output object matches the Script Object schema.
- No extra engine responsibilities appear in output.
- No visual, subtitle, voice, or creator-personality fields appear.

### Content Quality Review

Review at least 20 generated scripts for:

- factual accuracy
- natural spoken flow
- correct strategy adherence
- safe claim wording
- appropriate length
- no hallucinated details
- no creator voice leakage
- no visual planning leakage

### Deterministic Consistency

With the same inputs and deterministic fallback path, output structure and safety behavior must be stable.

### LLM Fallback Testing

The engine must pass tests for:

- timeout
- rate limit
- empty response
- malformed JSON
- unsafe output
- hallucinated facts

In all cases, the engine must avoid crashing the pipeline and must not save unsafe generated content.

