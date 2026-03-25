"""Resilience utilities for CLI commands."""

import logging
import os
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
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

# Conditional import for Windows compatibility
try:
    import fcntl

    HAS_FLOCK = True
except ImportError:
    fcntl = None  # type: ignore[assignment]
    HAS_FLOCK = False

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


# Global rate limiting constants
RATE_LIMIT_FILE = ".rate_limit"  # Filename in token directory
MIN_INTERVAL = 1.0  # Minimum seconds between API calls
MAX_WAIT = 2.0  # Maximum wait time (clock skew protection)
LOCK_TIMEOUT = 30.0  # Max time to wait for lock acquisition


def _try_acquire_lock(f: Any) -> bool:
    """Try to acquire lock without blocking.

    Returns True if lock acquired, False if would block.
    """
    if not HAS_FLOCK or fcntl is None:
        return True
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False


def _acquire_lock_with_timeout(f: Any, timeout: float) -> bool:
    """Attempt to acquire exclusive lock with timeout.

    Args:
        f: File object to lock
        timeout: Maximum time to wait for lock

    Returns:
        True if lock acquired, False if timed out.

    """
    if not HAS_FLOCK or fcntl is None:
        return True  # No locking available, proceed

    start = time.monotonic()

    while not _try_acquire_lock(f):
        if time.monotonic() - start > timeout:
            return False
        # Small sleep to avoid busy-waiting
        time.sleep(0.1)

    return True


@contextmanager
def global_rate_limit(token_dir: Path) -> Generator[None, None, None]:
    """Cross-process rate limiter using file locking.

    Ensures minimum interval between API calls across all CLI processes.
    Falls back to no-op on platforms without fcntl (Windows) or when
    GARMIN_DISABLE_RATE_LIMIT environment variable is set.

    Args:
        token_dir: Directory containing tokens (lock file stored here)

    """
    # Check for disable flag
    if os.environ.get("GARMIN_DISABLE_RATE_LIMIT"):
        yield
        return

    # Fall back to no-op on Windows or if fcntl unavailable
    if not HAS_FLOCK or fcntl is None:
        yield
        return

    lock_path = token_dir / RATE_LIMIT_FILE

    # Use 'a+' mode to create file if missing (avoids TOCTOU race)
    with lock_path.open("a+") as f:
        # Acquire exclusive lock with timeout
        acquired = _acquire_lock_with_timeout(f, LOCK_TIMEOUT)

        if not acquired:
            logger.warning(
                "Rate limit lock acquisition timed out after %.1fs. "
                "Proceeding without rate limiting.",
                LOCK_TIMEOUT,
            )
            yield
            return

        try:
            # Read last request time (handle errors gracefully)
            f.seek(0)
            content = f.read().strip()
            try:
                last_time = float(content) if content else 0.0
            except ValueError:
                # Corrupt file content - treat as no previous request
                last_time = 0.0

            # Calculate and apply wait (with clock skew protection)
            now = time.time()
            wait_time = MIN_INTERVAL - (now - last_time)
            wait_time = max(0, min(wait_time, MAX_WAIT))  # Clamp to [0, MAX_WAIT]

            if wait_time > 0:
                time.sleep(wait_time)

            # Update timestamp with durable write
            f.seek(0)
            f.truncate()
            f.write(str(time.time()))
            f.flush()
            os.fsync(f.fileno())  # Ensure durability

            yield

        finally:
            # Release lock
            fcntl.flock(f, fcntl.LOCK_UN)
