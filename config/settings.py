"""
Purpose:
Centralize runtime settings for the deterministic Trend Intelligence Engine.

Input:
configuration values

Output:
runtime settings
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional environment dependency
    load_dotenv = None


if load_dotenv is not None:
    load_dotenv()


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CACHE_DIR = PROJECT_ROOT / "data" / "cache"
GOOGLE_TRENDS_CACHE_FILE = CACHE_DIR / "google_trends.json"
GOOGLE_TRENDS_CACHE_TTL_SECONDS = 60 * 60 * 6

OUTPUT_TRENDS_PATH = PROJECT_ROOT / "outputs" / "trends.json"
OUTPUT_EDITORIAL_TRENDS_PATH = PROJECT_ROOT / "outputs" / "editorial_trends.json"
EDITORIAL_ANALYSIS_PROMPT_PATH = PROJECT_ROOT / "prompts" / "groq" / "editorial_analysis.txt"

SCRIPT_PROVIDER = os.getenv("SCRIPT_PROVIDER", "groq")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_REQUEST_TIMEOUT = 30
GROQ_MAX_RETRIES = 3
GROQ_RETRY_DELAY_SECONDS = 2

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
