# Script Strategy Engine Specification
**Document Version**: 1.0.0  
**Status**: DRAFT DESIGN FOR REVIEW  
**Author**: Senior AI Systems Architect  

---

## 1. Executive Summary & Purpose

The **Script Strategy Engine** is a critical mid-tier orchestration layer in the ARKY-AI-SYSTEM pipeline. Its sole responsibility is to decide **HOW a story should be told**. 

```
[Editorial Engine Output] ──> [Script Strategy Engine] ──> [Script Generation Engine]
                                      │
                         (Determines Storytelling Recipe)
```

### What the Engine DOES:
*   Analyzes raw editorial metadata and decides the structure, pacing, hook mechanics, retention loops, and narrative sequence.
*   Acts as a blueprint or "director's brief" that guides the downstream writing process.

### What the Engine DOES NOT Do:
*   It does **NOT** write actual script lines, dialogue, hooks, or narration (delegated to the Script Generation/Creator Voice Engines).
*   It does **NOT** plan visual scenes or overlays (delegated to the Visual planning/Asset Selector Engines).
*   It does **NOT** determine video editing styles, transitions, subtitle styles, or audio tracks.
*   It does **NOT** perform trend discovery or editorial analyses (already frozen in the Scraper and Editorial layers).

---

## 2. Input Specification

The input to this engine is a single normalized JSON object produced by the **Editorial Intelligence Engine**. Below is the catalog of expected input fields:

### 1. `topic` (String)
*   **Why it exists**: The primary search keyword or headline representing the trend.
*   **Required**: Yes.
*   **Usage**: Used to check against name-entity matches and verify that the hook introduces the core topic immediately.

### 2. `story_type` (String)
*   **Why it exists**: The thematic classification of the trend (e.g., `controversy`, `tribute`, `meme`).
*   **Required**: Yes.
*   **Usage**: Directly selects the baseline storytelling strategy, dictate pacing profiles, and determines the emotional curve.

### 3. `main_entities` (Array of Strings)
*   **Why it exists**: List of key individuals, brands, platforms, or products involved.
*   **Required**: Yes (can be empty array).
*   **Usage**: Determines the narrative focus and the sequence in which entities are introduced during the script.

### 4. `story_summary` (String)
*   **Why it exists**: A concise summary of the core narrative.
*   **Required**: Yes.
*   **Usage**: Provides the semantic background used to calculate reveal order and identify where to position curiosity gaps.

### 5. `why_people_care` (String)
*   **Why it exists**: Clarifies the psychological or cultural driver behind the trend's popularity.
*   **Required**: Yes.
*   **Usage**: Directs the selection of the hook style (e.g., if it appeals to FOMO, safety, nostalgia, or outrage).

### 6. `primary_conflict` (String)
*   **Why it exists**: Identifies the central friction (e.g., person vs. person, creator vs. platform, expectations vs. reality).
*   **Required**: Yes.
*   **Usage**: Defines the dramatic climax of the script. Used to structure open loops that are resolved only at the climax.

### 7. `confidence` (Float)
*   **Why it exists**: Represents the LLM's assessment of input clarity and completeness (value from `0.0` to `1.0`).
*   **Required**: Yes.
*   **Usage**: Determines information density. Low confidence triggers slow pacing with higher explanatory scaffolding; high confidence allows fast, high-density deliveries.

### 8. `editorial_tags` (Array of Strings)
*   **Why it exists**: Meta-tags for classification.
*   **Required**: No (Optional).
*   **Usage**: Assists in choosing micro-elements, such as slang indicators or platform-specific context.

### 9. `risk_level` (String)
*   **Why it exists**: Security check indicating potential controversial or sensitive content (`low`, `medium`, `high`).
*   **Required**: Yes.
*   **Usage**: Constrains hook intensity. If risk is `high`, hooks must be factual and non-inflammatory to protect channel safety.

