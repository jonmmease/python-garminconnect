"""Data export logic for MCP server — handles --data-dir and --data-gcs modes."""

from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Module-level config set by server.py at startup
_data_dir: str | None = None
_gcs_enabled: bool = False


def configure(data_dir: str | None = None, gcs_enabled: bool = False) -> None:
    """Configure the export module. Called once at server startup."""
    global _data_dir, _gcs_enabled  # noqa: PLW0603
    _data_dir = data_dir
    _gcs_enabled = gcs_enabled


def is_export_available() -> bool:
    """Check if any export mode is configured."""
    return _data_dir is not None or _gcs_enabled


def export_data(
    domain: str,
    metric: str,
    date_info: str,
    data: Any,
) -> dict[str, str]:
    """Export data to file and return a reference.

    Args:
        domain: Data domain (e.g., 'wellness', 'heart', 'body')
        metric: Specific metric (e.g., 'steps_daily', 'rates')
        date_info: Date or date range string for filename
        data: JSON-serializable data to export

    Returns:
        dict with 'path' (for data-dir mode) or 'url' (for GCS mode)

    Raises:
        RuntimeError: If no export mode is configured

    """
    if not is_export_available():
        msg = (
            "No export mode configured. "
            "Start the server with --data-dir or --data-gcs."
        )
        raise RuntimeError(msg)

    filename = f"{metric}_{date_info}.json"
    json_bytes = json.dumps(data, indent=2, default=str).encode("utf-8")

    if _data_dir is not None:
        return _export_to_dir(domain, filename, json_bytes)

    return _export_to_gcs(domain, filename, json_bytes)


def export_binary(
    domain: str,
    filename: str,
    data: bytes,
) -> dict[str, str]:
    """Export binary data (e.g., activity files) and return a reference.

    Args:
        domain: Data domain (e.g., 'activities')
        filename: Output filename (e.g., 'activity_12345.fit')
        data: Raw bytes to export

    Returns:
        dict with 'path' or 'url'

    """
    if _data_dir is not None:
        return _export_binary_to_dir(domain, filename, data)

    return _export_binary_to_gcs(filename, data)


def _export_to_dir(domain: str, filename: str, json_bytes: bytes) -> dict[str, str]:
    """Write JSON data to the local data directory."""
    assert _data_dir is not None  # noqa: S101
    base = Path(_data_dir) / ".garmin-connect" / "data" / domain
    base.mkdir(parents=True, exist_ok=True)
    filepath = base / filename
    filepath.write_bytes(json_bytes)
    # Return relative path from data_dir
    rel_path = filepath.relative_to(Path(_data_dir))
    logger.debug("Exported to %s", rel_path)
    return {"path": str(rel_path)}


def _export_to_gcs(domain: str, filename: str, json_bytes: bytes) -> dict[str, str]:
    """Write JSON data to GCS via jons-mcp-file-server."""
    from jons_mcp_file_server import get_file_server

    server = get_file_server(backend="gcs")
    with tempfile.NamedTemporaryFile(
        suffix=".json", prefix=f"{domain}_", delete=False
    ) as tmp:
        tmp.write(json_bytes)
        tmp_path = tmp.name

    registration = server.register_download(tmp_path, filename)
    logger.debug("Exported to GCS: %s", registration["url"])
    return {"url": registration["url"]}


def _export_binary_to_dir(domain: str, filename: str, data: bytes) -> dict[str, str]:
    """Write binary data to the local data directory."""
    assert _data_dir is not None  # noqa: S101
    base = Path(_data_dir) / ".garmin-connect" / "data" / domain
    base.mkdir(parents=True, exist_ok=True)
    filepath = base / filename
    filepath.write_bytes(data)
    rel_path = filepath.relative_to(Path(_data_dir))
    return {"path": str(rel_path)}


def _export_binary_to_gcs(filename: str, data: bytes) -> dict[str, str]:
    """Write binary data to GCS via jons-mcp-file-server."""
    from jons_mcp_file_server import get_file_server

    server = get_file_server(backend="gcs")
    with tempfile.NamedTemporaryFile(prefix="garmin_", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    registration = server.register_download(tmp_path, filename)
    return {"url": registration["url"]}
