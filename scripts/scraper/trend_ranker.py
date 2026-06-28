"""
Purpose:
Assign deterministic priority scores to entertainment trends.

Input:
accepted entertainment trend dictionaries

Output:
ranked trend dictionaries with trend_score
"""

from __future__ import annotations

import logging
import math
import time
from typing import Any


UPVOTE_WEIGHT = 30
COMMENT_WEIGHT = 20
SEARCH_VOLUME_WEIGHT = 30
FRESHNESS_WEIGHT = 20
SOURCE_WEIGHT = 10
METADATA_WEIGHT = 10
MAX_SCORE = 100
MIN_SCORE = 1
FRESHNESS_WINDOW_HOURS = 72
SECONDS_PER_HOUR = 3600
REDDIT_SOURCE_WEIGHT = 10
GOOGLE_TRENDS_SOURCE_WEIGHT = 7
DEFAULT_SOURCE_WEIGHT = 5
REDDIT_ENGAGEMENT_SCALE = 1000
COMMENT_ENGAGEMENT_SCALE = 250
SEARCH_VOLUME_SCALE = 100

logger = logging.getLogger(__name__)


def _clamp_score(score: float) -> int:
    """
    Purpose:
    Clamp a score to the configured output range.

    Arguments:
    score: raw score value

    Returns:
    integer score between MIN_SCORE and MAX_SCORE
    """
    return max(MIN_SCORE, min(MAX_SCORE, round(score)))


def _normalize_number(value: Any, scale: int) -> float:
    """
    Purpose:
    Normalize a numeric signal to a 0 to 1 range.

    Arguments:
    value: raw numeric value
    scale: value scale for logarithmic normalization

    Returns:
    normalized numeric signal
    """
    numeric_value = max(float(value or 0), 0.0)

    if numeric_value <= 0:
        return 0.0

    return min(math.log1p(numeric_value) / math.log1p(scale), 1.0)


def calculate_reddit_score(trend: dict[str, Any]) -> float:
    """
    Purpose:
    Calculate Reddit engagement score.

    Arguments:
    trend: accepted entertainment trend dictionary

    Returns:
    Reddit score contribution
    """
    upvote_score = _normalize_number(trend.get("upvotes"), REDDIT_ENGAGEMENT_SCALE)
    comment_score = _normalize_number(trend.get("comments"), COMMENT_ENGAGEMENT_SCALE)

    return (upvote_score * UPVOTE_WEIGHT) + (comment_score * COMMENT_WEIGHT)


def calculate_google_score(trend: dict[str, Any]) -> float:
    """
    Purpose:
    Calculate Google Trends search-volume score.

    Arguments:
    trend: accepted entertainment trend dictionary

    Returns:
    Google Trends score contribution
    """
    volume_score = _normalize_number(trend.get("search_volume"), SEARCH_VOLUME_SCALE)
    return volume_score * SEARCH_VOLUME_WEIGHT


def calculate_freshness(trend: dict[str, Any]) -> float:
    """
    Purpose:
    Calculate recency score contribution.

    Arguments:
    trend: accepted entertainment trend dictionary

    Returns:
    freshness score contribution
    """
    created_at = trend.get("created_utc") or trend.get("timestamp")

    if not created_at:
        return 0.0

    age_hours = max((time.time() - float(created_at)) / SECONDS_PER_HOUR, 0.0)
    freshness_ratio = max(1 - (age_hours / FRESHNESS_WINDOW_HOURS), 0.0)

    return freshness_ratio * FRESHNESS_WEIGHT


def calculate_source_score(trend: dict[str, Any]) -> float:
    """
    Purpose:
    Calculate source priority score contribution.

    Arguments:
    trend: accepted entertainment trend dictionary

    Returns:
    source score contribution
    """
    source = trend.get("source")

    if source == "reddit":
        return REDDIT_SOURCE_WEIGHT

    if source == "google_trends":
        return GOOGLE_TRENDS_SOURCE_WEIGHT

    return DEFAULT_SOURCE_WEIGHT


def calculate_metadata_bonus(trend: dict[str, Any]) -> float:
    """
    Purpose:
    Calculate metadata completeness bonus.

    Arguments:
    trend: accepted entertainment trend dictionary

    Returns:
    metadata bonus contribution
    """
    metadata_fields = ["body", "author", "url", "subreddit", "region"]
    filled_fields = sum(1 for field in metadata_fields if trend.get(field))
    metadata = trend.get("metadata")
    metadata_count = len(metadata) if isinstance(metadata, dict) else 0
    completeness_ratio = min((filled_fields + metadata_count) / len(metadata_fields), 1.0)

    return completeness_ratio * METADATA_WEIGHT


def calculate_final_score(trend: dict[str, Any]) -> int:
    """
    Purpose:
    Calculate final deterministic trend priority score.

    Arguments:
    trend: accepted entertainment trend dictionary

    Returns:
    final trend score from 1 to 100
    """
    source = trend.get("source")
    score = calculate_freshness(trend)
    score += calculate_source_score(trend)
    score += calculate_metadata_bonus(trend)

    if source == "reddit":
        score += calculate_reddit_score(trend)
    elif source == "google_trends":
        score += calculate_google_score(trend)
    else:
        score += calculate_reddit_score(trend)
        score += calculate_google_score(trend)

    return _clamp_score(score)


def rank_trends(trends: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Purpose:
    Add trend scores and sort trends by priority.

    Arguments:
    trends: accepted entertainment trend dictionaries

    Returns:
    ranked trend dictionaries with trend_score
    """
    logger.info("Trend ranking input count: %s", len(trends))

    ranked_trends = []

    for trend in trends:
        scored_trend = trend.copy()
        scored_trend["trend_score"] = calculate_final_score(trend)
        ranked_trends.append(scored_trend)

    ranked_trends.sort(key=lambda item: item["trend_score"], reverse=True)

    if ranked_trends:
        logger.info("Highest trend score: %s", ranked_trends[0]["trend_score"])
        logger.info("Lowest trend score: %s", ranked_trends[-1]["trend_score"])

    logger.info("Trend ranking completed")
    return ranked_trends


if __name__ == "__main__":
    now = time.time()
    sample_trends = [
        {
            "topic": "Movie trailer trends online",
            "source": "reddit",
            "upvotes": 850,
            "comments": 120,
            "created_utc": now - 1800,
            "url": "https://example.com/movie",
            "author": "moviefan",
        },
        {
            "topic": "Celebrity interview rises in searches",
            "source": "google_trends",
            "search_volume": 75,
            "timestamp": now - 7200,
            "region": "US",
        },
        {
            "topic": "Streaming show discussion returns",
            "source": "reddit",
            "upvotes": 120,
            "comments": 18,
            "created_utc": now - 172800,
        },
    ]

    ranked = rank_trends(sample_trends)
    print([(trend["topic"], trend["trend_score"]) for trend in ranked])
    print([trend["topic"] for trend in ranked])
