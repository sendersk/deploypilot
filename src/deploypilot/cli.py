"""Command-line interface for DeployPilot."""

from pathlib import Path
from typing import Annotated, Literal

import typer

from deploypilot import __version__
from deploypilot.loader import WorkflowLoadError, load_workflow
from deploypilot.logging_config import configure_logging
from deploypilot.results import WorkflowStatus
from deploypilot.workflow import WorkflowExecutor

app = typer.Typer(
    name="deploypilot",
    help="Orchestrate deployment workflows.",
    no_args_is_help=False,
    invoke_without_command=True,
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Display the application version and exit when requested."""
    if value:
        typer.echo(f"DeployPilot version {__version__}")
        raise typer.Exit()


@app.callback()
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
    if ctx.invoked_subcommand is None and not ctx.resilient_parsing:
        typer.echo(ctx.get_help())
        raise typer.Exit(code=0)


@app.command()
def validate(
    workflow_file: Annotated[
        Path,
        typer.Argument(
            help="Path to the YAML workflow configuration.",
            exists=False,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
) -> None:
    """Validate a workflow configuration without executing it."""
    try:
        workflow = load_workflow(workflow_file)
    except WorkflowLoadError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Workflow '{workflow.name}' is valid.")
    typer.echo(f"Deployment steps: {len(workflow.steps)}")
    typer.echo(f"Rollback steps: {len(workflow.rollback_steps)}")


@app.command()
def run(
    workflow_file: Annotated[
        Path,
        typer.Argument(help="Path to the workflow YAML file."),
    ],
    log_level: Annotated[
        Literal["DEBUG", "INFO", "WARNING", "ERROR"],
        typer.Option(
            "--log-level",
            case_sensitive=False,
            help="Set the logging level.",
        ),
    ] = "INFO",
) -> None:
    """Execute a deployment workflow."""
    try:
        workflow = load_workflow(workflow_file)
    except WorkflowLoadError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    configure_logging(log_level)

    result = WorkflowExecutor().execute(workflow)

    typer.echo(f"Workflow: {result.workflow_name}")
    typer.echo(f"Status: {result.status.value}")
    typer.echo(f"Duration: {result.duration_seconds:.2f}s")

    typer.echo("Steps:")

    for step in result.steps:
        duration = f"{step.duration_seconds:.2f}s"
        typer.echo(f"  [{step.status.value}] {step.step_name} ({duration})")
        if step.message:
            typer.echo(f"    {step.message}")

    if result.rollback_steps:
        typer.echo(f"Rollback status: {result.rollback_status.value}")
        typer.echo("Rollback:")
        for step in result.rollback_steps:
            duration = f"{step.duration_seconds:.2f}s"
            typer.echo(f"  [{step.status.value}] {step.step_name} ({duration})")
            if step.message:
                typer.echo(f"    {step.message}")

    if result.status == WorkflowStatus.FAILED:
        raise typer.Exit(code=1)