### 10. `evergreen` (Boolean)
*   **Why it exists**: Indicates whether the topic has long-term value or is a short-lived flash trend.
*   **Required**: Yes.
*   **Usage**: Determines the call-to-action (CTA) style at the ending. Timely trends get immediate interactive CTAs; evergreen trends get subscription-builder or generic CTAs.

---

## 3. Boundary & Responsibility Matrices

To maintain modularity, the architectural boundaries of the Script Strategy Engine are strictly frozen as follows:

| Decision Area | Script Strategy Engine Decides (YES) | Downstream/Upstream Engines Decide (NO) |
|---|---|---|
| **Facts & Context** | How to sequence the facts. | The facts themselves (determined by Editorial / Scraper). |
| **Hook Mechanics** | The *structure* of the hook (e.g., "shocking question", "immediate conflict statement"). | The *exact wording* of the hook (determined by Script Gen). |
| **Narrative Flow** | The choice of arc (e.g., Three-Act vs. Reverse Chronological). | The script body sentences, vocabulary, and vocabulary level. |
| **Creator Voice** | Pacing guidelines (e.g., `fast`, `deliberate`). | Persona traits, accents, tone-of-voice, humor styles. |
| **Pacing & Breaks** | Where to place silent pauses or suspense beats. | The actual audio synthesis, speed rate, or voice actor profiles. |
| **Retention Hooks** | The exact timing and content of open and closed loops. | Visual cues, b-roll selects, or sound effects (SFX) choices. |

---

## 4. Storytelling Strategies by Story Type

The engine maps specific `story_type` classifications to optimized storytelling profiles:

### A. Controversy
*   **Narrative Arc**: Conflict-First.
*   **Opening/Hook**: Shocking statement highlighting the division or disagreement.
*   **Pacing**: Fast. Rapid back-and-forth perspective changes.
*   **Reveal Order**: Core accusation -> Supporting evidence -> Target response -> Broad impact.
*   **Ending**: Open-ended question prompting audience comments to drive engagement.
*   **Emotion Curve**: Anger/Disbelief -> Curiosity -> Analytical -> Tension.

### B. Creator Update
*   **Narrative Arc**: Relatable Journey.
*   **Opening/Hook**: Personal transition or announcement hook (e.g., "Why X is quitting...").
*   **Pacing**: Medium. Conversational and direct.
*   **Reveal Order**: Current status -> Secret backstory -> Action taken -> Future impact.
*   **Ending**: Supportive, community-focused call to action.
*   **Emotion Curve**: Empathy -> Surprise -> Hope -> Solidarity.

### C. Tribute
*   **Narrative Arc**: Chronological Rise and Honor.
*   **Opening/Hook**: Inspiring achievement summary.
*   **Pacing**: Slow-Medium. Respectful and deliberate.
*   **Reveal Order**: Early struggles -> Breakthrough moment -> Peak influence -> Legacy impact.
*   **Ending**: Thought-provoking summary of their lasting impact.
*   **Emotion Curve**: Nostalgia -> Inspiration -> Sadness -> Upliftment.

### D. Meme
*   **Narrative Arc**: Setup-to-Punchline.
*   **Opening/Hook**: Relatable joke or visual trend reference.
*   **Pacing**: Very Fast. Snappy and high-density.
*   **Reveal Order**: The absurd context -> The visual trigger -> The community response -> Remix variants.
*   **Ending**: Rapid punchline or self-referential joke.
*   **Emotion Curve**: Confusion -> Amusement -> Shared joy.

### E. Wholesome
*   **Narrative Arc**: Problem-to-Resolution.
*   **Opening/Hook**: Heartwarming contrast hook.
*   **Pacing**: Slow-Medium. Warm and emotional.
*   **Reveal Order**: The challenge/sad starting state -> The act of kindness -> The positive reaction -> Broader impact.
*   **Ending**: Inspirational quote or positive wrap-up.
*   **Emotion Curve**: Sympathy -> Warmth -> Joy -> Gratitude.

