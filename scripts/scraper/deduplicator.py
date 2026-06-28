"""
Purpose:
Remove duplicate or near-duplicate trend records.

Input:
normalized trend dictionaries

Output:
deduplicated trend dictionaries
"""

from __future__ import annotations

import logging
import re
import string
from difflib import SequenceMatcher
from typing import Any

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover - optional dependency
    fuzz = None


SIMILARITY_THRESHOLD = 90
NORMALIZE_CASE = True
REMOVE_PUNCTUATION = True

logger = logging.getLogger(__name__)


def normalize_title(title: str) -> str:
    """
    Purpose:
    Normalize a trend title for duplicate comparison.

    Arguments:
    title: trend topic text

    Returns:
    normalized title string
    """
    normalized = str(title or "")

    if NORMALIZE_CASE:
        normalized = normalized.lower()

    if REMOVE_PUNCTUATION:
        normalized = normalized.translate(str.maketrans("", "", string.punctuation))

    return re.sub(r"\s+", " ", normalized).strip()


def similarity_score(first_title: str, second_title: str) -> int:
    """
    Purpose:
    Calculate deterministic fuzzy similarity between two titles.

    Arguments:
    first_title: first normalized title
    second_title: second normalized title

    Returns:
    similarity score from 0 to 100
    """
    if first_title == second_title:
        return 100

    if not first_title or not second_title:
        return 0

    if fuzz is not None:
        return int(fuzz.ratio(first_title, second_title))

    return int(SequenceMatcher(None, first_title, second_title).ratio() * 100)


def _metadata_strength(trend: dict[str, Any]) -> int:
    """
    Purpose:
    Estimate how complete a trend record is.

    Arguments:
    trend: normalized trend dictionary

    Returns:
    metadata completeness score
    """
    metadata = trend.get("metadata")
    metadata_count = len(metadata) if isinstance(metadata, dict) else 0
    filled_fields = sum(1 for value in trend.values() if value not in ("", None, {}, []))

    return metadata_count + filled_fields


def choose_best(first_trend: dict[str, Any], second_trend: dict[str, Any]) -> dict[str, Any]:
    """
    Purpose:
    Choose the stronger record among duplicate trends.

    Arguments:
    first_trend: first duplicate trend dictionary
    second_trend: second duplicate trend dictionary

    Returns:
    preferred trend dictionary
    """
    first_upvotes = int(first_trend.get("upvotes") or 0)
    second_upvotes = int(second_trend.get("upvotes") or 0)

    if first_upvotes != second_upvotes:
        return first_trend if first_upvotes > second_upvotes else second_trend

    first_comments = int(first_trend.get("comments") or 0)
    second_comments = int(second_trend.get("comments") or 0)

    if first_comments != second_comments:
        return first_trend if first_comments > second_comments else second_trend

    first_strength = _metadata_strength(first_trend)
    second_strength = _metadata_strength(second_trend)

    if first_strength != second_strength:
        return first_trend if first_strength > second_strength else second_trend

    return first_trend


def _is_duplicate(first_trend: dict[str, Any], second_trend: dict[str, Any]) -> bool:
    """
    Purpose:
    Determine whether two trend records are duplicates.

    Arguments:
    first_trend: first trend dictionary
    second_trend: second trend dictionary

    Returns:
    True when records are duplicates, otherwise False
    """
    first_title = normalize_title(first_trend.get("topic", ""))
    second_title = normalize_title(second_trend.get("topic", ""))

    return similarity_score(first_title, second_title) >= SIMILARITY_THRESHOLD


def remove_duplicates(trends: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Purpose:
    Remove duplicate trend records while preserving the strongest record.

    Arguments:
    trends: normalized trend dictionaries

    Returns:
    deduplicated trend dictionaries
    """
    logger.info("Deduplication input count: %s", len(trends))

    unique_trends: list[dict[str, Any]] = []
    duplicates_removed = 0

    for trend in trends:
        duplicate_index = None

        for index, existing_trend in enumerate(unique_trends):
            if _is_duplicate(existing_trend, trend):
                duplicate_index = index
                break

        if duplicate_index is None:
            unique_trends.append(trend)
            continue

        unique_trends[duplicate_index] = choose_best(unique_trends[duplicate_index], trend)
        duplicates_removed += 1

    logger.info("Duplicates removed: %s", duplicates_removed)
    logger.info("Deduplication final count: %s", len(unique_trends))

    return unique_trends


if __name__ == "__main__":
    sample_trends = [
        {"topic": "New Movie Trailer Drops!", "upvotes": 10, "comments": 2},
        {"topic": "new movie trailer drops", "upvotes": 25, "comments": 1},
        {"topic": "Celebrity Interview Goes Viral", "metadata": {"region": "US"}},
        {"topic": "Celebrity interview goes viral.", "metadata": {"region": "IN", "type": "daily"}},
    ]

    cleaned_trends = remove_duplicates(sample_trends)
    print(f"Before count: {len(sample_trends)}")
    print(f"After count: {len(cleaned_trends)}")
    print(f"Removed count: {len(sample_trends) - len(cleaned_trends)}")
