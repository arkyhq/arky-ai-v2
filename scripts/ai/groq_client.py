"""
Purpose:
Send prompts to Groq and extract JSON responses.

Input:
prompt text

Output:
parsed JSON response dictionaries
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any

try:
    from groq import Groq
except ImportError:  # pragma: no cover - optional environment dependency
    Groq = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import (
    GROQ_API_KEY,
    GROQ_MAX_RETRIES,
    GROQ_MODEL,
    GROQ_REQUEST_TIMEOUT,
    GROQ_RETRY_DELAY_SECONDS,
    SCRIPT_PROVIDER,
)


logger = logging.getLogger(__name__)


def extract_json(response_text: str) -> dict[str, Any]:
    """
    Purpose:
    Extract a JSON object from model response text.

    Arguments:
    response_text: raw model response text

    Returns:
    parsed JSON dictionary
    """
    cleaned_text = response_text.strip()

    if cleaned_text.startswith("```"):
        cleaned_text = re.sub(r"^```(?:json)?", "", cleaned_text, flags=re.IGNORECASE).strip()
        cleaned_text = re.sub(r"```$", "", cleaned_text).strip()

    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned_text, flags=re.DOTALL)

        if not match:
            raise

        return json.loads(match.group(0))


def request_json(prompt: str) -> dict[str, Any]:
    """
    Purpose:
    Request a JSON response from Groq with retries.

    Arguments:
    prompt: final prompt text

    Returns:
    parsed JSON response dictionary
    """
    if SCRIPT_PROVIDER.lower() != "groq":
        raise RuntimeError(f"Unsupported script provider: {SCRIPT_PROVIDER}")

    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured")

    if Groq is None:
        raise RuntimeError("groq package is not installed")

    client = Groq(api_key=GROQ_API_KEY, timeout=GROQ_REQUEST_TIMEOUT)

    for attempt in range(1, GROQ_MAX_RETRIES + 1):
        try:
            logger.info("Groq request attempt %s/%s", attempt, GROQ_MAX_RETRIES)
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            return extract_json(content)
        except Exception as exc:
            logger.warning("Groq request failed on attempt %s/%s: %s", attempt, GROQ_MAX_RETRIES, exc)

            if attempt < GROQ_MAX_RETRIES:
                time.sleep(GROQ_RETRY_DELAY_SECONDS)

    raise RuntimeError("Groq request failed after retries")
