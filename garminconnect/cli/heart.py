"""Heart rate commands for Garmin Connect CLI."""

from typing import Any

import click

from .formatters import format_output
from .utils import handle_api_error, parse_date, require_auth


@click.group()
def cli() -> None:
    """Heart rate and HRV data."""


@cli.command()
@click.argument("date", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def rates(ctx: click.Context, date: str, as_json: bool) -> None:
    """Get heart rate data for a date.

    DATE: Date in format YYYY-MM-DD, 'today', 'yesterday', or -N for N days ago.

    Examples:
      garmin heart rates                  # Today's heart rate data
      garmin heart rates 2024-01-15       # Specific date
      garmin heart rates yesterday        # Yesterday's data
      garmin heart rates -7               # 7 days ago

    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:
        data = client.get_heart_rates(parsed_date)
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@cli.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def zones(ctx: click.Context, as_json: bool) -> None:
    """Get heart rate zone configuration.

    Returns heart rate zone thresholds configured for the user,
    including zones 1-5 with floor values for each sport type.

    Examples:
      garmin heart zones                  # Get HR zone configuration
      garmin heart zones --json           # JSON output

    """
    client = ctx.obj["client"]

    try:
        data = client.get_heart_rate_zones()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@cli.command()
@click.argument("date", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def resting(ctx: click.Context, date: str, as_json: bool) -> None:
    """Get resting heart rate for a date.

    Extracts resting heart rate from the heart rate data for a specific date.

    DATE: Date in format YYYY-MM-DD, 'today', 'yesterday', or -N for N days ago.

    Examples:
      garmin heart resting                # Today's resting HR
      garmin heart resting 2024-01-15     # Specific date
      garmin heart resting -1             # Yesterday

    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:
        data = client.get_heart_rates(parsed_date)

        # Extract resting heart rate from the response
        if data and "restingHeartRate" in data:
            resting_hr: dict[str, Any] = {
                "date": parsed_date,
                "restingHeartRate": data["restingHeartRate"]
            }
            # Include additional metadata if available
            if "lastSevenDaysAvgRestingHeartRate" in data:
                resting_hr["lastSevenDaysAvg"] = data["lastSevenDaysAvgRestingHeartRate"]

            click.echo(format_output(resting_hr, as_json))
        else:
            click.echo(f"No resting heart rate data available for {parsed_date}")
    except Exception as e:
        handle_api_error(e)


@cli.command()
@click.argument("date", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def hrv(ctx: click.Context, date: str, as_json: bool) -> None:
    """Get Heart Rate Variability (HRV) data for a date.

    DATE: Date in format YYYY-MM-DD, 'today', 'yesterday', or -N for N days ago.

    Examples:
      garmin heart hrv                    # Today's HRV data
      garmin heart hrv 2024-01-15         # Specific date
      garmin heart hrv yesterday          # Yesterday's data
      garmin heart hrv -7                 # 7 days ago

    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:
        data = client.get_hrv_data(parsed_date)
        if data is None:
            click.echo(f"No HRV data available for {parsed_date}")
        else:
            click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@cli.command(name="hrv-range")
@click.argument("start")
@click.argument("end")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def hrv_range(ctx: click.Context, start: str, end: str, as_json: bool) -> None:
    """Get HRV summary data for a date range.

    Provides daily HRV statistics over a date range, useful for
    tracking HRV trends and recovery patterns.

    START: Start date in format YYYY-MM-DD, 'today', 'yesterday', or -N
    END: End date in format YYYY-MM-DD, 'today', 'yesterday', or -N

    Examples:
      garmin heart hrv-range 2024-01-01 2024-01-31    # January 2024
      garmin heart hrv-range -30 today                # Last 30 days
      garmin heart hrv-range -7 -1                    # Last week

    """
    client = ctx.obj["client"]
    start_date = parse_date(start)
    end_date = parse_date(end)

    try:
        data = client.get_hrv_summary(start_date, end_date)
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)
