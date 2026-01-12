"""Device commands for Garmin Connect CLI."""

import click

from .formatters import format_output
from .utils import handle_api_error, parse_date, require_auth


@click.group(name="devices")
def cli() -> None:
    """Device information and management."""


@cli.command(name="list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def list_devices(ctx: click.Context, as_json: bool) -> None:
    """List registered devices."""
    client = ctx.obj["client"]

    try:
        data = client.get_devices()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@cli.command(name="settings")
@click.argument("device_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def device_settings(ctx: click.Context, device_id: str, as_json: bool) -> None:
    """Get device settings by ID."""
    client = ctx.obj["client"]

    try:
        data = client.get_device_settings(device_id)
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@cli.command(name="primary")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def primary_device(ctx: click.Context, as_json: bool) -> None:
    """Get primary training device."""
    client = ctx.obj["client"]

    try:
        data = client.get_primary_training_device()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@cli.command(name="alarms")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def device_alarms(ctx: click.Context, as_json: bool) -> None:
    """List device alarms."""
    client = ctx.obj["client"]

    try:
        data = client.get_device_alarms()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@cli.command(name="last-used")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def last_used_device(ctx: click.Context, as_json: bool) -> None:
    """Get last used device."""
    client = ctx.obj["client"]

    try:
        data = client.get_device_last_used()
        click.echo(format_output(data, as_json))
    except Exception as e:
        handle_api_error(e)


@cli.command(name="solar")
@click.argument("device_id")
@click.argument("start", required=False)
@click.argument("end", required=False)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def solar_data(
    ctx: click.Context, device_id: str, start: str | None, end: str | None, as_json: bool
) -> None:
    """Get solar data for device.

    Arguments:
        DEVICE_ID: Device identifier
        START: Start date (optional, format: YYYY-MM-DD, 'today', 'yesterday', '-N')
        END: End date (optional, format: YYYY-MM-DD, 'today', 'yesterday', '-N')

    """
    client = ctx.obj["client"]

    try:
        # Parse date arguments if provided
        start_date = parse_date(start) if start else None
        end_date = parse_date(end) if end else None

        data = client.get_solar_data(device_id, start_date, end_date)
        click.echo(format_output(data, as_json))
    except ValueError as e:
        raise click.ClickException(str(e)) from e
    except Exception as e:
        handle_api_error(e)
