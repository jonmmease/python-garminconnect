"""MCP tools for device data."""

from __future__ import annotations

import logging
from typing import Any

from garminconnect.mcp.server import garmin_api_call, get_garmin_client

logger = logging.getLogger(__name__)

VALID_DEVICE_ACTIONS = (
    "list",
    "settings",
    "primary",
    "alarms",
    "last_used",
    "solar",
)


async def _fetch_device_data(
    client: Any,
    action: str,
    device_id: str | None,
    date: str | None,
    end_date: str | None,
) -> dict[str, Any]:
    """Fetch device data for the given action."""
    if action == "list":
        return {"data": await garmin_api_call(client.get_devices)}

    if action == "settings":
        if not device_id:
            return {"error": "device_id is required for settings action"}
        return {"data": await garmin_api_call(client.get_device_settings, device_id)}

    if action == "primary":
        return {"data": await garmin_api_call(client.get_primary_training_device)}

    if action == "alarms":
        return {"data": await garmin_api_call(client.get_device_alarms)}

    if action == "last_used":
        return {"data": await garmin_api_call(client.get_device_last_used)}

    # action == "solar"
    if not device_id:
        return {"error": "device_id is required for solar action"}
    if not date:
        return {"error": "date is required for solar action"}
    return {
        "data": await garmin_api_call(
            client.get_device_solar_data, device_id, date, end_date
        )
    }


async def get_devices(
    action: str = "list",
    device_id: str | None = None,
    date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Get device information from Garmin Connect.

    Args:
        action: The device action to perform. One of:
            - list: List all registered devices
            - settings: Get settings for a specific device (requires device_id)
            - primary: Get primary training device info
            - alarms: Get active alarms from all devices
            - last_used: Get the last used device
            - solar: Get solar data for a device (requires device_id and date)
        device_id: Device ID. Required for 'settings' and 'solar' actions.
        date: Date in YYYY-MM-DD format. Required for 'solar' action.
        end_date: End date in YYYY-MM-DD format. Optional for 'solar' action.

    Returns:
        dict with 'data' key containing device data, or 'error' key on failure.

    """
    if action not in VALID_DEVICE_ACTIONS:
        return {
            "error": f"Invalid action '{action}'. Must be one of: {', '.join(VALID_DEVICE_ACTIONS)}"
        }

    client = get_garmin_client()
    return await _fetch_device_data(client, action, device_id, date, end_date)
