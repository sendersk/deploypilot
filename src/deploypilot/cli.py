"""Command-line interface for DeployPilot."""

from typing import Annotated

import typer

from deploypilot import __version__

app = typer.Typer(
    name="deploypilot",
    help="Orchestrate deployment workflows.",
    no_args_is_help=False,
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Display the application version and exit when requested."""
    if value:
        typer.echo(f"DeployPilot version {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
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
    if ctx.invoked_subcommand is None and version is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(code=0)