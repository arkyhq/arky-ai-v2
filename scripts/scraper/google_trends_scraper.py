"""
Purpose:
Collect Google Trends entertainment trend candidates.

Input:
None

Output:
normalized Google Trends dictionaries
"""

from __future__ import annotations

import logging
import re
import string
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pytrends.request import TrendReq


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import (
    GOOGLE_TRENDS_CACHE_FILE,
    GOOGLE_TRENDS_CACHE_TTL_SECONDS,
    GOOGLE_TRENDS_MAX_KEYWORDS_PER_REQUEST,
    GOOGLE_TRENDS_MAX_RESULTS_PER_REGION,
    GOOGLE_TRENDS_MAX_SEED_QUERIES_PER_REGION,
    GOOGLE_TRENDS_MIN_PRESELECT_SCORE,
    GOOGLE_TRENDS_REGIONS,
    GOOGLE_TRENDS_REQUEST_TIMEOUT,
    GOOGLE_TRENDS_RESULTS_PER_QUERY_TYPE,
    GOOGLE_TRENDS_RETRY_COUNT,
    GOOGLE_TRENDS_RETRY_DELAY,
    NORMALIZE_CASE,
    REMOVE_PUNCTUATION,
)
from scripts.utils.cache_manager import get_cached_data, get_stale_cached_data, save_cache


REGIONS = GOOGLE_TRENDS_REGIONS
REQUEST_TIMEOUT = GOOGLE_TRENDS_REQUEST_TIMEOUT
MAX_RESULTS_PER_REGION = GOOGLE_TRENDS_MAX_RESULTS_PER_REGION
RETRY_COUNT = GOOGLE_TRENDS_RETRY_COUNT
RETRY_DELAY = GOOGLE_TRENDS_RETRY_DELAY
GOOGLE_TRENDS_SOURCE = "google_trends"
MAX_KEYWORDS_PER_REQUEST = GOOGLE_TRENDS_MAX_KEYWORDS_PER_REQUEST
MAX_SEED_QUERIES_PER_REGION = GOOGLE_TRENDS_MAX_SEED_QUERIES_PER_REGION
RESULTS_PER_QUERY_TYPE = GOOGLE_TRENDS_RESULTS_PER_QUERY_TYPE
MIN_PRESELECT_SCORE = GOOGLE_TRENDS_MIN_PRESELECT_SCORE

ENTERTAINMENT_SEED_QUERIES = [
    "netflix",
    "streaming movies",
    "movie trailers",
    "celebrity gossip",
    "youtube creators",
    "movies",
    "tv shows",
    "streaming",
    "celebrity",
    "actors",
    "music",
    "singers",
    "youtube creators",
    "tiktok creators",
    "instagram creators",
    "gaming creators",
    "anime",
    "marvel",
    "disney",
    "pop culture",
    "award shows",
    "internet celebrity",
]

ENTERTAINMENT_PRESELECT_KEYWORDS = {
    "netflix": 4,
    "streaming": 4,
    "movie": 3,
    "film": 3,
    "trailer": 3,
    "tv": 3,
    "television": 3,
    "series": 3,
    "celebrity": 3,
    "celeb": 3,
    "actor": 3,
    "actress": 3,
    "music": 3,
    "artist": 3,
    "singer": 3,
    "album": 3,
    "song": 3,
    "youtube": 3,
    "youtuber": 3,
    "tiktok": 3,
    "instagram": 3,
    "influencer": 3,
    "creator": 3,
    "streamer": 3,
    "anime": 3,
    "marvel": 3,
    "disney": 3,
    "oscars": 3,
    "grammys": 3,
    "emmys": 3,
    "award": 2,
    "fandom": 2,
    "meme": 2,
    "movies": 1,
    "actors": 1,
    "directors": 1,
    "pop culture": 1,
}

OBVIOUSLY_IRRELEVANT_KEYWORDS = [
    "election",
    "government",
    "politics",
    "weather",
    "stock",
    "finance",
    "earthquake",
    "flood",
    "crime",
    "disease",
    "sports",
]

logger = logging.getLogger(__name__)


def _load_regions(regions: list[str] | None = None) -> list[str]:
    """
    Purpose:
    Resolve Google Trends regions to collect.

    Arguments:
    regions: optional region codes

    Returns:
    region code list
    """
    return regions or REGIONS


