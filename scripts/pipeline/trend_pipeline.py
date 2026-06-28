"""
Purpose:
Coordinate the deterministic Trend Intelligence Engine.

Input:
None

Output:
ranked trend dictionaries and outputs/trends.json
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import OUTPUT_TRENDS_PATH


OUTPUT_PATH = OUTPUT_TRENDS_PATH
logger = logging.getLogger(__name__)


def collect_all_trends() -> tuple[list[dict[str, Any]], dict[str, int]]:
    """
    Purpose:
    Collect normalized trends from available sources.

    Arguments:
    None

    Returns:
    merged trend dictionaries and collection counts
    """
    reddit_trends: list[dict[str, Any]] = []
    google_trends: list[dict[str, Any]] = []

    try:
        from scripts.scraper.reddit_scraper import scrape_reddit_posts

        reddit_trends = scrape_reddit_posts()
    except Exception as exc:
        logger.warning("Reddit collection failed: %s", exc)

    logger.info("Reddit collected: %s", len(reddit_trends))

    try:
        from scripts.scraper.google_trends_scraper import collect_trends

        google_trends = collect_trends()
    except Exception as exc:
        logger.warning("Google Trends collection failed: %s", exc)

    logger.info("Google collected: %s", len(google_trends))

    merged_trends = reddit_trends + google_trends
    logger.info("Merged count: %s", len(merged_trends))

    return merged_trends, {
        "reddit_collected": len(reddit_trends),
        "google_collected": len(google_trends),
        "merged": len(merged_trends),
    }


def process_trends(trends: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """
    Purpose:
    Run deterministic processing modules in pipeline order.

    Arguments:
    trends: merged normalized trend dictionaries

    Returns:
    ranked trend dictionaries and processing counts
    """
    if not trends:
        logger.error("No trends collected from any source")
        return [], {
            "deduplicated": 0,
            "duplicates_removed": 0,
            "accepted": 0,
            "ranked": 0,
        }

    from scripts.scraper.deduplicator import remove_duplicates
    from scripts.scraper.entertainment_filter import filter_trends
    from scripts.scraper.trend_ranker import rank_trends

    deduplicated_trends = remove_duplicates(trends)
    duplicates_removed = len(trends) - len(deduplicated_trends)
    logger.info("Duplicate removal completed: %s removed", duplicates_removed)

    filtered_trends = filter_trends(deduplicated_trends)
    logger.info("Filtered count: %s", len(filtered_trends))

    ranked_trends = rank_trends(filtered_trends)
    logger.info("Ranked count: %s", len(ranked_trends))

    return ranked_trends, {
        "deduplicated": len(deduplicated_trends),
        "duplicates_removed": duplicates_removed,
        "accepted": len(filtered_trends),
        "ranked": len(ranked_trends),
    }


def save_results(trends: list[dict[str, Any]], output_path: Path = OUTPUT_PATH) -> Path:
    """
    Purpose:
    Save ranked trends to the current JSON output file.

    Arguments:
    trends: ranked trend dictionaries
    output_path: output JSON file path

    Returns:
    saved output path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(trends, output_file, indent=4, ensure_ascii=False)

    logger.info("Saved output: %s", output_path)
    return output_path


def run_pipeline() -> tuple[list[dict[str, Any]], dict[str, int | float], Path]:
    """
    Purpose:
    Run the full deterministic Trend Intelligence Engine.

    Arguments:
    None

    Returns:
    ranked trends, pipeline counts, and saved output path
    """
    logger.info("Starting pipeline")
    started_at = time.perf_counter()

    merged_trends, collection_counts = collect_all_trends()
    ranked_trends, processing_counts = process_trends(merged_trends)
    output_path = save_results(ranked_trends)

    summary = collection_counts | processing_counts
    summary["execution_time"] = round(time.perf_counter() - started_at, 3)
    logger.info("Completed")

    return ranked_trends, summary, output_path


def main() -> None:
    """
    Purpose:
    Run the pipeline and print a concise summary.

    Arguments:
    None

    Returns:
    None
    """
    ranked_trends, summary, output_path = run_pipeline()

    print("---------------------------------")
    print(f"Reddit trends: {summary['reddit_collected']}")
    print(f"Google trends: {summary['google_collected']}")
    print(f"Merged: {summary['merged']}")
    print(f"Duplicates removed: {summary['duplicates_removed']}")
    print(f"Entertainment trends: {summary['accepted']}")
    print(f"Final ranked trends: {summary['ranked']}")
    print(f"Execution time: {summary['execution_time']}s")
    print("Saved:")
    print(output_path.relative_to(PROJECT_ROOT))
    print("---------------------------------")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