### F. Industry Update
*   **Narrative Arc**: Pyramidal (Most critical details first).
*   **Opening/Hook**: Direct value-proposition hook ("How this change impacts you").
*   **Pacing**: Medium-Fast. Direct and informational.
*   **Reveal Order**: The change -> Direct consequences -> Winners/Losers -> Actionable advice.
*   **Ending**: Analytical recommendation or warning.
*   **Emotion Curve**: Anxiety -> Clarity -> Empowerment.

---

## 5. Retention Design Framework

Retention is designed through the structured creation and resolution of curiosity loops.

```
       [HOOK] ──────────────────────────────────────────┐
          │ (Opens Core Loop: Major Mystery)            │
          ▼                                             │
   [SECTION 1: Build-up]                                │
          │ (Opens Micro Loop: Sub-question)            │
          ▼                                             │
   [SECTION 2: Mid-Point] ◄─────────────────────────────┼─ (Holds Viewers)
          │ (Closes Micro Loop / Resolves Sub-question) │
          ▼                                             │
   [SECTION 3: Climax] ◄────────────────────────────────┘
          │ (Closes Core Loop: Final Payoff)
          ▼
       [OUTRO] (Call to Action / Loop End)
```

### Loop Mechanics:
1.  **Open Loops**: A narrative device where a question is posed or a mystery is introduced, but the answer is delayed.
    *   *Usage*: Must be established in the first 3 seconds (e.g., "They thought this movie was lost forever, until a janitor found a secret vault").
    *   *Constraint*: The resolution (payoff) must not occur until the final 15% of the script to prevent early drop-offs.
2.  **Curiosity Loops**: Interlinking small questions throughout the middle of the script.
    *   *Usage*: As soon as one question is answered, another must be immediately opened (e.g., "...and that's when they opened the box. But what was inside was even stranger").
    *   *Constraint*: Limit to maximum 3 nested loops to avoid confusing the viewer.
3.  **Closed Loops**: Resolving smaller sub-questions quickly to provide micro-satisfactions and build trust.
    *   *Usage*: Keep pacing alive in information-heavy sections.

### Payoff and Pacing Rules:
*   **Payoff Timing**: Climax must land between 80% and 90% of the video duration. Outros must be under 5 seconds to prevent drop-offs during the call to action.
*   **Information Pacing**: Deliver information in bursts. High-density facts followed by a brief 1-second digestion sentence.
*   **Surprise Moments**: Introduce an unexpected twist or transition at the 50% mark to re-engage viewers whose attention may be drifting.

---

## 6. Output Schema JSON Contract

