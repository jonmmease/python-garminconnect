"""FastMCP server for Garmin Connect."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

from fastmcp import FastMCP

from . import export as export_module
from .rate_limit import AsyncRateLimiter

if TYPE_CHECKING:
    from garminconnect import Garmin

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Module-level state
_garmin_client: Garmin | None = None
_rate_limiter: AsyncRateLimiter | None = None

# Global flags set by CLI args before server starts
gcs_enabled: bool = False
data_dir: str | None = None
token_dir: str | None = None


def get_garmin_client() -> Garmin:
    """Get the shared Garmin client instance.

    Raises:
        RuntimeError: If client is not initialized (server not started).

    """
    if _garmin_client is None:
        msg = "Garmin client not initialized. Is the server running?"
        raise RuntimeError(msg)
    return _garmin_client


def get_rate_limiter() -> AsyncRateLimiter:
    """Get the shared rate limiter instance."""
    if _rate_limiter is None:
        msg = "Rate limiter not initialized."
        raise RuntimeError(msg)
    return _rate_limiter


async def garmin_api_call(func: object, *args: object, **kwargs: object) -> Any:
    """Call a Garmin API method with rate limiting and retry.

    Wraps a synchronous Garmin API call with:
    1. Rate limiting (1s minimum interval)
    2. asyncio.to_thread() for non-blocking execution
    3. Retry on 429/connection errors (via tenacity)

    """
    rate_limiter = get_rate_limiter()

    async with rate_limiter:
        return await asyncio.to_thread(_call_with_retry, func, *args, **kwargs)


def _call_with_retry(func: object, *args: object, **kwargs: object) -> Any:
    """Call a function with tenacity retry on 429 and connection errors."""
    from tenacity import (
        retry,
        retry_if_exception_type,
        stop_after_attempt,
        wait_exponential,
    )

    from garminconnect import (
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    )

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type(
            (GarminConnectTooManyRequestsError, GarminConnectConnectionError)
        ),
        reraise=True,
    )
    def _inner() -> object:
        return func(*args, **kwargs)  # type: ignore[operator]

    return _inner()


@asynccontextmanager
async def lifespan(_app: FastMCP) -> AsyncIterator[None]:
    """Lifespan context manager — initialize Garmin client on startup."""
    global _garmin_client, _rate_limiter  # noqa: PLW0603

    from garminconnect import Garmin

    # Determine token directory
    tdir = token_dir or os.environ.get("GARMINTOKENS", "~/.garminconnect")
    from pathlib import Path

    tdir = str(Path(tdir).expanduser())

    # Configure export module
    export_module.configure(data_dir=data_dir, gcs_enabled=gcs_enabled)

    # Initialize rate limiter
    _rate_limiter = AsyncRateLimiter(min_interval=1.0)

    # Initialize Garmin client
    try:
        _garmin_client = Garmin()
        _garmin_client.login(tdir)
        name = _garmin_client.get_full_name() or "Unknown"
        logger.info("Authenticated as: %s", name)
    except Exception:
        logger.exception(
            "Failed to authenticate with Garmin Connect. "
            "Run 'garmin auth login' to authenticate, "
            "then restart the MCP server."
        )
        _garmin_client = None

    try:
        yield
    finally:
        # Cleanup
        if gcs_enabled:
            try:
                from jons_mcp_file_server import cleanup_file_server

                cleanup_file_server()
            except ImportError:
                pass
        _garmin_client = None
        _rate_limiter = None


# Create FastMCP server instance
mcp = FastMCP(
    name="garmin-connect",
    lifespan=lifespan,
    instructions="Garmin Connect MCP server. Use auth_status to check connection.",
)


def _register_tools() -> None:
    """Register all tool functions with the MCP server."""
    from .tools import get_all_tools

    for tool_fn in get_all_tools():
        mcp.tool()(tool_fn)


def main() -> None:
    """Entry point for the garmin-mcp command."""
    parser = argparse.ArgumentParser(
        description="Garmin Connect MCP Server",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help=(
            "Local directory for data exports. "
            "Files are written to <dir>/.garmin-connect/data/."
        ),
    )
    parser.add_argument(
        "--data-gcs",
        action="store_true",
        help=(
            "Use GCS signed URLs for data exports. "
            "Requires GCS_BUCKET environment variable."
        ),
    )
    parser.add_argument(
        "--token-dir",
        type=str,
        default=None,
        help="Token directory (default: ~/.garminconnect or GARMINTOKENS env var)",
    )

    args = parser.parse_args()

    # Validate args
    if args.data_gcs and args.data_dir:
        logger.error("Cannot specify both --data-dir and --data-gcs")
        sys.exit(1)

    if args.data_gcs and not os.environ.get("GCS_BUCKET"):
        logger.error("--data-gcs requires GCS_BUCKET environment variable")
        sys.exit(1)

    # Set global flags before server starts
    global gcs_enabled, data_dir, token_dir  # noqa: PLW0603
    gcs_enabled = args.data_gcs
    data_dir = args.data_dir
    token_dir = args.token_dir

    # Register tools and run
    _register_tools()
    mcp.run()
