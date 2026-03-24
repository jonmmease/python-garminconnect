"""Authentication status MCP tool for Garmin Connect."""

from __future__ import annotations

import logging
from typing import Any

from garminconnect.mcp.server import get_garmin_client

logger = logging.getLogger(__name__)


async def auth_status() -> dict[str, Any]:
    """Check Garmin Connect authentication status and return user info.

    Returns connection status, user profile information, and export mode.
    No parameters required.

    Returns:
        Dictionary with authentication status and user details.

    """
    # Import _garmin_client at call time to get current value
    from garminconnect.mcp.server import _garmin_client

    if _garmin_client is None:
        return {
            "authenticated": False,
            "message": (
                "Not authenticated with Garmin Connect. "
                "Run 'garmin auth login' to authenticate, "
                "then restart the MCP server."
            ),
        }

    client = get_garmin_client()

    result: dict[str, Any] = {
        "authenticated": True,
        "full_name": client.get_full_name(),
        "unit_system": client.get_unit_system(),
    }

    # Add user profile info
    try:
        from garminconnect.mcp.server import garmin_api_call

        profile = await garmin_api_call(client.get_user_profile)
        result["user_profile"] = profile
    except Exception:
        logger.debug("Could not fetch user profile", exc_info=True)

    # Report export mode
    from garminconnect.mcp.server import data_dir, gcs_enabled

    if data_dir is not None:
        result["export_mode"] = "data-dir"
        result["data_dir"] = data_dir
    elif gcs_enabled:
        result["export_mode"] = "data-gcs"
    else:
        result["export_mode"] = "none"

    return result
