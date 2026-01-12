"""Tests for Garmin Connect CLI."""

import json
import os
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from garminconnect import GarminConnectAuthenticationError
from garminconnect.cli.auth import cli as auth_cli
from garminconnect.cli.formatters import format_output
from garminconnect.cli.utils import (
    clear_tokens,
    get_token_dir,
    parse_date,
    tokens_exist,
)


class TestDateParsing:
    """Test date parsing utilities."""

    def test_parse_today(self) -> None:
        """Test 'today' parses to current date."""
        result = parse_date("today")
        assert result == date.today().strftime("%Y-%m-%d")

    def test_parse_today_case_insensitive(self) -> None:
        """Test 'TODAY' parses to current date."""
        result = parse_date("TODAY")
        assert result == date.today().strftime("%Y-%m-%d")

    def test_parse_yesterday(self) -> None:
        """Test 'yesterday' parses to previous day."""
        result = parse_date("yesterday")
        expected = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        assert result == expected

    def test_parse_yesterday_case_insensitive(self) -> None:
        """Test 'YESTERDAY' parses to previous day."""
        result = parse_date("YESTERDAY")
        expected = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        assert result == expected

    def test_parse_negative_offset_one_day(self) -> None:
        """Test -1 parses to yesterday."""
        result = parse_date("-1")
        expected = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        assert result == expected

    def test_parse_negative_offset_seven_days(self) -> None:
        """Test -7 parses to 7 days ago."""
        result = parse_date("-7")
        expected = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
        assert result == expected

    def test_parse_negative_offset_thirty_days(self) -> None:
        """Test -30 parses to 30 days ago."""
        result = parse_date("-30")
        expected = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        assert result == expected

    def test_parse_specific_date(self) -> None:
        """Test specific YYYY-MM-DD date."""
        result = parse_date("2024-03-15")
        assert result == "2024-03-15"

    def test_parse_specific_date_leap_year(self) -> None:
        """Test leap year date."""
        result = parse_date("2024-02-29")
        assert result == "2024-02-29"

    def test_parse_invalid_date_format(self) -> None:
        """Test invalid date format raises ValueError."""
        with pytest.raises(ValueError, match=r"Invalid date.*Use YYYY-MM-DD"):
            parse_date("03/15/2024")

    def test_parse_invalid_date_string(self) -> None:
        """Test invalid date string raises ValueError."""
        with pytest.raises(ValueError, match=r"Invalid date.*Use YYYY-MM-DD"):
            parse_date("not-a-date")

    def test_parse_invalid_leap_year_date(self) -> None:
        """Test invalid leap year date raises ValueError."""
        with pytest.raises(ValueError, match=r"Invalid date.*Use YYYY-MM-DD"):
            parse_date("2023-02-29")

    def test_parse_invalid_month(self) -> None:
        """Test invalid month raises ValueError."""
        with pytest.raises(ValueError, match=r"Invalid date.*Use YYYY-MM-DD"):
            parse_date("2024-13-01")

    def test_parse_invalid_day(self) -> None:
        """Test invalid day raises ValueError."""
        with pytest.raises(ValueError, match=r"Invalid date.*Use YYYY-MM-DD"):
            parse_date("2024-04-31")


