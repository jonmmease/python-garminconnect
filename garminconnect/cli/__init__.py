"""CLI package for garminconnect.

A command-line interface for interacting with Garmin Connect.
"""

import click

from .activities import activities
from .auth import cli as auth_cli
from .body import cli as body_cli
from .devices import cli as devices_cli
from .heart import cli as heart_cli
from .nutrition import nutrition
from .sleep import cli as sleep_cli
from .wellness import wellness_cli


@click.group()
@click.version_option(package_name="garminconnect")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Garmin Connect CLI - Access your Garmin data from the terminal.

    Use 'garmin auth login' to authenticate before using other commands.
    """
    ctx.ensure_object(dict)


# Register command groups
cli.add_command(auth_cli, name="auth")
cli.add_command(activities, name="activities")
cli.add_command(body_cli, name="body")
cli.add_command(devices_cli, name="devices")
cli.add_command(heart_cli, name="heart")
cli.add_command(nutrition, name="nutrition")
cli.add_command(sleep_cli, name="sleep")
cli.add_command(wellness_cli, name="wellness")


def main() -> None:
    """Entry point for the CLI."""
    cli()


__all__ = ["cli", "main"]
