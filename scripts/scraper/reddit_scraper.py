"""
Purpose:
Collect Reddit entertainment trend candidates.

Input:
None

Output:
normalized Reddit post dictionaries
"""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

try:
    import praw
except ImportError:  # pragma: no cover - optional runtime dependency
    praw = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import (
    REDDIT_BACKOFF_MULTIPLIER,
    REDDIT_MAX_RETRIES,
    REDDIT_POSTS_PER_SUBREDDIT,
    REDDIT_REQUEST_TIMEOUT_SECONDS,
    REDDIT_RETRY_DELAY_SECONDS,
    REDDIT_SUBREDDITS,
    REDDIT_USER_AGENT,
)


ENTERTAINMENT_SUBREDDITS = REDDIT_SUBREDDITS
POSTS_PER_SUBREDDIT = REDDIT_POSTS_PER_SUBREDDIT
REQUEST_TIMEOUT_SECONDS = REDDIT_REQUEST_TIMEOUT_SECONDS
USER_AGENT = REDDIT_USER_AGENT
MAX_RETRIES = REDDIT_MAX_RETRIES
RETRY_DELAY_SECONDS = REDDIT_RETRY_DELAY_SECONDS
BACKOFF_MULTIPLIER = REDDIT_BACKOFF_MULTIPLIER
REDDIT_SOURCE = "reddit"

logger = logging.getLogger(__name__)


def _load_credentials() -> dict[str, str] | None:
    """
    Purpose:
    Load Reddit API credentials from environment variables.

    Arguments:
    None

    Returns:
    credential dictionary when complete, otherwise None
    """
    load_dotenv()

    credentials = {
        "client_id": os.getenv("REDDIT_CLIENT_ID", "").strip(),
        "client_secret": os.getenv("REDDIT_CLIENT_SECRET", "").strip(),
        "user_agent": os.getenv("REDDIT_USER_AGENT", "").strip(),
    }

    if all(credentials.values()):
        return credentials

    return None


def _normalize_post(post: Any, subreddit: str, source_type: str) -> dict[str, Any]:
    """
    Purpose:
    Normalize Reddit post data into the project schema.

    Arguments:
    post: Reddit post object or JSON dictionary
    subreddit: subreddit name
    source_type: source format identifier

    Returns:
    normalized Reddit post dictionary
    """
    if source_type == "praw":
        return {
            "topic": str(getattr(post, "title", "") or ""),
            "body": str(getattr(post, "selftext", "") or ""),
            "source": REDDIT_SOURCE,
            "subreddit": str(getattr(getattr(post, "subreddit", ""), "display_name", subreddit)),
            "author": str(getattr(post, "author", "") or ""),
            "upvotes": int(getattr(post, "score", 0) or 0),
            "comments": int(getattr(post, "num_comments", 0) or 0),
            "url": str(getattr(post, "url", "") or ""),
            "created_utc": float(getattr(post, "created_utc", 0.0) or 0.0),
            "nsfw": bool(getattr(post, "over_18", False)),
            "spoiler": bool(getattr(post, "spoiler", False)),
        }

    data = post.get("data", post)

    return {
        "topic": str(data.get("title", "") or ""),
        "body": str(data.get("selftext", "") or ""),
        "source": REDDIT_SOURCE,
        "subreddit": str(data.get("subreddit", subreddit) or subreddit),
        "author": str(data.get("author", "") or ""),
        "upvotes": int(data.get("ups", data.get("score", 0)) or 0),
        "comments": int(data.get("num_comments", 0) or 0),
        "url": str(data.get("url", "") or ""),
        "created_utc": float(data.get("created_utc", 0.0) or 0.0),
        "nsfw": bool(data.get("over_18", False)),
        "spoiler": bool(data.get("spoiler", False)),
    }


def _scrape_with_praw(credentials: dict[str, str], subreddits: list[str]) -> list[dict[str, Any]]:
    """
    Purpose:
    Scrape Reddit posts through the official API wrapper.

    Arguments:
    credentials: Reddit API credential dictionary
    subreddits: subreddit names to scrape

    Returns:
    normalized Reddit post dictionaries
    """
    if praw is None:
        raise RuntimeError("PRAW is not installed")

    reddit = praw.Reddit(
        client_id=credentials["client_id"],
        client_secret=credentials["client_secret"],
        user_agent=credentials["user_agent"],
    )

    posts: list[dict[str, Any]] = []

    for subreddit in subreddits:
        logger.info("Scraping subreddit with PRAW: r/%s", subreddit)
        try:
            subreddit_posts = _fetch_praw_subreddit(reddit, subreddit)
            posts.extend(subreddit_posts)
            logger.info("Collected %s posts from r/%s", len(subreddit_posts), subreddit)
        except Exception as exc:
            logger.warning("PRAW failed for r/%s: %s", subreddit, exc)

    if not posts:
        raise RuntimeError("PRAW collected no posts")

    return posts