The output of the Script Strategy Engine must conform exactly to the following JSON Schema:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ScriptStrategy",
  "type": "object",
  "properties": {
    "opening_style": {
      "type": "string",
      "enum": ["question", "shock_assertion", "contradiction", "story_in_medias_res"],
      "description": "The stylistic approach for the hook."
    },
    "hook_strength": {
      "type": "string",
      "enum": ["high", "medium", "low"],
      "description": "Target intensity of the hook."
    },
    "story_arc": {
      "type": "string",
      "enum": ["three_act", "problem_solution", "chronological", "climax_first"],
      "description": "Narrative structure to follow."
    },
    "reveal_order": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Order of facts/entities to be revealed."
    },
    "emotion_curve": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["curiosity", "tension", "surprise", "satisfaction", "anger", "empathy"]
      },
      "description": "Target emotional flow of the narrative segments."
    },
    "viewer_question": {
      "type": "string",
      "description": "The main question driving the open loop."
    },
    "curiosity_gap": {
      "type": "string",
      "description": "The specific information withheld until the climax."
    },
    "retention_pattern": {
      "type": "string",
      "enum": ["nested_loops", "rapid_fire", "tension_build"],
      "description": "Retention style based on story type."
    },
    "ending_style": {
      "type": "string",
      "enum": ["cliffhanger_engagement", "actionable_summary", "loop_outro"],
      "description": "Style of the final outro."
    },
    "pacing": {
      "type": "string",
      "enum": ["fast", "medium", "slow"],
      "description": "Speed profile of word delivery."
    },
    "information_density": {
      "type": "string",
      "enum": ["high", "medium", "low"],
      "description": "Fact count per unit of time."
    },
    "pause_points": {
      "type": "array",
      "items": { "type": "integer" },
      "description": "Indices in the reveal order where dramatic pauses should be placed."
    },
    "scene_priority": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Narrative elements to emphasize visually."
    },
    "transition_style": {
      "type": "string",
      "enum": ["verbal_bridge", "abrupt_pivot", "question_prompt"],
      "description": "Preferred narrative transition style."
    }
  },
  "required": [
    "opening_style",
    "hook_strength",
    "story_arc",
    "reveal_order",
    "emotion_curve",
    "viewer_question",
    "curiosity_gap",
    "retention_pattern",
    "ending_style",
    "pacing",
    "information_density",
    "scene_priority",
    "transition_style"
  ]
}
```

---

## 7. Failure Handling & Edge Case Strategy

To guarantee the engine never crashes, the following fallback matrix is established:

| Edge Case | Strategy Response / Fallback |
|---|---|
| **Missing Editorial Fields** | If fields like `primary_conflict` or `why_people_care` are empty, strategy defaults to a generic informational profile: `story_arc` is set to `chronological`, and `primary_conflict` falls back to `"general curiosity"`. |
| **Low Confidence (`confidence` < 0.5)** | Pacing is downgraded to `slow` or `medium` to allow more context, and `information_density` is set to `low`. The hook strength is reduced to prevent overhyping weak trends. |
| **Generic Trends** | When a topic lacks specific entities, `retention_pattern` switches to `rapid_fire` to maintain interest using short trivia beats rather than a deep narrative arc. |
| **Conflicting Metadata** | If `risk_level` is `high` but `story_type` is `controversy`, the engine enforces safety: `hook_strength` is limited to `medium`, and `opening_style` must be `question` or `contradiction` rather than `shock_assertion`. |
| **Unknown Story Type** | Defaults to `story_type` = `entertainment`. Pacing is set to `medium`, arc to `three_act`, and transitions to `verbal_bridge`. |

---

## 8. Validation & Coercion Rules

To maintain high data quality, the engine implements these strict post-processing validation steps:

1.  **Reveal Order Alignment**: The list of strings in `reveal_order` must contain at least one entity listed in the input's `main_entities`. If not, the engine automatically prepends the primary entity to the `reveal_order`.
2.  **Pacing and Density Coercion**: If `confidence` is `< 0.3`, `pacing` must be set to `slow` and `information_density` to `low`, overriding any LLM decisions to protect clarity.
3.  **Safety Constraints**: If `risk_level` == `high`, then `hook_strength` must be coerced to `medium` or `low`, and `opening_style` cannot be `shock_assertion`.

---

## 9. Integration Matrix

The Script Strategy Engine acts as the bridge connecting Editorial intelligence to script generation:

```
[Editorial Engine Output JSON]
       │
       ▼ (Validates schema & confidence)
[Script Strategy Engine]
       │
       ├─► Evaluates Story Type Rules
       ├─► Generates Strategy JSON
       ▼
[Script Strategy JSON Output]
       │
       ▼ (Injected as System Instructions)
[Script Generation Engine] (Generates raw script copy)
```

1.  **Upstream Connection**: Reads directly from `outputs/editorial_trends.json`. If this file is empty or missing, the Strategy Engine raises a handled exception and halts the current segment pipeline run.
2.  **Downstream Connection**: Generates `outputs/strategy_trends.json`. The Script Generation Engine takes both the editorial JSON and this strategy JSON to construct the final video script.

---

## 10. Freeze Criteria

Before the Script Strategy Engine can be frozen for production, it must meet the following criteria:

1.  **Schema Compliance (100%)**: Generates strategy output matching the JSON schema precisely across 100 consecutive test cases.
2.  **Zero-Crash Guarantee**: Handled fallbacks must prevent pipeline failures when processing empty arrays, null values, or missing fields.
3.  **Safety Constraint Enforcement (100%)**: Under testing, every trend flagged as `high` risk must successfully trigger hook-strength coercion to prevent unsafe content generation.
