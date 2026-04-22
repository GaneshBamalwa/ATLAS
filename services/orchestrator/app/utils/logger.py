"""
utils/logger.py - Structured logging for the orchestrator.
"""

import logging
import sys
import time
from functools import wraps
from typing import Callable, Any


def setup_logger(name: str = "orchestrator") -> logging.Logger:
    """Create and return a structured logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)-8s %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


# Module-level default logger
logger = setup_logger("orchestrator")


def log_execution_time(func: Callable) -> Callable:
    """Decorator to log execution time of async functions."""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(f"[TIMING] {func.__name__} completed in {elapsed:.1f}ms")
            return result
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(f"[TIMING] {func.__name__} FAILED after {elapsed:.1f}ms — {exc}")
            raise
    return wrapper
