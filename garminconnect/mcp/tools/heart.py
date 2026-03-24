"""MCP tools for Garmin Connect heart rate data."""

from __future__ import annotations

import logging
from datetime import date as date_type
from typing import Any

from garminconnect.mcp.export import export_data, is_export_available
from garminconnect.mcp.server import garmin_api_call, get_garmin_client

logger = logging.getLogger(__name__)

# Valid metrics for get_heart_data
ALL_HEART_METRICS = {"rates", "hrv", "hrv_summary", "resting", "zones"}

_SINGLE_DATE_METRICS = {"rates", "hrv", "resting"}
_DATE_RANGE_METRICS = {"hrv_summary"}
_NO_DATE_METRICS = {"zones"}


async def get_heart_data(
    metric: str,
    date: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    export: bool = False,
) -> dict[str, Any]:
    """Retrieve heart rate metrics from Garmin Connect.

    Args:
        metric: The heart metric to retrieve. Valid values:
            - "rates": Heart rate data for a specific date (intraday readings)
            - "hrv": Heart Rate Variability data for a specific date
            - "hrv_summary": HRV summary statistics over a date range
                (requires start_date and end_date)
            - "resting": Resting heart rate for a specific date
            - "zones": Heart rate zone configuration (no date needed)

        date: Date in 'YYYY-MM-DD' format for single-date metrics.
            Defaults to today.
        start_date: Start date in 'YYYY-MM-DD' format for hrv_summary.
        end_date: End date in 'YYYY-MM-DD' format for hrv_summary.
        export: If True and export is configured, save data to file.

    Returns:
        Dictionary with 'data' key containing the metric data, and optionally
        an 'export' key with file path or URL if export is enabled.

    """
    if metric not in ALL_HEART_METRICS:
        return {
            "error": (
                f"Invalid metric '{metric}'. "
                f"Valid values: {sorted(ALL_HEART_METRICS)}"
            )
        }

    client = get_garmin_client()
    today = date_type.today().isoformat()

    data: Any
    date_info: str

    if metric == "rates":
        cdate = date or today
        data = await garmin_api_call(client.get_heart_rates, cdate)
        date_info = cdate

    elif metric == "hrv":
        cdate = date or today
        data = await garmin_api_call(client.get_hrv_data, cdate)
        date_info = cdate

    elif metric == "hrv_summary":
        if not start_date or not end_date:
            return {"error": "hrv_summary requires both start_date and end_date"}
        data = await garmin_api_call(client.get_hrv_summary, start_date, end_date)
        date_info = f"{start_date}_to_{end_date}"

    elif metric == "resting":
        cdate = date or today
        data = await garmin_api_call(client.get_rhr_day, cdate)
        date_info = cdate

    elif metric == "zones":
        data = await garmin_api_call(client.get_heart_rate_zones)
        date_info = today

    else:
        return {"error": f"Metric '{metric}' is not yet implemented"}

    if export and is_export_available():
        ref = export_data("heart", metric, date_info, data)
        return {"export": ref}
    return {"data": data}
