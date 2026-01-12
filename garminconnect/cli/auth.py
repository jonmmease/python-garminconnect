"""Authentication commands for Garmin Connect CLI."""

import click

from garminconnect import Garmin, GarminConnectAuthenticationError

from .utils import clear_tokens, get_token_dir, tokens_exist


def prompt_mfa() -> str:
    """Prompt user for MFA code."""
    click.echo("\nMulti-Factor Authentication required.", err=True)
    click.echo(
        "Check your email or authenticator app for the verification code.", err=True
    )
    return click.prompt("Enter MFA code", type=str)


@click.group()
def cli() -> None:
    """Authentication management."""


@cli.command()
@click.option("--email", prompt=True, help="Garmin Connect email")
@click.option(
    "--password", prompt=True, hide_input=True, help="Garmin Connect password"
)
def login(email: str, password: str) -> None:
    """Authenticate with Garmin Connect and store tokens.

    Tokens are saved to ~/.garminconnect/ (or GARMINTOKENS path).
    These tokens are shared with the python library.
    """
    token_dir = get_token_dir()

    try:
        client = Garmin(email, password, prompt_mfa=prompt_mfa)
        client.login()

        # Garth saves tokens during login, ensure they're in our location
        client.garth.dump(str(token_dir))

        click.echo("\nAuthentication successful!", err=True)
        click.echo(f"Tokens saved to: {token_dir}", err=True)
        click.echo(f"Logged in as: {client.display_name}", err=True)

    except GarminConnectAuthenticationError as e:
        raise click.ClickException(f"Authentication failed: {e}") from e


@cli.command()
def logout() -> None:
    """Remove stored authentication tokens."""
    if not tokens_exist():
        click.echo("No tokens found.", err=True)
        return

    clear_tokens()
    click.echo("Tokens removed.", err=True)


@cli.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def status(as_json: bool) -> None:
    """Show current authentication status."""
    token_dir = get_token_dir()
    has_tokens = tokens_exist()

    if as_json:
        import json

        result = {
            "authenticated": has_tokens,
            "token_dir": str(token_dir),
        }

        if has_tokens:
            try:
                client = Garmin()
                client.login()
                result["display_name"] = client.display_name
                result["valid"] = True
            except Exception:
                result["valid"] = False

        click.echo(json.dumps(result, indent=2))
        return

    if has_tokens:
        try:
            client = Garmin()
            client.login()
            click.echo(f"Authenticated as: {client.display_name}", err=True)
            click.echo(f"Token location: {token_dir}", err=True)
        except Exception:
            click.echo("Tokens exist but may be expired", err=True)
            click.echo("Run: garmin auth login", err=True)
    else:
        click.echo("Not authenticated", err=True)
        click.echo("Run: garmin auth login", err=True)
