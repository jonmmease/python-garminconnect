"""MCP tools for body composition and measurement data."""

from __future__ import annotations

import logging
from typing import Any

from garminconnect.mcp.export import export_data, is_export_available
from garminconnect.mcp.server import garmin_api_call, get_garmin_client

logger = logging.getLogger(__name__)

VALID_BODY_METRICS = (
    "composition",
    "weigh_ins",
    "daily_weigh_ins",
    "blood_pressure",
    "stats_and_body",
    "max_metrics",
    "lactate_threshold",
)

VALID_MANAGE_ACTIONS = (
    "add_weigh_in",
    "delete_weigh_in",
    "add_blood_pressure",
    "delete_blood_pressure",
)


async def _fetch_body_metric(
    client: Any,
    metric: str,
    date: str | None,
    end_date: str | None,
) -> tuple[Any, str] | dict[str, str]:
    """Fetch a body metric, returning (data, date_info) or an error dict."""
    date_info = date or "latest"

    if metric == "composition":
        if not date:
            return {"error": "date is required for composition metric"}
        data = await garmin_api_call(client.get_body_composition, date, end_date)
        if end_date:
            date_info = f"{date}_to_{end_date}"
        return data, date_info

    if metric == "weigh_ins":
        if not date or not end_date:
            return {"error": "Both date and end_date are required for weigh_ins metric"}
        data = await garmin_api_call(client.get_weigh_ins, date, end_date)
        return data, f"{date}_to_{end_date}"

    if metric == "daily_weigh_ins":
        if not date:
            return {"error": "date is required for daily_weigh_ins metric"}
        return await garmin_api_call(client.get_daily_weigh_ins, date), date_info

    if metric == "blood_pressure":
        if not date:
            return {"error": "date is required for blood_pressure metric"}
        data = await garmin_api_call(client.get_blood_pressure, date, end_date)
        if end_date:
            date_info = f"{date}_to_{end_date}"
        return data, date_info

    if metric == "stats_and_body":
        if not date:
            return {"error": "date is required for stats_and_body metric"}
        return await garmin_api_call(client.get_stats_and_body, date), date_info

    if metric == "max_metrics":
        if not date:
            return {"error": "date is required for max_metrics metric"}
        return await garmin_api_call(client.get_max_metrics, date), date_info

    # metric == "lactate_threshold"
    if date:
        data = await garmin_api_call(
            client.get_lactate_threshold,
            latest=False,
            start_date=date,
            end_date=end_date,
        )
        if end_date:
            date_info = f"{date}_to_{end_date}"
        return data, date_info
    return await garmin_api_call(client.get_lactate_threshold, latest=True), date_info


async def get_body_data(
    metric: str,
    date: str | None = None,
    end_date: str | None = None,
    export: bool = False,
) -> dict[str, Any]:
    """Get body composition and measurement data from Garmin Connect.

    Args:
        metric: The body metric to retrieve. One of:
            - composition: Body composition data (weight, BMI, body fat, etc.)
            - weigh_ins: Weigh-in records for a date range (requires date and end_date)
            - daily_weigh_ins: All weigh-ins for a single date
            - blood_pressure: Blood pressure readings
            - stats_and_body: Combined activity stats and body composition
            - max_metrics: Max metric data (VO2 max, etc.)
            - lactate_threshold: Running lactate threshold info (date not required for latest)
        date: Date in YYYY-MM-DD format. Required for most metrics.
        end_date: End date in YYYY-MM-DD format. Used for date range queries
            (composition, weigh_ins, blood_pressure). Defaults to date if not provided.
        export: If True, export data to configured storage.

    Returns:
        dict with 'data' key containing the metric data, and optionally 'export' key.

    """
    if metric not in VALID_BODY_METRICS:
        return {
            "error": f"Invalid metric '{metric}'. Must be one of: {', '.join(VALID_BODY_METRICS)}"
        }

    client = get_garmin_client()
    fetch_result = await _fetch_body_metric(client, metric, date, end_date)

    if isinstance(fetch_result, dict):
        return fetch_result

    data, date_info = fetch_result
    if export and is_export_available():
        ref = export_data("body", metric, date_info, data)
        return {"export": ref}
    return {"data": data}


async def _do_manage_action(
    client: Any,
    action: str,
    date: str | None,
    weight: float | None,
    unit: str,
    timestamp: str,
    systolic: int | None,
    diastolic: int | None,
    pulse: int | None,
    notes: str,
    weight_pk: str | None,
    version: str | None,
) -> dict[str, Any]:
    """Execute a body measurement management action."""
    if action == "add_weigh_in":
        if weight is None:
            return {"error": "weight is required for add_weigh_in"}
        result = await garmin_api_call(client.add_weigh_in, weight, unit, timestamp)
        return {"result": result}

    if action == "delete_weigh_in":
        if not weight_pk or not date:
            return {"error": "weight_pk and date are required for delete_weigh_in"}
        result = await garmin_api_call(client.delete_weigh_in, weight_pk, date)
        return {"result": result}

    if action == "add_blood_pressure":
        if systolic is None or diastolic is None or pulse is None:
            return {
                "error": "systolic, diastolic, and pulse are required for add_blood_pressure"
            }
        result = await garmin_api_call(
            client.set_blood_pressure, systolic, diastolic, pulse, timestamp, notes
        )
        return {"result": result}

    # action == "delete_blood_pressure"
    if not version or not date:
        return {"error": "version and date are required for delete_blood_pressure"}
    result = await garmin_api_call(client.delete_blood_pressure, version, date)
    return {"result": result}


async def manage_body_measurements(
    action: str,
    date: str | None = None,
    weight: float | None = None,
    unit: str = "kg",
    timestamp: str = "",
    systolic: int | None = None,
    diastolic: int | None = None,
    pulse: int | None = None,
    notes: str = "",
    weight_pk: str | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    """Add or delete body measurements (weigh-ins, blood pressure).

    Args:
        action: The action to perform. One of:
            - add_weigh_in: Add a weight measurement
            - delete_weigh_in: Delete a specific weigh-in by weight_pk and date
            - add_blood_pressure: Add a blood pressure reading
            - delete_blood_pressure: Delete a blood pressure reading by version and date
        date: Date in YYYY-MM-DD format. Required for delete actions.
        weight: Weight value. Required for add_weigh_in.
        unit: Weight unit, 'kg' or 'lbs'. Default 'kg'.
        timestamp: ISO format timestamp for the measurement. Defaults to now.
        systolic: Systolic blood pressure. Required for add_blood_pressure.
        diastolic: Diastolic blood pressure. Required for add_blood_pressure.
        pulse: Pulse/heart rate. Required for add_blood_pressure.
        notes: Optional notes for blood pressure reading.
        weight_pk: Weight primary key. Required for delete_weigh_in.
        version: Blood pressure version. Required for delete_blood_pressure.

    Returns:
        dict with 'result' key on success, or 'error' key on failure.

    """
    if action not in VALID_MANAGE_ACTIONS:
        return {
            "error": f"Invalid action '{action}'. Must be one of: {', '.join(VALID_MANAGE_ACTIONS)}"
        }

    client = get_garmin_client()
    return await _do_manage_action(
        client,
        action,
        date,
        weight,
        unit,
        timestamp,
        systolic,
        diastolic,
        pulse,
        notes,
        weight_pk,
        version,
    )
