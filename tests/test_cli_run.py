"""Tests for the workflow execution CLI command."""

from pathlib import Path
from unittest.mock import MagicMock

from typer.testing import CliRunner

from deploypilot.cli import app
from deploypilot.results import (
    StepResult,
    StepStatus,
    WorkflowResult,
    WorkflowStatus,
)

runner = CliRunner()


def create_workflow_file(tmp_path: Path) -> Path:
    """Create a minimal valid workflow file."""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text(
        "name: test-workflow\n"
        "steps:\n"
        "  - name: test-step\n"
        "    type: command\n"
        "    command: [python, --version]\n",
        encoding="utf-8",
    )
    return workflow_file


def test_run_displays_successful_workflow(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Display the summary when workflow execution succeeds."""
    workflow_file = create_workflow_file(tmp_path)
    result = WorkflowResult(
        workflow_name="test-workflow",
        steps=[
            StepResult(
                step_name="test-step",
                status=StepStatus.SUCCEEDED,
                duration_seconds=0.25,
                message="Command completed successfully.",
                exit_code=0,
            )
        ],
        status=WorkflowStatus.SUCCEEDED,
        duration_seconds=0.25,
    )
    executor = MagicMock()
    executor.execute.return_value = result
    monkeypatch.setattr(
        "deploypilot.cli.WorkflowExecutor",
        lambda: executor,
    )

    response = runner.invoke(app, ["run", str(workflow_file)])

    assert response.exit_code == 0
    assert "Workflow: test-workflow" in response.stdout
    assert "Status: succeeded" in response.stdout
    assert "[succeeded] test-step" in response.stdout
    executor.execute.assert_called_once()


def test_run_returns_one_when_workflow_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Return a non-zero exit code when a workflow fails."""
    workflow_file = create_workflow_file(tmp_path)
    result = WorkflowResult(
        workflow_name="test-workflow",
        steps=[
            StepResult(
                step_name="test-step",
                status=StepStatus.FAILED,
                duration_seconds=0.1,
                message="Command returned a non-zero exit code.",
                exit_code=1,
            )
        ],
        status=WorkflowStatus.FAILED,
        duration_seconds=0.1,
    )
    executor = MagicMock()
    executor.execute.return_value = result
    monkeypatch.setattr(
        "deploypilot.cli.WorkflowExecutor",
        lambda: executor,
    )

    response = runner.invoke(app, ["run", str(workflow_file)])

    assert response.exit_code == 1
    assert "Status: failed" in response.stdout
    assert "[failed] test-step" in response.stdout


def test_run_handles_missing_workflow_file(tmp_path: Path) -> None:
    """Report a readable error when the workflow file is missing."""
    missing_file = tmp_path / "missing.yaml"

    response = runner.invoke(app, ["run", str(missing_file)])

    assert response.exit_code == 1
    assert "Error:" in response.output


def test_run_rejects_invalid_workflow_file(tmp_path: Path) -> None:
    """Report a readable error when the workflow file is invalid."""
    workflow_file = tmp_path / "invalid.yaml"
    workflow_file.write_text("steps: [", encoding="utf-8")

    response = runner.invoke(app, ["run", str(workflow_file)])

    assert response.exit_code == 1
    assert "Error:" in response.output
