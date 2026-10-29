"""Tests for the workflow execution CLI command."""

import json
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
        lambda **kwargs: executor,
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
        lambda **kwargs: executor,
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


def test_run_accepts_debug_log_level(tmp_path: Path, monkeypatch) -> None:
    """Accept DEBUG as a logging level."""
    workflow_file = create_workflow_file(tmp_path)
    result = WorkflowResult(
        workflow_name="test-workflow",
        steps=[
            StepResult(
                step_name="test-step",
                status=StepStatus.SUCCEEDED,
                duration_seconds=0.1,
            )
        ],
        status=WorkflowStatus.SUCCEEDED,
        duration_seconds=0.1,
    )
    executor = MagicMock()
    executor.execute.return_value = result
    monkeypatch.setattr(
        "deploypilot.cli.WorkflowExecutor",
        lambda **kwargs: executor,
    )

    response = runner.invoke(
        app,
        ["run", str(workflow_file), "--log-level", "DEBUG"],
    )

    assert response.exit_code == 0


def test_run_rejects_unsupported_log_level(tmp_path: Path) -> None:
    """Reject unsupported logging levels through the CLI."""
    workflow_file = create_workflow_file(tmp_path)

    response = runner.invoke(
        app,
        ["run", str(workflow_file), "--log-level", "TRACE"],
    )

    assert response.exit_code != 0
    assert "TRACE" in response.output


def test_run_writes_json_report(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Write the workflow summary to the requested JSON file."""
    workflow_file = create_workflow_file(tmp_path)
    report_file = tmp_path / "reports" / "deployment.json"

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
        lambda **kwargs: executor,
    )

    response = runner.invoke(
        app,
        [
            "run",
            str(workflow_file),
            "--output-json",
            str(report_file),
        ],
    )

    assert response.exit_code == 0
    assert report_file.is_file()
    report = json.loads(report_file.read_text(encoding="utf-8"))
    assert report["workflow_name"] == "test-workflow"
    assert report["status"] == "succeeded"
    assert report["steps"][0]["step_name"] == "test-step"
    assert report["rollback_steps"] == []
    assert report["rollback_status"] == "not_required"


def test_run_writes_json_report_when_workflow_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Preserve a failure report when execution fails."""
    workflow_file = create_workflow_file(tmp_path)
    report_file = tmp_path / "deployment.json"

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
        lambda **kwargs: executor,
    )

    response = runner.invoke(
        app,
        [
            "run",
            str(workflow_file),
            "--output-json",
            str(report_file),
        ],
    )

    assert response.exit_code == 1
    assert report_file.is_file()
    report = json.loads(report_file.read_text(encoding="utf-8"))
    assert report["status"] == "failed"


def test_run_reports_json_write_error(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Return an error if the JSON report cannot be written."""
    workflow_file = create_workflow_file(tmp_path)
    report_path = tmp_path / "missing-parent" / "report.json"

    result = WorkflowResult(
        workflow_name="test-workflow",
        steps=[],
        status=WorkflowStatus.SUCCEEDED,
        duration_seconds=0.0,
    )
    executor = MagicMock()
    executor.execute.return_value = result
    monkeypatch.setattr(
        "deploypilot.cli.WorkflowExecutor",
        lambda **kwargs: executor,
    )

    def fail_mkdir(*args, **kwargs) -> None:
        """Simulate a report directory creation failure."""
        raise OSError("Simulated filesystem error.")

    monkeypatch.setattr(Path, "mkdir", fail_mkdir)

    response = runner.invoke(
        app,
        ["run", str(workflow_file), "--output-json", str(report_path)],
    )

    assert response.exit_code == 1
    assert "Error: unable to write JSON report" in response.output