class TestOutputFormatting:
    """Test output formatting."""

    def test_format_dict_as_json(self) -> None:
        """Test dict formatting as JSON."""
        data = {"key": "value", "number": 42}
        result = format_output(data, as_json=True)
        parsed = json.loads(result)
        assert parsed == data

    def test_format_dict_with_nested_data_as_json(self) -> None:
        """Test dict with nested data as JSON."""
        data = {"key": "value", "nested": {"inner": 123}, "list": [1, 2, 3]}
        result = format_output(data, as_json=True)
        parsed = json.loads(result)
        assert parsed == data

    def test_format_dict_as_table(self) -> None:
        """Test dict formatting as table."""
        data = {"key": "value", "number": 42}
        result = format_output(data, as_json=False)
        assert "key" in result
        assert "value" in result
        assert "number" in result
        assert "42" in result

    def test_format_dict_excludes_private_fields(self) -> None:
        """Test dict formatting excludes private fields in table mode."""
        data = {"key": "value", "userProfileId": 12345, "uuid": "abc-123"}
        result = format_output(data, as_json=False)
        assert "key" in result
        assert "value" in result
        assert "userProfileId" not in result
        assert "uuid" not in result

    def test_format_dict_includes_private_fields_in_json(self) -> None:
        """Test dict formatting includes private fields in JSON mode."""
        data = {"key": "value", "userProfileId": 12345}
        result = format_output(data, as_json=True)
        parsed = json.loads(result)
        assert parsed["userProfileId"] == 12345

    def test_format_list_as_json(self) -> None:
        """Test list formatting as JSON."""
        data = [{"a": 1}, {"a": 2}]
        result = format_output(data, as_json=True)
        parsed = json.loads(result)
        assert parsed == data

    def test_format_list_of_dicts_as_table(self) -> None:
        """Test list of dicts as table."""
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        result = format_output(data, as_json=False)
        assert "name" in result
        assert "age" in result
        assert "Alice" in result
        assert "Bob" in result

    def test_format_empty_list(self) -> None:
        """Test empty list returns 'No data'."""
        result = format_output([], as_json=False)
        assert result == "No data."

    def test_format_empty_list_as_json(self) -> None:
        """Test empty list as JSON returns []."""
        result = format_output([], as_json=True)
        assert json.loads(result) == []

    def test_format_none(self) -> None:
        """Test None handling in table mode."""
        result = format_output(None, as_json=False)
        assert result == "No data."

    def test_format_none_as_json(self) -> None:
        """Test None handling in JSON mode."""
        result = format_output(None, as_json=True)
        assert result == "null"

    def test_format_value_bool_true(self) -> None:
        """Test boolean true formats as 'Yes'."""
        data = {"active": True}
        result = format_output(data, as_json=False)
        assert "Yes" in result

    def test_format_value_bool_false(self) -> None:
        """Test boolean false formats as 'No'."""
        data = {"active": False}
        result = format_output(data, as_json=False)
        assert "No" in result

    def test_format_value_float(self) -> None:
        """Test float formatting."""
        data = {"value": 3.14159}
        result = format_output(data, as_json=False)
        assert "3.14" in result

    def test_format_value_float_whole_number(self) -> None:
        """Test float that's a whole number formats without decimals."""
        data = {"value": 42.0}
        result = format_output(data, as_json=False)
        assert "42" in result
        assert "42.0" not in result

    def test_format_value_none_as_dash(self) -> None:
        """Test None value formats as dash in tables."""
        data = {"key": None}
        result = format_output(data, as_json=False)
        assert "-" in result


class TestTokenManagement:
    """Test token directory and token management utilities."""

    def test_get_token_dir_default(self) -> None:
        """Test default token directory is ~/.garminconnect."""
        with patch.dict(os.environ, {}, clear=True):
            token_dir = get_token_dir()
            assert token_dir == Path.home() / ".garminconnect"

    def test_get_token_dir_from_env(self, tmp_path: Path) -> None:
        """Test token directory from GARMINTOKENS env var."""
        custom_dir = tmp_path / "custom_tokens"
        with patch.dict(os.environ, {"GARMINTOKENS": str(custom_dir)}):
            token_dir = get_token_dir()
            assert token_dir == custom_dir

    def test_tokens_exist_false_when_missing(self, tmp_path: Path) -> None:
        """Test tokens_exist returns False when tokens don't exist."""
        with patch.dict(os.environ, {"GARMINTOKENS": str(tmp_path)}):
            assert not tokens_exist()

    def test_tokens_exist_false_when_partial(self, tmp_path: Path) -> None:
        """Test tokens_exist returns False when only one token exists."""
        oauth1 = tmp_path / "oauth1_token.json"
        oauth1.write_text("{}")
        with patch.dict(os.environ, {"GARMINTOKENS": str(tmp_path)}):
            assert not tokens_exist()

    def test_tokens_exist_true_when_both_present(self, tmp_path: Path) -> None:
        """Test tokens_exist returns True when both tokens exist."""
        oauth1 = tmp_path / "oauth1_token.json"
        oauth2 = tmp_path / "oauth2_token.json"
        oauth1.write_text("{}")
        oauth2.write_text("{}")
        with patch.dict(os.environ, {"GARMINTOKENS": str(tmp_path)}):
            assert tokens_exist()

    def test_clear_tokens_removes_both(self, tmp_path: Path) -> None:
        """Test clear_tokens removes both token files."""
        oauth1 = tmp_path / "oauth1_token.json"
        oauth2 = tmp_path / "oauth2_token.json"
        oauth1.write_text("{}")
        oauth2.write_text("{}")

        with patch.dict(os.environ, {"GARMINTOKENS": str(tmp_path)}):
            clear_tokens()
            assert not oauth1.exists()
            assert not oauth2.exists()

    def test_clear_tokens_handles_missing_files(self, tmp_path: Path) -> None:
        """Test clear_tokens doesn't error if tokens don't exist."""
        with patch.dict(os.environ, {"GARMINTOKENS": str(tmp_path)}):
            clear_tokens()  # Should not raise


