
"""Tests for the DeployPilot command-line interface."""

from typer.testing import CliRunner

from deploypilot import __version__
from deploypilot.cli import app

runner = CliRunner()


def test_help_displays_application_description() -> None:
    """Verify that the help output describes the application."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Orchestrate deployment workflows." in result.output


def test_version_displays_current_package_version() -> None:
    """Verify that the version option displays the package version."""
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert f"DeployPilot version {__version__}" in result.output


def test_no_arguments_displays_help() -> None:
    """Verify that invoking the CLI without arguments displays help."""
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "Usage:" in result.output
