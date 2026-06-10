"""core/logging.py - Loguru setup."""

import sys
from loguru import logger
from config import settings

LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"


def setup_logging() -> None:
    logger.remove()
    logger.add(sys.stdout, format=LOG_FORMAT, level=settings.LOG_LEVEL, enqueue=True)
    logger.add(sys.stderr, level="ERROR", format=LOG_FORMAT, enqueue=True)


__all__ = ["logger", "setup_logging"]
