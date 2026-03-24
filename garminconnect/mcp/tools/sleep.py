"""MCP tools for sleep data."""

from __future__ import annotations

import logging
from typing import Any

from garminconnect.mcp.export import export_data, is_export_available
from garminconnect.mcp.server import garmin_api_call, get_garmin_client

logger = logging.getLogger(__name__)


async def get_sleep_data(
    date: str,
    end_date: str | None = None,
    export: bool = False,
) -> dict[str, Any]:
    """Get sleep data from Garmin Connect.

    When only date is provided, returns detailed sleep data for that single night.
    When both date and end_date are provided, returns aggregated sleep statistics
    for the date range.

    Args:
        date: Date in YYYY-MM-DD format. For single-night data, this is the
            date you went to sleep.
        end_date: End date in YYYY-MM-DD format. When provided, returns
            aggregated sleep stats for the date range instead of single-night data.
        export: If True, export data to configured storage.

    Returns:
        dict with 'data' key containing sleep data, and optionally 'export' key.

    """
    client = get_garmin_client()

    if end_date:
        data = await garmin_api_call(client.get_sleep_stats, date, end_date)
        date_info = f"{date}_to_{end_date}"
        metric = "stats"
    else:
        data = await garmin_api_call(client.get_sleep_data, date)
        date_info = date
        metric = "data"

    if export and is_export_available():
        ref = export_data("sleep", metric, date_info, data)
        return {"export": ref}
    return {"data": data}
