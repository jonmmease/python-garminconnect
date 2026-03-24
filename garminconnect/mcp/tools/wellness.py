"""MCP tools for Garmin Connect wellness data."""

from __future__ import annotations

import logging
from datetime import date as date_type
from typing import Any

from garminconnect.mcp.export import export_data, is_export_available
from garminconnect.mcp.server import garmin_api_call, get_garmin_client

logger = logging.getLogger(__name__)

# Valid metrics for get_wellness_data
_SINGLE_DATE_METRICS = {
    "steps",
    "stress",
    "spo2",
    "respiration",
    "body_battery_events",
    "hydration",
    "floors",
    "movement",
    "intensity_minutes",
    "events",
    "stats",
    "training_readiness",
    "training_status",
}

_DATE_RANGE_METRICS = {
    "steps_daily",
    "steps_weekly",
    "stress_weekly",
    "intensity_minutes_weekly",
    "body_battery",
    "endurance_score",
    "hill_score",
    "race_predictions",
    "hrv_summary",
}

_NO_DATE_METRICS = {
    "race_predictions",
}

ALL_WELLNESS_METRICS = _SINGLE_DATE_METRICS | _DATE_RANGE_METRICS


async def get_wellness_data(
    metric: str,
    date: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    weeks: int | None = None,
    race_type: str | None = None,
    export: bool = False,
) -> dict[str, Any]:
    """Retrieve wellness and fitness metrics from Garmin Connect.

    Args:
        metric: The wellness metric to retrieve. Valid values:
            Single-date metrics (use 'date', defaults to today):
            - "steps": Intraday step data for a specific date
            - "stress": Stress level data for a specific date
            - "spo2": Blood oxygen saturation data for a specific date
            - "respiration": Respiration rate data for a specific date
            - "body_battery_events": Body battery events (sleep, activities) for a date
            - "hydration": Hydration intake data for a specific date
            - "floors": Floors climbed data for a specific date
            - "movement": Daily movement/step timeline data for a specific date
            - "intensity_minutes": Intensity minutes data for a specific date
            - "events": All-day stress/events data for a specific date
            - "stats": Full daily activity summary (steps, calories, distance, etc.)
            - "training_readiness": Training readiness score for a specific date
            - "training_status": Training status data for a specific date

            Date-range metrics (use 'start_date' and 'end_date'):
            - "steps_daily": Daily step totals over a date range
            - "steps_weekly": Weekly step aggregates (use 'date' as end date, 'weeks' for count)
            - "stress_weekly": Weekly stress aggregates (use 'date' as end date, 'weeks' for count)
            - "intensity_minutes_weekly": Weekly intensity minutes over a date range
            - "body_battery": Body battery values over a date range
            - "endurance_score": Endurance score (single date or range)
            - "hill_score": Hill score (single date or range)
            - "race_predictions": Race time predictions (no params for latest, or date range with race_type)
            - "hrv_summary": HRV summary statistics over a date range

        date: Date in 'YYYY-MM-DD' format. Used for single-date metrics and as
            end date for weekly metrics. Defaults to today.
        start_date: Start date in 'YYYY-MM-DD' format for date-range metrics.
        end_date: End date in 'YYYY-MM-DD' format for date-range metrics.
        weeks: Number of weeks for weekly metrics (default: 52).
        race_type: Type for race predictions: "daily" or "monthly".
        export: If True and export is configured, save data to file.

    Returns:
        Dictionary with 'data' key containing the metric data, and optionally
        an 'export' key with file path or URL if export is enabled.

    """
    all_metrics = ALL_WELLNESS_METRICS
    if metric not in all_metrics:
        return {
            "error": f"Invalid metric '{metric}'. Valid values: {sorted(all_metrics)}"
        }

    client = get_garmin_client()
    today = date_type.today().isoformat()

    # Route to the correct Garmin API method
    data: Any
    date_info: str

    if metric == "steps":
        cdate = date or today
        data = await garmin_api_call(client.get_steps_data, cdate)
        date_info = cdate

    elif metric == "steps_daily":
        if not start_date or not end_date:
            return {"error": "steps_daily requires both start_date and end_date"}
        data = await garmin_api_call(client.get_daily_steps, start_date, end_date)
        date_info = f"{start_date}_to_{end_date}"

    elif metric == "steps_weekly":
        end = date or today
        w = weeks or 52
        data = await garmin_api_call(client.get_weekly_steps, end, w)
        date_info = f"{end}_{w}w"

    elif metric == "stress":
        cdate = date or today
        data = await garmin_api_call(client.get_stress_data, cdate)
        date_info = cdate

    elif metric == "stress_weekly":
        end = date or today
        w = weeks or 52
        data = await garmin_api_call(client.get_weekly_stress, end, w)
        date_info = f"{end}_{w}w"

    elif metric == "spo2":
        cdate = date or today
        data = await garmin_api_call(client.get_spo2_data, cdate)
        date_info = cdate

    elif metric == "respiration":
        cdate = date or today
        data = await garmin_api_call(client.get_respiration_data, cdate)
        date_info = cdate

    elif metric == "body_battery":
        sd = start_date or date or today
        ed = end_date
        data = await garmin_api_call(client.get_body_battery, sd, ed)
        date_info = f"{sd}_to_{ed}" if ed else sd

    elif metric == "body_battery_events":
        cdate = date or today
        data = await garmin_api_call(client.get_body_battery_events, cdate)
        date_info = cdate

    elif metric == "hydration":
        cdate = date or today
        data = await garmin_api_call(client.get_hydration_data, cdate)
        date_info = cdate

    elif metric == "floors":
        cdate = date or today
        data = await garmin_api_call(client.get_floors, cdate)
        date_info = cdate

    elif metric == "movement":
        cdate = date or today
        data = await garmin_api_call(client.get_daily_movement, cdate)
        date_info = cdate

    elif metric == "intensity_minutes":
        cdate = date or today
        data = await garmin_api_call(client.get_intensity_minutes_data, cdate)
        date_info = cdate

    elif metric == "intensity_minutes_weekly":
        if not start_date or not end_date:
            return {
                "error": "intensity_minutes_weekly requires both start_date and end_date"
            }
        data = await garmin_api_call(
            client.get_weekly_intensity_minutes, start_date, end_date
        )
        date_info = f"{start_date}_to_{end_date}"

    elif metric == "events":
        cdate = date or today
        data = await garmin_api_call(client.get_all_day_stress, cdate)
        date_info = cdate

    elif metric == "stats":
        cdate = date or today
        data = await garmin_api_call(client.get_stats, cdate)
        date_info = cdate

    elif metric == "endurance_score":
        sd = start_date or date or today
        ed = end_date
        data = await garmin_api_call(client.get_endurance_score, sd, ed)
        date_info = f"{sd}_to_{ed}" if ed else sd

    elif metric == "hill_score":
        sd = start_date or date or today
        ed = end_date
        data = await garmin_api_call(client.get_hill_score, sd, ed)
        date_info = f"{sd}_to_{ed}" if ed else sd

    elif metric == "training_readiness":
        cdate = date or today
        data = await garmin_api_call(client.get_training_readiness, cdate)
        date_info = cdate

    elif metric == "training_status":
        cdate = date or today
        data = await garmin_api_call(client.get_training_status, cdate)
        date_info = cdate

    elif metric == "race_predictions":
        if start_date and end_date and race_type:
            data = await garmin_api_call(
                client.get_race_predictions, start_date, end_date, race_type
            )
            date_info = f"{start_date}_to_{end_date}_{race_type}"
        else:
            data = await garmin_api_call(client.get_race_predictions)
            date_info = today

    elif metric == "hrv_summary":
        if not start_date or not end_date:
            return {"error": "hrv_summary requires both start_date and end_date"}
        data = await garmin_api_call(client.get_hrv_summary, start_date, end_date)
        date_info = f"{start_date}_to_{end_date}"

    else:
        return {"error": f"Metric '{metric}' is not yet implemented"}

    if export and is_export_available():
        ref = export_data("wellness", metric, date_info, data)
        return {"export": ref}
    return {"data": data}


