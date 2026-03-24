"""In-process rate limiter for Garmin API calls."""

import asyncio
import time


class AsyncRateLimiter:
    """Enforce minimum interval between API calls within one process.

    Uses asyncio.Lock to serialize access and a monotonic timestamp
    to ensure at least `min_interval` seconds between calls.
    """

    def __init__(self, min_interval: float = 1.0) -> None:
        self._min_interval = min_interval
        self._last_call: float = 0.0
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> "AsyncRateLimiter":
        """Acquire the rate limiter, sleeping if needed."""
        await self._lock.acquire()
        now = time.monotonic()
        wait = self._min_interval - (now - self._last_call)
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_call = time.monotonic()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Release the rate limiter."""
        self._lock.release()
