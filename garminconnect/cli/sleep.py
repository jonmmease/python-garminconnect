"""Sleep data commands for Garmin Connect CLI."""

import click

from .formatters import format_output
from .utils import handle_api_error, parse_date, require_auth


@click.group()
def cli() -> None:
    """Sleep data and statistics."""


@cli.command()
@click.argument("date", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def data(ctx: click.Context, date: str, as_json: bool) -> None:
    """Get sleep data for a date.

    DATE can be:
      - 'today' (default)
      - 'yesterday'
      - '-N' (N days ago, e.g., '-7' for a week ago)
      - 'YYYY-MM-DD' (specific date)

    Examples:
      garminconnect sleep data
      garminconnect sleep data yesterday
      garminconnect sleep data 2024-01-15
      garminconnect sleep data -7 --json

    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:
        result = client.get_sleep_data(parsed_date)
        click.echo(format_output(result, as_json))
    except Exception as e:
        handle_api_error(e)


@cli.command()
@click.argument("start")
@click.argument("end")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def stats(ctx: click.Context, start: str, end: str, as_json: bool) -> None:
    """Get sleep statistics for a date range.

    START and END can be:
      - 'today', 'yesterday'
      - '-N' (N days ago)
      - 'YYYY-MM-DD' (specific date)

    Examples:
      garminconnect sleep stats -7 today
      garminconnect sleep stats 2024-01-01 2024-01-31
      garminconnect sleep stats yesterday today --json

    """
    client = ctx.obj["client"]
    parsed_start = parse_date(start)
    parsed_end = parse_date(end)

    try:
        result = client.get_sleep_stats(parsed_start, parsed_end)
        click.echo(format_output(result, as_json))
    except Exception as e:
        handle_api_error(e)


@cli.command("add-note")
@click.argument("date")
@click.argument("note")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def add_note(ctx: click.Context, date: str, note: str, as_json: bool) -> None:
    """Add a note to sleep data for a date.

    DATE can be:
      - 'today'
      - 'yesterday'
      - '-N' (N days ago)
      - 'YYYY-MM-DD' (specific date)

    NOTE is the text to add to the sleep entry.

    Examples:
      garminconnect sleep add-note today "Woke up feeling refreshed"
      garminconnect sleep add-note 2024-01-15 "Had trouble falling asleep"
      garminconnect sleep add-note yesterday "Interrupted sleep due to noise"

    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:
        result = client.set_sleep_note(parsed_date, note)
        click.echo(format_output(result, as_json))
    except Exception as e:
        handle_api_error(e)