def _fetch_praw_subreddit(reddit: Any, subreddit: str) -> list[dict[str, Any]]:
    """
    Purpose:
    Fetch posts for one subreddit through PRAW with retries.

    Arguments:
    reddit: PRAW Reddit client
    subreddit: subreddit name to scrape

    Returns:
    normalized Reddit post dictionaries
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return [
                _normalize_post(post, subreddit, "praw")
                for post in reddit.subreddit(subreddit).hot(limit=POSTS_PER_SUBREDDIT)
            ]
        except Exception as exc:
            logger.warning(
                "PRAW request failed for r/%s on attempt %s/%s: %s",
                subreddit,
                attempt,
                MAX_RETRIES,
                exc,
            )
            if attempt < MAX_RETRIES:
                time.sleep(_retry_delay(attempt))

    return []


def _fetch_subreddit(subreddit: str) -> list[dict[str, Any]]:
    """
    Purpose:
    Fetch public Reddit JSON posts for one subreddit.

    Arguments:
    subreddit: subreddit name to scrape

    Returns:
    public JSON post dictionaries
    """
    url = f"https://www.reddit.com/r/{subreddit}/hot.json"
    headers = {"User-Agent": USER_AGENT}
    params = {"limit": POSTS_PER_SUBREDDIT}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            if response.status_code == 403:
                logger.warning("Reddit public JSON blocked r/%s with HTTP 403", subreddit)
                return []

            response.raise_for_status()
            return response.json().get("data", {}).get("children", [])
        except requests.RequestException as exc:
            logger.warning(
                "JSON request failed for r/%s on attempt %s/%s: %s",
                subreddit,
                attempt,
                MAX_RETRIES,
                exc,
            )
            if attempt < MAX_RETRIES:
                time.sleep(_retry_delay(attempt))

    return []


def _retry_delay(attempt: int) -> int:
    """
    Purpose:
    Calculate exponential retry delay.

    Arguments:
    attempt: current retry attempt

    Returns:
    delay in seconds
    """
    return RETRY_DELAY_SECONDS * (BACKOFF_MULTIPLIER ** (attempt - 1))


def _scrape_public_json(subreddits: list[str]) -> list[dict[str, Any]]:
    """
    Purpose:
    Scrape Reddit posts through public JSON endpoints.

    Arguments:
    subreddits: subreddit names to scrape

    Returns:
    normalized Reddit post dictionaries
    """
    posts: list[dict[str, Any]] = []

    for subreddit in subreddits:
        logger.info("Scraping subreddit with public JSON: r/%s", subreddit)
        try:
            raw_posts = _fetch_subreddit(subreddit)
            subreddit_posts = [
                _normalize_post(post, subreddit, "json")
                for post in raw_posts
            ]
            posts.extend(subreddit_posts)
            logger.info("Collected %s posts from r/%s", len(subreddit_posts), subreddit)
        except Exception as exc:
            logger.warning("JSON scraping failed for r/%s: %s", subreddit, exc)

    return posts


def scrape_reddit_posts(subreddits: list[str] | None = None) -> list[dict[str, Any]]:
    """
    Purpose:
    Collect normalized entertainment posts from Reddit.

    Arguments:
    subreddits: optional subreddit names to scrape

    Returns:
    normalized Reddit post dictionaries
    """
    selected_subreddits = subreddits or ENTERTAINMENT_SUBREDDITS
    logger.info("Reddit scraping started")

    credentials = _load_credentials()

    if credentials:
        try:
            posts = _scrape_with_praw(credentials, selected_subreddits)
            logger.info("Reddit scraping completed with %s posts", len(posts))
            return posts
        except Exception as exc:
            logger.warning("Reddit API scraping failed; falling back to public JSON: %s", exc)

    posts = _scrape_public_json(selected_subreddits)
    logger.info("Reddit scraping completed with %s posts", len(posts))
    return posts


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    collected_posts = scrape_reddit_posts()
    print(f"Posts collected: {len(collected_posts)}")
    print(collected_posts[:3])
