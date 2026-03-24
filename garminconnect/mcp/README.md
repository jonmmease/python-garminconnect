# Garmin Connect MCP Server

An MCP server exposing Garmin Connect health and fitness data to AI agents.

## Prerequisites

1. Install with MCP extras:
   ```bash
   pip install "garminconnect[mcp]"
   ```

2. Authenticate via the CLI (one-time):
   ```bash
   garmin auth login
   ```
   Tokens are stored in `~/.garminconnect/` by default.

## Usage

```bash
# Basic — inline data only
garmin-mcp

# With local file export (for Claude Code / Cowork)
garmin-mcp --data-dir /path/to/project

# With GCS export (for Claude Desktop)
GCS_BUCKET=my-bucket garmin-mcp --data-gcs
```

## Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

### Local file export mode

```json
{
  "mcpServers": {
    "garmin-connect": {
      "command": "/path/to/garmin-mcp",
      "args": ["--data-dir", "/path/to/data"]
    }
  }
}
```

### GCS export mode (for agents without filesystem access)

```json
{
  "mcpServers": {
    "garmin-connect": {
      "command": "/path/to/garmin-mcp",
      "args": ["--data-gcs"],
      "env": {
        "GCS_BUCKET": "your-gcs-bucket-name",
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/service-account.json"
      }
    }
  }
}
```

### Using a virtual environment

If installed in a venv, point to the full path:

```json
{
  "mcpServers": {
    "garmin-connect": {
      "command": "/path/to/venv/bin/garmin-mcp",
      "args": ["--data-dir", "/path/to/data"]
    }
  }
}
```

### Custom token directory

```json
{
  "mcpServers": {
    "garmin-connect": {
      "command": "/path/to/garmin-mcp",
      "args": ["--token-dir", "/path/to/tokens", "--data-dir", "/path/to/data"]
    }
  }
}
```

Or via environment variable:

```json
{
  "mcpServers": {
    "garmin-connect": {
      "command": "/path/to/garmin-mcp",
      "args": ["--data-dir", "/path/to/data"],
      "env": {
        "GARMINTOKENS": "/path/to/tokens"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `auth_status` | Check authentication and get user profile |
| `get_wellness_data` | Steps, stress, SpO2, body battery, hydration, and more (21 metrics) |
| `get_heart_data` | Heart rate, HRV, resting HR, zones |
| `get_sleep_data` | Sleep stages and statistics |
| `get_body_data` | Body composition, weigh-ins, blood pressure |
| `get_activities` | List, search, and get activity details |
| `get_nutrition_data` | Nutrition summaries, food logs, custom foods/meals |
| `get_devices` | Device info, settings, alarms |
| `get_training_data` | Workouts, training plans, personal records |
| `manage_activity` | Rename, retype, upload, download, delete activities |
| `manage_body_measurements` | Add/delete weigh-ins and blood pressure |
| `manage_nutrition` | CRUD custom foods (with images), meals, and food logs |
| `manage_wellness` | Add hydration, set sleep notes |
| `request_upload` | Get upload URL for images or activity files |

## Data Export

Read tools accept an `export` parameter. When `true`, data is written to a file and only the file reference is returned (no inline data). This keeps large datasets out of the context window.

- **`--data-dir` mode**: Files written to `<dir>/.garmin-connect/data/<domain>/`. Returns `{"export": {"path": "..."}}`.
- **`--data-gcs` mode**: Files uploaded to GCS. Returns `{"export": {"url": "..."}}`.

When `export` is `false` (default), data is returned inline as `{"data": ...}`.
