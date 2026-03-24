"""Training-related MCP tools for Garmin Connect."""

from __future__ import annotations

import logging
from typing import Any

from garminconnect.mcp.server import garmin_api_call, get_garmin_client

logger = logging.getLogger(__name__)

_VALID_ACTIONS = (
    "workouts",
    "workout_by_id",
    "plans",
    "plan_by_id",
    "personal_records",
    "goals",
)

_ID_REQUIRED_ACTIONS = {"workout_by_id", "plan_by_id"}


async def get_training_data(
    action: str,
    id: int | None = None,
    start: int = 0,
    limit: int = 100,
    status: str = "active",
) -> dict[str, Any]:
    """Get training data from Garmin Connect.

    Args:
        action: One of 'workouts', 'workout_by_id', 'plans', 'plan_by_id',
                'personal_records', 'goals'.
        id: Required for 'workout_by_id' and 'plan_by_id' actions.
        start: Start index for paginated results (workouts, goals).
        limit: Max number of results for paginated results (workouts, goals).
        status: Goal status filter — 'active', 'future', or 'past' (goals only).

    Returns:
        Dictionary with the requested training data.

    """
    if action not in _VALID_ACTIONS:
        return {
            "error": f"Unknown action: {action}. Valid actions: {', '.join(_VALID_ACTIONS)}"
        }

    if action in _ID_REQUIRED_ACTIONS and id is None:
        return {"error": f"id is required for {action} action"}

    client = get_garmin_client()
    result: dict[str, Any] = {"action": action}

    data = await _dispatch(
        action, client, id=id, start=start, limit=limit, status=status
    )
    result["data"] = data

    # Include relevant parameters in response
    if action in ("workouts", "goals"):
        result["start"] = start
        result["limit"] = limit
    if action in _ID_REQUIRED_ACTIONS:
        result["id"] = id
    if action == "goals":
        result["status"] = status

    return result


async def _dispatch(
    action: str,
    client: Any,
    *,
    id: int | None,
    start: int,
    limit: int,
    status: str,
) -> Any:
    """Dispatch the API call based on action."""
    if action == "workouts":
        return await garmin_api_call(client.get_workouts, start, limit)
    if action == "workout_by_id":
        return await garmin_api_call(client.get_workout_by_id, id)
    if action == "plans":
        return await garmin_api_call(client.get_training_plans)
    if action == "plan_by_id":
        return await garmin_api_call(client.get_training_plan_by_id, id)
    if action == "personal_records":
        return await garmin_api_call(client.get_personal_record)
    # goals
    return await garmin_api_call(client.get_goals, status, start, limit)
