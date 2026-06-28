"""
Purpose:
Load editorial prompts and inject trend values.

Input:
prompt template and trend fields

Output:
final prompt text
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import EDITORIAL_ANALYSIS_PROMPT_PATH


def load_prompt(prompt_path: Path = EDITORIAL_ANALYSIS_PROMPT_PATH) -> str:
    """
    Purpose:
    Load a prompt template from disk.

    Arguments:
    prompt_path: prompt template file path

    Returns:
    prompt template text
    """
    return prompt_path.read_text(encoding="utf-8").strip()


def build_editorial_prompt(trend: dict[str, Any]) -> str:
    """
    Purpose:
    Build the final editorial analysis prompt for one trend.

    Arguments:
    trend: normalized ranked trend dictionary

    Returns:
    final prompt text
    """
    prompt = load_prompt()
    trend_payload = {
        "topic": trend.get("topic", ""),
        "source": trend.get("source", ""),
        "category": trend.get("category", ""),
        "trend_score": trend.get("trend_score"),
    }

    return f"{prompt}\n\nTrend:\n{json.dumps(trend_payload, ensure_ascii=False)}"