def _create_client() -> TrendReq:
    """
    Purpose:
    Create a pytrends client.

    Arguments:
    None

    Returns:
    configured pytrends client
    """
    return TrendReq(timeout=(REQUEST_TIMEOUT, REQUEST_TIMEOUT))


def _retry_request(request_func: Callable[[], Any], description: str) -> Any | None:
    """
    Purpose:
    Retry a pytrends request that may fail temporarily.

    Arguments:
    request_func: callable pytrends request
    description: request description for logging

    Returns:
    request result or None
    """
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            return request_func()
        except Exception as exc:
            logger.warning(
                "%s failed on attempt %s/%s: %s",
                description,
                attempt,
                RETRY_COUNT,
                exc,
            )
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY)

    return None


def _chunk_keywords(keywords: list[str]) -> list[list[str]]:
    """
    Purpose:
    Split seed queries into pytrends-compatible request groups.

    Arguments:
    keywords: seed query strings

    Returns:
    grouped seed query strings
    """
    return [
        keywords[index : index + MAX_KEYWORDS_PER_REQUEST]
        for index in range(0, len(keywords), MAX_KEYWORDS_PER_REQUEST)
    ]


def _load_seed_queries() -> list[str]:
    """
    Purpose:
    Resolve active entertainment seed queries for collection.

    Arguments:
    None

    Returns:
    active entertainment seed query strings
    """
    return ENTERTAINMENT_SEED_QUERIES[:MAX_SEED_QUERIES_PER_REGION]


def _normalize_text(text: str) -> str:
    """
    Purpose:
    Normalize text for deterministic pre-selection.

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
    normalized_keyword = _normalize_text(keyword)
    return bool(re.search(rf"\b{re.escape(normalized_keyword)}\b", text))


def _normalize_trend(
    topic: Any,
    region: str,
    search_volume: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Purpose:
    Normalize a Google Trends item into the project schema.

    Arguments:
    topic: trend topic value
    region: region code
    search_volume: optional search volume value
    metadata: optional source metadata

    Returns:
    normalized Google Trends dictionary
    """
    return {
        "topic": str(topic or ""),
        "body": "",
        "source": GOOGLE_TRENDS_SOURCE,
        "region": region,
        "search_volume": search_volume,
        "url": "",
        "timestamp": time.time(),
        "metadata": metadata or {},
    }


def _is_entertainment_candidate(trend: dict[str, Any]) -> bool:
    """
    Purpose:
    Pre-select likely entertainment candidates before returning data.

    Arguments:
    trend: normalized Google Trends dictionary

    Returns:
    True when trend is likely entertainment-related, otherwise False
    """
    topic = _normalize_text(trend.get("topic", ""))

    if any(_contains_keyword(topic, keyword) for keyword in OBVIOUSLY_IRRELEVANT_KEYWORDS):
        return False

    return _preselection_score(trend) >= MIN_PRESELECT_SCORE


def _preselection_score(trend: dict[str, Any]) -> int:
    """
    Purpose:
    Score how likely a collected query is entertainment-oriented.

    Arguments:
    trend: normalized Google Trends dictionary

    Returns:
    deterministic pre-selection score
    """
    topic = _normalize_text(trend.get("topic", ""))
    score = 0

    for keyword, weight in ENTERTAINMENT_PRESELECT_KEYWORDS.items():
        if _contains_keyword(topic, keyword):
            score += weight

    return score


