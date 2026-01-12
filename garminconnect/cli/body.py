"""Body composition commands for Garmin Connect CLI."""

import click

from .formatters import format_output
from .utils import handle_api_error, parse_date, require_auth


@click.group()
def cli() -> None:
    """Body composition and measurements."""


@cli.command()
@click.argument("date", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def stats(ctx: click.Context, date: str, as_json: bool) -> None:
    """Get body stats for a date.

    DATE: Date (today, yesterday, -N, or YYYY-MM-DD). Default: today
    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:
        data = client.get_stats_and_body(parsed_date)
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@cli.command()
@click.argument("start", default="today")
@click.argument("end", required=False)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def composition(ctx: click.Context, start: str, end: str | None, as_json: bool) -> None:
    """Get body composition data for a date range.

    START: Start date (today, yesterday, -N, or YYYY-MM-DD). Default: today

    END: End date (optional, defaults to START)
    """
    client = ctx.obj["client"]
    start_date = parse_date(start)
    end_date = parse_date(end) if end else None

    try:
        data = client.get_body_composition(start_date, end_date)
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@cli.command("weigh-ins")
@click.option("--start", "-s", default="-7", help="Start date (today, yesterday, -N, or YYYY-MM-DD)")
@click.option("--end", "-e", default="today", help="End date (today, yesterday, -N, or YYYY-MM-DD)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def weigh_ins(ctx: click.Context, start: str, end: str, as_json: bool) -> None:
    """Get weigh-ins between dates.

    Defaults to last 7 days.
    """
    client = ctx.obj["client"]
    start_date = parse_date(start)
    end_date = parse_date(end)

    try:
        data = client.get_weigh_ins(start_date, end_date)
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@cli.command("weigh-in-daily")
@click.argument("date", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def weigh_in_daily(ctx: click.Context, date: str, as_json: bool) -> None:
    """Get weigh-ins for a specific date.

    DATE: Date (today, yesterday, -N, or YYYY-MM-DD). Default: today
    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:
        data = client.get_daily_weigh_ins(parsed_date)
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@cli.command("add-weigh-in")
@click.argument("weight", type=float)
@click.option("--unit", type=click.Choice(["kg", "lbs"]), default="kg", help="Weight unit")
@click.option("--percent-fat", type=float, help="Body fat percentage")
@click.option("--percent-hydration", type=float, help="Hydration percentage")
@click.option("--bone-mass", type=float, help="Bone mass in kg")
@click.option("--muscle-mass", type=float, help="Muscle mass in kg")
@click.option("--timestamp", help="Timestamp (YYYY-MM-DDThh:mm:ss)")
@click.pass_context
@require_auth
def add_weigh_in(
    ctx: click.Context,
    weight: float,
    unit: str,
    percent_fat: float | None,
    percent_hydration: float | None,
    bone_mass: float | None,
    muscle_mass: float | None,
    timestamp: str | None,
) -> None:
    """Add a weigh-in measurement.

    WEIGHT: Weight value (in kg or lbs)

    Use --unit to specify kg or lbs. Additional body composition metrics can be
    added with optional flags.
    """
    client = ctx.obj["client"]

    try:
        # If any composition data provided, use add_body_composition
        if any([percent_fat, percent_hydration, bone_mass, muscle_mass]):
            # Convert lbs to kg if needed (add_body_composition expects kg)
            weight_kg = weight if unit == "kg" else weight * 0.453592

            data = client.add_body_composition(
                timestamp=timestamp,
                weight=weight_kg,
                percent_fat=percent_fat,
                percent_hydration=percent_hydration,
                bone_mass=bone_mass,
                muscle_mass=muscle_mass,
            )
        else:
            # Simple weigh-in without composition data
            data = client.add_weigh_in(
                weight=weight, unitKey=unit, timestamp=timestamp or ""
            )

        if data:
            click.echo(click.style("Weigh-in added successfully", fg="green"))
        else:
            click.echo(click.style("Weigh-in added (no response data)", fg="yellow"))
    except Exception as e:
        handle_api_error(e)


@cli.command("delete-weigh-in")
@click.argument("pk")
@click.argument("date", default="today")
@click.pass_context
@require_auth
def delete_weigh_in(ctx: click.Context, pk: str, date: str) -> None:
    """Delete a weigh-in measurement.

    PK: Primary key (version) of the weigh-in to delete

    DATE: Date of the weigh-in (today, yesterday, -N, or YYYY-MM-DD). Default: today
    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:
        client.delete_weigh_in(pk, parsed_date)
        click.echo(click.style("Weigh-in deleted successfully", fg="green"))
    except Exception as e:
        handle_api_error(e)


@cli.command("blood-pressure")
@click.option("--start", "-s", default="-7", help="Start date (today, yesterday, -N, or YYYY-MM-DD)")
@click.option("--end", "-e", default="today", help="End date (today, yesterday, -N, or YYYY-MM-DD)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def blood_pressure(ctx: click.Context, start: str, end: str, as_json: bool) -> None:
    """Get blood pressure measurements between dates.

    Defaults to last 7 days.
    """
    client = ctx.obj["client"]
    start_date = parse_date(start)
    end_date = parse_date(end)

    try:
        data = client.get_blood_pressure(start_date, end_date)
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@cli.command("add-blood-pressure")
@click.argument("systolic", type=int)
@click.argument("diastolic", type=int)
@click.argument("pulse", type=int)
@click.option("--notes", help="Optional notes")
@click.option("--timestamp", help="Timestamp (YYYY-MM-DDThh:mm:ss)")
@click.pass_context
@require_auth
def add_blood_pressure(
    ctx: click.Context,
    systolic: int,
    diastolic: int,
    pulse: int,
    notes: str | None,
    timestamp: str | None,
) -> None:
    """Add a blood pressure measurement.

    SYSTOLIC: Systolic pressure (70-260 mmHg)

    DIASTOLIC: Diastolic pressure (40-150 mmHg)

    PULSE: Pulse rate (20-250 bpm)
    """
    client = ctx.obj["client"]

    try:
        data = client.set_blood_pressure(
            systolic=systolic,
            diastolic=diastolic,
            pulse=pulse,
            timestamp=timestamp or "",
            notes=notes or "",
        )
        click.echo(click.style("Blood pressure added successfully", fg="green"))
        if data:
            click.echo(format_output(data, as_json=False))
    except Exception as e:
        handle_api_error(e)


@cli.command("delete-blood-pressure")
@click.argument("version")
@click.argument("date", default="today")
@click.pass_context
@require_auth
def delete_blood_pressure(ctx: click.Context, version: str, date: str) -> None:
    """Delete a blood pressure measurement.

    VERSION: Version ID of the measurement to delete

    DATE: Date of the measurement (today, yesterday, -N, or YYYY-MM-DD). Default: today
    """
    client = ctx.obj["client"]
    parsed_date = parse_date(date)

    try:
        client.delete_blood_pressure(version, parsed_date)
        click.echo(click.style("Blood pressure measurement deleted successfully", fg="green"))
    except Exception as e:
        handle_api_error(e)
