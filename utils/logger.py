"""
Purpose:
Provide reusable optional logging infrastructure for repository tooling.

Input:
logger name and optional log level

Output:
configured Python logger
"""

from __future__ import annotations

import logging
import os


DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
DEFAULT_LOG_LEVEL = "INFO"


def get_logger(name: str, level: str | None = None) -> logging.Logger:
    """
    Purpose:
    Return a reusable configured logger.

    Arguments:
    name: logger name
    level: optional logging level name

    Returns:
    configured logger instance
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
        logger.addHandler(handler)

    configured_level = level or os.getenv("ARKY_LOG_LEVEL", DEFAULT_LOG_LEVEL)
    logger.setLevel(getattr(logging, configured_level.upper(), logging.INFO))
    logger.propagate = False
    return logger
