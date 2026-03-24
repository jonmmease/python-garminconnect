"""MCP tools for file uploads via jons-mcp-file-server."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def request_upload(
    filename: str | None = None, max_bytes: int = 50 * 1024 * 1024
) -> dict:
    """Request an upload URL for uploading a file to Garmin Connect.

    Returns an upload URL, token, expiration, and a curl command example.
    The token can be used later with tools that accept an image_token
    (e.g., manage_nutrition create_food/update_food).

    Args:
        filename: Optional filename hint (e.g., "food_photo.jpg").
        max_bytes: Maximum upload size in bytes (default 50 MB).

    Returns:
        Dict with upload_url, token, expires_in_seconds, and curl command.

    """
    from jons_mcp_file_server import get_file_server

    from garminconnect.mcp.server import gcs_enabled

    server = get_file_server(backend="gcs" if gcs_enabled else "localhost")
    registration = server.register_upload(filename=filename, max_bytes=max_bytes)

    return {
        "upload_url": registration["uploadUrl"],
        "token": registration["uploadToken"],
        "expires_in_seconds": registration["expiresIn"],
        "curl": registration["curl"],
    }
