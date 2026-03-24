"""MCP tools for Garmin Connect activities."""

from __future__ import annotations

import logging
from typing import Any

from garminconnect.mcp.export import export_binary, is_export_available
from garminconnect.mcp.server import garmin_api_call, get_garmin_client

logger = logging.getLogger(__name__)

_GET_ACTIONS = frozenset(
    {"list", "get", "by_date", "types", "count", "first_last", "last", "calendar"}
)

_MANAGE_ACTIONS = frozenset(
    {"rename", "retype", "upload", "delete", "download", "create"}
)

_INCLUDE_OPTIONS = frozenset(
    {
        "details",
        "splits",
        "typed_splits",
        "weather",
        "hr_zones",
        "power_zones",
        "gear",
        "exercise_sets",
    }
)

_DOWNLOAD_FORMATS = frozenset({"fit", "tcx", "gpx", "kml", "csv"})


async def get_activities(
    action: str,
    start: int = 0,
    limit: int = 20,
    activity_type: str | None = None,
    activity_id: str | None = None,
    include: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sort_order: str | None = None,
    year: int | None = None,
    month: int | None = None,
) -> dict[str, Any]:
    """Query activities from Garmin Connect.

    Actions:
    - list: Get a paginated list of activities (params: start, limit, activity_type)
    - get: Get a single activity by ID, with optional extra data (params: activity_id, include)
      include options: details, splits, typed_splits, weather, hr_zones, power_zones, gear, exercise_sets
    - by_date: Get activities between dates (params: start_date, end_date, activity_type, sort_order)
    - types: Get all available activity types
    - count: Get total number of activities
    - first_last: Get first and last activity dates
    - last: Get the most recent activity
    - calendar: Get calendar data for a month (params: year, month)
    """
    if action not in _GET_ACTIONS:
        return {"error": f"Invalid action '{action}'. Valid: {sorted(_GET_ACTIONS)}"}

    client = get_garmin_client()

    if action == "list":
        data = await garmin_api_call(client.get_activities, start, limit, activity_type)
        return {"activities": data}

    if action == "get":
        if not activity_id:
            return {"error": "activity_id is required for 'get' action"}

        result: dict[str, Any] = {}
        result["activity"] = await garmin_api_call(client.get_activity, activity_id)

        if include:
            invalid = set(include) - _INCLUDE_OPTIONS
            if invalid:
                return {
                    "error": (
                        f"Invalid include options: {sorted(invalid)}. "
                        f"Valid: {sorted(_INCLUDE_OPTIONS)}"
                    )
                }

            include_handlers: dict[str, tuple[Any, list[Any]]] = {
                "details": (client.get_activity_details, [activity_id]),
                "splits": (client.get_activity_splits, [activity_id]),
                "typed_splits": (client.get_activity_typed_splits, [activity_id]),
                "weather": (client.get_activity_weather, [activity_id]),
                "hr_zones": (client.get_activity_hr_in_timezones, [activity_id]),
                "power_zones": (client.get_activity_power_in_timezones, [activity_id]),
                "gear": (client.get_activity_gear, [activity_id]),
                "exercise_sets": (client.get_activity_exercise_sets, [activity_id]),
            }

            for key in include:
                func, args = include_handlers[key]
                try:
                    result[key] = await garmin_api_call(func, *args)
                except Exception:
                    logger.warning(
                        "Failed to fetch %s for activity %s", key, activity_id
                    )
                    result[key] = {"error": f"Failed to fetch {key}"}

        return result

    if action == "by_date":
        if not start_date:
            return {"error": "start_date is required for 'by_date' action"}
        data = await garmin_api_call(
            client.get_activities_by_date,
            start_date,
            end_date,
            activity_type,
            sort_order,
        )
        return {"activities": data}

    if action == "types":
        data = await garmin_api_call(client.get_activity_types)
        return {"activity_types": data}

    if action == "count":
        count = await garmin_api_call(client.count_activities)
        return {"total_count": count}

    if action == "first_last":
        data = await garmin_api_call(client.get_activities_first_last)
        return {"first_last": data}

    if action == "last":
        data = await garmin_api_call(client.get_last_activity)
        return {"last_activity": data}

    if action == "calendar":
        if year is None or month is None:
            return {"error": "year and month are required for 'calendar' action"}
        data = await garmin_api_call(client.get_calendar_month, year, month)
        return {"calendar": data}

    return {"error": f"Unhandled action: {action}"}


