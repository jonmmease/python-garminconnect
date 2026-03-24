"""MCP tools for Garmin Connect."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


def get_all_tools() -> list[Callable[..., Any]]:
    """Return all tool functions to register with the MCP server."""
    from .activities import get_activities, manage_activity
    from .auth import auth_status
    from .body import get_body_data, manage_body_measurements
    from .devices import get_devices
    from .heart import get_heart_data
    from .nutrition import get_nutrition_data, manage_nutrition
    from .sleep import get_sleep_data
    from .training import get_training_data
    from .uploads import request_upload
    from .wellness import get_wellness_data, manage_wellness

    tools: list[Callable[..., Any]] = [
        auth_status,
        get_training_data,
        get_body_data,
        manage_body_measurements,
        get_sleep_data,
        get_devices,
        get_wellness_data,
        manage_wellness,
        get_heart_data,
        get_activities,
        manage_activity,
        get_nutrition_data,
        manage_nutrition,
        request_upload,
    ]

    return tools
