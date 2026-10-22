"""Tests for command execution."""

import subprocess
from unittest.mock import MagicMock, patch

from deploypilot.results import StepStatus
from deploypilot.runner import CommandRunner


def test_run_returns_success_for_zero_exit_code() -> None:
    """Report success when a command exits with code zero."""
    completed = MagicMock(returncode=0)

    with patch("deploypilot.runner.subprocess.run", return_value=completed):
        result = CommandRunner().run("check-python", ["python", "--version"], 10)

    assert result.status == StepStatus.SUCCEEDED
    assert result.exit_code == 0
    assert result.duration_seconds >= 0


def test_run_returns_failure_for_nonzero_exit_code() -> None:
    """Report failure when a command exits with a non-zero code."""
    completed = MagicMock(returncode=1)

    with patch("deploypilot.runner.subprocess.run", return_value=completed):
        result = CommandRunner().run("check-command", ["invalid-command"], 10)

    assert result.status == StepStatus.FAILED
    assert result.exit_code == 1


def test_run_handles_timeout() -> None:
    """Report failure when a command times out."""
    with patch(
        "deploypilot.runner.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd=["slow-command"], timeout=1),
    ):
        result = CommandRunner().run("slow-step", ["slow-command"], 1)

    assert result.status == StepStatus.FAILED
    assert "timed out" in (result.message or "").lower()
    assert result.exit_code is None


def test_run_handles_execution_error() -> None:
    """Report failure when the operating system cannot start a command."""
    with patch(
        "deploypilot.runner.subprocess.run",
        side_effect=OSError("Executable not found"),
    ):
        result = CommandRunner().run("missing-command", ["missing-command"], 10)

    assert result.status == StepStatus.FAILED
    assert "Unable to execute command" in (result.message or "")


def test_run_does_not_use_shell() -> None:
    """Execute commands without invoking a shell."""
    completed = MagicMock(returncode=0)

    with patch(
        "deploypilot.runner.subprocess.run",
        return_value=completed,
    ) as mocked_run:
        CommandRunner().run("check-python", ["python", "--version"], 10)

    assert mocked_run.call_args.kwargs["shell"] is False
    assert mocked_run.call_args.args[0] == ["python", "--version"]
