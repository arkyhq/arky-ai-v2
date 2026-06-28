"""
Purpose:
Centralize runtime settings for the deterministic Trend Intelligence Engine.

Input:
configuration values

Output:
runtime settings
"""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CACHE_DIR = PROJECT_ROOT / "data" / "cache"
GOOGLE_TRENDS_CACHE_FILE = CACHE_DIR / "google_trends.json"
GOOGLE_TRENDS_CACHE_TTL_SECONDS = 60 * 60 * 6

OUTPUT_TRENDS_PATH = PROJECT_ROOT / "outputs" / "trends.json"

REDDIT_SUBREDDITS = [
    "Fauxmoi",
    "popculturechat",
    "BollyBlindsNGossip",
    "InstaCelebsGossip",
    "youtubedrama",
    "OutOfTheLoop",
    "television",
    "movies",
    "MarvelStudios",
    "TikTokCringe",
]
REDDIT_POSTS_PER_SUBREDDIT = 25
REDDIT_REQUEST_TIMEOUT_SECONDS = 10
REDDIT_USER_AGENT = "ARKY-AI-SYSTEM/1.0 entertainment trend collector"
REDDIT_MAX_RETRIES = 3
REDDIT_RETRY_DELAY_SECONDS = 2
REDDIT_BACKOFF_MULTIPLIER = 2

GOOGLE_TRENDS_REGIONS = [
    "IN",
    "US",
]
GOOGLE_TRENDS_REQUEST_TIMEOUT = 10
GOOGLE_TRENDS_MAX_RESULTS_PER_REGION = 25
GOOGLE_TRENDS_RETRY_COUNT = 3
GOOGLE_TRENDS_RETRY_DELAY = 2
GOOGLE_TRENDS_MAX_KEYWORDS_PER_REQUEST = 5
GOOGLE_TRENDS_MAX_SEED_QUERIES_PER_REGION = 5
GOOGLE_TRENDS_RESULTS_PER_QUERY_TYPE = 8
GOOGLE_TRENDS_MIN_PRESELECT_SCORE = 2

NORMALIZE_CASE = True
REMOVE_PUNCTUATION = True