class TestAuthCommands:
    """Test authentication CLI commands."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_auth_help(self, runner: CliRunner) -> None:
        """Test auth --help works."""
        result = runner.invoke(auth_cli, ["--help"])
        assert result.exit_code == 0
        assert "login" in result.output
        assert "logout" in result.output
        assert "status" in result.output

    def test_login_help(self, runner: CliRunner) -> None:
        """Test login --help works."""
        result = runner.invoke(auth_cli, ["login", "--help"])
        assert result.exit_code == 0
        assert "email" in result.output.lower()
        assert "password" in result.output.lower()

    @patch("garminconnect.cli.auth.Garmin")
    def test_login_success(
        self, mock_garmin_class: MagicMock, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test successful login."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.display_name = "Test User"
        mock_client.garth.dump = MagicMock()
        mock_garmin_class.return_value = mock_client

        with patch.dict(os.environ, {"GARMINTOKENS": str(tmp_path)}):
            result = runner.invoke(
                auth_cli, ["login"], input="test@example.com\npassword123\n"
            )

        assert result.exit_code == 0
        assert "Authentication successful" in result.output
        assert "Test User" in result.output
        mock_client.login.assert_called_once()

    @patch("garminconnect.cli.auth.Garmin")
    def test_login_authentication_error(
        self, mock_garmin_class: MagicMock, runner: CliRunner
    ) -> None:
        """Test login with authentication error."""
        mock_garmin_class.side_effect = GarminConnectAuthenticationError(
            "Invalid credentials"
        )

        result = runner.invoke(
            auth_cli, ["login"], input="test@example.com\nwrongpassword\n"
        )

        assert result.exit_code != 0
        assert "Authentication failed" in result.output

    def test_logout_when_no_tokens(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test logout when no tokens exist."""
        with patch.dict(os.environ, {"GARMINTOKENS": str(tmp_path)}):
            result = runner.invoke(auth_cli, ["logout"])

        assert result.exit_code == 0
        assert "No tokens found" in result.output

    def test_logout_removes_tokens(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test logout removes existing tokens."""
        oauth1 = tmp_path / "oauth1_token.json"
        oauth2 = tmp_path / "oauth2_token.json"
        oauth1.write_text("{}")
        oauth2.write_text("{}")

        with patch.dict(os.environ, {"GARMINTOKENS": str(tmp_path)}):
            result = runner.invoke(auth_cli, ["logout"])

        assert result.exit_code == 0
        assert "Tokens removed" in result.output
        assert not oauth1.exists()
        assert not oauth2.exists()

    def test_status_not_authenticated(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test status when not authenticated."""
        with patch.dict(os.environ, {"GARMINTOKENS": str(tmp_path)}):
            result = runner.invoke(auth_cli, ["status"])

        assert result.exit_code == 0
        assert "Not authenticated" in result.output
        assert "garmin auth login" in result.output

    def test_status_not_authenticated_json(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test status --json when not authenticated."""
        with patch.dict(os.environ, {"GARMINTOKENS": str(tmp_path)}):
            result = runner.invoke(auth_cli, ["status", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["authenticated"] is False
        assert "token_dir" in data

    @patch("garminconnect.cli.auth.Garmin")
    def test_status_authenticated(
        self, mock_garmin_class: MagicMock, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test status when authenticated with valid tokens."""
        oauth1 = tmp_path / "oauth1_token.json"
        oauth2 = tmp_path / "oauth2_token.json"
        oauth1.write_text("{}")
        oauth2.write_text("{}")

        mock_client = MagicMock()
        mock_client.display_name = "Test User"
        mock_garmin_class.return_value = mock_client

        with patch.dict(os.environ, {"GARMINTOKENS": str(tmp_path)}):
            result = runner.invoke(auth_cli, ["status"])

        assert result.exit_code == 0
        assert "Test User" in result.output
        assert str(tmp_path) in result.output

    @patch("garminconnect.cli.auth.Garmin")
    def test_status_authenticated_json(
        self, mock_garmin_class: MagicMock, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test status --json when authenticated with valid tokens."""
        oauth1 = tmp_path / "oauth1_token.json"
        oauth2 = tmp_path / "oauth2_token.json"
        oauth1.write_text("{}")
        oauth2.write_text("{}")

        mock_client = MagicMock()
        mock_client.display_name = "Test User"
        mock_garmin_class.return_value = mock_client

        with patch.dict(os.environ, {"GARMINTOKENS": str(tmp_path)}):
            result = runner.invoke(auth_cli, ["status", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["authenticated"] is True
        assert data["valid"] is True
        assert data["display_name"] == "Test User"

    @patch("garminconnect.cli.auth.Garmin")
    def test_status_tokens_expired(
        self, mock_garmin_class: MagicMock, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test status when tokens exist but are expired."""
        oauth1 = tmp_path / "oauth1_token.json"
        oauth2 = tmp_path / "oauth2_token.json"
        oauth1.write_text("{}")
        oauth2.write_text("{}")

        mock_garmin_class.return_value.login.side_effect = Exception("Token expired")

        with patch.dict(os.environ, {"GARMINTOKENS": str(tmp_path)}):
            result = runner.invoke(auth_cli, ["status"])

        assert result.exit_code == 0
        assert "expired" in result.output.lower()
        assert "garmin auth login" in result.output
