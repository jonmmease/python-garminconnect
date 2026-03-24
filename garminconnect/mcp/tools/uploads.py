"""MCP tools for file uploads via jons-mcp-file-server."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def request_upload(
    filename: str | None = None, max_bytes: int = 50 * 1024 * 1024
) -> dict:
    """Request an upload URL for uploading a file.

    Call this first, then upload the file using the returned curl command.
    The curl response will contain a `fileToken` — pass THAT token
    (not the `token` from this response) to tools that accept image_token
    (e.g., manage_nutrition create_food/update_food) or file_token
    (e.g., manage_activity upload).

    Workflow:
    1. Call request_upload() → get upload_url, token, curl
    2. Run the curl command to upload the file → response contains fileToken
    3. Pass the fileToken to manage_nutrition(image_token=fileToken)

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
