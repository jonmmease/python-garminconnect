"""Activity management commands for garminconnect CLI."""

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from garminconnect import Garmin

from .formatters import format_output
from .utils import handle_api_error, parse_date, require_auth


@click.group()
def activities() -> None:
    """Activity management commands."""


@activities.command(name="list")
@click.option("--limit", default=20, type=int, help="Number of activities to fetch")
@click.option("--start", default=0, type=int, help="Start index")
@click.option("--type", "activitytype", help="Filter by activity type")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def list_activities(
    ctx: click.Context, limit: int, start: int, activitytype: str | None, as_json: bool
) -> None:
    """List activities with optional filtering.

    Examples:
        garmin activities list --limit 10
        garmin activities list --type running --json

    """
    client: Garmin = ctx.obj["client"]

    try:
        activities = client.get_activities(start=start, limit=limit, activitytype=activitytype)
        click.echo(format_output(activities, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@activities.command(name="get")
@click.argument("activity_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def get_activity(ctx: click.Context, activity_id: str, as_json: bool) -> None:
    """Get activity summary and details.

    Fetches both basic activity info and detailed statistics.
    """
    client: Garmin = ctx.obj["client"]

    try:
        activity = client.get_activity(activity_id)
        details = client.get_activity_details(activity_id)

        # Merge basic info and details
        combined = {**activity, "details": details}
        click.echo(format_output(combined, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@activities.command(name="download")
@click.argument("activity_id")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["fit", "tcx", "gpx", "kml", "csv"], case_sensitive=False),
    default="fit",
    help="Download format",
)
@click.option("-o", "--output", "output_file", type=click.Path(), help="Output file path")
@click.pass_context
@require_auth
def download(ctx: click.Context, activity_id: str, fmt: str, output_file: str | None) -> None:
    """Download activity file.

    Without -o, generates descriptive filename: {date}_{name}_{id}.{format}

    Examples:
        garmin activities download 12345678 --format gpx
        garmin activities download 12345678 -o my_run.fit

    """
    client: Garmin = ctx.obj["client"]

    try:
        # Get activity details for smart naming
        if output_file is None:
            activity = client.get_activity(activity_id)
            name = activity.get("activityName", "activity").replace(" ", "_").replace("/", "-")
            date_str = activity.get("startTimeLocal", "")[:10]  # YYYY-MM-DD
            output_file = f"{date_str}_{name}_{activity_id}.{fmt.lower()}"

        # Map format string to enum
        fmt_upper = fmt.upper()
        if fmt_upper == "FIT":
            dl_fmt = client.ActivityDownloadFormat.ORIGINAL
        elif fmt_upper == "TCX":
            dl_fmt = client.ActivityDownloadFormat.TCX
        elif fmt_upper == "GPX":
            dl_fmt = client.ActivityDownloadFormat.GPX
        elif fmt_upper == "KML":
            dl_fmt = client.ActivityDownloadFormat.KML
        elif fmt_upper == "CSV":
            dl_fmt = client.ActivityDownloadFormat.CSV
        else:
            raise ValueError(f"Unknown format: {fmt}")

        # Download data
        data = client.download_activity(activity_id, dl_fmt=dl_fmt)

        # Write to file
        from pathlib import Path

        Path(output_file).write_bytes(data)

        click.echo(f"Downloaded: {output_file}", err=True)

    except Exception as e:
        handle_api_error(e)


@activities.command(name="upload")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def upload(ctx: click.Context, file_path: str, as_json: bool) -> None:
    """Upload activity file (FIT, GPX, or TCX format).

    Example:
        garmin activities upload my_run.fit

    """
    client: Garmin = ctx.obj["client"]

    try:
        result = client.upload_activity(file_path)
        click.echo(format_output(result, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@activities.command(name="delete")
@click.argument("activity_id")
@click.confirmation_option(prompt="Are you sure you want to delete this activity?")
@click.pass_context
@require_auth
def delete(ctx: click.Context, activity_id: str) -> None:
    """Delete an activity.

    Requires confirmation before deletion.
    """
    client: Garmin = ctx.obj["client"]

    try:
        client.delete_activity(activity_id)
        click.echo(f"Activity {activity_id} deleted successfully", err=True)
    except Exception as e:
        handle_api_error(e)


@activities.command(name="by-date")
@click.argument("start_date")
@click.argument("end_date")
@click.option("--type", "activitytype", help="Filter by activity type")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def by_date(
    ctx: click.Context, start_date: str, end_date: str, activitytype: str | None, as_json: bool
) -> None:
    """Get activities between two dates.

    Dates support: YYYY-MM-DD, 'today', 'yesterday', '-N' (days ago)

    Examples:
        garmin activities by-date 2024-01-01 2024-01-31
        garmin activities by-date -7 today --type running

    """
    client: Garmin = ctx.obj["client"]

    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        activities = client.get_activities_by_date(start, end, activitytype)
        click.echo(format_output(activities, as_json=as_json))
    except ValueError as e:
        raise click.ClickException(str(e)) from e
    except Exception as e:
        handle_api_error(e)


@activities.command(name="for-date")
@click.argument("date_str")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def for_date(ctx: click.Context, date_str: str, as_json: bool) -> None:
    """Get activities for a specific date.

    Date supports: YYYY-MM-DD, 'today', 'yesterday', '-N' (days ago)

    Examples:
        garmin activities for-date today
        garmin activities for-date -1
        garmin activities for-date 2024-01-15

    """
    client: Garmin = ctx.obj["client"]

    try:
        parsed_date = parse_date(date_str)
        activities = client.get_activities_fordate(parsed_date)
        click.echo(format_output(activities, as_json=as_json))
    except ValueError as e:
        raise click.ClickException(str(e)) from e
    except Exception as e:
        handle_api_error(e)


@activities.command(name="types")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def types(ctx: click.Context, as_json: bool) -> None:
    """Get all available activity types."""
    client: Garmin = ctx.obj["client"]

    try:
        activity_types = client.get_activity_types()
        click.echo(format_output(activity_types, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@activities.command(name="first-last")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def first_last(ctx: click.Context, as_json: bool) -> None:
    """Get first and last activity IDs and dates."""
    client = ctx.obj["client"]

    try:
        result = client.get_activities_first_last()
        click.echo(format_output(result, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@activities.command(name="splits")
@click.argument("activity_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def splits(ctx: click.Context, activity_id: str, as_json: bool) -> None:
    """Get activity splits (e.g., per-kilometer or per-mile data)."""
    client: Garmin = ctx.obj["client"]

    try:
        splits_data = client.get_activity_splits(activity_id)
        click.echo(format_output(splits_data, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@activities.command(name="typed-splits")
@click.argument("activity_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def typed_splits(ctx: click.Context, activity_id: str, as_json: bool) -> None:
    """Get typed activity splits with more detailed breakdown."""
    client: Garmin = ctx.obj["client"]

    try:
        splits_data = client.get_activity_typed_splits(activity_id)
        click.echo(format_output(splits_data, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@activities.command(name="weather")
@click.argument("activity_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def weather(ctx: click.Context, activity_id: str, as_json: bool) -> None:
    """Get weather data for an activity."""
    client: Garmin = ctx.obj["client"]

    try:
        weather_data = client.get_activity_weather(activity_id)
        click.echo(format_output(weather_data, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@activities.command(name="hr-zones")
@click.argument("activity_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def hr_zones(ctx: click.Context, activity_id: str, as_json: bool) -> None:
    """Get heart rate time in zones for an activity."""
    client: Garmin = ctx.obj["client"]

    try:
        hr_data = client.get_activity_hr_in_timezones(activity_id)
        click.echo(format_output(hr_data, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@activities.command(name="gear")
@click.argument("activity_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def gear(ctx: click.Context, activity_id: str, as_json: bool) -> None:
    """Get gear used for an activity."""
    client: Garmin = ctx.obj["client"]

    try:
        gear_data = client.get_activity_gear(activity_id)
        click.echo(format_output(gear_data, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@activities.command(name="set-name")
@click.argument("activity_id")
@click.argument("name")
@click.pass_context
@require_auth
def set_name(ctx: click.Context, activity_id: str, name: str) -> None:
    """Set activity name.

    Example:
        garmin activities set-name 12345678 "Morning Run"

    """
    client: Garmin = ctx.obj["client"]

    try:
        client.set_activity_name(activity_id, name)
        click.echo(f"Activity {activity_id} renamed to: {name}", err=True)
    except Exception as e:
        handle_api_error(e)


@activities.command(name="set-type")
@click.argument("activity_id")
@click.argument("type_id", type=int)
@click.argument("type_key")
@click.argument("parent_type_id", type=int)
@click.pass_context
@require_auth
def set_type(
    ctx: click.Context, activity_id: str, type_id: int, type_key: str, parent_type_id: int
) -> None:
    """Set activity type.

    Requires type_id, type_key, and parent_type_id. Use 'activities types' to see available types.

    Example:
        garmin activities set-type 12345678 1 running 17

    """
    client = ctx.obj["client"]

    try:
        client.set_activity_type(activity_id, type_id, type_key, parent_type_id)
        click.echo(f"Activity {activity_id} type set to: {type_key} (ID: {type_id})", err=True)
    except Exception as e:
        handle_api_error(e)
