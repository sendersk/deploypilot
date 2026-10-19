"""Command-line interface for DeployPilot."""

from typing import Annotated

import typer

from deploypilot import __version__

app = typer.Typer(
    name="deploypilot",
    help="Orchestrate deployment workflows.",
    no_args_is_help=True,
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Display the application version and exit when requested."""
    if value:
        typer.echo(f"DeployPilot version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show the application version and exit.",
        ),
    ] = None,
) -> None:
    """Manage and execute deployment workflows."""