async def manage_activity(
    action: str,
    activity_id: str | None = None,
    name: str | None = None,
    type_id: int | None = None,
    type_key: str | None = None,
    parent_type_id: int | None = None,
    file_token: str | None = None,
    download_format: str | None = None,
    start_time: str | None = None,
    time_zone: str | None = None,
    duration_min: int | None = None,
    distance_km: float | None = None,
    activity_type: str | None = None,
    activity_name: str | None = None,
) -> dict[str, Any]:
    """Manage activities on Garmin Connect.

    Actions:
    - rename: Rename an activity (params: activity_id, name)
    - retype: Change activity type (params: activity_id, type_id, type_key, parent_type_id)
    - upload: Upload an activity file (params: file_token from request_upload)
    - delete: Delete an activity (params: activity_id)
    - download: Download activity file (params: activity_id, download_format: fit/tcx/gpx/kml/csv)
      Requires --data-dir or --data-gcs. Returns path or URL to the downloaded file.
    - create: Create a manual activity (params: start_time, time_zone, duration_min,
      distance_km, activity_type, activity_name)
      start_time format: "2023-12-02T10:00:00.000"
      time_zone example: "Europe/Paris"
      activity_type: type key like "running", "cycling", "resort_skiing"
    """
    if action not in _MANAGE_ACTIONS:
        return {"error": f"Invalid action '{action}'. Valid: {sorted(_MANAGE_ACTIONS)}"}

    client = get_garmin_client()

    if action == "rename":
        if not activity_id or not name:
            return {"error": "activity_id and name are required for 'rename' action"}
        await garmin_api_call(client.set_activity_name, activity_id, name)
        return {"status": "ok", "activity_id": activity_id, "new_name": name}

    if action == "retype":
        if not activity_id or type_id is None or not type_key or parent_type_id is None:
            return {
                "error": (
                    "activity_id, type_id, type_key, and parent_type_id "
                    "are required for 'retype' action"
                )
            }
        await garmin_api_call(
            client.set_activity_type, activity_id, type_id, type_key, parent_type_id
        )
        return {"status": "ok", "activity_id": activity_id, "new_type": type_key}

    if action == "upload":
        if not file_token:
            return {"error": "file_token is required for 'upload' action"}

        from jons_mcp_file_server import get_file_server

        from garminconnect.mcp.server import gcs_enabled

        server = get_file_server(backend="gcs" if gcs_enabled else "localhost")
        upload = server.resolve_upload(file_token)
        local_path = upload["local_path"]

        result = await garmin_api_call(client.upload_activity, local_path)
        return {"status": "ok", "upload_result": result}

    if action == "delete":
        if not activity_id:
            return {"error": "activity_id is required for 'delete' action"}
        await garmin_api_call(client.delete_activity, activity_id)
        return {"status": "ok", "activity_id": activity_id, "deleted": True}

    if action == "download":
        if not activity_id:
            return {"error": "activity_id is required for 'download' action"}
        if not is_export_available():
            return {
                "error": (
                    "No export mode configured. "
                    "Start the server with --data-dir or --data-gcs."
                )
            }

        fmt = (download_format or "tcx").lower()
        if fmt not in _DOWNLOAD_FORMATS:
            return {
                "error": (
                    f"Invalid download_format '{fmt}'. "
                    f"Valid: {sorted(_DOWNLOAD_FORMATS)}"
                )
            }

        from garminconnect import Garmin

        format_map = {
            "fit": Garmin.ActivityDownloadFormat.ORIGINAL,
            "tcx": Garmin.ActivityDownloadFormat.TCX,
            "gpx": Garmin.ActivityDownloadFormat.GPX,
            "kml": Garmin.ActivityDownloadFormat.KML,
            "csv": Garmin.ActivityDownloadFormat.CSV,
        }

        dl_fmt = format_map[fmt]
        ext = "zip" if fmt == "fit" else fmt
        data = await garmin_api_call(client.download_activity, activity_id, dl_fmt)

        filename = f"activity_{activity_id}.{ext}"
        ref = export_binary("activities", filename, data)
        return {"status": "ok", "activity_id": activity_id, "format": fmt, **ref}

    if action == "create":
        if (
            not start_time
            or not time_zone
            or duration_min is None
            or distance_km is None
        ):
            return {
                "error": (
                    "start_time, time_zone, duration_min, and distance_km "
                    "are required for 'create' action"
                )
            }
        if not activity_type:
            return {"error": "activity_type is required for 'create' action"}
        if not activity_name:
            return {"error": "activity_name is required for 'create' action"}

        result = await garmin_api_call(
            client.create_manual_activity,
            start_time,
            time_zone,
            activity_type,
            distance_km,
            duration_min,
            activity_name,
        )
        return {"status": "ok", "create_result": result}

    return {"error": f"Unhandled action: {action}"}
