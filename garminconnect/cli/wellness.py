"""Wellness and health data commands for garminconnect CLI."""

from typing import Any

import click

from .formatters import format_output
from .resilience import api_retry
from .utils import handle_api_error, parse_date, require_auth


@click.group(name="wellness")
def wellness_cli() -> None:
    """Wellness and health data commands."""


@wellness_cli.command()
@click.argument("date", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def stats(ctx: click.Context, date: str, as_json: bool) -> None:
    """Get daily wellness stats for DATE (default: today).

    DATE can be: today, yesterday, -N (days ago), or YYYY-MM-DD
    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:

        @api_retry
        def fetch() -> dict[str, Any]:
            return client.get_stats(parsed_date)

        data = fetch()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@wellness_cli.command()
@click.argument("date", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def steps(ctx: click.Context, date: str, as_json: bool) -> None:
    """Get steps data for DATE (default: today).

    DATE can be: today, yesterday, -N (days ago), or YYYY-MM-DD
    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:

        @api_retry
        def fetch() -> list[dict[str, Any]]:
            return client.get_steps_data(parsed_date)

        data = fetch()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@wellness_cli.command()
@click.argument("start")
@click.argument("end")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def steps_daily(ctx: click.Context, start: str, end: str, as_json: bool) -> None:
    """Get daily steps data from START to END date.

    Dates can be: today, yesterday, -N (days ago), or YYYY-MM-DD
    Note: Garmin API has a 28-day limit per request.
    """
    client = ctx.obj["client"]
    parsed_start = parse_date(start)
    parsed_end = parse_date(end)

    try:

        @api_retry
        def fetch() -> list[dict[str, Any]]:
            return client.get_daily_steps(parsed_start, parsed_end)

        data = fetch()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@wellness_cli.command()
@click.argument("end", default="today")
@click.option("--weeks", default=52, help="Number of weeks to fetch (default: 52)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def steps_weekly(ctx: click.Context, end: str, weeks: int, as_json: bool) -> None:
    """Get weekly steps aggregates ending at END date (default: today).

    END can be: today, yesterday, -N (days ago), or YYYY-MM-DD
    """
    client = ctx.obj["client"]
    parsed_end = parse_date(end)

    try:

        @api_retry
        def fetch() -> list[dict[str, Any]]:
            return client.get_weekly_steps(parsed_end, weeks)

        data = fetch()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@wellness_cli.command()
@click.argument("date", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def floors(ctx: click.Context, date: str, as_json: bool) -> None:
    """Get floors climbed data for DATE (default: today).

    DATE can be: today, yesterday, -N (days ago), or YYYY-MM-DD
    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:

        @api_retry
        def fetch() -> dict[str, Any]:
            return client.get_floors(parsed_date)

        data = fetch()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@wellness_cli.command()
@click.argument("date", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def movement(ctx: click.Context, date: str, as_json: bool) -> None:
    """Get daily movement data for DATE (default: today).

    DATE can be: today, yesterday, -N (days ago), or YYYY-MM-DD
    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:

        @api_retry
        def fetch() -> dict[str, Any]:
            return client.get_daily_movement(parsed_date)

        data = fetch()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@wellness_cli.command()
@click.argument("date", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def stress(ctx: click.Context, date: str, as_json: bool) -> None:
    """Get stress data for DATE (default: today).

    DATE can be: today, yesterday, -N (days ago), or YYYY-MM-DD
    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:

        @api_retry
        def fetch() -> dict[str, Any]:
            return client.get_stress_data(parsed_date)

        data = fetch()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@wellness_cli.command()
@click.argument("end", default="today")
@click.option("--weeks", default=52, help="Number of weeks to fetch (default: 52)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def stress_weekly(ctx: click.Context, end: str, weeks: int, as_json: bool) -> None:
    """Get weekly stress aggregates ending at END date (default: today).

    END can be: today, yesterday, -N (days ago), or YYYY-MM-DD
    """
    client = ctx.obj["client"]
    parsed_end = parse_date(end)

    try:

        @api_retry
        def fetch() -> list[dict[str, Any]]:
            return client.get_weekly_stress(parsed_end, weeks)

        data = fetch()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@wellness_cli.command()
@click.argument("date", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def hydration(ctx: click.Context, date: str, as_json: bool) -> None:
    """Get hydration data for DATE (default: today).

    DATE can be: today, yesterday, -N (days ago), or YYYY-MM-DD
    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:

        @api_retry
        def fetch() -> dict[str, Any]:
            return client.get_hydration_data(parsed_date)

        data = fetch()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@wellness_cli.command()
@click.argument("ml", type=float)
@click.pass_context
@require_auth
def hydration_add(ctx: click.Context, ml: float) -> None:
    """Add hydration data in milliliters.

    ML: Amount of water in milliliters (e.g., 500)
    """
    client = ctx.obj["client"]

    try:

        @api_retry
        def add() -> Any:
            return client.add_hydration_data(ml)

        add()
        click.echo(f"Added {ml} ml of hydration data.")
    except Exception as e:
        handle_api_error(e)


@wellness_cli.command()
@click.argument("date", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def respiration(ctx: click.Context, date: str, as_json: bool) -> None:
    """Get respiration data for DATE (default: today).

    DATE can be: today, yesterday, -N (days ago), or YYYY-MM-DD
    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:

        @api_retry
        def fetch() -> dict[str, Any]:
            return client.get_respiration_data(parsed_date)

        data = fetch()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@wellness_cli.command()
@click.argument("date", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def spo2(ctx: click.Context, date: str, as_json: bool) -> None:
    """Get SpO2 (blood oxygen) data for DATE (default: today).

    DATE can be: today, yesterday, -N (days ago), or YYYY-MM-DD
    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:

        @api_retry
        def fetch() -> dict[str, Any]:
            return client.get_spo2_data(parsed_date)

        data = fetch()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@wellness_cli.command()
@click.argument("date", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def intensity_minutes(ctx: click.Context, date: str, as_json: bool) -> None:
    """Get daily intensity minutes for DATE (default: today).

    DATE can be: today, yesterday, -N (days ago), or YYYY-MM-DD
    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:

        @api_retry
        def fetch() -> dict[str, Any]:
            return client.get_intensity_minutes_data(parsed_date)

        data = fetch()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@wellness_cli.command()
@click.argument("start")
@click.argument("end")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def intensity_minutes_weekly(ctx: click.Context, start: str, end: str, as_json: bool) -> None:
    """Get weekly intensity minutes from START to END date.

    Dates can be: today, yesterday, -N (days ago), or YYYY-MM-DD
    """
    client = ctx.obj["client"]
    parsed_start = parse_date(start)
    parsed_end = parse_date(end)

    try:

        @api_retry
        def fetch() -> list[dict[str, Any]]:
            return client.get_weekly_intensity_minutes(parsed_start, parsed_end)

        data = fetch()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@wellness_cli.command()
@click.argument("date", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def body_battery(ctx: click.Context, date: str, as_json: bool) -> None:
    """Get body battery data for DATE (default: today).

    DATE can be: today, yesterday, -N (days ago), or YYYY-MM-DD
    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:

        @api_retry
        def fetch() -> list[dict[str, Any]]:
            return client.get_body_battery(parsed_date, parsed_date)

        data = fetch()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@wellness_cli.command()
@click.argument("date", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def body_battery_events(ctx: click.Context, date: str, as_json: bool) -> None:
    """Get body battery events for DATE (default: today).

    Events include sleep, activities, auto-detected activities, and naps.
    DATE can be: today, yesterday, -N (days ago), or YYYY-MM-DD
    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:

        @api_retry
        def fetch() -> list[dict[str, Any]]:
            return client.get_body_battery_events(parsed_date)

        data = fetch()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@wellness_cli.command()
@click.argument("date", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def events(ctx: click.Context, date: str, as_json: bool) -> None:
    """Get all-day events for DATE (default: today).

    Includes auto-detected activities, even if not recorded on the watch.
    DATE can be: today, yesterday, -N (days ago), or YYYY-MM-DD
    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:

        @api_retry
        def fetch() -> dict[str, Any]:
            return client.get_all_day_events(parsed_date)

        data = fetch()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)
