"""Tests for the workflow validation CLI command."""

from pathlib import Path

from typer.testing import CliRunner

from deploypilot.cli import app

runner = CliRunner()


def test_validate_accepts_valid_workflow(tmp_path: Path) -> None:
    """Report successful validation for a valid workflow."""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text(
        """
name: test-deployment
steps:
  - name: verify
    type: command
    command: ["python", "--version"]
rollback_steps:
  - name: restore
    type: command
    command: ["python", "--version"]
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", str(workflow_file)])

    assert result.exit_code == 0
    assert "Workflow 'test-deployment' is valid." in result.output
    assert "Deployment steps: 1" in result.output
    assert "Rollback steps: 1" in result.output


def test_validate_rejects_missing_file(tmp_path: Path) -> None:
    """Return a nonzero exit code when the file is missing."""
    result = runner.invoke(
        app,
        ["validate", str(tmp_path / "missing.yaml")],
    )

    assert result.exit_code == 1
    assert "Error:" in result.output
    assert "Unable to read workflow file" in result.output


def test_validate_rejects_invalid_yaml(tmp_path: Path) -> None:
    """Return a nonzero exit code for malformed YAML."""
    workflow_file = tmp_path / "invalid.yaml"
    workflow_file.write_text("name: [invalid", encoding="utf-8")

    result = runner.invoke(app, ["validate", str(workflow_file)])

    assert result.exit_code == 1
    assert "Invalid YAML syntax" in result.output


def test_validate_does_not_execute_commands(tmp_path: Path) -> None:
    """Verify validation does not execute configured commands."""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text(
        """
name: safe-validation
steps:
  - name: verify
    type: command
    command: ["this-command-must-not-run"]
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", str(workflow_file)])

    assert result.exit_code == 0
    assert "is valid" in result.output


def test_validate_displays_workflow_summary(tmp_path: Path) -> None:
    """Verify that validation displays the workflow summary."""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text(
        """
name: test-deployment
steps:
  - name: check-python
    type: command
    command:
      - python
      - --version
""".strip(),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", str(workflow_file)])

    assert result.exit_code == 0
    assert "Workflow 'test-deployment' is valid." in result.output
    assert "Deployment steps: 1" in result.output
    assert "Rollback steps: 0" in result.output