# Valid actions for manage_wellness
_VALID_ACTIONS = {"add_hydration", "set_sleep_note"}


async def manage_wellness(
    action: str,
    date: str | None = None,
    value_in_ml: float | None = None,
    timestamp: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """Manage wellness data on Garmin Connect (add/update).

    Args:
        action: The action to perform. Valid values:
            - "add_hydration": Add hydration data in milliliters
            - "set_sleep_note": Set a note on a sleep entry

        date: Date in 'YYYY-MM-DD' format. Defaults to today.
        value_in_ml: Amount of water in ml (required for add_hydration).
            Positive values add, negative values subtract.
        timestamp: Timestamp for hydration in 'YYYY-MM-DDThh:mm:ss' format
            (optional for add_hydration, defaults to current time).
        note: Note text (required for set_sleep_note).

    Returns:
        Dictionary with 'data' key containing the API response.

    """
    if action not in _VALID_ACTIONS:
        return {
            "error": f"Invalid action '{action}'. Valid values: {sorted(_VALID_ACTIONS)}"
        }

    client = get_garmin_client()
    today = date_type.today().isoformat()

    if action == "add_hydration":
        if value_in_ml is None:
            return {"error": "add_hydration requires 'value_in_ml' parameter"}
        cdate = date or today
        data = await garmin_api_call(
            client.add_hydration_data,
            value_in_ml,
            timestamp=timestamp,
            cdate=cdate,
        )
        return {"data": data}

    if action == "set_sleep_note":
        if note is None:
            return {"error": "set_sleep_note requires 'note' parameter"}
        cdate = date or today
        data = await garmin_api_call(client.set_sleep_note, cdate, note)
        return {"data": data}

    return {"error": f"Action '{action}' is not yet implemented"}