def _preselect_trends(trends: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Purpose:
    Keep likely entertainment candidates from collected Google Trends.

    Arguments:
    trends: normalized Google Trends dictionaries

    Returns:
    pre-selected Google Trends dictionaries
    """
    selected_trends = [trend for trend in trends if _is_entertainment_candidate(trend)]

    return sorted(
        selected_trends,
        key=lambda trend: (
            _preselection_score(trend),
            int(trend.get("search_volume") or 0),
        ),
        reverse=True,
    )


def _extract_related_queries(region: str, related_data: Any) -> list[dict[str, Any]]:
    """
    Purpose:
    Convert related entertainment queries into normalized dictionaries.

    Arguments:
    region: region code
    related_data: pytrends related query result

    Returns:
    normalized Google Trends dictionaries
    """
    trends: list[dict[str, Any]] = []

    if not related_data:
        return trends

    for seed_query, query_groups in related_data.items():
        if not query_groups:
            continue

        for trend_type in ("rising", "top"):
            queries = query_groups.get(trend_type)

            if queries is None or getattr(queries, "empty", False):
                continue

            for _, row in queries.head(RESULTS_PER_QUERY_TYPE).iterrows():
                topic = row.get("query", "")
                raw_value = row.get("value")
                search_volume = int(raw_value) if raw_value is not None else None
                trends.append(
                    _normalize_trend(
                        topic,
                        region,
                        search_volume=search_volume,
                        metadata={
                            "trend_type": f"related_{trend_type}",
                            "seed_query": seed_query,
                        },
                    )
                )

    return trends


def _unique_trends(trends: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Purpose:
    Remove repeated Google Trends rows collected from overlapping seeds.

    Arguments:
    trends: normalized Google Trends dictionaries

    Returns:
    unique Google Trends dictionaries
    """
    unique_trends: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()

    for trend in trends:
        key = (_normalize_text(trend.get("topic", "")), str(trend.get("region", "")))

        if key in seen_keys:
            continue

        seen_keys.add(key)
        unique_trends.append(trend)

    return unique_trends


def _collect_region(region: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """
    Purpose:
    Collect Google Trends data for one region.

    Arguments:
    region: region code

    Returns:
    normalized Google Trends dictionaries and collection counts
    """
    logger.info("Collecting Google Trends region: %s", region)
    client = _create_client()
    raw_trends: list[dict[str, Any]] = []

    for seed_group in _chunk_keywords(_load_seed_queries()):
        related_data = _retry_request(
            lambda group=seed_group: _collect_related_queries(client, region, group),
            f"Entertainment related query request for {region}",
        )
        raw_trends.extend(_extract_related_queries(region, related_data))

    raw_trends = _unique_trends(raw_trends)
    preselected_trends = _preselect_trends(raw_trends)
    returned_trends = preselected_trends[:MAX_RESULTS_PER_REGION]

    logger.info("Raw Google Trends collected for %s: %s", region, len(raw_trends))
    logger.info("Pre-selected entertainment candidates for %s: %s", region, len(preselected_trends))
    logger.info("Returned Google Trends items for %s: %s", region, len(returned_trends))
    return returned_trends, {
        "raw": len(raw_trends),
        "preselected": len(preselected_trends),
        "returned": len(returned_trends),
    }


def _collect_related_queries(
    client: TrendReq,
    region: str,
    seed_queries: list[str],
) -> dict[str, Any] | None:
    """
    Purpose:
    Collect related entertainment queries for one region.

    Arguments:
    client: pytrends client
    region: region code
    seed_queries: entertainment seed queries

    Returns:
    pytrends related query result or None
    """
    client.build_payload(seed_queries, geo=region)
    return client.related_queries()


def collect_trends(regions: list[str] | None = None) -> list[dict[str, Any]]:
    """
    Purpose:
    Collect normalized Google Trends items.

    Arguments:
    regions: optional region codes

    Returns:
    normalized Google Trends dictionaries
    """
    selected_regions = _load_regions(regions)
    all_trends: list[dict[str, Any]] = []
    raw_count = 0
    preselected_count = 0
    cache_enabled = regions is None

    logger.info("Google Trends collection started")

    if cache_enabled:
        cached_trends = get_cached_data(
            GOOGLE_TRENDS_CACHE_FILE,
            GOOGLE_TRENDS_CACHE_TTL_SECONDS,
            default=None,
        )

        if isinstance(cached_trends, list):
            logger.info("Google Trends cache hit with %s trends", len(cached_trends))
            return cached_trends

    for region in selected_regions:
        try:
            region_trends, region_counts = _collect_region(region)
            all_trends.extend(region_trends)
            raw_count += region_counts["raw"]
            preselected_count += region_counts["preselected"]
        except Exception as exc:
            logger.warning("Google Trends collection failed for %s: %s", region, exc)

    logger.info("Raw Google Trends collected: %s", raw_count)
    logger.info("Pre-selected entertainment candidates: %s", preselected_count)
    logger.info("Google Trends collection finished with %s trends", len(all_trends))

    if cache_enabled and all_trends:
        save_cache(GOOGLE_TRENDS_CACHE_FILE, all_trends)
    elif cache_enabled:
        stale_trends = get_stale_cached_data(GOOGLE_TRENDS_CACHE_FILE, default=None)

        if isinstance(stale_trends, list):
            logger.warning("Google Trends refresh failed; using stale cache with %s trends", len(stale_trends))
            return stale_trends

    return all_trends


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    collected_trends = collect_trends()
    print(f"Trends collected: {len(collected_trends)}")
    print(collected_trends[:3])
