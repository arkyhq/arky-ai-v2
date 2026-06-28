"""
Purpose:
Filter trend records for entertainment relevance.

Input:
normalized trend dictionaries

Output:
accepted entertainment trend dictionaries
"""

from __future__ import annotations

import logging
import re
import string
from typing import Any


MIN_SCORE = 2
NORMALIZE_CASE = True
REMOVE_PUNCTUATION = True

ENTERTAINMENT_KEYWORDS = {
    "celebrity": 3,
    "celeb": 3,
    "gossip": 3,
    "actor": 3,
    "actress": 3,
    "artist": 2,
    "singer": 3,
    "rapper": 3,
    "music": 2,
    "album": 2,
    "song": 2,
    "movie": 3,
    "film": 3,
    "box office": 3,
    "trailer": 2,
    "tv": 2,
    "television": 2,
    "series": 2,
    "netflix": 3,
    "streaming": 2,
    "anime": 3,
    "marvel": 3,
    "dc": 2,
    "disney": 2,
    "award": 2,
    "oscars": 3,
    "grammys": 3,
    "emmys": 3,
    "youtube": 3,
    "youtuber": 3,
    "influencer": 3,
    "tiktok": 3,
    "instagram": 2,
    "creator": 2,
    "creator drama": 4,
    "fandom": 3,
    "meme": 2,
    "gaming creator": 3,
    "streamer": 3,
}

NEGATIVE_KEYWORDS = {
    "politics": -4,
    "election": -4,
    "government": -4,
    "minister": -3,
    "crime": -4,
    "murder": -4,
    "finance": -4,
    "stock": -4,
    "market": -2,
    "weather": -4,
    "storm": -3,
    "earthquake": -4,
    "flood": -4,
    "medical": -4,
    "disease": -4,
    "sports": -4,
    "football": -3,
    "cricket": -3,
    "education": -3,
    "school": -2,
    "shopping": -3,
    "programming": -3,
    "software": -2,
    "technology": -2,
}

OPTIONAL_CATEGORY_HINTS = {
    "subreddit": {
        "Fauxmoi": 2,
        "popculturechat": 2,
        "BollyBlindsNGossip": 2,
        "InstaCelebsGossip": 2,
        "youtubedrama": 2,
        "television": 2,
        "movies": 2,
        "MarvelStudios": 2,
        "TikTokCringe": 2,
    },
    "source": {
        "google_trends": 0,
        "reddit": 0,
    },
}

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """
    Purpose:
    Normalize text for deterministic keyword matching.

    Arguments:
    text: raw text value

    Returns:
    normalized text string
    """
    normalized = str(text or "")

    if NORMALIZE_CASE:
        normalized = normalized.lower()

    if REMOVE_PUNCTUATION:
        normalized = normalized.translate(str.maketrans("", "", string.punctuation))

    return re.sub(r"\s+", " ", normalized).strip()


def _contains_keyword(text: str, keyword: str) -> bool:
    """
    Purpose:
    Check whether normalized text contains a keyword.

    Arguments:
    text: normalized text
    keyword: keyword to match

    Returns:
    True when keyword is present, otherwise False
    """
    normalized_keyword = normalize_text(keyword)
    return bool(re.search(rf"\b{re.escape(normalized_keyword)}\b", text))


def _category_hint_score(trend: dict[str, Any]) -> int:
    """
    Purpose:
    Calculate score from trusted source category hints.

    Arguments:
    trend: normalized trend dictionary

    Returns:
    category hint score
    """
    score = 0

    for field, values in OPTIONAL_CATEGORY_HINTS.items():
        field_value = trend.get(field)
        if field_value in values:
            score += values[field_value]

    return score


def calculate_score(trend: dict[str, Any]) -> int:
    """
    Purpose:
    Calculate deterministic entertainment relevance score.

    Arguments:
    trend: normalized trend dictionary

    Returns:
    entertainment relevance score
    """
    topic = normalize_text(trend.get("topic", ""))
    body = normalize_text(trend.get("body", ""))
    searchable_text = f"{topic} {body}".strip()

    score = _category_hint_score(trend)

    for keyword, weight in ENTERTAINMENT_KEYWORDS.items():
        if _contains_keyword(searchable_text, keyword):
            score += weight

    for keyword, weight in NEGATIVE_KEYWORDS.items():
        if _contains_keyword(searchable_text, keyword):
            score += weight

    return score


def is_entertainment(trend: dict[str, Any]) -> bool:
    """
    Purpose:
    Decide whether a trend should enter the entertainment pipeline.

    Arguments:
    trend: normalized trend dictionary

    Returns:
    True when trend is entertainment-related, otherwise False
    """
    return calculate_score(trend) >= MIN_SCORE


def filter_trends(trends: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Purpose:
    Keep only entertainment-related trend records.

    Arguments:
    trends: normalized trend dictionaries

    Returns:
    accepted entertainment trend dictionaries
    """
    logger.info("Entertainment filter input count: %s", len(trends))

    accepted_trends = [trend for trend in trends if is_entertainment(trend)]
    rejected_count = len(trends) - len(accepted_trends)

    logger.info("Entertainment filter accepted: %s", len(accepted_trends))
    logger.info("Entertainment filter rejected: %s", rejected_count)
    logger.info("Entertainment filter completed")

    return accepted_trends


if __name__ == "__main__":
    sample_trends = [
        {"topic": "New movie trailer breaks streaming records", "body": ""},
        {"topic": "Election debate dominates politics news", "body": ""},
        {"topic": "Celebrity gossip explodes after Instagram post", "body": ""},
        {"topic": "Weather alert issued before heavy storm", "body": ""},
        {"topic": "Gaming creator drama trends on YouTube", "body": ""},
    ]

    accepted = filter_trends(sample_trends)
    print(f"Accepted count: {len(accepted)}")
    print(f"Rejected count: {len(sample_trends) - len(accepted)}")
    print(f"Accepted titles: {[trend.get('topic', '') for trend in accepted]}")
