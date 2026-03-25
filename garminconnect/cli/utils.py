"""Shared utilities for garminconnect CLI."""

import os
from collections.abc import Callable
from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar

import click

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)
from garminconnect.cli.resilience import global_rate_limit

F = TypeVar("F", bound=Callable[..., Any])

DEFAULT_TOKEN_DIR = Path.home() / ".garminconnect"


def get_token_dir() -> Path:
    """Get token directory from GARMINTOKENS env var or default."""
    env_path = os.environ.get("GARMINTOKENS")
    if env_path:
        return Path(env_path)
    return DEFAULT_TOKEN_DIR


def tokens_exist() -> bool:
    """Check if valid tokens exist."""
    token_dir = get_token_dir()
    oauth1 = token_dir / "oauth1_token.json"
    oauth2 = token_dir / "oauth2_token.json"
    return oauth1.exists() and oauth2.exists()


def clear_tokens() -> None:
    """Remove stored tokens."""
    token_dir = get_token_dir()
    for token_file in ["oauth1_token.json", "oauth2_token.json"]:
        path = token_dir / token_file
        if path.exists():
            path.unlink()


def parse_date(value: str) -> str:
    """Parse date input to YYYY-MM-DD format.

    Accepts: today, yesterday, -N (days ago), YYYY-MM-DD
    """
    value_lower = value.lower()

    if value_lower == "today":
        return date.today().strftime("%Y-%m-%d")

    if value_lower == "yesterday":
        return (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Negative offset: -7 means 7 days ago
    if value.startswith("-") and value[1:].isdigit():
        days = int(value)
        return (date.today() + timedelta(days=days)).strftime("%Y-%m-%d")

    # Assume YYYY-MM-DD format
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError as e:
        raise ValueError(
            f"Invalid date: {value}. Use YYYY-MM-DD, 'today', 'yesterday', or '-N'."
        ) from e


def require_auth(f: F) -> F:
    """Decorator to ensure authentication before command execution.

    Also applies global rate limiting to prevent API rate limit errors
    when multiple CLI commands run in parallel.
    """

    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        ctx = click.get_current_context()

        if not tokens_exist():
            raise click.ClickException(
                "Not authenticated. Please run: garmin auth login"
            )

        # Apply global rate limit before API access
        with global_rate_limit(get_token_dir()):
            try:
                client = Garmin()
                client.login(tokenstore=str(get_token_dir()))
                ctx.obj["client"] = client
            except GarminConnectAuthenticationError as e:
                raise click.ClickException(
                    f"Authentication failed: {e}\n"
                    f"Please re-authenticate: garmin auth login"
                ) from None

            return f(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


def handle_api_error(e: Exception) -> None:
    """Convert API exceptions to user-friendly Click errors."""
    if isinstance(e, GarminConnectAuthenticationError):
        raise click.ClickException(
            "Authentication failed. Run 'garmin auth login' to re-authenticate."
        )
    if isinstance(e, GarminConnectTooManyRequestsError):
        raise click.ClickException(
            "Rate limit exceeded. Please wait before trying again."
        )
    if isinstance(e, GarminConnectConnectionError):
        raise click.ClickException(f"Connection error: {e}")
    raise click.ClickException(str(e))
