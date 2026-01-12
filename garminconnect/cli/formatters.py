"""Output formatting for CLI commands."""

import json
from typing import Any

from tabulate import tabulate  # type: ignore[import-untyped]

# Fields to hide in table output (still present in JSON)
EXCLUDE_FIELDS = {
    "userProfileId",
    "userProfilePk",
    "uuid",
    "version",
    "lastUpdated",
    "sourceType",
    "userId",
    "userAccessToken",
    "wellnessDataId",
}


def format_output(  # noqa: PLR0911
    data: dict[str, Any] | list[dict[str, Any]] | None,
    as_json: bool = False,
) -> str:
    """Format API response as table or JSON.

    Args:
        data: API response (dict, list of dicts, or None)
        as_json: If True, output JSON; otherwise output table

    Returns:
        Formatted string for output

    """
    if data is None:
        return "No data." if not as_json else "null"

    if as_json:
        return json.dumps(data, indent=2, default=str)

    if isinstance(data, dict):
        # Key-value table for single record
        rows = [
            [k, _format_value(v)]
            for k, v in data.items()
            if k not in EXCLUDE_FIELDS
        ]
        return tabulate(rows, headers=["Field", "Value"], tablefmt="simple")

    if isinstance(data, list):
        if not data:
            return "No data."

        # Handle list of dicts
        if isinstance(data[0], dict):
            headers = [k for k in data[0] if k not in EXCLUDE_FIELDS]
            rows = [
                [_format_value(row.get(h, "")) for h in headers]
                for row in data
            ]
            return tabulate(rows, headers=headers, tablefmt="simple")

        # Handle list of primitives
        return "\n".join(str(item) for item in data)

    return str(data)


def _format_value(value: Any) -> str:  # noqa: PLR0911
    """Format a single value for table display."""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        # Format floats to reasonable precision
        if value == int(value):
            return str(int(value))
        return f"{value:.2f}"
    if isinstance(value, dict):
        # Nested dicts: show summary
        return f"{{...}} ({len(value)} fields)"
    if isinstance(value, list):
        return f"[...] ({len(value)} items)"
    return str(value)
