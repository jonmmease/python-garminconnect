"""Resilience utilities for CLI commands."""

import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

import click
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from garminconnect import (
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Reusable retry decorator for API calls
api_retry = retry(
    stop=stop_after_attempt(4),  # 1 initial + 3 retries
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type(
        (
            GarminConnectTooManyRequestsError,
            GarminConnectConnectionError,
        )
    ),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)


def rate_limited_batch(
    items: list[T],
    func: Callable[[T], Any],
    delay_between: float = 0.5,
    verbose: bool = False,
) -> list[Any]:
    """Execute a function on a batch of items with rate limiting.

    Args:
        items: List of items to process
        func: Function to call on each item
        delay_between: Seconds to wait between calls
        verbose: If True, show progress messages

    Returns:
        List of results from func calls

    """
    results = []
    for i, item in enumerate(items):
        if i > 0 and delay_between > 0:
            time.sleep(delay_between)

        if verbose and len(items) > 10 and i % 10 == 0:
            click.echo(f"Processing {i + 1}/{len(items)}...", err=True)

        results.append(func(item))

    return results
